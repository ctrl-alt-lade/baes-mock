import csv
import io
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from app.database import db
from app.routers.auth import get_student_record

router = APIRouter(prefix="/api/admin", tags=["Administration"])

ADMIN_PIN = "1234"


def verify_admin_pin(pin: str) -> None:
    """Validate administrator PIN. Raises 403 Forbidden if invalid."""
    if pin != ADMIN_PIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or missing administrator PIN.",
        )


@router.get("/dashboard", summary="Admin Candidate Dashboard")
async def get_admin_dashboard(
    pin: str = Query("", description="Administrator PIN for access control (e.g. ?pin=1234)")
) -> List[Dict[str, Any]]:
    """
    Fetch all student candidates and their examination results.
    
    Merges documents from the 'students' and 'results' collections:
    - matric_no (string)
    - has_taken (boolean)
    - scores (dictionary of course percentage scores, included if taken)
    - gpa (float Nigerian 5.0 scale GPA, included if taken)
    - submitted_answers (dictionary of submitted answer indices, included if taken)
    
    Requires ?pin=1234 query parameter.
    """
    verify_admin_pin(pin)

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not initialized. Please configure serviceAccountKey.json.",
        )

    # 1. Fetch all documents from 'results' collection
    results_map: Dict[str, Dict[str, Any]] = {}
    for doc in db.collection("results").stream():
        r_data = doc.to_dict() or {}
        r_matric = (r_data.get("matric_no") or doc.id).strip().upper()
        results_map[r_matric] = r_data

    # 2. Fetch all documents from 'students' collection and merge
    merged_list: List[Dict[str, Any]] = []
    seen_matrics = set()

    for doc in db.collection("students").stream():
        s_data = doc.to_dict() or {}
        raw_matric = s_data.get("matric_no") or doc.id
        s_matric = str(raw_matric).strip().upper()
        seen_matrics.add(s_matric)

        # Match against results collection
        result_item = results_map.get(s_matric)
        has_taken = bool(s_data.get("has_taken", False) or (result_item is not None))

        record: Dict[str, Any] = {
            "matric_no": raw_matric,
            "has_taken": has_taken,
        }

        # Include scores, gpa, and submitted_answers if the student has taken the exam
        if has_taken:
            record["scores"] = result_item.get("scores") if result_item else None
            record["gpa"] = result_item.get("gpa") if result_item else None
            record["submitted_answers"] = (
                result_item.get("submitted_answers") or result_item.get("answers")
            ) if result_item else None

        merged_list.append(record)

    # 3. Include any result whose matriculation number was not in students collection
    for r_matric, result_item in results_map.items():
        if r_matric not in seen_matrics:
            record = {
                "matric_no": result_item.get("matric_no") or r_matric,
                "has_taken": True,
                "scores": result_item.get("scores"),
                "gpa": result_item.get("gpa"),
                "submitted_answers": (
                    result_item.get("submitted_answers") or result_item.get("answers")
                ),
            }
            merged_list.append(record)

    # Sort sequentially by matriculation number
    merged_list.sort(key=lambda s: str(s.get("matric_no", "")))

    return merged_list


@router.get("/export", summary="Export Results to CSV")
async def export_results_csv(
    pin: str = Query("", description="Administrator PIN for access control (e.g. ?pin=1234)")
):
    """
    Stream a generated CSV file containing all candidate results from the 'results' collection.
    
    Columns included:
    - Matric Number
    - PHY 101 Score (%)
    - CHM 101 Score (%)
    - MTH 101 Score (%)
    - Final GPA (Nigerian 5-point scale)
    
    Requires ?pin=1234 query parameter.
    """
    verify_admin_pin(pin)

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not initialized. Please configure serviceAccountKey.json.",
        )

    def iter_csv_rows():
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # Write CSV header row
        writer.writerow(["Matric Number", "PHY 101", "CHM 101", "MTH 101", "Final GPA"])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        # Stream documents from results collection
        results_stream = db.collection("results").stream()
        for doc in results_stream:
            data = doc.to_dict() or {}
            matric_no = data.get("matric_no") or doc.id
            scores = data.get("scores") or {}

            # Read individual course percentage scores
            phy_score = scores.get("PHY 101", data.get("phy_101", data.get("PHY 101", 0.0)))
            chm_score = scores.get("CHM 101", data.get("chm_101", data.get("CHM 101", 0.0)))
            mth_score = scores.get("MTH 101", data.get("mth_101", data.get("MTH 101", 0.0)))
            final_gpa = data.get("gpa", 0.0)

            writer.writerow([matric_no, phy_score, chm_score, mth_score, final_gpa])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        iter_csv_rows(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=cbt_results_export.csv",
            "Cache-Control": "no-cache",
        },
    )


@router.post("/reset-student", summary="Reset Student Exam Attempt")
async def reset_student(
    matric_no: Optional[str] = Query(None, description="Candidate matriculation number to reset"),
    pin: Optional[str] = Query(None, description="Administrator PIN for access control (e.g. ?pin=1234)"),
    request: Request = None,
):
    """
    Reset a student's examination attempt.
    
    1. Validates administrator PIN (403 if invalid).
    2. Deletes candidate's record in 'results' collection if exists.
    3. Updates candidate's record in 'students' collection: sets has_taken to False.
    4. Returns confirmation response.
    """
    body_data = {}
    if request:
        try:
            body_data = await request.json()
        except Exception:
            body_data = {}

    auth_pin = pin or body_data.get("pin") or ""
    verify_admin_pin(auth_pin)

    raw_matric = matric_no or body_data.get("matric_no") or ""
    if not raw_matric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameter: matric_no",
        )

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not initialized. Please configure serviceAccountKey.json.",
        )

    clean_matric = raw_matric.strip().upper()

    # 1. In Firestore, delete results/{matric_no} if it exists
    res_ref = db.collection("results").document(clean_matric)
    if res_ref.get().exists:
        res_ref.delete()

    # Check un-uppercased doc ID as a safety precaution
    if raw_matric.strip() != clean_matric:
        alt_res_ref = db.collection("results").document(raw_matric.strip())
        if alt_res_ref.get().exists:
            alt_res_ref.delete()

    # 2. Update students/{matric_no} to set {"has_taken": False}
    student_ref, _ = get_student_record(clean_matric)
    if student_ref:
        student_ref.update({"has_taken": False})
    else:
        doc_ref = db.collection("students").document(clean_matric)
        if doc_ref.get().exists:
            doc_ref.update({"has_taken": False})
        else:
            doc_ref.set({"matric_no": clean_matric, "has_taken": False}, merge=True)

    return {"success": True, "message": f"Reset {clean_matric} successfully"}

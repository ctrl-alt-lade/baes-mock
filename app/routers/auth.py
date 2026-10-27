from fastapi import APIRouter, HTTPException, status
from app.database import db
from app.models import LoginRequest

router = APIRouter(tags=["Authentication"])


def get_student_record(matric_no: str):
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not initialized.",
        )

    clean_matric = matric_no.strip()

    # 1. Direct document ID lookup (exact or uppercase)
    doc = db.collection("students").document(clean_matric).get()
    if doc.exists:
        return doc.reference, doc.to_dict()

    doc_upper = db.collection("students").document(clean_matric.upper()).get()
    if doc_upper.exists:
        return doc_upper.reference, doc_upper.to_dict()

    # 2. Field query fallback
    query = (
        db.collection("students")
        .where("matric_no", "==", clean_matric)
        .limit(1)
        .stream()
    )
    for record in query:
        return record.reference, record.to_dict()

    query_upper = (
        db.collection("students")
        .where("matric_no", "==", clean_matric.upper())
        .limit(1)
        .stream()
    )
    for record in query_upper:
        return record.reference, record.to_dict()

    return None, None


@router.post("/login", summary="Candidate Login")
async def student_login(payload: LoginRequest):
    _, student_data = get_student_record(payload.matric_no)

    if not student_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with matric number '{payload.matric_no}' not found.",
        )

    if student_data.get("has_taken", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exam already submitted",
        )

    return {
        "status": "success",
        "message": "Login successful. You may proceed with the examination.",
        "student": {
            "matric_no": student_data.get("matric_no", payload.matric_no),
            "name": student_data.get("name", "Student"),
            "department": student_data.get("department", "Engineering"),
            "has_taken": False,
        },
    }
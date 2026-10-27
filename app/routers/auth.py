from fastapi import APIRouter, HTTPException, status
from app.database import db
from app.models import LoginRequest

router = APIRouter(prefix="/api", tags=["Authentication"])


def get_student_record(matric_no: str):
    """
    Search for a student in Firestore by document ID or 'matric_no' field.
    Returns a tuple of (document_reference, document_data_dict) or (None, None).
    """
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not initialized. Please configure serviceAccountKey.json.",
        )

    clean_matric = matric_no.strip()

    # 1. Lookup by document ID (case-sensitive and upper-cased)
    doc_ref = db.collection("students").document(clean_matric)
    doc = doc_ref.get()
    if doc.exists:
        return doc_ref, doc.to_dict()

    doc_ref_upper = db.collection("students").document(clean_matric.upper())
    doc_upper = doc_ref_upper.get()
    if doc_upper.exists:
        return doc_ref_upper, doc_upper.to_dict()

    # 2. Query where matric_no field matches
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
    """
    Authenticate candidate by matriculation number.
    
    - 200: Successfully authenticated and eligible to take the CBT exam.
    - 403: Exam has already been submitted by candidate.
    - 404: Matriculation number not found in student database.
    """
    _, student_data = get_student_record(payload.matric_no)

    if not student_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with matric number '{payload.matric_no}' not found.",
        )

    # Check if student has already submitted the exam
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

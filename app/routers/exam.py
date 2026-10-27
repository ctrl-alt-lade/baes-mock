from typing import Optional
import random
from typing import Dict, Any, Tuple, List
from fastapi import APIRouter, HTTPException, status, Query
from google.cloud import firestore
from app.database import db
from app.models import AnswerPayload
from app.routers.auth import get_student_record

router = APIRouter(prefix="/api", tags=["Examination"])

# ================= EXAM CONFIGURATION & PRESETS =================
EXAM_MODE = "35"  # Toggle between "35", "70", or "all"

PRESETS = {
    "35": {"PHY 101": 35, "CHM 101": 35, "MTH 101": 35},
    "70": {"PHY 101": 70, "CHM 101": 70, "MTH 101": 70},
    "all": None,
}

COURSE_CONFIG = {
    "PHY 101": {"units": 3, "aliases": ["PHY 101", "PHY101", "PHY", "PHYSICS", "PHYSICS 101"]},
    "CHM 101": {"units": 3, "aliases": ["CHM 101", "CHM101", "CHM", "CHEMISTRY", "CHEMISTRY 101"]},
    "MTH 101": {"units": 2, "aliases": ["MTH 101", "MTH101", "MTH", "MATHEMATICS", "MATH 101", "MATH"]},
}


def normalize_course(raw_course: str) -> str:
    """Normalize raw course title or code to standard format (e.g. 'PHY 101')."""
    if not raw_course:
        return "UNKNOWN"
    cleaned = raw_course.strip().upper()
    for standard_name, cfg in COURSE_CONFIG.items():
        if cleaned in cfg["aliases"]:
            return standard_name
    return cleaned


def calculate_grade_point(percentage: float) -> Tuple[int, str]:
    """
    Calculate Nigerian 5-point scale grade point and letter grade:
    70-100 = 5 (A)
    60-69  = 4 (B)
    50-59  = 3 (C)
    45-49  = 2 (D)
    40-44  = 1 (E)
    0-39   = 0 (F)
    """
    rounded = round(percentage, 2)
    if rounded >= 70.0:
        return 5, "A"
    elif rounded >= 60.0:
        return 4, "B"
    elif rounded >= 50.0:
        return 3, "C"
    elif rounded >= 45.0:
        return 2, "D"
    elif rounded >= 40.0:
        return 1, "E"
    else:
        return 0, "F"


def get_grouped_questions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch all exam questions from Firestore grouped by course.
    Questions within each course are sorted deterministically by document ID
    prior to sampling so seeded randomization is 100% reproducible.
    """
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not initialized. Please configure serviceAccountKey.json.",
        )

    grouped: Dict[str, List[Dict[str, Any]]] = {
        "PHY 101": [],
        "CHM 101": [],
        "MTH 101": [],
    }

    questions_stream = db.collection("questions").stream()
    for doc in questions_stream:
        raw_dict = doc.to_dict() or {}
        q_data = dict(raw_dict)
        q_data["id"] = doc.id
        raw_course = q_data.get("course") or q_data.get("course_code") or q_data.get("subject", "")
        course_name = normalize_course(raw_course)

        if course_name in grouped:
            grouped[course_name].append(q_data)

    # Sort deterministically by question ID before sampling
    for course_name in grouped:
        grouped[course_name].sort(key=lambda q: str(q.get("id", "")))

    return grouped


def select_assigned_questions(
    matric_no: str, grouped: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Select randomized subset of questions for a student based on their matric number.
    Uses rng.sample(course_questions, quota) when a quota is configured, and shuffles
    the question order per course using the seeded rng.
    """
    clean_matric = matric_no.strip().upper()
    rng = random.Random(clean_matric)
    preset = PRESETS.get(EXAM_MODE)

    assigned: Dict[str, List[Dict[str, Any]]] = {}
    for course_name in ["PHY 101", "CHM 101", "MTH 101"]:
        course_questions = grouped.get(course_name, [])
        quota = preset.get(course_name) if preset else None

        if quota is not None and quota < len(course_questions):
            sampled = rng.sample(course_questions, quota)
        else:
            sampled = list(course_questions)

        # Shuffle the question order per course using the same seeded rng
        rng.shuffle(sampled)
        assigned[course_name] = sampled

    return assigned


@router.get("/questions")
def get_questions(matric_no: Optional[str] = Query(None)):
    # Fallback to a default seed if matric_no is missing
    matric_clean = matric_no.strip().upper() if matric_no else "DEFAULT_SEED"
    """
    Fetch exam questions for candidate:
    1. Validates required matric_no query parameter.
    2. Groups questions by course and selects a seeded random subset.
    3. Shuffles question order per course.
    4. Strips out answer keys before returning to client.
    """
    clean_matric = matric_no.strip()
    if not clean_matric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="matric_no query parameter is required.",
        )

    grouped = get_grouped_questions()
    assigned_by_course = select_assigned_questions(clean_matric, grouped)

    sanitized_questions = []
    for course_name in ["PHY 101", "CHM 101", "MTH 101"]:
        for q in assigned_by_course.get(course_name, []):
            q_data = dict(q)
            # Security: Strip answer keys before returning to client
            q_data.pop("answer_index", None)
            q_data.pop("correct_answer", None)
            q_data.pop("correct_index", None)
            sanitized_questions.append(q_data)

    return {
        "status": "success",
        "total": len(sanitized_questions),
        "exam_mode": EXAM_MODE,
        "questions": sanitized_questions,
    }


@router.post("/submit", summary="Submit Exam and Compute Result")
async def submit_exam(payload: AnswerPayload):
    """
    Grade candidate submission:
    1. Verify student matriculation number and submission eligibility.
    2. Retrieve the deterministic assigned questions for this candidate.
    3. Grade submitted answers against the actual assigned questions.
    4. Calculate percentage scores based on the actual number of questions assigned
       to each course in the active EXAM_MODE (e.g. PHY: Correct / 12 * 100).
    5. Compute GPA using the Nigerian 5-point scale (PHY=3 units, CHM=3 units, MTH=2 units).
    6. Save results to 'results' collection with a server timestamp.
    7. Mark student 'has_taken' status as true.
    8. Return the graded breakdown and computed GPA.
    """
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not initialized. Please configure serviceAccountKey.json.",
        )

    clean_matric = payload.matric_no.strip()

    # 1. Verify student exists and has not submitted yet
    student_ref, student_data = get_student_record(clean_matric)
    if not student_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with matric number '{clean_matric}' not found.",
        )

    if student_data.get("has_taken", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exam already submitted",
        )

    canonical_matric = student_data.get("matric_no") or clean_matric.upper()

    # 2. Get deterministically assigned questions for this student
    grouped = get_grouped_questions()
    assigned_by_course = select_assigned_questions(canonical_matric, grouped)

    # 3. Grade answers against the student's assigned questions
    breakdown = {}
    total_quality_points = 0.0
    total_credit_units = 0

    for course_code, cfg in COURSE_CONFIG.items():
        units = cfg["units"]
        assigned_list = assigned_by_course.get(course_code, [])
        assigned_total = len(assigned_list)
        correct_count = 0

        for q in assigned_list:
            q_id = q["id"]
            correct_index = q.get("answer_index")
            if correct_index is None:
                correct_index = q.get("correct_index")

            student_choice = payload.answers.get(q_id)
            if student_choice is not None and correct_index is not None:
                if int(student_choice) == int(correct_index):
                    correct_count += 1

        # Percentage score based on actual number of questions assigned in active EXAM_MODE
        percentage = (
            round((correct_count / assigned_total) * 100.0, 2)
            if assigned_total > 0
            else 0.0
        )
        grade_point, letter_grade = calculate_grade_point(percentage)
        quality_points = grade_point * units

        total_quality_points += quality_points
        total_credit_units += units

        breakdown[course_code] = {
            "score_percentage": percentage,
            "correct_answers": correct_count,
            "total_questions": assigned_total,
            "credit_units": units,
            "grade_point": grade_point,
            "letter_grade": letter_grade,
            "quality_points": quality_points,
        }

    # 4. Compute Nigerian 5-point GPA
    final_gpa = (
        round(total_quality_points / total_credit_units, 2)
        if total_credit_units > 0
        else 0.0
    )

    # 5. Save results to 'results' collection
    result_data = {
        "matric_no": student_data.get("matric_no", clean_matric),
        "student_name": student_data.get("name", "Student"),
        "exam_mode": EXAM_MODE,
        "scores": {
            "PHY 101": breakdown["PHY 101"]["score_percentage"],
            "CHM 101": breakdown["CHM 101"]["score_percentage"],
            "MTH 101": breakdown["MTH 101"]["score_percentage"],
        },
        "grade_points": {
            "PHY 101": breakdown["PHY 101"]["grade_point"],
            "CHM 101": breakdown["CHM 101"]["grade_point"],
            "MTH 101": breakdown["MTH 101"]["grade_point"],
        },
        "gpa": final_gpa,
        "total_quality_points": total_quality_points,
        "total_credit_units": total_credit_units,
        "breakdown": breakdown,
        "submitted_answers": payload.answers,
        "submitted_at": firestore.SERVER_TIMESTAMP,
    }

    db.collection("results").document(clean_matric).set(result_data)

    # 6. Update student's has_taken status to True
    if student_ref:
        student_ref.update(
            {
                "has_taken": True,
                "exam_submitted_at": firestore.SERVER_TIMESTAMP,
            }
        )

    # 7. Return graded summary
    return {
        "status": "success",
        "message": "Exam submitted and graded successfully.",
        "matric_no": clean_matric,
        "gpa": final_gpa,
        "total_quality_points": total_quality_points,
        "total_credit_units": total_credit_units,
        "course_breakdown": breakdown,
    }

from typing import Dict
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema for candidate login request."""
    matric_no: str = Field(
        ...,
        description="Candidate matriculation or registration number",
        examples=["STU/2026/001"],
    )


class AnswerPayload(BaseModel):
    """Schema for candidate exam answer submission."""
    matric_no: str = Field(
        ...,
        description="Candidate matriculation or registration number",
        examples=["STU/2026/001"],
    )
    answers: Dict[str, int] = Field(
        ...,
        description="Key-value mapping of question IDs to selected option index (0-indexed)",
        examples=[{"q1": 2, "q2": 0, "q3": 3}],
    )

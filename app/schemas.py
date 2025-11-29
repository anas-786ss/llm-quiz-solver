from pydantic import BaseModel, HttpUrl, Field
from typing import Any, Optional, Dict

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: HttpUrl
    # allow extra fields
    class Config:
        extra = "allow"

class SubmitResponse(BaseModel):
    correct: bool
    url: Optional[str] = None
    reason: Optional[str] = None
    # other fields allowed
    class Config:
        extra = "allow"

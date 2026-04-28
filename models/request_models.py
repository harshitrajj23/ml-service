from pydantic import BaseModel, Field
from typing import List, Optional

class UserProfile(BaseModel):
    preferences: List[str] = Field(..., example=["code", "short"])
    level: str = Field(..., example="beginner")

class AskRequest(BaseModel):
    query: str = Field(..., example="How do I use async in Python?")
    user_profile: UserProfile
    user_id: Optional[str] = Field("default_user", example="user_123")

class AskResponse(BaseModel):
    answer: str
    type: str = Field(..., description="code-heavy | short | explanation")
    recommendations: List[str]

class FeedbackRequest(BaseModel):
    user_id: str
    query: str
    liked: bool
    type: str

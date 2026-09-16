from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class TicketCreate(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    order_value_inr: float | None = Field(default=None, ge=0)
    days_since_delivery: int | None = Field(default=None, ge=0)
    days_since_dispatch: int | None = Field(default=None, ge=0)
    product_type: str | None = None
    opened_status: str | None = None
    order_status: str | None = None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    action: str
    reason: str
    confidence: float
    sources: list[str]
    created_at: datetime


class TicketResponse(BaseModel):
    id: int
    message: str
    order_value_inr: float | None
    days_since_delivery: int | None
    days_since_dispatch: int | None
    product_type: str | None
    opened_status: str | None
    order_status: str | None
    created_at: datetime
    decision: DecisionResponse | None = None

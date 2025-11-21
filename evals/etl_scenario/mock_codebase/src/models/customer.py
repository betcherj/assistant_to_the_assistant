"""Customer Pydantic model."""
from typing import Optional
from pydantic import BaseModel, EmailStr


class Customer(BaseModel):
    """Customer model."""
    name: str
    reference: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


"""Order Pydantic model with domain-specific fields."""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class ShippingAddress(BaseModel):
    """Shipping address model."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = Field(..., description="Country code (required for validation)")


class OrderLineItem(BaseModel):
    """Order line item model."""
    sku: str = Field(..., description="Stock Keeping Unit (SKU) - must match inventory format")
    quantity: int = Field(..., gt=0, description="Quantity must be positive")
    unit_price: float = Field(..., gt=0, description="Unit price must be positive")


class Customer(BaseModel):
    """Customer model."""
    name: str
    reference: str = Field(..., description="Customer reference (required for validation)")
    email: Optional[str] = None


class Order(BaseModel):
    """Order model with domain-specific terminology."""
    order_id: str = Field(..., description="Purchase Order (PO) number")
    customer: Customer
    order_date: date = Field(..., description="Order date cannot be in the future")
    line_items: List[OrderLineItem]
    shipping_address: Optional[ShippingAddress] = None
    shipping_terms: Optional[str] = Field(None, description="Shipping terms (e.g., FOB Origin, FOB Destination)")
    payment_terms: Optional[str] = Field(None, description="Payment terms (e.g., Net 30, Net 60)")
    estimated_arrival: Optional[date] = Field(None, description="ETA - Estimated Time of Arrival")
    priority: Optional[str] = Field(None, description="Order priority (URGENT orders processed within 5 minutes)")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="LLM confidence score")
    validation_status: Optional[str] = Field(None, description="Validation status: valid, invalid, pending")


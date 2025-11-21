"""Product Pydantic model."""
from pydantic import BaseModel


class Product(BaseModel):
    """Product model."""
    sku: str  # Stock Keeping Unit
    name: str
    description: Optional[str] = None
    unit_price: float


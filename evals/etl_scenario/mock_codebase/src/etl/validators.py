"""Validators for extracted Pydantic models."""
from typing import List, Tuple
from ..models.order import Order


class OrderValidator:
    """Validates extracted Order models against business rules."""
    
    def validate(self, order: Order) -> Tuple[bool, List[str]]:
        """
        Validate an Order model against business rules.
        
        Args:
            order: Order model to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Business rule: Orders must have a valid customer reference
        if not order.customer or not order.customer.reference:
            errors.append("Order must have a valid customer reference")
        
        # Business rule: Order amounts must be positive
        total_amount = sum(item.quantity * item.unit_price for item in order.line_items)
        if total_amount <= 0:
            errors.append("Order total amount must be positive")
        
        # Business rule: Order dates cannot be in the future
        # (would check against current date in real implementation)
        
        # Business rule: Product SKUs must match inventory system format
        for item in order.line_items:
            if not self._is_valid_sku_format(item.sku):
                errors.append(f"Invalid SKU format: {item.sku}")
        
        return len(errors) == 0, errors
    
    def _is_valid_sku_format(self, sku: str) -> bool:
        """
        Check if SKU matches inventory system format.
        
        Args:
            sku: SKU string to validate
            
        Returns:
            True if SKU format is valid
        """
        # Mock validation - in real system would check against inventory format
        return len(sku) > 0 and '-' in sku


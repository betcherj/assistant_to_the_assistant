"""Order extractor that uses LLM to extract Order Pydantic models from text."""
from typing import Optional
from ..models.order import Order
from .llm_parser import LLMParser
from ..utils.prompt_templates import ORDER_EXTRACTION_PROMPT


class OrderExtractor:
    """Extracts Order models from natural language text using LLM."""
    
    def __init__(self, llm_parser: LLMParser):
        """
        Initialize the order extractor.
        
        Args:
            llm_parser: LLM parser instance
        """
        self.llm_parser = llm_parser
    
    def extract_order(self, text: str) -> Optional[Order]:
        """
        Extract Order model from text.
        
        Args:
            text: Natural language text containing order information
            
        Returns:
            Extracted Order model or None if extraction fails
        """
        # Use LLM to extract order data
        extraction_result = self.llm_parser.extract_entities(
            text=text,
            entity_type="Order",
            prompt_template=ORDER_EXTRACTION_PROMPT
        )
        
        # Convert extraction result to Order Pydantic model
        # In real implementation, would parse JSON and validate
        try:
            order_data = extraction_result.get("extracted_data", {})
            return Order(**order_data)
        except Exception:
            return None
    
    def extract_from_email_attachment(self, attachment_text: str) -> Optional[Order]:
        """
        Extract order from email attachment text.
        
        Args:
            attachment_text: Text content from email attachment
            
        Returns:
            Extracted Order model
        """
        return self.extract_order(attachment_text)


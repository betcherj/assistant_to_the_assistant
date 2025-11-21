"""LLM prompt templates with domain-specific language."""
from typing import Dict


# Order extraction prompt template with domain-specific terminology
ORDER_EXTRACTION_PROMPT = """Extract an Order entity from the following text.

The text may contain domain-specific terminology:
- "PO" refers to Purchase Order
- "SKU" refers to Stock Keeping Unit
- "ETA" refers to Estimated Time of Arrival
- "FOB" refers to Free On Board shipping terms
- "Net 30" refers to payment terms (30 days)

Extract the following fields:
- order_id (Purchase Order number)
- customer (name and reference)
- order_date
- line_items (each with sku, quantity, unit_price)
- shipping_address (if present)
- shipping_terms (e.g., FOB Origin, FOB Destination)
- payment_terms (e.g., Net 30, Net 60)
- estimated_arrival (ETA)

Text to extract from:
{text}

Return the extracted data as a JSON object matching the Order Pydantic model structure."""


# Customer extraction prompt template
CUSTOMER_EXTRACTION_PROMPT = """Extract a Customer entity from the following text.

Extract:
- name
- reference (customer reference number)
- email (if present)
- phone (if present)

Text to extract from:
{text}

Return the extracted data as a JSON object matching the Customer Pydantic model structure."""


# Prompt templates dictionary
PROMPT_TEMPLATES: Dict[str, str] = {
    "order": ORDER_EXTRACTION_PROMPT,
    "customer": CUSTOMER_EXTRACTION_PROMPT,
}


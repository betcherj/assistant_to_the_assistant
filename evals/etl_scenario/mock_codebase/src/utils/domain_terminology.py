"""Domain-specific terminology mappings."""
from typing import Dict


# Domain-specific language mappings
DOMAIN_TERMS: Dict[str, str] = {
    # Order model terminology
    "PO": "Purchase Order",
    "SKU": "Stock Keeping Unit",
    "ETA": "Estimated Time of Arrival",
    "FOB": "Free On Board",
    "Net 30": "Payment terms: 30 days",
    "Net 60": "Payment terms: 60 days",
    
    # Prompt model terminology
    "Entity extraction": "Identifying business entities in text",
    "Field mapping": "Mapping extracted text to Pydantic model fields",
    "Confidence score": "LLM's confidence in extraction accuracy",
    "Validation rules": "Business rules for data quality",
}


def expand_abbreviation(abbrev: str) -> str:
    """
    Expand domain-specific abbreviation.
    
    Args:
        abbrev: Abbreviation to expand
        
    Returns:
        Expanded term or original if not found
    """
    return DOMAIN_TERMS.get(abbrev.upper(), abbrev)


def is_domain_term(term: str) -> bool:
    """
    Check if term is a domain-specific abbreviation.
    
    Args:
        term: Term to check
        
    Returns:
        True if term is a domain abbreviation
    """
    return term.upper() in DOMAIN_TERMS


"""Utility for extracting keywords from text."""
import re
from typing import List, Set


# Common stop words to filter out
STOP_WORDS: Set[str] = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
    'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
    'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
}


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text by filtering out stop words.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum length of keywords to include
        max_keywords: Maximum number of keywords to return
    
    Returns:
        List of unique keywords, limited to max_keywords
    """
    # Simple keyword extraction
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out stop words and short words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) >= min_length]
    
    # Return unique keywords, limit to max_keywords
    unique_keywords = list(dict.fromkeys(keywords))  # Preserves order while removing duplicates
    return unique_keywords[:max_keywords]


def matches_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """
    Check if any keyword appears in the text.
    
    Args:
        text: Text to search in
        keywords: List of keywords to search for
        case_sensitive: Whether to perform case-sensitive matching
    
    Returns:
        True if any keyword matches
    """
    if case_sensitive:
        text_lower = text
        keywords_lower = keywords
    else:
        text_lower = text.lower()
        keywords_lower = [kw.lower() for kw in keywords]
    
    return any(kw in text_lower for kw in keywords_lower if len(kw) > 3)


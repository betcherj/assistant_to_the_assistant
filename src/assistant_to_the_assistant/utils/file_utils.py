"""File reading utilities for business context artifacts."""
import logging
from pathlib import Path
from typing import Optional, Tuple

from ..types import BusinessContextArtifact

logger = logging.getLogger(__name__)


def read_business_context_artifact(artifact: BusinessContextArtifact) -> Optional[str]:
    """
    Read content from a business context artifact file.
    
    Args:
        artifact: BusinessContextArtifact instance
    
    Returns:
        File content as string, or None if file cannot be read
    """
    try:
        artifact_path = Path(artifact.artifact_path)
        
        if not artifact_path.exists():
            logger.warning(f"Artifact file does not exist: {artifact_path}")
            return None
        
        content = artifact_path.read_text(encoding='utf-8')
        return content
        
    except Exception as e:
        logger.warning(f"Error reading business context artifact {artifact.filename}: {e}")
        return None


def get_artifact_summary(artifact: BusinessContextArtifact, max_length: int = 800) -> str:
    """
    Get a summary/preview of an artifact's content.
    
    Args:
        artifact: BusinessContextArtifact instance
        max_length: Maximum length of summary
    
    Returns:
        Summary string (first max_length chars or overview section if available)
    """
    content = read_business_context_artifact(artifact)
    
    if not content:
        return f"Business context document: {artifact.filename}"
    
    # Try to extract overview section if present
    if "## Overview" in content or "**Overview**" in content:
        overview_start = content.find("## Overview")
        if overview_start == -1:
            overview_start = content.find("**Overview**")
        
        if overview_start != -1:
            # Find end of overview section
            overview_end = content.find("\n##", overview_start + 10)
            if overview_end == -1:
                overview_end = content.find("\n**", overview_start + 10)
            
            if overview_end > overview_start:
                summary = content[overview_start:overview_end]
                if len(summary) <= max_length:
                    return summary
    
    # Fallback to first max_length characters
    summary = content[:max_length] + "..." if len(content) > max_length else content
    return summary


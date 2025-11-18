"""Pydantic types for codebase components."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Note: Component is also used in prompt_artifacts, imported from here to avoid duplication


class Component(BaseModel):
    """A codebase component with its metadata."""
    name: str = Field(..., description="Component name")
    description: str = Field(..., description="Natural language description of the component")
    file_paths: List[str] = Field(default_factory=list, description="File paths in this component")
    dependencies: List[str] = Field(default_factory=list, description="Other component names this depends on")
    responsibilities: List[str] = Field(default_factory=list, description="Component responsibilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ComponentIndex(BaseModel):
    """Index of all components in the project."""
    components: List[Component] = Field(default_factory=list, description="List of all components")
    indexed_at: Optional[str] = Field(None, description="Timestamp of when indexing occurred")
    project_root: Optional[str] = Field(None, description="Root path of the project")



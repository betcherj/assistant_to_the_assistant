"""Pydantic types for prompt artifacts."""
from typing import List, Optional
from pydantic import BaseModel, Field

# Import Component from components to avoid duplication
from .components import Component


class BusinessGoals(BaseModel):
    """Business goals and constraints for the system."""
    purpose: str = Field(..., description="Purpose of system within the business context")
    external_constraints: List[str] = Field(
        default_factory=list,
        description="External constraints not visible within the code"
    )


class BaseIOExample(BaseModel):
    """Base class for input/output examples."""
    input_description: str = Field(..., description="Description of input")
    output_description: str = Field(..., description="Description of output")
    example: Optional[str] = Field(None, description="Concrete example if available")


class SystemIOExample(BaseIOExample):
    """System-level input/output example."""
    pass


class InfrastructureSection(BaseModel):
    """A section of infrastructure documentation."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Markdown content of the section")
    section_type: str = Field(..., description="Type: cicd, deployment, storage, networking, compute, etc.")
    keywords: List[str] = Field(default_factory=list, description="Keywords for relevance matching")


class InfrastructureDescription(BaseModel):
    """Infrastructure description."""
    deployment: Optional[str] = Field(None, description="Deployment environment description")
    databases: List[str] = Field(default_factory=list, description="Database descriptions")
    services: List[str] = Field(default_factory=list, description="External services")
    configuration: Optional[str] = Field(None, description="Configuration details")
    sections: List[InfrastructureSection] = Field(
        default_factory=list,
        description="Structured markdown sections of infrastructure documentation"
    )
    markdown_document: Optional[str] = Field(None, description="Complete markdown document")


class SystemDescription(BaseModel):
    """System-level description."""
    io_examples: List[SystemIOExample] = Field(
        default_factory=list,
        description="System level input/output examples"
    )
    components: List[Component] = Field(
        default_factory=list,
        description="Component descriptions"
    )
    infrastructure: InfrastructureDescription = Field(
        default_factory=InfrastructureDescription,
        description="Infrastructure description"
    )


class AgentGuidelines(BaseModel):
    """LLM guardrails and team-specific best practices."""
    guardrails: List[str] = Field(
        default_factory=list,
        description="LLM guardrails and constraints"
    )
    best_practices: List[str] = Field(
        default_factory=list,
        description="Team-specific best practices"
    )
    coding_standards: List[str] = Field(
        default_factory=list,
        description="Coding standards and conventions"
    )


class FeatureExample(BaseIOExample):
    """Feature-level input/output example."""
    pass


class FeaturePrompt(BaseModel):
    """Feature/fix/instance prompt description."""
    description: str = Field(..., description="What we are trying to do in this prompt")
    feature_type: str = Field(default="feature", description="Type: feature, fix, or instance")
    examples: List[FeatureExample] = Field(
        default_factory=list,
        description="Feature-level input/output examples if relevant"
    )


class BusinessContextArtifact(BaseModel):
    """A business context artifact from indexed documents."""
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type: pdf, csv, markdown")
    source_path: str = Field(..., description="Source path (local or S3)")
    artifact_path: str = Field(..., description="Path to markdown artifact file")
    indexed_at: str = Field(..., description="ISO timestamp when indexed")


class BusinessContext(BaseModel):
    """Business context from indexed documents."""
    artifacts: List[BusinessContextArtifact] = Field(
        default_factory=list,
        description="List of business context artifacts"
    )
    indexed_at: str = Field(..., description="ISO timestamp when indexed")


class PromptArtifacts(BaseModel):
    """Complete prompt artifacts collection."""
    business_goals: BusinessGoals
    system_description: SystemDescription
    agent_guidelines: AgentGuidelines
    feature_prompt: FeaturePrompt
    business_context: Optional[BusinessContext] = Field(
        None,
        description="Business context from indexed documents"
    )



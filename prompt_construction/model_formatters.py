"""Model-specific prompt formatters."""
from typing import Dict, Any, Optional

from ..types import PromptArtifacts, Component


class ModelFormatter:
    """Base class for model-specific prompt formatters."""
    
    def format(
        self,
        artifacts: PromptArtifacts,
        selected_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format prompt artifacts into a model-specific prompt.
        
        Args:
            artifacts: Complete prompt artifacts
            selected_context: Optional selected context (if None, include all)
        
        Returns:
            Formatted prompt string
        """
        raise NotImplementedError


class GPT4Formatter(ModelFormatter):
    """Formatter for GPT-4 and similar OpenAI models."""
    
    def format(
        self,
        artifacts: PromptArtifacts,
        selected_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format prompt for GPT-4."""
        parts = []
        
        # Header
        parts.append("# Software Development Task\n")
        
        # Business Goals
        if artifacts.business_goals:
            parts.append("## Business Context\n")
            parts.append(f"**Purpose:** {artifacts.business_goals.purpose}\n")
            if artifacts.business_goals.external_constraints:
                parts.append("\n**External Constraints:**\n")
                for constraint in artifacts.business_goals.external_constraints:
                    parts.append(f"- {constraint}\n")
            parts.append("\n")
        
        # Business Context Artifacts (from indexed documents)
        # Only include selected artifacts if available, otherwise include all
        business_context_artifacts = []
        if selected_context and selected_context.get("business_context_artifacts"):
            business_context_artifacts = selected_context["business_context_artifacts"]
        elif artifacts.business_context and artifacts.business_context.artifacts:
            business_context_artifacts = artifacts.business_context.artifacts
        
        if business_context_artifacts:
            parts.append("## Business Context Documentation\n")
            parts.append("The following business context documents provide additional domain knowledge:\n\n")
            
            for artifact in business_context_artifacts:
                # Read the markdown artifact file
                try:
                    from pathlib import Path
                    artifact_path = Path(artifact.artifact_path)
                    if artifact_path.exists():
                        artifact_content = artifact_path.read_text(encoding='utf-8')
                        parts.append(artifact_content)
                        parts.append("\n\n---\n\n")
                except Exception as e:
                    # If we can't read the file, just include metadata
                    parts.append(f"### {artifact.filename}\n")
                    parts.append(f"*Source: {artifact.source_path}*\n")
                    parts.append(f"*Type: {artifact.file_type.upper()}*\n\n")
            parts.append("\n")
        
        # System Description
        if artifacts.system_description:
            parts.append("## System Description\n")
            
            # IO Examples
            if artifacts.system_description.io_examples:
                parts.append("### System Input/Output Examples\n")
                for io_ex in artifacts.system_description.io_examples:
                    parts.append(f"**Input:** {io_ex.input_description}\n")
                    parts.append(f"**Output:** {io_ex.output_description}\n")
                    if io_ex.example:
                        parts.append(f"**Example:**\n```\n{io_ex.example}\n```\n")
                parts.append("\n")
            
            # Components
            components_to_include = artifacts.system_description.components
            if selected_context and selected_context.get("components"):
                components_to_include = selected_context["components"]
            
            if components_to_include:
                parts.append("### Components\n")
                for component in components_to_include:
                    parts.append(f"#### {component.name}\n")
                    parts.append(f"{component.description}\n")
                    if component.responsibilities:
                        parts.append("**Responsibilities:**\n")
                        for resp in component.responsibilities:
                            parts.append(f"- {resp}\n")
                    if component.dependencies:
                        parts.append(f"**Dependencies:** {', '.join(component.dependencies)}\n")
                    if component.file_paths:
                        parts.append(f"**Files:** {', '.join(component.file_paths[:5])}\n")
                    parts.append("\n")
            
            # Infrastructure
            include_infra = True
            infrastructure_sections = None
            if selected_context is not None:
                include_infra = selected_context.get("include_infrastructure", True)
                infrastructure_sections = selected_context.get("infrastructure_sections", [])
            
            if include_infra and artifacts.system_description.infrastructure:
                infra = artifacts.system_description.infrastructure
                parts.append("### Infrastructure\n")
                
                # Include selected infrastructure sections if available
                if infrastructure_sections:
                    for section in infrastructure_sections:
                        parts.append(f"#### {section.title}\n")
                        parts.append(section.content)
                        parts.append("\n\n")
                else:
                    # Fallback to legacy format
                    if infra.deployment:
                        parts.append(f"**Deployment:** {infra.deployment}\n")
                    if infra.databases:
                        parts.append(f"**Databases:** {', '.join(infra.databases)}\n")
                    if infra.services:
                        parts.append(f"**Services:** {', '.join(infra.services)}\n")
                    if infra.configuration:
                        parts.append(f"**Configuration:** {infra.configuration}\n")
                    # Also include all sections if available
                    if infra.sections:
                        for section in infra.sections:
                            parts.append(f"#### {section.title}\n")
                            parts.append(section.content)
                            parts.append("\n\n")
                parts.append("\n")
        
        # Agent Guidelines
        if artifacts.agent_guidelines:
            parts.append("## Development Guidelines\n")
            
            if artifacts.agent_guidelines.guardrails:
                parts.append("### Guardrails\n")
                for guardrail in artifacts.agent_guidelines.guardrails:
                    parts.append(f"- {guardrail}\n")
                parts.append("\n")
            
            if artifacts.agent_guidelines.best_practices:
                parts.append("### Best Practices\n")
                for practice in artifacts.agent_guidelines.best_practices:
                    parts.append(f"- {practice}\n")
                parts.append("\n")
            
            if artifacts.agent_guidelines.coding_standards:
                parts.append("### Coding Standards\n")
                for standard in artifacts.agent_guidelines.coding_standards:
                    parts.append(f"- {standard}\n")
                parts.append("\n")
        
        # Feature Prompt
        parts.append("## Task\n")
        parts.append(f"**Type:** {artifacts.feature_prompt.feature_type}\n")
        parts.append(f"**Description:** {artifacts.feature_prompt.description}\n\n")
        
        if artifacts.feature_prompt.examples:
            parts.append("### Feature Examples\n")
            for example in artifacts.feature_prompt.examples:
                parts.append(f"**Input:** {example.input_description}\n")
                parts.append(f"**Output:** {example.output_description}\n")
                if example.example:
                    parts.append(f"**Example:**\n```\n{example.example}\n```\n")
            parts.append("\n")
        
        parts.append("---\n")
        parts.append("Please implement this feature following the guidelines and using the system context provided above.\n")
        
        return "".join(parts)


class ClaudeFormatter(ModelFormatter):
    """Formatter for Claude models."""
    
    def format(
        self,
        artifacts: PromptArtifacts,
        selected_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format prompt for Claude (similar to GPT-4 but can be customized)."""
        # Claude can use similar format, but we can customize if needed
        formatter = GPT4Formatter()
        prompt = formatter.format(artifacts, selected_context)
        
        # Add Claude-specific instructions if needed
        return prompt


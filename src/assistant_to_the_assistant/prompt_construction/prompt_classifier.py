"""LLM-based classifier for analyzing feature descriptions and selecting relevant artifacts."""
import logging
from typing import Dict, Any, List, Optional

from ..types import (
    Component,
    InfrastructureSection,
    BusinessGoals,
    SystemDescription,
    AgentGuidelines,
    BusinessContext,
    BusinessContextArtifact,
)
from ..utils import BaseLLMClient, make_json_llm_call
from ..utils.keyword_extractor import extract_keywords, matches_keywords
from ..utils.file_utils import get_artifact_summary

logger = logging.getLogger(__name__)


class PromptClassifier(BaseLLMClient):
    """Uses LLM to classify feature descriptions and select relevant artifacts."""
    
    def classify_and_select(
        self,
        feature_description: str,
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze feature description and select relevant artifacts.
        
        Args:
            feature_description: Description of the feature to implement
            resources: All available project resources
        
        Returns:
            Dictionary with selected artifacts and classification metadata
        """
        # Prepare context for classification
        classification_context = self._prepare_classification_context(resources)
        
        # Use LLM to classify and select relevant artifacts
        classification_result = self._llm_classify(
            feature_description,
            classification_context
        )
        
        # Extract selected artifacts based on classification
        selected_artifacts = self._extract_selected_artifacts(
            classification_result,
            resources
        )
        
        return {
            "selected_artifacts": selected_artifacts,
            "classification": classification_result,
            "reasoning": classification_result.get("reasoning", "")
        }
    
    def _prepare_classification_context(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for classification."""
        context = {
            "components": [],
            "infrastructure_sections": [],
            "business_goals": None,
            "agent_guidelines": None,
            "system_io_examples": [],
            "business_context_artifacts": [],
        }
        
        # Extract component summaries
        component_index = resources.get("component_index")
        if component_index and component_index.components:
            context["components"] = [
                {
                    "name": comp.name,
                    "description": comp.description,
                    "responsibilities": comp.responsibilities,
                    "dependencies": comp.dependencies,
                }
                for comp in component_index.components
            ]
        
        # Extract infrastructure sections
        system_description = resources.get("system_description")
        if system_description and system_description.infrastructure:
            infrastructure = system_description.infrastructure
            if infrastructure.sections:
                context["infrastructure_sections"] = [
                    {
                        "title": section.title,
                        "section_type": section.section_type,
                        "keywords": section.keywords,
                        "summary": section.content[:500] + "..." if len(section.content) > 500 else section.content
                    }
                    for section in infrastructure.sections
                ]
        
        # Extract business goals
        business_goals = resources.get("business_goals")
        if business_goals:
            context["business_goals"] = {
                "purpose": business_goals.purpose,
                "external_constraints": business_goals.external_constraints
            }
        
        # Extract agent guidelines
        agent_guidelines = resources.get("agent_guidelines")
        if agent_guidelines:
            context["agent_guidelines"] = {
                "guardrails": agent_guidelines.guardrails,
                "best_practices": agent_guidelines.best_practices,
                "coding_standards": agent_guidelines.coding_standards
            }
        
        # Extract system IO examples
        if system_description and system_description.io_examples:
            context["system_io_examples"] = [
                {
                    "input": io_ex.input_description,
                    "output": io_ex.output_description
                }
                for io_ex in system_description.io_examples
            ]
        
        # Extract business context artifacts
        business_context = resources.get("business_context")
        if business_context and business_context.artifacts:
            context["business_context_artifacts"] = self._prepare_business_context_summaries(
                business_context.artifacts
            )
        
        return context
    
    def _llm_classify(
        self,
        feature_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to classify feature and select relevant artifacts."""
        
        # Build classification prompt
        prompt = self._build_classification_prompt(feature_description, context)
        
        system_message = (
            "You are an expert at analyzing software feature requirements and identifying "
            "relevant context needed for implementation. Your goal is to maximize the effectiveness "
            "of the final prompt by selecting only the most relevant artifacts that directly "
            "contribute to implementing the feature. Be selective - include only artifacts that "
            "provide essential context. Too much irrelevant context can reduce prompt effectiveness. "
            "Consider relevance scores to prioritize the most important artifacts."
        )
        
        try:
            result = make_json_llm_call(
                client=self.client,
                model=self.model,
                system_message=system_message,
                user_message=prompt,
                temperature=0.3
            )
            return result
            
        except Exception as e:
            logger.error(f"Error during LLM classification: {e}", exc_info=True)
            # Fallback to simple keyword matching
            return self._fallback_classification(feature_description, context)
    
    def _build_classification_prompt(
        self,
        feature_description: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM classification."""
        
        components_summary = ""
        if context["components"]:
            components_list = "\n".join([
                f"- {comp['name']}: {comp['description']}"
                for comp in context["components"][:20]  # Limit for token efficiency
            ])
            components_summary = f"""
Available Components:
{components_list}
"""
        
        infrastructure_summary = ""
        if context["infrastructure_sections"]:
            infra_list = "\n".join([
                f"- {section['title']} ({section['section_type']}): Keywords: {', '.join(section['keywords'][:5])}"
                for section in context["infrastructure_sections"]
            ])
            infrastructure_summary = f"""
Available Infrastructure Sections:
{infra_list}
"""
        
        business_goals_summary = ""
        if context["business_goals"]:
            business_goals_summary = f"""
Business Goals:
- Purpose: {context['business_goals']['purpose']}
- Constraints: {', '.join(context['business_goals']['external_constraints'][:5])}
"""
        
        guidelines_summary = ""
        if context["agent_guidelines"]:
            guidelines_summary = f"""
Development Guidelines:
- Guardrails: {len(context['agent_guidelines']['guardrails'])} rules
- Best Practices: {len(context['agent_guidelines']['best_practices'])} practices
- Coding Standards: {len(context['agent_guidelines']['coding_standards'])} standards
"""
        
        business_context_summary = ""
        if context["business_context_artifacts"]:
            bc_list = "\n".join([
                f"- {art['filename']} ({art['file_type']}): {art['summary']}"
                for art in context["business_context_artifacts"]
            ])
            business_context_summary = f"""
Available Business Context Documents:
{bc_list}
"""
        
        return f"""Analyze the following feature description and determine which artifacts are most relevant for implementation.

Your goal is to maximize the effectiveness of the final prompt by selecting only the most relevant artifacts that directly contribute to implementing this feature. Be selective - too much context can reduce prompt effectiveness.

Consider:
- Which components are directly involved in implementing this feature?
- Which infrastructure sections are relevant to deployment/configuration?
- Which business context documents contain domain knowledge needed for this feature?
- Which guidelines and constraints are most important for this specific feature?

Feature Description:
{feature_description}

Available Artifacts:
{components_summary}
{infrastructure_summary}
{business_goals_summary}
{guidelines_summary}
{business_context_summary}

Return a JSON object with:
{{
  "relevant_component_names": ["component1", "component2", ...],
  "relevant_infrastructure_sections": ["section_title1", "section_title2", ...],
  "relevant_business_context_filenames": ["filename1.pdf", "filename2.csv", ...],
  "include_business_goals": true/false,
  "include_agent_guidelines": true/false,
  "include_system_io_examples": true/false,
  "reasoning": "Brief explanation of why these artifacts were selected and how they maximize prompt effectiveness",
  "feature_category": "api|database|ui|infrastructure|integration|other",
  "complexity": "low|medium|high",
  "relevance_scores": {{
    "components": {{"component1": 0.9, "component2": 0.7}},
    "infrastructure": {{"section1": 0.8}},
    "business_context": {{"filename1.pdf": 0.9, "filename2.csv": 0.5}}
  }}
}}
"""
    
    def _extract_selected_artifacts(
        self,
        classification: Dict[str, Any],
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract selected artifacts based on classification result."""
        selected = {
            "components": [],
            "infrastructure_sections": [],
            "business_context_artifacts": [],
            "include_business_goals": classification.get("include_business_goals", True),
            "include_agent_guidelines": classification.get("include_agent_guidelines", True),
            "include_system_io_examples": classification.get("include_system_io_examples", False),
        }
        
        # Select components
        component_index = resources.get("component_index")
        if component_index and component_index.components:
            relevant_names = classification.get("relevant_component_names", [])
            selected["components"] = [
                comp for comp in component_index.components
                if comp.name in relevant_names
            ]
        
        # Select infrastructure sections
        system_description = resources.get("system_description")
        if system_description and system_description.infrastructure:
            infrastructure = system_description.infrastructure
            if infrastructure.sections:
                relevant_titles = classification.get("relevant_infrastructure_sections", [])
                selected["infrastructure_sections"] = [
                    section for section in infrastructure.sections
                    if section.title in relevant_titles
                ]
        
        # Select business context artifacts
        business_context = resources.get("business_context")
        if business_context and business_context.artifacts:
            relevant_filenames = classification.get("relevant_business_context_filenames", [])
            # Use relevance scores if available to filter low-relevance artifacts
            relevance_scores = classification.get("relevance_scores", {}).get("business_context", {})
            min_relevance = 0.5  # Minimum relevance score threshold
            
            selected["business_context_artifacts"] = [
                artifact for artifact in business_context.artifacts
                if artifact.filename in relevant_filenames or 
                relevance_scores.get(artifact.filename, 0) >= min_relevance
            ]
        
        return selected
    
    def _fallback_classification(
        self,
        feature_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback classification using simple keyword matching."""
        keywords = extract_keywords(feature_description)
        
        relevant_components = []
        if context["components"]:
            for comp in context["components"]:
                comp_text = f"{comp['name']} {comp['description']}"
                if matches_keywords(comp_text, keywords):
                    relevant_components.append(comp["name"])
        
        relevant_sections = []
        if context["infrastructure_sections"]:
            for section in context["infrastructure_sections"]:
                section_text = f"{section['title']} {' '.join(section['keywords'])}"
                if matches_keywords(section_text, keywords):
                    relevant_sections.append(section["title"])
        
        # Fallback business context selection
        relevant_bc = []
        if context.get("business_context_artifacts"):
            for bc_art in context["business_context_artifacts"]:
                bc_text = f"{bc_art['filename']} {bc_art['summary']}"
                if matches_keywords(bc_text, keywords):
                    relevant_bc.append(bc_art["filename"])
        
        return {
            "relevant_component_names": relevant_components[:5],
            "relevant_infrastructure_sections": relevant_sections[:3],
            "relevant_business_context_filenames": relevant_bc[:3],
            "include_business_goals": True,
            "include_agent_guidelines": True,
            "include_system_io_examples": False,
            "reasoning": "Fallback classification using keyword matching",
            "feature_category": "other",
            "complexity": "medium",
            "relevance_scores": {}
        }
    
    def _prepare_business_context_summaries(
        self,
        artifacts: List[BusinessContextArtifact]
    ) -> List[Dict[str, Any]]:
        """
        Prepare business context artifact summaries for classification.
        
        Reads the markdown artifact files and extracts summaries.
        """
        summaries = []
        
        for artifact in artifacts:
            summary = get_artifact_summary(artifact, max_length=800)
            
            summaries.append({
                "filename": artifact.filename,
                "file_type": artifact.file_type,
                "source_path": artifact.source_path,
                "summary": summary,
                "artifact_path": artifact.artifact_path
            })
        
        return summaries


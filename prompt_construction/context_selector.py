"""Selects relevant context based on feature description."""
from typing import Dict, Any, List, Optional
import re

from ..types import Component, ComponentIndex, InfrastructureSection


class ContextSelector:
    """Selects relevant project context for a feature."""
    
    def select_relevant_context(
        self,
        feature_description: str,
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Select relevant context based on feature description.
        
        Args:
            feature_description: Description of the feature
            resources: All available resources
        
        Returns:
            Dictionary with selected relevant context
        """
        selected = {
            "components": [],
            "include_infrastructure": False,
            "include_all_io_examples": False,
            "infrastructure_sections": [],
        }
        
        component_index = resources.get("component_index")
        if component_index and component_index.components:
            # Select relevant components based on keywords
            relevant_components = self._select_relevant_components(
                feature_description,
                component_index.components
            )
            selected["components"] = relevant_components
        
        # Select relevant infrastructure sections
        system_description = resources.get("system_description")
        if system_description and system_description.infrastructure:
            infrastructure = system_description.infrastructure
            if infrastructure.sections:
                relevant_sections = self._select_relevant_infrastructure_sections(
                    feature_description,
                    infrastructure.sections
                )
                selected["infrastructure_sections"] = relevant_sections
                if relevant_sections:
                    selected["include_infrastructure"] = True
        
        # Check if infrastructure is relevant (fallback)
        if not selected["infrastructure_sections"] and self._is_infrastructure_relevant(feature_description):
            selected["include_infrastructure"] = True
        
        # Check if all IO examples are relevant
        if system_description and system_description.io_examples:
            selected["include_all_io_examples"] = True
        
        return selected
    
    def _select_relevant_components(
        self,
        feature_description: str,
        components: List[Component]
    ) -> List[Component]:
        """Select components relevant to the feature."""
        description_lower = feature_description.lower()
        relevant = []
        
        # Extract keywords from feature description
        keywords = self._extract_keywords(feature_description)
        
        for component in components:
            # Check if component name or description matches keywords
            component_text = f"{component.name} {component.description}".lower()
            
            # Simple keyword matching
            if any(keyword in component_text for keyword in keywords):
                relevant.append(component)
            # Check responsibilities
            elif any(keyword in " ".join(component.responsibilities).lower() for keyword in keywords):
                relevant.append(component)
        
        # If no matches, return top-level components (those with few dependencies)
        if not relevant:
            relevant = sorted(
                components,
                key=lambda c: len(c.dependencies)
            )[:3]
        
        return relevant
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Return unique keywords, limit to top 10
        return list(set(keywords))[:10]
    
    def _select_relevant_infrastructure_sections(
        self,
        feature_description: str,
        sections: List[InfrastructureSection]
    ) -> List[InfrastructureSection]:
        """Select relevant infrastructure sections based on feature description."""
        description_lower = feature_description.lower()
        keywords = self._extract_keywords(feature_description)
        
        relevant_sections = []
        
        for section in sections:
            # Check if section keywords match feature keywords
            section_keywords_lower = [k.lower() for k in section.keywords]
            section_title_lower = section.title.lower()
            section_type_lower = section.section_type.lower()
            
            # Match if any keyword appears in section keywords, title, or type
            if any(keyword in section_keywords_lower for keyword in keywords):
                relevant_sections.append(section)
            elif any(keyword in section_title_lower for keyword in keywords):
                relevant_sections.append(section)
            elif any(keyword in section_type_lower for keyword in keywords):
                relevant_sections.append(section)
            # Also check if feature description mentions section-specific terms
            elif self._matches_section_type(description_lower, section.section_type):
                relevant_sections.append(section)
        
        return relevant_sections
    
    def _matches_section_type(self, description: str, section_type: str) -> bool:
        """Check if description matches a specific section type."""
        type_keywords = {
            'cicd': ['ci', 'cd', 'pipeline', 'deploy', 'build', 'test', 'gitlab', 'runner'],
            'deployment': ['deploy', 'container', 'docker', 'ecs', 'fargate', 'task'],
            'storage': ['storage', 's3', 'database', 'rds', 'dynamodb', 'data', 'persist'],
            'networking': ['network', 'vpc', 'subnet', 'security', 'load', 'balancer', 'alb'],
            'compute': ['compute', 'instance', 'ec2', 'lambda', 'server', 'resource'],
        }
        
        keywords = type_keywords.get(section_type.lower(), [])
        return any(keyword in description for keyword in keywords)
    
    def _is_infrastructure_relevant(self, feature_description: str) -> bool:
        """Check if infrastructure context is relevant."""
        infra_keywords = [
            'deploy', 'infrastructure', 'docker', 'kubernetes', 'aws', 'gcp',
            'azure', 'database', 'db', 'service', 'api', 'endpoint', 'server',
            'config', 'environment', 'production', 'staging'
        ]
        
        description_lower = feature_description.lower()
        return any(keyword in description_lower for keyword in infra_keywords)


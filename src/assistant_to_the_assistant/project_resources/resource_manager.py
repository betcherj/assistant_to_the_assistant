"""Manages project-specific resources used to populate feature prompts."""
import json
from pathlib import Path
from typing import Optional, Dict, Any, TypeVar, Type
from pydantic import BaseModel

from ..types import (
    BusinessGoals,
    SystemDescription,
    AgentGuidelines,
    ComponentIndex,
    InfrastructureDescription,
    BusinessContext,
    BusinessContextArtifact,
)
from ..project_indexer import ProjectIndexer

T = TypeVar('T', bound=BaseModel)


class ProjectResourceManager:
    """Manages project resources (manually defined or created by indexer)."""
    
    def __init__(self, resources_dir: Optional[str] = None):
        """
        Initialize resource manager.
        
        Args:
            resources_dir: Directory to store resources (defaults to .project-resources)
        """
        self.resources_dir = Path(resources_dir) if resources_dir else Path(".project-resources")
        self.resources_dir.mkdir(exist_ok=True)
        
        # Resource file paths
        self.business_goals_path = self.resources_dir / "business_goals.json"
        self.system_description_path = self.resources_dir / "system_description.json"
        self.agent_guidelines_path = self.resources_dir / "agent_guidelines.json"
        self.component_index_path = self.resources_dir / "component_index.json"
        self.infrastructure_path = self.resources_dir / "infrastructure.json"
        self.business_context_path = self.resources_dir / "business_context.json"
        self.business_context_dir = self.resources_dir / "business-context"
    
    def _save_resource(self, resource: BaseModel, file_path: Path) -> None:
        """Generic method to save a Pydantic model to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(resource.model_dump(), f, indent=2)
    
    def _load_resource(self, resource_type: Type[T], file_path: Path) -> Optional[T]:
        """Generic method to load a Pydantic model from JSON file."""
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            data = json.load(f)
            return resource_type(**data)
    
    def save_business_goals(self, business_goals: BusinessGoals) -> None:
        """Save business goals to disk."""
        self._save_resource(business_goals, self.business_goals_path)
    
    def load_business_goals(self) -> Optional[BusinessGoals]:
        """Load business goals from disk."""
        return self._load_resource(BusinessGoals, self.business_goals_path)
    
    def save_system_description(self, system_description: SystemDescription) -> None:
        """Save system description to disk."""
        self._save_resource(system_description, self.system_description_path)
    
    def load_system_description(self) -> Optional[SystemDescription]:
        """Load system description from disk."""
        return self._load_resource(SystemDescription, self.system_description_path)
    
    def save_agent_guidelines(self, agent_guidelines: AgentGuidelines) -> None:
        """Save agent guidelines to disk."""
        self._save_resource(agent_guidelines, self.agent_guidelines_path)
    
    def load_agent_guidelines(self) -> Optional[AgentGuidelines]:
        """Load agent guidelines from disk."""
        return self._load_resource(AgentGuidelines, self.agent_guidelines_path)
    
    def save_component_index(self, component_index: ComponentIndex) -> None:
        """Save component index to disk."""
        self._save_resource(component_index, self.component_index_path)
    
    def load_component_index(self) -> Optional[ComponentIndex]:
        """Load component index from disk."""
        return self._load_resource(ComponentIndex, self.component_index_path)
    
    def save_infrastructure(self, infrastructure: InfrastructureDescription) -> None:
        """Save infrastructure description to disk."""
        self._save_resource(infrastructure, self.infrastructure_path)
    
    def load_infrastructure(self) -> Optional[InfrastructureDescription]:
        """Load infrastructure description from disk."""
        return self._load_resource(InfrastructureDescription, self.infrastructure_path)
    
    def index_project(
        self,
        codebase_paths: list[str],
        config_paths: Optional[list[str]] = None,
        dockerfile_path: Optional[str] = None,
        readme_path: Optional[str] = None,
        document_paths: Optional[list[str]] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview"
    ) -> Dict[str, Any]:
        """
        Index project and save all resources.
        
        Args:
            codebase_paths: Paths to codebase files/directories to index
            config_paths: Paths to configuration files
            dockerfile_path: Path to Dockerfile
            readme_path: Path to README
            document_paths: Paths to contextual documents
            api_key: OpenAI API key
            model: LLM model to use
        
        Returns:
            Dictionary with indexing results
        """
        indexer = ProjectIndexer(api_key=api_key, model=model)
        
        # Index codebase
        component_index = indexer.index_codebase(codebase_paths)
        self.save_component_index(component_index)
        
        # Index infrastructure
        infra_dict = indexer.index_infrastructure(
            config_paths=config_paths,
            dockerfile_path=dockerfile_path,
            readme_path=readme_path
        )
        infrastructure = InfrastructureDescription(**infra_dict)
        self.save_infrastructure(infrastructure)
        
        # Update system description with infrastructure
        system_description = self.load_system_description() or SystemDescription()
        system_description.infrastructure = infrastructure
        self.save_system_description(system_description)
        
        # Index documents if provided
        document_summaries = {}
        if document_paths:
            document_summaries = indexer.index_documents(document_paths)
        
        return {
            "component_index": component_index,
            "infrastructure": infrastructure,
            "document_summaries": document_summaries,
            "status": "indexed"
        }
    
    def save_business_context(self, business_context: BusinessContext) -> None:
        """Save business context to disk."""
        self._save_resource(business_context, self.business_context_path)
    
    def load_business_context(self) -> Optional[BusinessContext]:
        """Load business context from disk."""
        return self._load_resource(BusinessContext, self.business_context_path)
    
    def get_all_resources(self) -> Dict[str, Any]:
        """Get all loaded resources."""
        return {
            "business_goals": self.load_business_goals(),
            "system_description": self.load_system_description(),
            "agent_guidelines": self.load_agent_guidelines(),
            "component_index": self.load_component_index(),
            "infrastructure": self.load_infrastructure(),
            "business_context": self.load_business_context(),
        }


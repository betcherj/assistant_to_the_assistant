"""Project indexer that uses LLM to create summaries of codebase components."""
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

from ..types import Component, ComponentIndex
from ..utils import make_json_llm_call

load_dotenv()

logger = logging.getLogger(__name__)


class ProjectIndexer:
    """Indexes project codebase, infrastructure, and documents using LLM."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        project_root: Optional[str] = None
    ):
        """
        Initialize the project indexer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: LLM model to use for indexing
            project_root: Root path of the project to index
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass api_key.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.project_root = Path(project_root) if project_root else Path.cwd()
    
    def index_codebase(
        self,
        paths: List[str],
        exclude_patterns: Optional[List[str]] = None
    ) -> ComponentIndex:
        """
        Index codebase components using LLM.
        
        Args:
            paths: List of file/directory paths to index
            exclude_patterns: Patterns to exclude (e.g., ['__pycache__', '*.pyc'])
        
        Returns:
            ComponentIndex with all discovered components
        """
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', '.git', 'node_modules', 'venv', 'env']
        
        # Collect files to analyze
        files_to_analyze = []
        for path_str in paths:
            path = Path(path_str)
            if not path.is_absolute():
                path = self.project_root / path
            
            if path.is_file():
                files_to_analyze.append(path)
            elif path.is_dir():
                files_to_analyze.extend(self._collect_files(path, exclude_patterns))
        
        # Group files into logical components
        components = self._analyze_and_group_files(files_to_analyze)
        
        return ComponentIndex(
            components=components,
            indexed_at=datetime.now().isoformat(),
            project_root=str(self.project_root)
        )
    
    def index_infrastructure(
        self,
        config_paths: Optional[List[str]] = None,
        dockerfile_path: Optional[str] = None,
        readme_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index infrastructure configuration.
        
        Args:
            config_paths: Paths to configuration files
            dockerfile_path: Path to Dockerfile
            readme_path: Path to README
        
        Returns:
            Dictionary with infrastructure description
        """
        infrastructure_info = {
            "deployment": None,
            "databases": [],
            "services": [],
            "configuration": None
        }
        
        # Read Dockerfile if available
        if dockerfile_path:
            dockerfile = Path(dockerfile_path)
            if dockerfile.exists():
                content = dockerfile.read_text()
                infrastructure_info["deployment"] = self._summarize_infrastructure(
                    content, "deployment configuration"
                )
        
        # Read config files
        if config_paths:
            config_contents = []
            for config_path in config_paths:
                path = Path(config_path)
                if path.exists():
                    config_contents.append(path.read_text())
            
            if config_contents:
                infrastructure_info["configuration"] = self._summarize_infrastructure(
                    "\n\n".join(config_contents), "configuration"
                )
        
        # Read README for additional context
        if readme_path:
            readme = Path(readme_path)
            if readme.exists():
                readme_content = readme.read_text()
                # Extract infrastructure mentions from README
                infrastructure_info["deployment"] = self._extract_infrastructure_from_readme(
                    readme_content
                )
        
        return infrastructure_info
    
    def index_documents(
        self,
        document_paths: List[str]
    ) -> Dict[str, str]:
        """
        Index contextual documents.
        
        Args:
            document_paths: Paths to documents to index
        
        Returns:
            Dictionary mapping document paths to summaries
        """
        summaries = {}
        
        for doc_path in document_paths:
            path = Path(doc_path)
            if path.exists():
                content = path.read_text()
                summary = self._summarize_document(content, path.name)
                summaries[str(path)] = summary
        
        return summaries
    
    def _collect_files(
        self,
        directory: Path,
        exclude_patterns: List[str]
    ) -> List[Path]:
        """Collect files from directory, excluding patterns."""
        files = []
        
        for root, dirs, filenames in os.walk(directory):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not any(
                Path(d).match(pattern) for pattern in exclude_patterns
            )]
            
            for filename in filenames:
                file_path = Path(root) / filename
                # Skip excluded files
                if not any(file_path.match(pattern) for pattern in exclude_patterns):
                    files.append(file_path)
        
        return files
    
    def _analyze_and_group_files(
        self,
        files: List[Path]
    ) -> List[Component]:
        """Analyze files and group them into components using LLM."""
        if not files:
            return []
        
        # Read file contents (limit size to avoid token limits)
        file_contents = {}
        for file_path in files[:100]:  # Limit to 100 files per batch
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Truncate very large files
                if len(content) > 10000:
                    content = content[:10000] + "\n... [truncated]"
                file_contents[str(file_path)] = content
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}", exc_info=True)
        
        # Use LLM to analyze and group files
        prompt = self._create_analysis_prompt(file_contents)
        
        system_message = (
            "You are a codebase analyzer. Analyze files and group them into logical components. "
            "Return a JSON array of components with name, description, file_paths, dependencies, "
            "and responsibilities."
        )
        
        try:
            result = make_json_llm_call(
                client=self.client,
                model=self.model,
                system_message=system_message,
                user_message=prompt,
                temperature=0.3
            )
            
            # Parse into Component objects
            components = []
            if "components" in result:
                for comp_data in result["components"]:
                    components.append(Component(**comp_data))
            
            return components
            
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}", exc_info=True)
            # Fallback: create simple components based on directory structure
            return self._fallback_component_grouping(files)
    
    def _create_analysis_prompt(self, file_contents: Dict[str, str]) -> str:
        """Create prompt for LLM analysis."""
        files_summary = "\n\n".join([
            f"File: {path}\n{content[:500]}..." if len(content) > 500 else f"File: {path}\n{content}"
            for path, content in list(file_contents.items())[:20]  # Limit for prompt size
        ])
        
        return f"""Analyze the following codebase files and group them into logical components.

For each component, provide:
- name: A descriptive name
- description: What this component does and how it fits into the system
- file_paths: List of file paths in this component
- dependencies: Other component names this depends on
- responsibilities: Key responsibilities of this component

Files to analyze:
{files_summary}

Return JSON in format:
{{
  "components": [
    {{
      "name": "component_name",
      "description": "...",
      "file_paths": ["path1", "path2"],
      "dependencies": ["other_component"],
      "responsibilities": ["responsibility1", "responsibility2"]
    }}
  ]
}}
"""
    
    def _fallback_component_grouping(self, files: List[Path]) -> List[Component]:
        """Fallback grouping by directory structure."""
        components = {}
        
        for file_path in files:
            # Group by parent directory
            parent = file_path.parent.name or "root"
            if parent not in components:
                components[parent] = {
                    "name": parent,
                    "file_paths": [],
                    "dependencies": [],
                    "responsibilities": []
                }
            components[parent]["file_paths"].append(str(file_path))
        
        return [
            Component(
                name=comp["name"],
                description=f"Component in {comp['name']} directory",
                file_paths=comp["file_paths"],
                dependencies=comp["dependencies"],
                responsibilities=comp["responsibilities"]
            )
            for comp in components.values()
        ]
    
    def _summarize_infrastructure(self, content: str, context: str) -> str:
        """Summarize infrastructure configuration using LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an infrastructure analyst. Summarize the {context} in natural language."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this {context}:\n\n{content[:5000]}"
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Error summarizing infrastructure: {e}", exc_info=True)
            return content[:500] + "..." if len(content) > 500 else content
    
    def _extract_infrastructure_from_readme(self, readme_content: str) -> str:
        """Extract infrastructure information from README."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract deployment and infrastructure information from README."
                    },
                    {
                        "role": "user",
                        "content": f"Extract infrastructure details from:\n\n{readme_content[:5000]}"
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Error extracting infrastructure: {e}", exc_info=True)
            return ""
    
    def _summarize_document(self, content: str, filename: str) -> str:
        """Summarize a document using LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize this document in 2-3 sentences, focusing on key information relevant to software development."
                    },
                    {
                        "role": "user",
                        "content": f"Document: {filename}\n\n{content[:5000]}"
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Error summarizing document: {e}", exc_info=True)
            return content[:200] + "..." if len(content) > 200 else content


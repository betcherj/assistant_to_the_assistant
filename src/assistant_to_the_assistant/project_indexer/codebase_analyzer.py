"""Utility functions for analyzing codebase structure."""
import ast
from pathlib import Path
from typing import List, Dict, Set
import re


class CodebaseAnalyzer:
    """Analyzes codebase structure without LLM."""
    
    @staticmethod
    def detect_language(file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.php': 'php',
        }
        return extension_map.get(file_path.suffix.lower(), 'unknown')
    
    @staticmethod
    def extract_python_imports(file_path: Path) -> List[str]:
        """Extract import statements from Python file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            return imports
        except Exception:
            return []
    
    @staticmethod
    def find_dependencies(file_paths: List[Path]) -> Dict[str, Set[str]]:
        """Find dependencies between files."""
        dependencies = {}
        
        for file_path in file_paths:
            if file_path.suffix == '.py':
                imports = CodebaseAnalyzer.extract_python_imports(file_path)
                dependencies[str(file_path)] = set(imports)
        
        return dependencies
    
    @staticmethod
    def group_by_directory(files: List[Path]) -> Dict[str, List[Path]]:
        """Group files by their parent directory."""
        groups = {}
        
        for file_path in files:
            parent = str(file_path.parent)
            if parent not in groups:
                groups[parent] = []
            groups[parent].append(file_path)
        
        return groups


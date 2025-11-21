"""Repository crawler for discovering infrastructure files in version control systems."""
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RepositoryCrawler:
    """Base class for repository crawlers."""
    
    def __init__(self, repo_url: str, token: Optional[str] = None):
        """
        Initialize repository crawler.
        
        Args:
            repo_url: Repository URL
            token: Authentication token (if needed)
        """
        self.repo_url = repo_url
        self.token = token
        self.temp_dir: Optional[Path] = None
    
    def clone(self) -> Path:
        """Clone repository to temporary directory."""
        raise NotImplementedError
    
    def discover_files(self, repo_path: Path) -> Dict[str, Optional[str]]:
        """
        Discover infrastructure files in repository.
        
        Returns:
            Dictionary mapping file types to paths (None if not found)
        """
        raise NotImplementedError
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class GitLabCrawler(RepositoryCrawler):
    """Crawler for GitLab repositories."""
    
    # Common file patterns to search for
    FILE_PATTERNS = {
        'gitlab_ci': ['.gitlab-ci.yml', '.gitlab-ci.yaml', 'gitlab-ci.yml', 'gitlab-ci.yaml'],
        'dockerfile': ['Dockerfile', 'Dockerfile.prod', 'Dockerfile.dev', 'docker/Dockerfile'],
        'docker_compose': ['docker-compose.yml', 'docker-compose.yaml', 'docker-compose.prod.yml', 'docker-compose.dev.yml'],
        'ecs_task_def': ['ecs-task-definition.json', 'aws/ecs-task-definition.json', 'infra/ecs-task-definition.json'],
        'cloudformation': ['cloudformation.yaml', 'cloudformation.yml', 'cloudformation.json', 
                          'aws/cloudformation.yaml', 'infra/cloudformation.yaml',
                          'template.yaml', 'template.yml', 'template.json'],
        'terraform': ['terraform.tfstate', 'terraform/terraform.tfstate', '.terraform/terraform.tfstate'],
    }
    
    def __init__(self, repo_url: str, token: Optional[str] = None, branch: Optional[str] = None):
        """
        Initialize GitLab crawler.
        
        Args:
            repo_url: GitLab repository URL
            token: GitLab access token
            branch: Branch to clone (defaults to default branch)
        """
        super().__init__(repo_url, token)
        self.branch = branch
        self.parsed_url = self._parse_gitlab_url(repo_url)
    
    def _parse_gitlab_url(self, url: str) -> Dict[str, str]:
        """Parse GitLab URL to extract components."""
        parsed = urlparse(url)
        
        # Handle different GitLab URL formats
        # https://gitlab.com/group/project.git
        # git@gitlab.com:group/project.git
        # https://gitlab.com/group/project
        
        if url.startswith('git@'):
            # SSH format: git@gitlab.com:group/project.git
            parts = url.replace('git@', '').replace('.git', '').split(':')
            host = parts[0]
            path = parts[1] if len(parts) > 1 else ''
        else:
            # HTTPS format
            host = parsed.netloc
            path = parsed.path.strip('/').replace('.git', '')
        
        return {
            'host': host,
            'path': path,
            'full_url': url
        }
    
    def clone(self) -> Path:
        """Clone GitLab repository to temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="assistant_crawler_"))
        
        # Prepare clone URL with token if provided
        clone_url = self.repo_url
        
        # If token is provided and URL is HTTPS, inject token
        if self.token and self.repo_url.startswith('https://'):
            parsed = urlparse(self.repo_url)
            clone_url = f"{parsed.scheme}://oauth2:{self.token}@{parsed.netloc}{parsed.path}"
        
        try:
            # Clone repository
            clone_cmd = ['git', 'clone', '--depth', '1']
            
            if self.branch:
                clone_cmd.extend(['-b', self.branch])
            
            clone_cmd.extend([clone_url, str(self.temp_dir)])
            
            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return self.temp_dir
            
        except subprocess.CalledProcessError as e:
            self.cleanup()
            raise ValueError(f"Failed to clone repository: {e.stderr}")
        except Exception as e:
            self.cleanup()
            raise ValueError(f"Error cloning repository: {str(e)}")
    
    def discover_files(self, repo_path: Optional[Path] = None) -> Dict[str, Optional[str]]:
        """
        Discover infrastructure files in repository.
        
        Args:
            repo_path: Path to repository (uses cloned path if None)
        
        Returns:
            Dictionary mapping file types to paths (None if not found)
        """
        if repo_path is None:
            repo_path = self.temp_dir
        
        if not repo_path or not repo_path.exists():
            raise ValueError("Repository path does not exist. Clone repository first.")
        
        discovered = {
            'gitlab_ci': None,
            'dockerfile': None,
            'docker_compose': None,
            'ecs_task_def': None,
            'cloudformation': None,
            'terraform': None,  # Will remain None as TF state is remote
        }
        
        # Search for each file type
        for file_type, patterns in self.FILE_PATTERNS.items():
            if file_type == 'terraform':
                # Skip terraform state - it's remote
                continue
            
            for pattern in patterns:
                file_path = repo_path / pattern
                if file_path.exists() and file_path.is_file():
                    discovered[file_type] = str(file_path)
                    break
        
        # Also search recursively for some files if not found in common locations
        if not discovered['gitlab_ci']:
            discovered['gitlab_ci'] = self._find_file_recursive(repo_path, '.gitlab-ci.yml')
        
        if not discovered['dockerfile']:
            discovered['dockerfile'] = self._find_file_recursive(repo_path, 'Dockerfile')
        
        if not discovered['docker_compose']:
            discovered['docker_compose'] = self._find_file_recursive(repo_path, 'docker-compose.yml')
        
        return discovered
    
    def _find_file_recursive(self, root_path: Path, filename: str) -> Optional[str]:
        """Recursively search for a file, excluding common ignore directories."""
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env', '.terraform'}
        
        for root, dirs, files in os.walk(root_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            if filename in files:
                return str(Path(root) / filename)
        
        return None
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file from the repository."""
        if not file_path:
            return None
        
        path = Path(file_path)
        if path.exists() and path.is_file():
            try:
                return path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                return None
        return None


class RepositoryCrawlerFactory:
    """Factory for creating appropriate repository crawler based on URL."""
    
    @staticmethod
    def create_crawler(
        repo_url: str,
        token: Optional[str] = None,
        branch: Optional[str] = None
    ) -> RepositoryCrawler:
        """
        Create appropriate crawler based on repository URL.
        
        Args:
            repo_url: Repository URL
            token: Authentication token
            branch: Branch to clone
        
        Returns:
            RepositoryCrawler instance
        """
        repo_url_lower = repo_url.lower()
        
        # Detect GitLab
        if 'gitlab.com' in repo_url_lower or 'gitlab' in repo_url_lower:
            return GitLabCrawler(repo_url, token, branch)
        
        # Future: Add GitHub, Bitbucket, etc.
        # elif 'github.com' in repo_url_lower:
        #     return GitHubCrawler(repo_url, token, branch)
        
        # Default to GitLab for now
        return GitLabCrawler(repo_url, token, branch)


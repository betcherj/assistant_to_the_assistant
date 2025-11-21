"""Enhanced infrastructure indexer that parses files and generates markdown descriptions."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..types import InfrastructureDescription, InfrastructureSection
from ..utils import BaseLLMClient
from .infrastructure_parsers import InfrastructureParser
from .repository_crawler import RepositoryCrawlerFactory

logger = logging.getLogger(__name__)


class InfrastructureIndexer(BaseLLMClient):
    """Indexes infrastructure files and generates structured markdown descriptions."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview"
    ):
        """
        Initialize the infrastructure indexer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: LLM model to use for indexing
        """
        super().__init__(api_key=api_key, model=model)
        self.parser = InfrastructureParser()
    
    def index_infrastructure(
        self,
        tfstate_path: Optional[str] = None,
        gitlab_ci_path: Optional[str] = None,
        dockerfile_path: Optional[str] = None,
        docker_compose_path: Optional[str] = None,
        ecs_task_def_path: Optional[str] = None,
        cloudformation_path: Optional[str] = None,
        gitlab_token: Optional[str] = None,
        gitlab_repo_url: Optional[str] = None,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        repo_url: Optional[str] = None,
        repo_token: Optional[str] = None,
        repo_branch: Optional[str] = None,
    ) -> InfrastructureDescription:
        """
        Index infrastructure files and generate structured markdown description.
        
        Args:
            tfstate_path: Path to Terraform state file (remote, must be provided)
            gitlab_ci_path: Path to .gitlab-ci.yml file (auto-discovered if repo_url provided)
            dockerfile_path: Path to Dockerfile (auto-discovered if repo_url provided)
            docker_compose_path: Path to docker-compose.yml (auto-discovered if repo_url provided)
            ecs_task_def_path: Path to ECS task definition JSON (auto-discovered if repo_url provided)
            cloudformation_path: Path to CloudFormation template (auto-discovered if repo_url provided)
            gitlab_token: GitLab access token (for additional context)
            gitlab_repo_url: GitLab repository URL (deprecated, use repo_url)
            aws_access_key: AWS access key (for additional context)
            aws_secret_key: AWS secret key
            aws_region: AWS region
            repo_url: Repository URL (will auto-discover files)
            repo_token: Repository access token
            repo_branch: Branch to clone (defaults to default branch)
        
        Returns:
            InfrastructureDescription with structured sections
        """
        # Use repo_url if provided, fallback to gitlab_repo_url for backward compatibility
        effective_repo_url = repo_url or gitlab_repo_url
        effective_repo_token = repo_token or gitlab_token
        
        # Auto-discover files from repository if repo_url is provided
        discovered_files = {}
        crawler = None
        
        if effective_repo_url:
            try:
                crawler = RepositoryCrawlerFactory.create_crawler(
                    repo_url=effective_repo_url,
                    token=effective_repo_token,
                    branch=repo_branch
                )
                
                # Clone repository
                repo_path = crawler.clone()
                
                # Discover files
                discovered_files = crawler.discover_files(repo_path)
                
                # Use discovered files if not explicitly provided
                gitlab_ci_path = gitlab_ci_path or discovered_files.get('gitlab_ci')
                dockerfile_path = dockerfile_path or discovered_files.get('dockerfile')
                docker_compose_path = docker_compose_path or discovered_files.get('docker_compose')
                ecs_task_def_path = ecs_task_def_path or discovered_files.get('ecs_task_def')
                cloudformation_path = cloudformation_path or discovered_files.get('cloudformation')
                
            except Exception as e:
                # Log error but continue with explicitly provided paths
                logger.warning(f"Failed to crawl repository {effective_repo_url}: {e}", exc_info=True)
                if crawler:
                    crawler.cleanup()
        
        # Parse all infrastructure files
        parsed_data = self.parser.parse_all(
            tfstate_path=tfstate_path,
            gitlab_ci_path=gitlab_ci_path,
            dockerfile_path=dockerfile_path,
            docker_compose_path=docker_compose_path,
            ecs_task_def_path=ecs_task_def_path,
            cloudformation_path=cloudformation_path,
        )
        
        # Cleanup crawler if used
        if crawler:
            crawler.cleanup()
        
        # Generate markdown sections using LLM
        sections = self._generate_markdown_sections(parsed_data)
        
        # Combine sections into full markdown document
        markdown_doc = self._combine_sections_to_markdown(sections)
        
        # Extract legacy fields for backward compatibility
        deployment_info = self._extract_deployment_info(parsed_data, sections)
        databases = self._extract_databases(parsed_data)
        services = self._extract_services(parsed_data)
        
        return InfrastructureDescription(
            deployment=deployment_info,
            databases=databases,
            services=services,
            configuration=None,  # Can be populated from sections
            sections=sections,
            markdown_document=markdown_doc
        )
    
    def _generate_markdown_sections(
        self,
        parsed_data: Dict[str, Any]
    ) -> List[InfrastructureSection]:
        """Generate markdown sections from parsed infrastructure data."""
        sections = []
        
        # Generate CI/CD section
        if parsed_data.get('gitlab_ci'):
            cicd_section = self._generate_cicd_section(parsed_data['gitlab_ci'])
            sections.append(cicd_section)
        
        # Generate deployment section
        deployment_data = {}
        if parsed_data.get('dockerfile'):
            deployment_data['dockerfile'] = parsed_data['dockerfile']
        if parsed_data.get('docker_compose'):
            deployment_data['docker_compose'] = parsed_data['docker_compose']
        if parsed_data.get('aws_ecs'):
            deployment_data['ecs'] = parsed_data['aws_ecs']
        if parsed_data.get('terraform'):
            deployment_data['terraform'] = parsed_data['terraform']
        
        if deployment_data:
            deployment_section = self._generate_deployment_section(deployment_data)
            sections.append(deployment_section)
        
        # Generate compute/resources section
        if parsed_data.get('terraform') or parsed_data.get('aws_cloudformation'):
            compute_section = self._generate_compute_section(parsed_data)
            sections.append(compute_section)
        
        # Generate storage section
        storage_section = self._generate_storage_section(parsed_data)
        if storage_section:
            sections.append(storage_section)
        
        # Generate networking section
        networking_section = self._generate_networking_section(parsed_data)
        if networking_section:
            sections.append(networking_section)
        
        return sections
    
    def _generate_cicd_section(self, gitlab_ci_data: Dict[str, Any]) -> InfrastructureSection:
        """Generate CI/CD pipeline section."""
        prompt = f"""Analyze the following GitLab CI/CD configuration and create a comprehensive markdown section describing the CI/CD pipeline.

Focus on:
- Pipeline stages and their purpose
- Key jobs and what they do
- Build and deployment processes
- Testing strategies
- Artifact management
- Environment configurations

GitLab CI Configuration:
{json.dumps(gitlab_ci_data, indent=2)}

Create a well-structured markdown section titled "CI/CD Pipeline" that describes:
1. Overview of the pipeline
2. Stages and workflow
3. Key jobs and their responsibilities
4. Deployment process
5. Testing and quality checks

Return only the markdown content, no code blocks."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an infrastructure documentation expert. Create clear, comprehensive markdown documentation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```", 2)[-1].rsplit("```", 1)[0].strip()
            
            keywords = self._extract_keywords_from_cicd(gitlab_ci_data)
            
            return InfrastructureSection(
                title="CI/CD Pipeline",
                content=content,
                section_type="cicd",
                keywords=keywords
            )
        except Exception as e:
            logger.warning(f"Error generating CI/CD section: {e}", exc_info=True)
            # Fallback to basic description
            return InfrastructureSection(
                title="CI/CD Pipeline",
                content=f"GitLab CI/CD pipeline with {gitlab_ci_data.get('job_count', 0)} jobs across {len(gitlab_ci_data.get('stages', []))} stages.",
                section_type="cicd",
                keywords=["cicd", "gitlab", "pipeline", "deployment"]
            )
    
    def _generate_deployment_section(self, deployment_data: Dict[str, Any]) -> InfrastructureSection:
        """Generate deployment section."""
        prompt = f"""Analyze the following deployment configuration and create a comprehensive markdown section describing the deployment infrastructure.

Focus on:
- Containerization strategy (Docker)
- Container orchestration (ECS, Kubernetes, etc.)
- Deployment environments
- Resource allocation
- Scaling configuration

Deployment Configuration:
{json.dumps(deployment_data, indent=2, default=str)}

Create a well-structured markdown section titled "Deployment Infrastructure" that describes:
1. Containerization approach
2. Deployment platform and orchestration
3. Resource requirements
4. Scaling and availability
5. Environment configuration

Return only the markdown content, no code blocks."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an infrastructure documentation expert. Create clear, comprehensive markdown documentation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```", 2)[-1].rsplit("```", 1)[0].strip()
            
            keywords = ["deployment", "docker", "containers", "aws", "ecs"]
            if deployment_data.get('terraform'):
                keywords.append("terraform")
            if deployment_data.get('ecs'):
                keywords.extend(["ecs", "fargate", "task"])
            
            return InfrastructureSection(
                title="Deployment Infrastructure",
                content=content,
                section_type="deployment",
                keywords=keywords
            )
        except Exception as e:
            logger.warning(f"Error generating deployment section: {e}", exc_info=True)
            return InfrastructureSection(
                title="Deployment Infrastructure",
                content="Deployment infrastructure configured with Docker containers and AWS ECS.",
                section_type="deployment",
                keywords=["deployment", "docker", "aws"]
            )
    
    def _generate_compute_section(self, parsed_data: Dict[str, Any]) -> InfrastructureSection:
        """Generate compute/resources section."""
        resources_data = {}
        if parsed_data.get('terraform'):
            resources_data['terraform_resources'] = parsed_data['terraform'].get('resources', [])
        if parsed_data.get('aws_cloudformation'):
            resources_data['cloudformation_resources'] = parsed_data['aws_cloudformation'].get('resources', {})
        
        if not resources_data:
            return None
        
        prompt = f"""Analyze the following infrastructure resources and create a comprehensive markdown section describing compute resources and infrastructure components.

Focus on:
- Compute instances and their configurations
- Resource types and purposes
- Resource dependencies
- Capacity and scaling

Infrastructure Resources:
{json.dumps(resources_data, indent=2, default=str)}

Create a well-structured markdown section titled "Compute Resources" that describes:
1. Overview of compute infrastructure
2. Key resource types
3. Resource configurations
4. Dependencies and relationships
5. Capacity planning

Return only the markdown content, no code blocks."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an infrastructure documentation expert. Create clear, comprehensive markdown documentation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```", 2)[-1].rsplit("```", 1)[0].strip()
            
            keywords = ["compute", "resources", "infrastructure", "aws"]
            if parsed_data.get('terraform'):
                keywords.append("terraform")
            
            return InfrastructureSection(
                title="Compute Resources",
                content=content,
                section_type="compute",
                keywords=keywords
            )
        except Exception as e:
            logger.warning(f"Error generating compute section: {e}", exc_info=True)
            return InfrastructureSection(
                title="Compute Resources",
                content="Infrastructure resources managed via Terraform and AWS.",
                section_type="compute",
                keywords=["compute", "resources"]
            )
    
    def _generate_storage_section(self, parsed_data: Dict[str, Any]) -> Optional[InfrastructureSection]:
        """Generate storage section."""
        storage_resources = []
        
        # Extract storage-related resources from Terraform
        if parsed_data.get('terraform'):
            for resource in parsed_data['terraform'].get('resources', []):
                resource_type = resource.get('type', '').lower()
                if any(storage_type in resource_type for storage_type in ['s3', 'rds', 'dynamodb', 'efs', 'ebs', 'storage']):
                    storage_resources.append(resource)
        
        # Extract from CloudFormation
        if parsed_data.get('aws_cloudformation'):
            for resource_name, resource_def in parsed_data['aws_cloudformation'].get('resources', {}).items():
                resource_type = resource_def.get('Type', '').lower()
                if any(storage_type in resource_type for storage_type in ['s3', 'rds', 'dynamodb', 'efs', 'ebs']):
                    storage_resources.append({'name': resource_name, 'definition': resource_def})
        
        if not storage_resources:
            return None
        
        prompt = f"""Analyze the following storage resources and create a comprehensive markdown section describing storage infrastructure.

Focus on:
- Storage types (S3, RDS, DynamoDB, etc.)
- Storage configurations
- Data persistence strategies
- Backup and recovery

Storage Resources:
{json.dumps(storage_resources, indent=2, default=str)}

Create a well-structured markdown section titled "Storage Infrastructure" that describes:
1. Storage types and purposes
2. Storage configurations
3. Data persistence and durability
4. Backup strategies

Return only the markdown content, no code blocks."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an infrastructure documentation expert. Create clear, comprehensive markdown documentation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```", 2)[-1].rsplit("```", 1)[0].strip()
            
            keywords = ["storage", "s3", "database", "rds", "aws"]
            
            return InfrastructureSection(
                title="Storage Infrastructure",
                content=content,
                section_type="storage",
                keywords=keywords
            )
        except Exception as e:
            logger.warning(f"Error generating storage section: {e}", exc_info=True)
            return None
    
    def _generate_networking_section(self, parsed_data: Dict[str, Any]) -> Optional[InfrastructureSection]:
        """Generate networking section."""
        networking_resources = []
        
        # Extract networking-related resources
        if parsed_data.get('terraform'):
            for resource in parsed_data['terraform'].get('resources', []):
                resource_type = resource.get('type', '').lower()
                if any(net_type in resource_type for net_type in ['vpc', 'subnet', 'security_group', 'route', 'load_balancer', 'alb', 'nlb']):
                    networking_resources.append(resource)
        
        if parsed_data.get('docker_compose'):
            networking_resources.append({
                'type': 'docker_networks',
                'networks': parsed_data['docker_compose'].get('networks', {})
            })
        
        if not networking_resources:
            return None
        
        prompt = f"""Analyze the following networking resources and create a comprehensive markdown section describing networking infrastructure.

Focus on:
- Network architecture (VPC, subnets)
- Security groups and firewalls
- Load balancers
- Network connectivity

Networking Resources:
{json.dumps(networking_resources, indent=2, default=str)}

Create a well-structured markdown section titled "Networking Infrastructure" that describes:
1. Network architecture
2. Security configurations
3. Load balancing
4. Network connectivity

Return only the markdown content, no code blocks."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an infrastructure documentation expert. Create clear, comprehensive markdown documentation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```", 2)[-1].rsplit("```", 1)[0].strip()
            
            keywords = ["networking", "vpc", "security", "load", "balancer", "aws"]
            
            return InfrastructureSection(
                title="Networking Infrastructure",
                content=content,
                section_type="networking",
                keywords=keywords
            )
        except Exception as e:
            logger.warning(f"Error generating networking section: {e}", exc_info=True)
            return None
    
    def _extract_keywords_from_cicd(self, gitlab_ci_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from GitLab CI data."""
        keywords = ["cicd", "gitlab", "pipeline", "deployment"]
        
        stages = gitlab_ci_data.get('stages', [])
        keywords.extend([stage.lower() for stage in stages])
        
        jobs = gitlab_ci_data.get('jobs', {})
        for job_name in jobs.keys():
            keywords.append(job_name.lower())
        
        return list(set(keywords))
    
    def _combine_sections_to_markdown(self, sections: List[InfrastructureSection]) -> str:
        """Combine sections into a complete markdown document."""
        if not sections:
            return ""
        
        markdown_parts = ["# Infrastructure Documentation\n"]
        
        for section in sections:
            markdown_parts.append(f"## {section.title}\n")
            markdown_parts.append(section.content)
            markdown_parts.append("\n\n")
        
        return "".join(markdown_parts)
    
    def _extract_deployment_info(
        self,
        parsed_data: Dict[str, Any],
        sections: List[InfrastructureSection]
    ) -> Optional[str]:
        """Extract deployment information for backward compatibility."""
        deployment_section = next((s for s in sections if s.section_type == "deployment"), None)
        if deployment_section:
            return deployment_section.content[:500] + "..." if len(deployment_section.content) > 500 else deployment_section.content
        return None
    
    def _extract_databases(self, parsed_data: Dict[str, Any]) -> List[str]:
        """Extract database information."""
        databases = []
        
        if parsed_data.get('terraform'):
            for resource in parsed_data['terraform'].get('resources', []):
                resource_type = resource.get('type', '').lower()
                if 'rds' in resource_type or 'database' in resource_type:
                    databases.append(f"{resource.get('type', 'Unknown')} database")
        
        return databases
    
    def _extract_services(self, parsed_data: Dict[str, Any]) -> List[str]:
        """Extract service information."""
        services = []
        
        if parsed_data.get('docker_compose'):
            services.extend(parsed_data['docker_compose'].get('services', {}).keys())
        
        return services


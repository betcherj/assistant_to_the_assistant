"""Parsers for infrastructure configuration files."""
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


class TerraformStateParser:
    """Parser for Terraform state files (.tfstate)."""
    
    @staticmethod
    def parse(tfstate_path: str) -> Dict[str, Any]:
        """
        Parse Terraform state file.
        
        Args:
            tfstate_path: Path to .tfstate file
        
        Returns:
            Dictionary with parsed terraform state information
        """
        path = Path(tfstate_path)
        if not path.exists():
            raise FileNotFoundError(f"Terraform state file not found: {tfstate_path}")
        
        try:
            with open(path, 'r') as f:
                state_data = json.load(f)
            
            resources = []
            outputs = {}
            
            # Extract resources
            if 'resources' in state_data:
                for resource in state_data['resources']:
                    resource_info = {
                        'type': resource.get('type', 'unknown'),
                        'name': resource.get('name', 'unknown'),
                        'provider': resource.get('provider', 'unknown'),
                        'instances': []
                    }
                    
                    # Extract instance information
                    if 'instances' in resource:
                        for instance in resource['instances']:
                            instance_info = {
                                'attributes': instance.get('attributes', {}),
                                'dependencies': instance.get('dependencies', [])
                            }
                            resource_info['instances'].append(instance_info)
                    
                    resources.append(resource_info)
            
            # Extract outputs
            if 'outputs' in state_data:
                outputs = state_data['outputs']
            
            return {
                'version': state_data.get('version', 'unknown'),
                'terraform_version': state_data.get('terraform_version', 'unknown'),
                'resources': resources,
                'outputs': outputs,
                'resource_count': len(resources)
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Terraform state file: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing Terraform state file: {e}")


class GitLabCIParser:
    """Parser for GitLab CI configuration files (.gitlab-ci.yml)."""
    
    @staticmethod
    def parse(gitlab_ci_path: str) -> Dict[str, Any]:
        """
        Parse GitLab CI configuration file.
        
        Args:
            gitlab_ci_path: Path to .gitlab-ci.yml file
        
        Returns:
            Dictionary with parsed GitLab CI configuration
        """
        path = Path(gitlab_ci_path)
        if not path.exists():
            raise FileNotFoundError(f"GitLab CI file not found: {gitlab_ci_path}")
        
        try:
            with open(path, 'r') as f:
                ci_config = yaml.safe_load(f)
            
            if not ci_config:
                return {}
            
            stages = ci_config.get('stages', [])
            jobs = {}
            variables = ci_config.get('variables', {})
            services = []
            before_script = ci_config.get('before_script', [])
            after_script = ci_config.get('after_script', [])
            
            # Extract job information
            for key, value in ci_config.items():
                if key not in ['stages', 'variables', 'before_script', 'after_script', 'include']:
                    if isinstance(value, dict):
                        job_info = {
                            'stage': value.get('stage', 'unknown'),
                            'script': value.get('script', []),
                            'image': value.get('image'),
                            'services': value.get('services', []),
                            'tags': value.get('tags', []),
                            'only': value.get('only'),
                            'except': value.get('except'),
                            'when': value.get('when', 'on_success'),
                            'artifacts': value.get('artifacts'),
                            'dependencies': value.get('dependencies', []),
                            'needs': value.get('needs', []),
                            'environment': value.get('environment'),
                            'cache': value.get('cache'),
                        }
                        jobs[key] = job_info
                        
                        # Collect services
                        if job_info['services']:
                            services.extend(job_info['services'])
            
            return {
                'stages': stages,
                'jobs': jobs,
                'variables': variables,
                'before_script': before_script,
                'after_script': after_script,
                'services': list(set(services)),
                'job_count': len(jobs)
            }
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in GitLab CI file: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing GitLab CI file: {e}")


class DockerParser:
    """Parser for Docker configuration files."""
    
    @staticmethod
    def parse_dockerfile(dockerfile_path: str) -> Dict[str, Any]:
        """
        Parse Dockerfile.
        
        Args:
            dockerfile_path: Path to Dockerfile
        
        Returns:
            Dictionary with parsed Dockerfile information
        """
        path = Path(dockerfile_path)
        if not path.exists():
            raise FileNotFoundError(f"Dockerfile not found: {dockerfile_path}")
        
        try:
            content = path.read_text()
            lines = content.split('\n')
            
            base_image = None
            exposed_ports = []
            environment_vars = []
            volumes = []
            commands = []
            workdir = None
            user = None
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse FROM instruction
                if line.upper().startswith('FROM'):
                    base_image = line.split()[1] if len(line.split()) > 1 else None
                
                # Parse EXPOSE instruction
                elif line.upper().startswith('EXPOSE'):
                    ports = line.split()[1:]
                    exposed_ports.extend(ports)
                
                # Parse ENV instruction
                elif line.upper().startswith('ENV'):
                    env_part = ' '.join(line.split()[1:])
                    if '=' in env_part:
                        env_vars = re.findall(r'(\w+)=([^\s]+)', env_part)
                        environment_vars.extend(env_vars)
                
                # Parse VOLUME instruction
                elif line.upper().startswith('VOLUME'):
                    volume_part = ' '.join(line.split()[1:])
                    volumes.append(volume_part)
                
                # Parse WORKDIR instruction
                elif line.upper().startswith('WORKDIR'):
                    workdir = ' '.join(line.split()[1:])
                
                # Parse USER instruction
                elif line.upper().startswith('USER'):
                    user = ' '.join(line.split()[1:])
                
                # Collect RUN commands
                elif line.upper().startswith('RUN'):
                    commands.append(' '.join(line.split()[1:]))
            
            return {
                'base_image': base_image,
                'exposed_ports': exposed_ports,
                'environment_vars': environment_vars,
                'volumes': volumes,
                'workdir': workdir,
                'user': user,
                'run_commands': commands,
                'content': content
            }
        except Exception as e:
            raise ValueError(f"Error parsing Dockerfile: {e}")
    
    @staticmethod
    def parse_docker_compose(docker_compose_path: str) -> Dict[str, Any]:
        """
        Parse docker-compose.yml file.
        
        Args:
            docker_compose_path: Path to docker-compose.yml
        
        Returns:
            Dictionary with parsed docker-compose information
        """
        path = Path(docker_compose_path)
        if not path.exists():
            raise FileNotFoundError(f"Docker compose file not found: {docker_compose_path}")
        
        try:
            with open(path, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            if not compose_config:
                return {}
            
            services = {}
            networks = compose_config.get('networks', {})
            volumes = compose_config.get('volumes', {})
            
            # Extract service information
            if 'services' in compose_config:
                for service_name, service_config in compose_config['services'].items():
                    service_info = {
                        'image': service_config.get('image'),
                        'build': service_config.get('build'),
                        'ports': service_config.get('ports', []),
                        'environment': service_config.get('environment', {}),
                        'volumes': service_config.get('volumes', []),
                        'networks': service_config.get('networks', []),
                        'depends_on': service_config.get('depends_on', []),
                        'command': service_config.get('command'),
                        'restart': service_config.get('restart'),
                    }
                    services[service_name] = service_info
            
            return {
                'version': compose_config.get('version'),
                'services': services,
                'networks': networks,
                'volumes': volumes,
                'service_count': len(services)
            }
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in docker-compose file: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing docker-compose file: {e}")


class AWSConfigParser:
    """Parser for AWS-specific configuration files."""
    
    @staticmethod
    def parse_ecs_task_definition(task_def_path: str) -> Dict[str, Any]:
        """Parse ECS task definition JSON file."""
        path = Path(task_def_path)
        if not path.exists():
            raise FileNotFoundError(f"ECS task definition not found: {task_def_path}")
        
        try:
            with open(path, 'r') as f:
                task_def = json.load(f)
            
            return {
                'family': task_def.get('family'),
                'network_mode': task_def.get('networkMode'),
                'cpu': task_def.get('cpu'),
                'memory': task_def.get('memory'),
                'container_definitions': task_def.get('containerDefinitions', []),
                'requires_compatibilities': task_def.get('requiresCompatibilities', []),
                'task_role_arn': task_def.get('taskRoleArn'),
                'execution_role_arn': task_def.get('executionRoleArn'),
            }
        except Exception as e:
            raise ValueError(f"Error parsing ECS task definition: {e}")
    
    @staticmethod
    def parse_cloudformation_template(cf_path: str) -> Dict[str, Any]:
        """Parse CloudFormation template (YAML or JSON)."""
        path = Path(cf_path)
        if not path.exists():
            raise FileNotFoundError(f"CloudFormation template not found: {cf_path}")
        
        try:
            content = path.read_text()
            
            # Try YAML first
            try:
                template = yaml.safe_load(content)
            except yaml.YAMLError:
                # Try JSON
                template = json.loads(content)
            
            return {
                'description': template.get('Description'),
                'parameters': template.get('Parameters', {}),
                'resources': template.get('Resources', {}),
                'outputs': template.get('Outputs', {}),
                'resource_count': len(template.get('Resources', {}))
            }
        except Exception as e:
            raise ValueError(f"Error parsing CloudFormation template: {e}")


class InfrastructureParser:
    """Main infrastructure parser that coordinates all parsers."""
    
    def __init__(self):
        self.tf_parser = TerraformStateParser()
        self.gitlab_parser = GitLabCIParser()
        self.docker_parser = DockerParser()
        self.aws_parser = AWSConfigParser()
    
    def parse_all(
        self,
        tfstate_path: Optional[str] = None,
        gitlab_ci_path: Optional[str] = None,
        dockerfile_path: Optional[str] = None,
        docker_compose_path: Optional[str] = None,
        ecs_task_def_path: Optional[str] = None,
        cloudformation_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parse all provided infrastructure files.
        
        Missing files are skipped gracefully - no errors are raised for missing files.
        
        Returns:
            Dictionary with all parsed infrastructure data
        """
        parsed_data = {
            'terraform': None,
            'gitlab_ci': None,
            'dockerfile': None,
            'docker_compose': None,
            'aws_ecs': None,
            'aws_cloudformation': None,
        }
        
        if tfstate_path:
            try:
                parsed_data['terraform'] = self.tf_parser.parse(tfstate_path)
            except FileNotFoundError:
                # Skip missing terraform state file silently
                pass
            except Exception as e:
                # Log other errors but don't fail
                logger.warning(f"Error parsing Terraform state file: {e}", exc_info=True)
                parsed_data['terraform_error'] = str(e)
        
        if gitlab_ci_path:
            try:
                parsed_data['gitlab_ci'] = self.gitlab_parser.parse(gitlab_ci_path)
            except FileNotFoundError:
                # Skip missing GitLab CI file silently
                pass
            except Exception as e:
                logger.warning(f"Error parsing GitLab CI file: {e}", exc_info=True)
                parsed_data['gitlab_ci_error'] = str(e)
        
        if dockerfile_path:
            try:
                parsed_data['dockerfile'] = self.docker_parser.parse_dockerfile(dockerfile_path)
            except FileNotFoundError:
                # Skip missing Dockerfile silently
                pass
            except Exception as e:
                logger.warning(f"Error parsing Dockerfile: {e}", exc_info=True)
                parsed_data['dockerfile_error'] = str(e)
        
        if docker_compose_path:
            try:
                parsed_data['docker_compose'] = self.docker_parser.parse_docker_compose(docker_compose_path)
            except FileNotFoundError:
                # Skip missing docker-compose file silently
                pass
            except Exception as e:
                logger.warning(f"Error parsing docker-compose file: {e}", exc_info=True)
                parsed_data['docker_compose_error'] = str(e)
        
        if ecs_task_def_path:
            try:
                parsed_data['aws_ecs'] = self.aws_parser.parse_ecs_task_definition(ecs_task_def_path)
            except FileNotFoundError:
                # Skip missing ECS task definition silently
                pass
            except Exception as e:
                logger.warning(f"Error parsing ECS task definition: {e}", exc_info=True)
                parsed_data['aws_ecs_error'] = str(e)
        
        if cloudformation_path:
            try:
                parsed_data['aws_cloudformation'] = self.aws_parser.parse_cloudformation_template(cloudformation_path)
            except FileNotFoundError:
                # Skip missing CloudFormation template silently
                pass
            except Exception as e:
                logger.warning(f"Error parsing CloudFormation template: {e}", exc_info=True)
                parsed_data['aws_cloudformation_error'] = str(e)
        
        return parsed_data


"""CLI entry point for Assistant to the Assistant."""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import yaml

from ..config import (
    DEFAULT_BUSINESS_GOALS_YAML,
    DEFAULT_AGENT_GUIDELINES_YAML,
    DEFAULT_SYSTEM_DESCRIPTION_YAML,
    DEFAULT_FEATURE_SPEC_YAML,
)
from ..project_indexer import InfrastructureIndexer, BusinessContextIndexer
from ..project_resources import ProjectResourceManager
from ..prompt_construction import PromptBuilder
from ..types import (
    BusinessGoals,
    AgentGuidelines,
    SystemDescription,
    SystemIOExample,
    Component,
    InfrastructureDescription,
)
from ..utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def load_yaml(file_path: Path) -> dict:
    """Load YAML file and return as dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def set_business_goals_from_yaml(yaml_path: Path, resource_manager: ProjectResourceManager):
    """Set business goals from YAML file."""
    data = load_yaml(yaml_path)
    business_goals = BusinessGoals(
        purpose=data.get('purpose', ''),
        external_constraints=data.get('external_constraints', [])
    )
    resource_manager.save_business_goals(business_goals)
    print("✓ Business goals saved")


def set_agent_guidelines_from_yaml(yaml_path: Path, resource_manager: ProjectResourceManager):
    """Set agent guidelines from YAML file."""
    data = load_yaml(yaml_path)
    agent_guidelines = AgentGuidelines(
        guardrails=data.get('guardrails', []),
        best_practices=data.get('best_practices', []),
        coding_standards=data.get('coding_standards', [])
    )
    resource_manager.save_agent_guidelines(agent_guidelines)
    print("✓ Agent guidelines saved")


def set_system_description_from_yaml(yaml_path: Path, resource_manager: ProjectResourceManager):
    """Set system description from YAML file."""
    data = load_yaml(yaml_path)
    
    io_examples = [
        SystemIOExample(**ex) for ex in data.get('io_examples', [])
    ]
    
    components = [
        Component(**comp) for comp in data.get('components', [])
    ]
    
    infrastructure_data = data.get('infrastructure', {})
    infrastructure = InfrastructureDescription(**infrastructure_data) if infrastructure_data else InfrastructureDescription()
    
    system_description = SystemDescription(
        io_examples=io_examples,
        components=components,
        infrastructure=infrastructure
    )
    resource_manager.save_system_description(system_description)
    print("✓ System description saved")


def generate_prompt_from_yaml(yaml_path: Path, resource_manager: ProjectResourceManager, prompt_builder: PromptBuilder):
    """Generate prompt from YAML file."""
    data = load_yaml(yaml_path)
    
    feature_description = data.get('feature_description', '')
    if not feature_description:
        raise ValueError("feature_description is required in YAML file")
    
    feature_type = data.get('feature_type', 'feature')
    model = data.get('model', 'gpt-4-turbo-preview')
    include_all_context = data.get('include_all_context', False)
    enable_classification = data.get('enable_classification', True)
    enable_optimization = data.get('enable_optimization', True)
    
    feature_examples = None
    if 'feature_examples' in data:
        # Pass dictionaries directly - prompt_builder will convert to FeatureExample objects
        feature_examples = data['feature_examples']
    
    result = prompt_builder.build_prompt(
        feature_description=feature_description,
        feature_type=feature_type,
        feature_examples=feature_examples,
        model=model,
        include_all_context=include_all_context,
        enable_classification=enable_classification,
        enable_optimization=enable_optimization
    )
    
    print("\n" + "="*80)
    print("GENERATED PROMPT:")
    print("="*80)
    print(result["prompt"])
    print("="*80)
    
    if result.get("classification"):
        print("\nClassification Results:")
        print(f"  Feature Category: {result['classification'].get('feature_category', 'unknown')}")
        print(f"  Complexity: {result['classification'].get('complexity', 'unknown')}")
        print(f"  Reasoning: {result['classification'].get('reasoning', 'N/A')}")
    
    print(f"\nOptimized: {result.get('optimized', False)}")
    print(f"Classified: {result.get('classified', False)}")
    
    # Optionally save to file
    output_file = data.get('output_file')
    if output_file:
        with open(output_file, 'w') as f:
            f.write(result["prompt"])
        print(f"\n✓ Prompt saved to {output_file}")


def index_project(args, resource_manager: ProjectResourceManager):
    """Index project codebase."""
    try:
        result = resource_manager.index_project(
            codebase_paths=args.codebase_paths or [],
            config_paths=args.config_paths or [],
            dockerfile_path=args.dockerfile_path,
            readme_path=args.readme_path,
            document_paths=args.document_paths or [],
            api_key=args.api_key,
            model=args.model
        )
        print(f"✓ Project indexed successfully")
        print(f"  Components indexed: {len(result['component_index'].components)}")
        print(f"  Infrastructure indexed: {result['infrastructure'] is not None}")
        print(f"  Documents indexed: {len(result.get('document_summaries', {}))}")
    except Exception as e:
        logger.error(f"Indexing failed: {e}", exc_info=True)
        sys.exit(1)


def index_infrastructure(args, resource_manager: ProjectResourceManager):
    """Index infrastructure files."""
    try:
        indexer = InfrastructureIndexer(
            api_key=args.api_key,
            model=args.model
        )
        
        infrastructure = indexer.index_infrastructure(
            repo_url=args.repo_url,
            repo_token=args.repo_token,
            repo_branch=args.repo_branch,
            tfstate_path=args.tfstate_path,
            gitlab_ci_path=args.gitlab_ci_path,
            dockerfile_path=args.dockerfile_path,
            docker_compose_path=args.docker_compose_path,
            ecs_task_def_path=args.ecs_task_def_path,
            cloudformation_path=args.cloudformation_path,
            gitlab_token=args.gitlab_token,
            gitlab_repo_url=args.gitlab_repo_url,
            aws_access_key=args.aws_access_key,
            aws_secret_key=args.aws_secret_key,
            aws_region=args.aws_region,
        )
        
        resource_manager.save_infrastructure(infrastructure)
        
        # Update system description with infrastructure
        system_description = resource_manager.load_system_description()
        if system_description:
            system_description.infrastructure = infrastructure
            resource_manager.save_system_description(system_description)
        else:
            system_description = SystemDescription(infrastructure=infrastructure)
            resource_manager.save_system_description(system_description)
        
        print(f"✓ Infrastructure indexed successfully")
        print(f"  Sections generated: {len(infrastructure.sections)}")
        print(f"  Section types: {[s.section_type for s in infrastructure.sections]}")
    except Exception as e:
        logger.error(f"Infrastructure indexing failed: {e}", exc_info=True)
        sys.exit(1)


def index_business_context(args, resource_manager: ProjectResourceManager):
    """Index business context files."""
    try:
        indexer = BusinessContextIndexer(
            api_key=args.api_key,
            model=args.model,
            aws_access_key=args.aws_access_key,
            aws_secret_key=args.aws_secret_key,
            aws_region=args.aws_region
        )
        
        result = indexer.index_business_context(
            file_paths=args.file_paths,
            output_dir=args.output_dir
        )
        
        from ..types import BusinessContext, BusinessContextArtifact
        
        artifacts = [
            BusinessContextArtifact(
                filename=art["filename"],
                file_type=art["file_type"],
                source_path=art["source_path"],
                artifact_path=art["artifact_path"],
                indexed_at=result["indexed_at"]
            )
            for art in result["artifacts"]
        ]
        
        business_context = BusinessContext(
            artifacts=artifacts,
            indexed_at=result["indexed_at"]
        )
        
        resource_manager.save_business_context(business_context)
        
        print(f"✓ Business context indexed successfully")
        print(f"  Total files: {result['total_files']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Output directory: {result['output_directory']}")
    except Exception as e:
        logger.error(f"Business context indexing failed: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Assistant to the Assistant - Low code LLM assisted software development framework",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Set business goals from YAML
    parser_business_goals = subparsers.add_parser(
        'set-business-goals',
        help='Set business goals from YAML file'
    )
    parser_business_goals.add_argument(
        'yaml_file',
        type=Path,
        nargs='?',
        default=DEFAULT_BUSINESS_GOALS_YAML,
        help=f'Path to YAML file with business goals (default: {DEFAULT_BUSINESS_GOALS_YAML})'
    )
    
    # Set agent guidelines from YAML
    parser_agent_guidelines = subparsers.add_parser(
        'set-agent-guidelines',
        help='Set agent guidelines from YAML file'
    )
    parser_agent_guidelines.add_argument(
        'yaml_file',
        type=Path,
        nargs='?',
        default=DEFAULT_AGENT_GUIDELINES_YAML,
        help=f'Path to YAML file with agent guidelines (default: {DEFAULT_AGENT_GUIDELINES_YAML})'
    )
    
    # Set system description from YAML
    parser_system_description = subparsers.add_parser(
        'set-system-description',
        help='Set system description from YAML file'
    )
    parser_system_description.add_argument(
        'yaml_file',
        type=Path,
        nargs='?',
        default=DEFAULT_SYSTEM_DESCRIPTION_YAML,
        help=f'Path to YAML file with system description (default: {DEFAULT_SYSTEM_DESCRIPTION_YAML})'
    )
    
    # Generate prompt from YAML
    parser_prompt = subparsers.add_parser(
        'generate-prompt',
        help='Generate prompt from YAML file'
    )
    parser_prompt.add_argument(
        'yaml_file',
        type=Path,
        nargs='?',
        default=DEFAULT_FEATURE_SPEC_YAML,
        help=f'Path to YAML file with feature specification (default: {DEFAULT_FEATURE_SPEC_YAML})'
    )
    parser_prompt.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (if not in env)'
    )
    
    # Index project
    parser_index = subparsers.add_parser(
        'index-project',
        help='Index project codebase, infrastructure, and documents'
    )
    parser_index.add_argument(
        '--codebase-paths',
        nargs='+',
        help='Paths to codebase files/directories to index'
    )
    parser_index.add_argument(
        '--config-paths',
        nargs='+',
        help='Paths to configuration files'
    )
    parser_index.add_argument(
        '--dockerfile-path',
        type=str,
        help='Path to Dockerfile'
    )
    parser_index.add_argument(
        '--readme-path',
        type=str,
        help='Path to README'
    )
    parser_index.add_argument(
        '--document-paths',
        nargs='+',
        help='Paths to contextual documents'
    )
    parser_index.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (if not in env)'
    )
    parser_index.add_argument(
        '--model',
        type=str,
        default='gpt-4-turbo-preview',
        help='LLM model to use'
    )
    
    # Index infrastructure
    parser_index_infra = subparsers.add_parser(
        'index-infrastructure',
        help='Index infrastructure files'
    )
    parser_index_infra.add_argument(
        '--repo-url',
        type=str,
        help='Repository URL (GitLab supported)'
    )
    parser_index_infra.add_argument(
        '--repo-token',
        type=str,
        help='Repository access token'
    )
    parser_index_infra.add_argument(
        '--repo-branch',
        type=str,
        help='Branch to clone'
    )
    parser_index_infra.add_argument(
        '--tfstate-path',
        type=str,
        help='Path to Terraform state file'
    )
    parser_index_infra.add_argument(
        '--gitlab-ci-path',
        type=str,
        help='Path to .gitlab-ci.yml file'
    )
    parser_index_infra.add_argument(
        '--dockerfile-path',
        type=str,
        help='Path to Dockerfile'
    )
    parser_index_infra.add_argument(
        '--docker-compose-path',
        type=str,
        help='Path to docker-compose.yml'
    )
    parser_index_infra.add_argument(
        '--ecs-task-def-path',
        type=str,
        help='Path to ECS task definition JSON'
    )
    parser_index_infra.add_argument(
        '--cloudformation-path',
        type=str,
        help='Path to CloudFormation template'
    )
    parser_index_infra.add_argument(
        '--aws-access-key',
        type=str,
        help='AWS access key'
    )
    parser_index_infra.add_argument(
        '--aws-secret-key',
        type=str,
        help='AWS secret key'
    )
    parser_index_infra.add_argument(
        '--aws-region',
        type=str,
        help='AWS region'
    )
    parser_index_infra.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (if not in env)'
    )
    parser_index_infra.add_argument(
        '--model',
        type=str,
        default='gpt-4-turbo-preview',
        help='LLM model to use'
    )
    
    # Index business context
    parser_index_business = subparsers.add_parser(
        'index-business-context',
        help='Index business context files (PDF, CSV, markdown)'
    )
    parser_index_business.add_argument(
        '--file-paths',
        nargs='+',
        required=True,
        help='List of file paths (local or S3 s3://bucket/key format)'
    )
    parser_index_business.add_argument(
        '--output-dir',
        type=str,
        help='Directory to save markdown artifacts'
    )
    parser_index_business.add_argument(
        '--aws-access-key',
        type=str,
        help='AWS access key for S3 access'
    )
    parser_index_business.add_argument(
        '--aws-secret-key',
        type=str,
        help='AWS secret key for S3 access'
    )
    parser_index_business.add_argument(
        '--aws-region',
        type=str,
        help='AWS region'
    )
    parser_index_business.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (if not in env)'
    )
    parser_index_business.add_argument(
        '--model',
        type=str,
        default='gpt-4-turbo-preview',
        help='LLM model to use'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(level=getattr(logging, args.log_level))
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize managers
    resource_manager = ProjectResourceManager()
    prompt_builder = PromptBuilder(resource_manager)
    
    try:
        if args.command == 'set-business-goals':
            set_business_goals_from_yaml(args.yaml_file, resource_manager)
        
        elif args.command == 'set-agent-guidelines':
            set_agent_guidelines_from_yaml(args.yaml_file, resource_manager)
        
        elif args.command == 'set-system-description':
            set_system_description_from_yaml(args.yaml_file, resource_manager)
        
        elif args.command == 'generate-prompt':
            generate_prompt_from_yaml(args.yaml_file, resource_manager, prompt_builder)
        
        elif args.command == 'index-project':
            index_project(args, resource_manager)
        
        elif args.command == 'index-infrastructure':
            index_infrastructure(args, resource_manager)
        
        elif args.command == 'index-business-context':
            index_business_context(args, resource_manager)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()


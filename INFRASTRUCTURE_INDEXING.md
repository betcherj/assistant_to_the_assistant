# Infrastructure Indexing Guide

## Overview

The infrastructure indexing feature parses infrastructure configuration files (Terraform state, GitLab CI, Docker, AWS configurations) and generates structured markdown documentation that is automatically included in feature prompts based on relevance.

## Supported File Types

1. **Terraform State Files** (`.tfstate`)
   - Parses resource definitions, outputs, and dependencies
   - Extracts compute, storage, and networking resources

2. **GitLab CI Configuration** (`.gitlab-ci.yml`)
   - Parses pipeline stages, jobs, and configurations
   - Extracts build, test, and deployment processes

3. **Docker Files**
   - `Dockerfile`: Parses base images, exposed ports, environment variables, volumes
   - `docker-compose.yml`: Parses services, networks, volumes, dependencies

4. **AWS Configurations**
   - ECS Task Definitions: Parses container definitions, resource requirements
   - CloudFormation Templates: Parses resources, parameters, outputs

## API Usage

### Index Infrastructure (with Repository Auto-Discovery)

The recommended approach is to provide a repository URL and let the system automatically discover infrastructure files:

```bash
curl -X POST "http://localhost:8000/index-infrastructure" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://gitlab.com/your-org/your-project",
    "repo_token": "your_gitlab_token",
    "repo_branch": "main",
    "tfstate_path": "s3://your-bucket/terraform.tfstate",
    "model": "gpt-4-turbo-preview"
  }'
```

The system will:
1. Clone the repository (GitLab supported, extensible to other VCS)
2. Automatically discover infrastructure files:
   - `.gitlab-ci.yml` (searched in root and common locations)
   - `Dockerfile` (searched recursively)
   - `docker-compose.yml` (searched recursively)
   - ECS task definitions (searched in `aws/` and `infra/` directories)
   - CloudFormation templates (searched in `aws/` and `infra/` directories)
3. Parse discovered files and generate markdown documentation
4. Skip missing files gracefully (no errors raised)

### Index Infrastructure (Manual File Paths)

You can also provide file paths manually:

```bash
curl -X POST "http://localhost:8000/index-infrastructure" \
  -H "Content-Type: application/json" \
  -d '{
    "tfstate_path": "./terraform/terraform.tfstate",
    "gitlab_ci_path": "./.gitlab-ci.yml",
    "dockerfile_path": "./Dockerfile",
    "docker_compose_path": "./docker-compose.yml",
    "ecs_task_def_path": "./aws/ecs-task-definition.json",
    "cloudformation_path": "./aws/cloudformation.yaml",
    "aws_access_key": "your_aws_key",
    "aws_secret_key": "your_aws_secret",
    "aws_region": "us-east-1",
    "model": "gpt-4-turbo-preview"
  }'
```

**Note**: If both `repo_url` and individual file paths are provided, the explicitly provided paths take precedence over auto-discovered ones.

### Response

The endpoint returns:
- Number of sections generated
- Section types (cicd, deployment, storage, networking, compute)
- Complete infrastructure description with markdown document

## Generated Sections

The infrastructure indexer generates the following markdown sections:

1. **CI/CD Pipeline**
   - Pipeline stages and workflow
   - Key jobs and responsibilities
   - Deployment process
   - Testing strategies

2. **Deployment Infrastructure**
   - Containerization approach
   - Deployment platform (ECS, Kubernetes, etc.)
   - Resource requirements
   - Scaling configuration

3. **Compute Resources**
   - Infrastructure resources
   - Resource types and configurations
   - Dependencies and relationships

4. **Storage Infrastructure**
   - Storage types (S3, RDS, DynamoDB, etc.)
   - Storage configurations
   - Data persistence strategies

5. **Networking Infrastructure**
   - Network architecture (VPC, subnets)
   - Security configurations
   - Load balancing

## Automatic Context Selection

When generating feature prompts, the system automatically selects relevant infrastructure sections based on:

- **Keyword matching**: Matches keywords from feature descriptions with section keywords
- **Section type matching**: Identifies relevant section types (cicd, deployment, storage, etc.)
- **Title matching**: Matches feature keywords with section titles

### Example

If a feature description mentions "deploy new container", the system will automatically include:
- CI/CD Pipeline section (for deployment process)
- Deployment Infrastructure section (for container configuration)

## Python API Usage

```python
from assistant_to_the_assistant.project_indexer import InfrastructureIndexer
from assistant_to_the_assistant.project_resources import ProjectResourceManager

# Initialize indexer
indexer = InfrastructureIndexer(
    api_key="your_openai_key",
    model="gpt-4-turbo-preview"
)

# Index infrastructure
infrastructure = indexer.index_infrastructure(
    tfstate_path="./terraform/terraform.tfstate",
    gitlab_ci_path="./.gitlab-ci.yml",
    dockerfile_path="./Dockerfile",
    docker_compose_path="./docker-compose.yml",
    ecs_task_def_path="./aws/ecs-task-definition.json"
)

# Save to resources
resource_manager = ProjectResourceManager()
resource_manager.save_infrastructure(infrastructure)

# Access sections
for section in infrastructure.sections:
    print(f"{section.title} ({section.section_type})")
    print(section.content)
    print(f"Keywords: {section.keywords}")
```

## Integration with Feature Prompts

Infrastructure sections are automatically included in feature prompts when:

1. Infrastructure has been indexed and saved
2. Feature description matches section keywords or types
3. Context selector determines relevance

The prompt builder will include relevant sections under the "Infrastructure" section of the generated prompt.

## File Path Handling

- **Relative paths**: Resolved relative to project root (if set) or current working directory
- **Absolute paths**: Used as-is
- **Missing files**: Parsing errors are caught and logged, but don't stop the indexing process

## Authentication

The following authentication parameters are accepted but not required for basic file parsing:

- `gitlab_token`: For accessing GitLab API (future enhancement)
- `gitlab_repo_url`: For repository context (future enhancement)
- `aws_access_key` / `aws_secret_key` / `aws_region`: For AWS API access (future enhancement)

Currently, these are stored but not actively used. They are reserved for future enhancements where live API queries might be needed.


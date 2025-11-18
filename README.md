# Assistant to the Assistant

**Low code LLM assisted software development framework**

A framework for writing prompts that improve accuracy and save developer time when using LLMs for software engineering. This system empowers engineers not familiar with LLMs or non-engineers to use Gen AI for SWE by injecting coding best practices and smart context to improve generated code results.

## Features

- **Project Indexing**: Automatically index codebases, infrastructure, databases, and contextual documents using LLM to create natural language descriptions
- **Smart Context Selection**: Dynamically select relevant context based on feature descriptions
- **Model-Specific Formatting**: Format prompts optimized for different LLM models (GPT-4, Claude, etc.)
- **Resource Management**: Store and manage project-specific resources (business goals, system descriptions, agent guidelines)
- **RESTful API**: FastAPI-based endpoints for easy integration

## Project Structure

```
assistant_to_the_assistant/
├── project_indexer/       # Functions to index codebases, infra, databases, and documents
├── project_resources/     # Project-specific resources (manually defined or created by indexer)
├── types/                 # Pydantic types for type validation and component objects
├── prompt_construction/   # Combines project info and business context to create formatted prompts
├── entry_point/           # FastAPI endpoints for interaction
└── main.py                # Application entry point
```

## Prompt Artifacts

The framework organizes prompts into the following artifacts:

1. **Business Goals**
   - Purpose of system within the business context
   - External constraints not visible within the code

2. **System Description**
   - System-level input/output examples
   - Component descriptions
   - Infrastructure description

3. **Agent Guidelines** (Agents.md)
   - LLM guardrails
   - Team-specific best practices
   - Coding standards

4. **Feature/Fix/Instance Prompt**
   - What we are trying to do in this prompt

5. **Feature Examples**
   - Input/output examples at feature level if relevant

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd assistant_to_the_assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Starting the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Index Project

Index your project codebase, infrastructure, and documents:

```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "codebase_paths": ["./src", "./lib"],
    "config_paths": ["./config.yaml"],
    "dockerfile_path": "./Dockerfile",
    "readme_path": "./README.md",
    "document_paths": ["./docs"],
    "model": "gpt-4-turbo-preview"
  }'
```

#### 1a. Index Infrastructure from Repository (NEW)

Automatically discover and index infrastructure files from a GitLab repository:

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

The endpoint will automatically discover:
- `.gitlab-ci.yml` files
- `Dockerfile` files
- `docker-compose.yml` files
- ECS task definitions
- CloudFormation templates

Missing files are skipped gracefully. Terraform state files must be provided separately as they are typically stored remotely.

#### 1b. Index Business Context (NEW)

Index business context files (PDF, CSV, markdown) from local or S3 paths:

```bash
curl -X POST "http://localhost:8000/index-business-context" \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": [
      "./docs/business-requirements.pdf",
      "./data/customer-data.csv",
      "s3://my-bucket/business-context/domain-knowledge.md"
    ],
    "aws_access_key": "your_aws_key",
    "aws_secret_key": "your_aws_secret",
    "aws_region": "us-east-1",
    "model": "gpt-4-turbo-preview"
  }'
```

The endpoint will:
- Extract text from PDF files
- Parse and summarize CSV files
- Process markdown files
- Create markdown index artifacts using LLM
- Store artifacts in `.project-resources/business-context/`

Supported file sources:
- Local file paths (e.g., `./docs/file.pdf`)
- S3 paths (e.g., `s3://bucket-name/path/to/file.csv`)

Supported file types:
- PDF (`.pdf`)
- CSV (`.csv`)
- Markdown (`.md`, `.markdown`)

The generated markdown artifacts are automatically included in feature prompts to provide necessary business context.

#### 2. Set Business Goals

Define the business context:

```bash
curl -X POST "http://localhost:8000/business-goals" \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "Build a REST API for managing user accounts",
    "external_constraints": [
      "Must comply with GDPR",
      "Must support 10k concurrent users"
    ]
  }'
```

#### 3. Set System Description

Define system-level information:

```bash
curl -X POST "http://localhost:8000/system-description" \
  -H "Content-Type: application/json" \
  -d '{
    "io_examples": [
      {
        "input_description": "POST /users with user data",
        "output_description": "Created user object with ID"
      }
    ],
    "components": [],
    "infrastructure": {
      "deployment": "Docker containers on AWS ECS",
      "databases": ["PostgreSQL"],
      "services": ["Redis cache"]
    }
  }'
```

#### 4. Set Agent Guidelines

Define coding standards and best practices:

```bash
curl -X POST "http://localhost:8000/agent-guidelines" \
  -H "Content-Type: application/json" \
  -d '{
    "guardrails": [
      "Never commit API keys to code",
      "Always validate user input"
    ],
    "best_practices": [
      "Use type hints",
      "Write docstrings for all functions",
      "Follow PEP 8 style guide"
    ],
    "coding_standards": [
      "Use async/await for I/O operations",
      "Return Pydantic models from API endpoints"
    ]
  }'
```

#### 5. Generate Prompt

Generate a formatted prompt for feature development with automatic classification and optimization:

```bash
curl -X POST "http://localhost:8000/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_description": "Add user authentication endpoint",
    "feature_type": "feature",
    "model": "gpt-4-turbo-preview",
    "include_all_context": false,
    "enable_classification": true,
    "enable_optimization": true,
    "return_metadata": true,
    "feature_examples": [
      {
        "input_description": "POST /auth/login with email and password",
        "output_description": "JWT token and user info",
        "example": "{\"email\": \"user@example.com\", \"password\": \"secret\"}"
      }
    ]
  }'
```

**New Features:**
- **Classification**: Uses LLM to analyze feature descriptions and automatically select relevant artifacts (components, infrastructure sections, guidelines)
- **Optimization**: Uses LLM to optimize prompts for specific model types (GPT-4, Claude, etc.) to maximize performance
- **Metadata**: Returns classification results and optimization details when `return_metadata` is true

The system will:
1. **Classify** the feature description to identify relevant components, infrastructure sections, and guidelines
2. **Build** an initial prompt with selected artifacts
3. **Optimize** the prompt for the target model type
4. Return the optimized prompt along with metadata about the process

#### 6. Get Business Context

Retrieve indexed business context:

```bash
curl "http://localhost:8000/business-context"
```

#### 7. Get All Resources

Retrieve all stored project resources:

```bash
curl "http://localhost:8000/resources"
```

### Python API Usage

You can also use the framework programmatically:

```python
from project_resources import ProjectResourceManager
from prompt_construction import PromptBuilder
from types import BusinessGoals, AgentGuidelines

# Initialize managers
resource_manager = ProjectResourceManager()
prompt_builder = PromptBuilder(resource_manager)

# Set business goals
business_goals = BusinessGoals(
    purpose="Build a REST API for managing user accounts",
    external_constraints=["Must comply with GDPR"]
)
resource_manager.save_business_goals(business_goals)

# Index project
resource_manager.index_project(
    codebase_paths=["./src"],
    config_paths=["./config.yaml"],
    model="gpt-4-turbo-preview"
)

# Generate prompt
prompt = prompt_builder.build_prompt(
    feature_description="Add user authentication endpoint",
    feature_type="feature",
    model="gpt-4-turbo-preview",
    include_all_context=False
)

print(prompt)
```

## How It Works

1. **Indexing Phase**: The project indexer analyzes your codebase using LLM to create natural language descriptions of components and how they fit into the larger system.

2. **Resource Storage**: Project-specific resources (business goals, system descriptions, agent guidelines) are stored and can be manually defined or auto-generated.

3. **Context Selection**: When generating a prompt, the system intelligently selects relevant components and context based on the feature description.

4. **Prompt Construction**: The prompt builder combines all relevant information into a model-specific formatted prompt.

5. **Model Selection**: The framework supports different LLM models and formats prompts accordingly.

## Configuration

Environment variables (`.env`):

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `PROJECT_ROOT`: Root path of your project (optional)
- `DEFAULT_MODEL`: Default LLM model to use (default: `gpt-4-turbo-preview`)

## Development

### Running Tests

```bash
# Add tests as needed
pytest
```

### Project Structure Details

- **project-indexer**: Uses LLM to analyze codebase and create component summaries
- **project-resources**: Manages storage and retrieval of project resources
- **types**: Pydantic models for type safety and validation
- **prompt-construction**: Builds formatted prompts with smart context selection
- **entry-point**: FastAPI REST API for easy integration

## Future Enhancements

- Add ability to refine prompts with target model as a judge
- Enhanced context selection using semantic similarity
- Support for more LLM providers (Anthropic, etc.)
- Classification system to balance performance/cost with model selection
- Web UI for easier interaction

## License

See LICENSE file for details.

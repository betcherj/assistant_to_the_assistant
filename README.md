# Assistant to the Assistant

**Low code LLM assisted software development framework**

A framework for writing prompts that improve accuracy and save developer time when using LLMs for software engineering. This system empowers engineers not familiar with LLMs or non-engineers to use Gen AI for SWE by injecting coding best practices and smart context to improve generated code results.

## Features

- **Project Indexing**: Automatically index codebases, infrastructure, databases, and contextual documents using LLM to create natural language descriptions
- **LLM-Based Classification**: Intelligently select relevant artifacts (components, infrastructure, business context) using LLM analysis
- **Smart Context Selection**: Dynamically select relevant context based on feature descriptions with keyword matching fallback
- **Prompt Optimization**: Optimize prompts for specific model types (GPT-4, Claude, etc.) using LLM-based optimization
- **Model-Specific Formatting**: Format prompts optimized for different LLM models (GPT-4, Claude, etc.)
- **Resource Management**: Store and manage project-specific resources (business goals, system descriptions, agent guidelines) with unified save/load methods
- **Shared Utilities**: Reusable utilities for LLM calls, keyword extraction, and file operations
- **RESTful API**: FastAPI-based endpoints for easy integration

## Project Structure

```
assistant_to_the_assistant/
├── project_indexer/       # Functions to index codebases, infra, databases, and documents
│   ├── indexer.py         # Main project indexer using LLM
│   ├── infrastructure_indexer.py  # Infrastructure file indexing
│   ├── business_context_indexer.py  # Business document indexing (PDF, CSV, markdown)
│   └── ...
├── project_resources/     # Project-specific resources (manually defined or created by indexer)
│   ├── resource_manager.py  # Manages storage and retrieval of project resources
│   └── storage.py          # Storage utilities
├── types/                 # Pydantic types for type validation and component objects
│   ├── components.py      # Component and ComponentIndex types
│   └── prompt_artifacts.py  # Prompt artifact types (BusinessGoals, SystemDescription, etc.)
├── prompt_construction/   # Combines project info and business context to create formatted prompts
│   ├── prompt_builder.py  # Main prompt builder with classification and optimization
│   ├── prompt_classifier.py  # LLM-based artifact selection
│   ├── prompt_optimizer.py   # LLM-based prompt optimization
│   ├── context_selector.py   # Context selection utilities
│   └── model_formatters.py   # Model-specific prompt formatters
├── utils/                 # Shared utilities and base classes
│   ├── llm_client.py      # BaseLLMClient and LLM API call utilities
│   ├── keyword_extractor.py  # Keyword extraction utilities
│   ├── file_utils.py      # File reading utilities
│   └── logging_config.py  # Logging configuration
├── entry_point/           # FastAPI endpoints for interaction
│   └── api.py             # REST API endpoints
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

### CLI Commands

The framework provides a command-line interface for managing project resources and generating prompts using YAML configuration files.

#### Installation

After installing the package, the CLI is available as `assistant-cli`:

```bash
pip install -e .
assistant-cli --help
```

#### Setting Business Goals from YAML

Set business goals using the default YAML file from the repo, or provide a custom path:

```bash
# Use default from examples/business_goals.yaml
assistant-cli set-business-goals

# Or specify a custom YAML file
assistant-cli set-business-goals path/to/custom_business_goals.yaml
```

The default YAML file (`examples/business_goals.yaml`) contains:
```yaml
purpose: |
  Build a REST API for managing user accounts with authentication and authorization.

external_constraints:
  - Must comply with GDPR regulations
  - Must support 10k concurrent users
```

#### Setting Agent Guidelines from YAML

Set agent guidelines using the default YAML file, or provide a custom path:

```bash
# Use default from examples/agent_guidelines.yaml
assistant-cli set-agent-guidelines

# Or specify a custom YAML file
assistant-cli set-agent-guidelines path/to/custom_guidelines.yaml
```

The default YAML file (`examples/agent_guidelines.yaml`) contains guardrails, best practices, and coding standards.

#### Setting System Description from YAML

Set system description using the default YAML file, or provide a custom path:

```bash
# Use default from examples/system_description.yaml
assistant-cli set-system-description

# Or specify a custom YAML file
assistant-cli set-system-description path/to/custom_system_description.yaml
```

#### Generating Prompts from YAML

Generate prompts using the default feature specification YAML file, or provide a custom path:

```bash
# Use default from examples/feature_spec.yaml
assistant-cli generate-prompt

# Or specify a custom YAML file
assistant-cli generate-prompt path/to/custom_feature_spec.yaml
```

The default feature specification YAML (`examples/feature_spec.yaml`) contains a sample feature request for user authentication.

#### Indexing Operations

Index project codebase:
```bash
assistant-cli index-project \
  --codebase-paths ./src ./lib \
  --config-paths ./config.yaml \
  --model gpt-4-turbo-preview
```

Index infrastructure:
```bash
assistant-cli index-infrastructure \
  --repo-url https://gitlab.com/your-org/your-project \
  --repo-token your_token \
  --model gpt-4-turbo-preview
```

Index business context:
```bash
assistant-cli index-business-context \
  --file-paths ./docs/requirements.pdf s3://bucket/data.csv \
  --aws-access-key your_key \
  --aws-secret-key your_secret \
  --aws-region us-east-1
```

See `examples/README.md` for detailed YAML file structures and more examples.

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
from assistant_to_the_assistant.project_resources import ProjectResourceManager
from assistant_to_the_assistant.prompt_construction import PromptBuilder
from assistant_to_the_assistant.types import BusinessGoals, AgentGuidelines

# Initialize managers
resource_manager = ProjectResourceManager()
prompt_builder = PromptBuilder(
    resource_manager=resource_manager,
    use_classifier=True,  # Enable LLM-based artifact selection
    use_optimizer=True    # Enable LLM-based prompt optimization
)

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

# Generate prompt with automatic classification and optimization
result = prompt_builder.build_prompt(
    feature_description="Add user authentication endpoint",
    feature_type="feature",
    model="gpt-4-turbo-preview",
    include_all_context=False,  # Use LLM-based selection
    enable_classification=True,  # Enable artifact classification
    enable_optimization=True     # Enable prompt optimization
)

print(result["prompt"])  # Optimized prompt
print(result["classification"])  # Classification metadata
print(result["optimized"])  # Whether optimization was applied
```

## How It Works

1. **Indexing Phase**: The project indexer analyzes your codebase using LLM to create natural language descriptions of components and how they fit into the larger system. Infrastructure files and business context documents are also indexed.

2. **Resource Storage**: Project-specific resources (business goals, system descriptions, agent guidelines) are stored using a unified resource management system with generic save/load methods.

3. **LLM-Based Classification**: When generating a prompt, the system uses an LLM classifier to intelligently select relevant artifacts (components, infrastructure sections, business context documents) based on the feature description, maximizing prompt effectiveness.

4. **Prompt Construction**: The prompt builder combines all selected information into a model-specific formatted prompt using specialized formatters.

5. **Prompt Optimization**: The system can optionally optimize prompts for specific model types (GPT-4, Claude, etc.) using LLM-based optimization to maximize performance.

6. **Model Selection**: The framework supports different LLM models and formats prompts accordingly using model-specific formatters.

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

- **project_indexer**: Uses LLM to analyze codebase and create component summaries
  - `ProjectIndexer`: Main codebase indexing using LLM analysis
  - `InfrastructureIndexer`: Parses and indexes infrastructure files (Docker, Terraform, CI/CD, etc.)
  - `BusinessContextIndexer`: Indexes business documents (PDF, CSV, markdown) from local or S3 paths

- **project_resources**: Manages storage and retrieval of project resources
  - `ProjectResourceManager`: Centralized resource management with generic save/load methods

- **types**: Pydantic models for type safety and validation
  - `Component`, `ComponentIndex`: Codebase component types
  - `BusinessGoals`, `SystemDescription`, `AgentGuidelines`: Prompt artifact types
  - `BaseIOExample`: Base type for input/output examples (shared by `SystemIOExample` and `FeatureExample`)

- **prompt_construction**: Builds formatted prompts with smart context selection
  - `PromptBuilder`: Main builder with LLM-based classification and optimization
  - `PromptClassifier`: Uses LLM to intelligently select relevant artifacts
  - `PromptOptimizer`: Optimizes prompts for specific model types
  - `ModelFormatter`: Base formatter with `GPT4Formatter` and `ClaudeFormatter` implementations

- **utils**: Shared utilities and base classes
  - `BaseLLMClient`: Base class for all LLM-based clients (reduces code duplication)
  - `make_llm_call()`, `make_json_llm_call()`: Standardized LLM API call utilities
  - `extract_keywords()`, `matches_keywords()`: Keyword extraction utilities
  - `read_business_context_artifact()`, `get_artifact_summary()`: File reading utilities

- **entry_point**: FastAPI REST API for easy integration

## Architecture Highlights

### Code Organization

The codebase follows DRY (Don't Repeat Yourself) principles with shared utilities:

- **BaseLLMClient**: All LLM-based classes (`PromptClassifier`, `PromptOptimizer`, `InfrastructureIndexer`, `BusinessContextIndexer`) inherit from this base class, eliminating duplicate OpenAI initialization code.

- **Shared Utilities**: Common patterns are extracted into reusable utilities:
  - `make_llm_call()` and `make_json_llm_call()`: Standardized LLM API calls with error handling
  - `extract_keywords()` and `matches_keywords()`: Consistent keyword extraction across components
  - `read_business_context_artifact()`: Unified file reading for business context artifacts

- **Type Reuse**: `BaseIOExample` provides a shared base for `SystemIOExample` and `FeatureExample`, reducing duplication.

- **Generic Resource Management**: `ProjectResourceManager` uses generic `_save_resource()` and `_load_resource()` methods, eliminating repetitive save/load code.

### Benefits

- **Reduced Code Duplication**: ~200+ lines of duplicate code eliminated
- **Improved Maintainability**: Changes to common patterns only need to be made once
- **Better Consistency**: All classes use the same utilities, ensuring consistent behavior
- **Easier Testing**: Utilities can be tested independently

## Future Enhancements

- Enhanced context selection using semantic similarity
- Support for more LLM providers (Anthropic, etc.)
- Classification system to balance performance/cost with model selection
- Web UI for easier interaction
- Additional model-specific optimizations

## License

See LICENSE file for details.

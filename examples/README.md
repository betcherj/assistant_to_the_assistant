# Example YAML Configuration Files

This directory contains example YAML configuration files for the Assistant to the Assistant CLI.

## Files

- **business_goals.yaml** - Defines business context and external constraints
- **agent_guidelines.yaml** - Defines coding standards, best practices, and guardrails
- **system_description.yaml** - Defines system-level I/O examples, components, and infrastructure
- **feature_spec.yaml** - Defines a feature request for prompt generation

## Usage

### Setting Business Goals

```bash
assistant-cli set-business-goals examples/business_goals.yaml
```

### Setting Agent Guidelines

```bash
assistant-cli set-agent-guidelines examples/agent_guidelines.yaml
```

### Setting System Description

```bash
assistant-cli set-system-description examples/system_description.yaml
```

### Generating a Prompt

```bash
assistant-cli generate-prompt examples/feature_spec.yaml
```

## YAML File Structure

### business_goals.yaml

```yaml
purpose: |
  Description of the system's purpose within the business context

external_constraints:
  - Constraint 1
  - Constraint 2
```

### agent_guidelines.yaml

```yaml
guardrails:
  - Never commit API keys to code
  - Always validate user input

best_practices:
  - Use type hints
  - Write docstrings

coding_standards:
  - Use async/await for I/O operations
  - Return Pydantic models from API endpoints
```

### system_description.yaml

```yaml
io_examples:
  - input_description: "Description of input"
    output_description: "Description of output"
    example: "Optional concrete example"

components: []  # Auto-indexed from codebase or manually added

infrastructure:
  deployment: "Deployment description"
  databases:
    - "Database 1"
  services:
    - "Service 1"
```

### feature_spec.yaml

```yaml
feature_description: |
  Description of the feature to implement

feature_type: feature  # feature, fix, or instance

model: gpt-4-turbo-preview

include_all_context: false
enable_classification: true
enable_optimization: true

feature_examples:
  - input_description: "Input description"
    output_description: "Output description"
    example: "Optional example"

output_file: generated_prompt.txt  # Optional
```


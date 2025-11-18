# Prompt Construction Guide

## Overview

The prompt construction system uses a two-stage LLM-powered pipeline to create optimized prompts for feature implementation:

1. **Classification**: Analyzes feature descriptions and selects relevant artifacts
2. **Optimization**: Refines prompts for specific model types to maximize performance

## Architecture

### Classification Stage

The `PromptClassifier` uses an LLM to:
- Analyze feature descriptions
- Identify relevant components from the codebase
- Select relevant infrastructure sections
- Determine which guidelines and constraints to include
- Classify feature complexity and category

**Input**: Feature description + all available artifacts  
**Output**: Selected artifacts with reasoning

### Optimization Stage

The `PromptOptimizer` uses an LLM to:
- Analyze the initial prompt structure
- Apply model-specific formatting guidelines
- Improve clarity and organization
- Optimize instruction style for target model
- Enhance context presentation

**Input**: Initial prompt + target model + model guidelines  
**Output**: Optimized prompt

## Model-Specific Guidelines

The optimizer applies different strategies based on model type:

### GPT-4 / GPT-4 Turbo
- Structured markdown with clear sections
- Direct and explicit instructions
- Can handle large context windows
- Benefits from few-shot examples
- Responds well to step-by-step reasoning

### GPT-3.5 Turbo
- Concise structured format
- Clear and concise instructions
- Moderate context window
- Prefer simpler, more direct instructions

### Claude Models
- Natural language with clear structure
- Conversational but precise style
- Excellent at handling large context
- Benefits from detailed examples
- Responds well to detailed explanations

## Usage

### API Endpoint

```bash
curl -X POST "http://localhost:8000/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_description": "Add user authentication endpoint",
    "model": "gpt-4-turbo-preview",
    "enable_classification": true,
    "enable_optimization": true,
    "return_metadata": true
  }'
```

### Python API

```python
from prompt_construction import PromptBuilder
from project_resources import ProjectResourceManager

resource_manager = ProjectResourceManager()
prompt_builder = PromptBuilder(
    resource_manager=resource_manager,
    use_classifier=True,   # Enable classification
    use_optimizer=True     # Enable optimization
)

result = prompt_builder.build_prompt(
    feature_description="Add user authentication endpoint",
    model="gpt-4-turbo-preview",
    enable_classification=True,
    enable_optimization=True
)

print(result["prompt"])  # Optimized prompt
print(result["classification"])  # Classification results
```

## Response Format

When `return_metadata` is `true`, the API returns:

```json
{
  "status": "success",
  "prompt": "Optimized prompt text...",
  "model": "gpt-4-turbo-preview",
  "feature_type": "feature",
  "metadata": {
    "classified": true,
    "optimized": true,
    "classification": {
      "relevant_component_names": ["auth", "api"],
      "relevant_infrastructure_sections": ["CI/CD Pipeline"],
      "include_business_goals": true,
      "include_agent_guidelines": true,
      "reasoning": "Authentication feature requires...",
      "feature_category": "api",
      "complexity": "medium"
    },
    "initial_prompt": "Initial prompt before optimization..."
  }
}
```

## Classification Details

The classifier analyzes:
- **Components**: Which codebase components are relevant
- **Infrastructure**: Which infrastructure sections apply
- **Business Goals**: Whether business context is needed
- **Guidelines**: Which coding standards apply
- **Feature Category**: api, database, ui, infrastructure, integration, other
- **Complexity**: low, medium, high

## Optimization Details

The optimizer:
- Restructures prompts for better model comprehension
- Adjusts detail level based on model capabilities
- Improves instruction clarity
- Optimizes formatting and organization
- Preserves all essential information

## Configuration

You can control classification and optimization:

```python
# Disable classification (use simple keyword matching)
prompt_builder = PromptBuilder(use_classifier=False)

# Disable optimization (return initial prompt)
prompt_builder = PromptBuilder(use_optimizer=False)

# Override per-request
result = prompt_builder.build_prompt(
    feature_description="...",
    enable_classification=False,  # Override default
    enable_optimization=True
)
```

## Performance Considerations

- **Classification**: Adds ~1-2 seconds per request
- **Optimization**: Adds ~2-3 seconds per request
- **Total overhead**: ~3-5 seconds for full pipeline

For faster responses, you can:
- Disable classification for simple features
- Disable optimization if prompt quality is acceptable
- Use `include_all_context=true` to skip classification

## Best Practices

1. **Enable both stages** for complex features requiring precise context
2. **Use classification** when you have many artifacts but only some are relevant
3. **Use optimization** when targeting specific model types
4. **Review metadata** to understand what artifacts were selected
5. **Compare initial vs optimized** prompts to see improvements

## Extending

### Adding New Model Types

Update `MODEL_GUIDELINES` in `prompt_optimizer.py`:

```python
MODEL_GUIDELINES = {
    "your-model": {
        "preferred_format": "...",
        "instruction_style": "...",
        # ...
    }
}
```

### Custom Classification Logic

Extend `PromptClassifier` to add custom classification rules or use different LLM prompts.

### Custom Optimization Strategies

Extend `PromptOptimizer` to add model-specific optimization strategies.


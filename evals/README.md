# Evaluation Framework

This directory contains evaluation tests for the Assistant to the Assistant framework.
The evals test the system's ability to:
- Ingest codebases and create component descriptions
- Ingest Terraform infrastructure as code
- Ingest business context descriptions
- Design and concatenate markdown prompts
- Select relevant component prompts based on feature descriptions using an LLM judge

## Structure

```
evals/
├── README.md                    # This file
├── test_etl_scenario.py         # Main evaluation test runner
└── etl_scenario/                # ETL scenario evaluation
    ├── business_context.yaml    # Business context for ETL system
    ├── feature_spec.yaml        # Feature specification for testing
    ├── infrastructure.yaml      # Infrastructure description
    ├── generated_prompt.md      # Generated prompt (output)
    └── mock_codebase/           # Mock codebase for testing
        └── src/
            ├── etl/             # ETL processing modules
            ├── models/          # Pydantic models
            └── utils/           # Utility modules
```

## ETL Scenario

The ETL scenario tests the framework with a realistic use case:

**Codebase**: An ETL repository that uses LLM natural language parsing to extract Pydantic models from text. The system has domain-specific language in prompts and order models.

**Key Components**:
- `DocumentProcessor`: Extracts text from PDFs and plain text files
- `LLMParser`: Uses OpenAI API to parse natural language and extract structured data
- `OrderExtractor`: Specialized extractor for Order Pydantic models
- `OrderValidator`: Validates extracted orders against business rules
- Domain terminology mappings (PO, SKU, FOB, Net 30, etc.)

**Business Context**: Describes the ETL system's purpose, domain terminology, business rules, and data entities.

**Infrastructure**: Describes AWS ECS deployment, PostgreSQL database, Redis cache, S3 storage, and networking configuration.

**Feature**: Add support for extracting order information from email attachments.

## Running Evaluations

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY=your_api_key_here
```

### Run ETL Scenario Evaluation

```bash
python evals/test_etl_scenario.py
```

The evaluation will:
1. Load business context from YAML
2. Load infrastructure description from YAML
3. Index the mock codebase
4. Generate a prompt for the feature specification
5. Test component selection using LLM classification
6. Validate that the generated prompt contains expected elements

### Expected Output

The evaluation will:
- Generate a markdown prompt saved to `evals/etl_scenario/generated_prompt.md`
- Print validation results for prompt generation and component selection
- Exit with code 0 if all tests pass, 1 if any test fails

## Evaluation Criteria

The evaluation tests validate:

1. **Prompt Generation**:
   - Feature description is included
   - Business context is included
   - Infrastructure information is included
   - Component descriptions are included
   - LLM classification was used
   - Prompt optimization was applied

2. **Component Selection**:
   - Relevant components were selected by the LLM judge
   - Selection reasoning is provided
   - Components match the feature requirements

## Business Context from S3

The framework supports business context files from S3, but S3 ingestion is marked as `#TODO` and will log warnings when S3 files are not found. This allows the evaluation to test the system's graceful handling of missing S3 files.

## Adding New Scenarios

To add a new evaluation scenario:

1. Create a new directory under `evals/` (e.g., `evals/my_scenario/`)
2. Add scenario files:
   - `business_context.yaml`: Business context description
   - `feature_spec.yaml`: Feature specification
   - `infrastructure.yaml`: Infrastructure description
   - `mock_codebase/`: Mock codebase structure
3. Create a test file (e.g., `test_my_scenario.py`) following the pattern in `test_etl_scenario.py`
4. Update this README with the new scenario description


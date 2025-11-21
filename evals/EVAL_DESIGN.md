# Evaluation Design Document

## Overview

This document describes the evaluation framework designed for the Assistant to the Assistant repository. The evals test the system's ability to ingest codebases, Terraform infrastructure as code, and business context descriptions to design and concatenate markdown prompts.

## Evaluation Goals

The evaluation framework tests:

1. **Codebase Ingestion**: Ability to ingest a codebase and create component descriptions
2. **Infrastructure Ingestion**: Ability to ingest Terraform infrastructure as code
3. **Business Context Ingestion**: Ability to ingest business context descriptions (with S3 support marked as TODO)
4. **Prompt Design**: Ability to design and concatenate markdown prompts
5. **Component Selection**: Ability to use an LLM judge to select relevant component prompts based on feature descriptions
6. **Local Storage**: Prompts and feature descriptions are stored locally in markdown files

## Architecture Changes

### Business Context Indexer Updates

The `BusinessContextIndexer` was updated to handle S3 files gracefully:

- **S3 File Handling**: When S3 files are encountered, the system logs a warning and marks the functionality as `#TODO`
- **Logging**: The system logs when S3 files are not found or cannot be accessed
- **Graceful Degradation**: The system continues processing other files even if S3 files fail

Key changes in `business_context_indexer.py`:
- `_read_from_s3()` method now includes TODO comments and proper logging
- S3 file processing is skipped with informative log messages
- System continues to work with local files even if S3 is unavailable

## ETL Scenario

### Scenario Description

The ETL scenario represents a realistic use case:

**Codebase**: An ETL (Extract, Transform, Load) repository that uses LLM natural language parsing to extract Pydantic models from text. The system has domain-specific language in prompts and order models.

**Key Components**:
- `DocumentProcessor`: Extracts text from PDFs and plain text files
- `LLMParser`: Uses OpenAI API to parse natural language and extract structured data
- `OrderExtractor`: Specialized extractor for Order Pydantic models
- `OrderValidator`: Validates extracted orders against business rules
- Domain terminology utilities (PO, SKU, FOB, Net 30, etc.)

### Scenario Files

1. **business_context.yaml**: 
   - Purpose of the ETL system
   - External constraints (GDPR, batch processing, etc.)
   - Domain terminology (PO, SKU, ETA, FOB, Net 30)
   - Business rules (order validation, priority processing)
   - Data entities (Order, Customer, Product, ShippingAddress)

2. **feature_spec.yaml**:
   - Feature: Add support for extracting order information from email attachments
   - Includes feature examples with domain-specific terminology
   - Configures prompt generation settings

3. **infrastructure.yaml**:
   - Deployment: AWS ECS Fargate with Docker containers
   - Databases: PostgreSQL, Redis, S3
   - Services: LLM API, Document Processing, Order Validation, Notifications
   - Structured infrastructure sections (CI/CD, Deployment, Compute, Storage, Networking)

4. **infrastructure.tf**:
   - Terraform configuration for AWS infrastructure
   - VPC, subnets, security groups
   - RDS PostgreSQL, ElastiCache Redis
   - S3 buckets, ECS cluster, Application Load Balancer

5. **mock_codebase/**:
   - Complete mock codebase structure
   - ETL processing modules
   - Pydantic models (Order, Customer, Product)
   - Domain terminology utilities
   - Prompt templates with domain-specific language

## Evaluation Test Structure

### Test File: `test_etl_scenario.py`

The evaluation test includes:

1. **Setup Phase**:
   - Loads business context from YAML
   - Loads infrastructure description from YAML
   - Indexes mock codebase to create component descriptions

2. **Prompt Generation Test**:
   - Generates a prompt for the feature specification
   - Validates that the prompt contains:
     - Feature description
     - Business context
     - Infrastructure information
     - Component descriptions
   - Verifies LLM classification and optimization were used

3. **Component Selection Test**:
   - Tests that relevant components are selected by the LLM judge
   - Validates that selection reasoning is provided
   - Checks that selected components match feature requirements

### Test Execution

Run the evaluation:
```bash
python evals/test_etl_scenario.py
```

Expected output:
- Generated markdown prompt saved to `evals/etl_scenario/generated_prompt.md`
- Validation results printed to console
- Exit code 0 if all tests pass, 1 if any test fails

## Validation Criteria

### Prompt Generation Validation

The generated prompt must contain:
- ✅ Feature description
- ✅ Business context (ETL system, domain terminology)
- ✅ Infrastructure information (ECS, AWS, deployment)
- ✅ Component descriptions (from indexed codebase)
- ✅ LLM classification was used
- ✅ Prompt optimization was applied

### Component Selection Validation

The LLM judge must:
- ✅ Select relevant components (order_extractor, document_processor)
- ✅ Provide reasoning for selection
- ✅ Match components to feature requirements

## S3 Business Context Handling

### Current Implementation

- S3 file paths are detected (format: `s3://bucket/key`)
- When S3 files are encountered:
  - System logs: "S3 file ingestion is not yet implemented. Skipping S3 file."
  - System logs: "S3 file not found or not accessible: {s3_path}"
  - Processing continues with other files
  - No errors are raised, graceful degradation

### TODO Items

The following are marked as `#TODO` in the code:
- Actual S3 file download and processing
- S3 client initialization and error handling improvements
- Support for additional S3 file formats

## Future Enhancements

1. **Additional Scenarios**: Add more evaluation scenarios for different use cases
2. **S3 Implementation**: Complete S3 file ingestion implementation
3. **Terraform Parsing**: Add actual Terraform file parsing to infrastructure indexer
4. **Component Selection Metrics**: Add metrics for component selection accuracy
5. **Prompt Quality Metrics**: Add metrics for prompt quality and effectiveness

## File Structure

```
evals/
├── README.md                    # Evaluation framework documentation
├── EVAL_DESIGN.md              # This file
├── test_etl_scenario.py         # Main evaluation test
└── etl_scenario/               # ETL scenario
    ├── business_context.yaml    # Business context
    ├── feature_spec.yaml        # Feature specification
    ├── infrastructure.yaml      # Infrastructure description
    ├── infrastructure.tf        # Terraform configuration
    ├── generated_prompt.md     # Generated prompt (output)
    └── mock_codebase/           # Mock codebase
        └── src/
            ├── etl/             # ETL modules
            ├── models/          # Pydantic models
            └── utils/           # Utilities
```

## Conclusion

The evaluation framework provides comprehensive testing of the Assistant to the Assistant system's core capabilities. The ETL scenario demonstrates a realistic use case with domain-specific language, complex infrastructure, and business context. The framework is designed to be extensible for additional scenarios and use cases.


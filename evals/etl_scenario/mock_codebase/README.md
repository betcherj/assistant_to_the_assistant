# Mock ETL Codebase

This directory contains a mock codebase structure for the ETL scenario evaluation.
The codebase represents an ETL system that uses LLM natural language parsing to extract
Pydantic models from text, with domain-specific language in prompts and order models.

## Structure

```
mock_codebase/
├── src/
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── document_processor.py      # Handles PDF/text extraction
│   │   ├── llm_parser.py              # LLM-based natural language parsing
│   │   ├── order_extractor.py         # Extracts Order models from text
│   │   └── validators.py              # Validates extracted models
│   ├── models/
│   │   ├── __init__.py
│   │   ├── order.py                   # Order Pydantic model
│   │   ├── customer.py                # Customer Pydantic model
│   │   └── product.py                 # Product Pydantic model
│   └── utils/
│       ├── __init__.py
│       ├── domain_terminology.py      # Domain-specific language mappings
│       └── prompt_templates.py        # LLM prompt templates
├── tests/
│   ├── test_order_extraction.py
│   └── test_validators.py
└── requirements.txt
```

## Key Components

1. **Document Processor**: Extracts text from PDFs and plain text files
2. **LLM Parser**: Uses OpenAI API to parse natural language and extract structured data
3. **Order Extractor**: Specialized extractor for Order Pydantic models
4. **Validators**: Business rule validation for extracted models
5. **Domain Terminology**: Maps domain-specific abbreviations (PO, SKU, FOB, etc.)


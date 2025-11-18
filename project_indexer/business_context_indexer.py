"""Business context indexer for PDF, CSV, and markdown files."""
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BusinessContextIndexer:
    """Indexes business context files (PDF, CSV, markdown) from local or S3 paths."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        aws_region: Optional[str] = None
    ):
        """
        Initialize the business context indexer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: LLM model to use for indexing
            aws_access_key: AWS access key for S3 access (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_key: AWS secret key for S3 access (defaults to AWS_SECRET_ACCESS_KEY env var)
            aws_region: AWS region (defaults to AWS_REGION env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass api_key.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        # Initialize S3 client if credentials are available
        self.s3_client = None
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        
        aws_access_key = aws_access_key or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if aws_access_key and aws_secret_key:
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=self.aws_region
                )
            except ImportError:
                logger.warning("boto3 not installed. S3 functionality will be unavailable.")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
    
    def index_business_context(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index business context files and create markdown artifacts.
        
        Args:
            file_paths: List of file paths (local or S3 s3://bucket/key format)
            output_dir: Directory to save markdown artifacts (defaults to .project-resources/business-context)
        
        Returns:
            Dictionary with indexing results and artifact paths
        """
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path(".project-resources") / "business-context"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        artifacts = []
        indexed_files = []
        
        for file_path in file_paths:
            try:
                # Determine if it's an S3 path
                if file_path.startswith("s3://"):
                    content, file_type, filename = self._read_from_s3(file_path)
                else:
                    content, file_type, filename = self._read_local_file(file_path)
                
                if not content:
                    logger.warning(f"Could not read content from {file_path}")
                    continue
                
                # Create markdown index artifact
                artifact = self._create_markdown_artifact(
                    content=content,
                    file_type=file_type,
                    filename=filename,
                    source_path=file_path
                )
                
                # Save artifact to file
                artifact_filename = self._sanitize_filename(filename)
                artifact_path = output_path / f"{artifact_filename}.md"
                artifact_path.write_text(artifact, encoding='utf-8')
                
                artifacts.append({
                    "filename": filename,
                    "file_type": file_type,
                    "source_path": file_path,
                    "artifact_path": str(artifact_path),
                    "artifact_size": len(artifact)
                })
                
                indexed_files.append(file_path)
                
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {e}", exc_info=True)
                continue
        
        return {
            "artifacts": artifacts,
            "indexed_files": indexed_files,
            "output_directory": str(output_path),
            "indexed_at": datetime.now().isoformat(),
            "total_files": len(file_paths),
            "successful": len(indexed_files)
        }
    
    def _read_from_s3(self, s3_path: str) -> Tuple[Optional[str], Optional[str], str]:
        """Read file content from S3."""
        if not self.s3_client:
            raise ValueError("S3 client not initialized. Provide AWS credentials.")
        
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("boto3 is required for S3 access. Install with: pip install boto3")
        
        # Parse S3 path: s3://bucket/key
        parsed = urlparse(s3_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        if not bucket or not key:
            raise ValueError(f"Invalid S3 path format: {s3_path}. Expected s3://bucket/key")
        
        try:
            # Download file to temporary location
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(key).suffix) as tmp_file:
                self.s3_client.download_fileobj(bucket, key, tmp_file)
                tmp_path = tmp_file.name
            
            # Read content based on file type
            file_type = self._detect_file_type(key)
            content, _, filename = self._read_local_file(tmp_path, file_type=file_type)
            
            # Cleanup temp file
            os.unlink(tmp_path)
            
            return content, file_type, Path(key).name
            
        except ClientError as e:
            logger.error(f"Error downloading from S3 {s3_path}: {e}")
            return None, None, Path(key).name
    
    def _read_local_file(self, file_path: str, file_type: Optional[str] = None) -> Tuple[Optional[str], Optional[str], str]:
        """Read file content from local filesystem."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_type is None:
            file_type = self._detect_file_type(file_path)
        
        filename = path.name
        
        try:
            if file_type == "pdf":
                content = self._read_pdf(path)
            elif file_type == "csv":
                content = self._read_csv(path)
            elif file_type == "markdown":
                content = self._read_markdown(path)
            else:
                # Try to read as text
                content = path.read_text(encoding='utf-8', errors='ignore')
            
            return content, file_type, filename
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}", exc_info=True)
            return None, None, filename
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension."""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == ".pdf":
            return "pdf"
        elif ext == ".csv":
            return "csv"
        elif ext in [".md", ".markdown"]:
            return "markdown"
        else:
            return "text"
    
    def _read_pdf(self, path: Path) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2
        except ImportError:
            try:
                import pdfplumber
            except ImportError:
                raise ImportError(
                    "PDF reading requires PyPDF2 or pdfplumber. "
                    "Install with: pip install PyPDF2 or pip install pdfplumber"
                )
            else:
                # Use pdfplumber
                with pdfplumber.open(path) as pdf:
                    text_parts = []
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    return "\n\n".join(text_parts)
        else:
            # Use PyPDF2
            text_parts = []
            with open(path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)
    
    def _read_csv(self, path: Path) -> str:
        """Read and format CSV file."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("CSV reading requires pandas. Install with: pip install pandas")
        
        try:
            df = pd.read_csv(path)
            
            # Convert to readable text format
            text_parts = []
            
            # Add column names
            text_parts.append("Columns: " + ", ".join(df.columns.tolist()))
            text_parts.append(f"\nTotal rows: {len(df)}")
            
            # Add sample data (first 10 rows)
            text_parts.append("\n\nSample data:")
            text_parts.append(df.head(10).to_string(index=False))
            
            # Add summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text_parts.append("\n\nSummary statistics:")
                text_parts.append(df[numeric_cols].describe().to_string())
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error reading CSV {path}: {e}", exc_info=True)
            # Fallback to raw text
            return path.read_text(encoding='utf-8', errors='ignore')
    
    def _read_markdown(self, path: Path) -> str:
        """Read markdown file."""
        return path.read_text(encoding='utf-8', errors='ignore')
    
    def _create_markdown_artifact(
        self,
        content: str,
        file_type: str,
        filename: str,
        source_path: str
    ) -> str:
        """
        Create a markdown index artifact from file content using LLM.
        
        Args:
            content: File content (text extracted from PDF/CSV/markdown)
            file_type: Type of file (pdf, csv, markdown)
            filename: Original filename
            source_path: Source path (local or S3)
        
        Returns:
            Markdown artifact string
        """
        # Truncate content if too long (keep first 15000 chars for LLM processing)
        content_preview = content[:15000] if len(content) > 15000 else content
        if len(content) > 15000:
            content_preview += "\n\n[Content truncated for processing...]"
        
        prompt = f"""Analyze the following business context document and create a comprehensive markdown index artifact.

The document is a {file_type.upper()} file named "{filename}" that contains business context information.

Focus on extracting:
- Key business concepts and terminology
- Business rules and constraints
- Domain-specific information
- Important data structures or entities
- Business processes or workflows mentioned
- Key metrics or KPIs
- Any technical requirements or constraints

Document Content:
{content_preview}

Create a well-structured markdown document with:
1. **Overview**: Brief summary of the document's purpose and key topics
2. **Key Concepts**: Important business concepts and terminology
3. **Business Rules**: Any rules, constraints, or requirements mentioned
4. **Data Structures**: Important data entities, fields, or structures
5. **Processes**: Business processes or workflows described
6. **Metrics**: Key metrics, KPIs, or measurements mentioned
7. **Technical Context**: Any technical requirements or constraints

Format the output as clean markdown without code blocks. Use headers, lists, and tables as appropriate.
Be concise but comprehensive. Focus on information that would be useful for software development context."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business context analyst. Create clear, structured markdown documentation from business documents that will be used to provide context for software development."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            artifact = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if artifact.startswith("```"):
                artifact = artifact.split("```", 2)[-1].rsplit("```", 1)[0].strip()
            
            # Add metadata header
            metadata_header = f"""# Business Context: {filename}

**Source**: {source_path}  
**File Type**: {file_type.upper()}  
**Indexed**: {datetime.now().isoformat()}

---

"""
            
            return metadata_header + artifact
            
        except Exception as e:
            logger.error(f"Error creating markdown artifact: {e}", exc_info=True)
            # Fallback: create basic markdown
            return f"""# Business Context: {filename}

**Source**: {source_path}  
**File Type**: {file_type.upper()}  
**Indexed**: {datetime.now().isoformat()}

## Content Summary

{content[:2000]}{"..." if len(content) > 2000 else ""}
"""
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for use as artifact filename."""
        # Remove extension
        name = Path(filename).stem
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # Limit length
        if len(name) > 100:
            name = name[:100]
        return name


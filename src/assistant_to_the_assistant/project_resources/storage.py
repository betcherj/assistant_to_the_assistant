"""Storage utilities for project resources."""
import json
from pathlib import Path
from typing import Any, Optional


class ResourceStorage:
    """Simple file-based storage for resources."""
    
    @staticmethod
    def save_json(data: Any, file_path: Path) -> None:
        """Save data as JSON."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def load_json(file_path: Path) -> Optional[Any]:
        """Load data from JSON file."""
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_text(text: str, file_path: Path) -> None:
        """Save text to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(text)
    
    @staticmethod
    def load_text(file_path: Path) -> Optional[str]:
        """Load text from file."""
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            return f.read()


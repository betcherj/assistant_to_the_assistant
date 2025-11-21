"""Default configuration paths for Assistant to the Assistant."""
from pathlib import Path

# Get the package root directory
PACKAGE_ROOT = Path(__file__).parent.parent.parent

# Default YAML file paths (relative to repo root)
DEFAULT_BUSINESS_GOALS_YAML = PACKAGE_ROOT / "examples" / "business_goals.yaml"
DEFAULT_AGENT_GUIDELINES_YAML = PACKAGE_ROOT / "examples" / "agent_guidelines.yaml"
DEFAULT_SYSTEM_DESCRIPTION_YAML = PACKAGE_ROOT / "examples" / "system_description.yaml"
DEFAULT_FEATURE_SPEC_YAML = PACKAGE_ROOT / "examples" / "feature_spec.yaml"


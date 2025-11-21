"""Builds prompts by combining project information and business context."""
from typing import Optional, Dict, Any, List

from ..types import (
    BusinessGoals,
    SystemDescription,
    AgentGuidelines,
    FeaturePrompt,
    PromptArtifacts,
    ComponentIndex,
)
from ..project_resources import ProjectResourceManager
from .model_formatters import ModelFormatter, GPT4Formatter, ClaudeFormatter
from .prompt_classifier import PromptClassifier
from .prompt_optimizer import PromptOptimizer


class PromptBuilder:
    """Builds formatted prompts for different LLM models."""
    
    def __init__(
        self,
        resource_manager: Optional[ProjectResourceManager] = None,
        use_classifier: bool = True,
        use_optimizer: bool = True,
        classifier_api_key: Optional[str] = None,
        optimizer_api_key: Optional[str] = None
    ):
        """
        Initialize prompt builder.
        
        The classifier is always initialized for LLM-based artifact selection. This ensures
        that artifact selection uses intelligent LLM analysis rather than keyword matching.
        
        Args:
            resource_manager: ProjectResourceManager instance (creates new if None)
            use_classifier: Whether to use LLM-based classification (default: True, classifier always initialized)
            use_optimizer: Whether to use LLM-based optimization (default: True)
            classifier_api_key: API key for classifier (defaults to OPENAI_API_KEY)
            optimizer_api_key: API key for optimizer (defaults to OPENAI_API_KEY)
        """
        self.resource_manager = resource_manager or ProjectResourceManager()
        self.use_classifier = use_classifier
        self.use_optimizer = use_optimizer
        self.classifier_api_key = classifier_api_key
        
        # Always initialize classifier for LLM-based artifact selection
        # The classifier will be used to select relevant artifacts based on feature description
        try:
            self.classifier = PromptClassifier(api_key=classifier_api_key)
        except Exception as e:
            # If classifier can't be initialized (e.g., no API key), log warning
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not initialize PromptClassifier: {e}. LLM-based artifact selection will not be available.")
            self.classifier = None
        
        if self.use_optimizer:
            self.optimizer = PromptOptimizer(api_key=optimizer_api_key)
        else:
            self.optimizer = None
        
        # Model formatters
        self.formatters: Dict[str, ModelFormatter] = {
            "gpt-4": GPT4Formatter(),
            "gpt-4-turbo": GPT4Formatter(),
            "gpt-4-turbo-preview": GPT4Formatter(),
            "gpt-3.5-turbo": GPT4Formatter(),
            "claude-3-opus": ClaudeFormatter(),
            "claude-3-sonnet": ClaudeFormatter(),
            "claude-3-haiku": ClaudeFormatter(),
        }
    
    def build_prompt(
        self,
        feature_description: str,
        feature_type: str = "feature",
        feature_examples: Optional[List[Dict[str, str]]] = None,
        model: str = "gpt-4-turbo-preview",
        include_all_context: bool = False,
        refine_with_model: bool = False,
        enable_classification: Optional[bool] = None,
        enable_optimization: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Build a complete prompt for feature development with LLM-based artifact selection and optimization.
        
        This method uses an LLM judge to intelligently select relevant artifacts (components, infrastructure,
        business context documents) based on the feature description. Keyword matching has been removed in
        favor of LLM-based selection to maximize prompt effectiveness.
        
        Args:
            feature_description: Description of what to build/fix
            feature_type: Type of prompt (feature, fix, instance)
            feature_examples: Optional feature-level examples
            model: Target LLM model
            include_all_context: If True, include all context without selection; if False, use LLM-based selection
            refine_with_model: If True, refine prompt using target model as judge (deprecated, use enable_optimization)
            enable_classification: Override classifier usage (defaults to use_classifier setting)
            enable_optimization: Override optimizer usage (defaults to use_optimizer setting)
        
        Returns:
            Dictionary with prompt, metadata, and classification results
        
        Raises:
            ValueError: If LLM-based classifier is required but not available (no API key)
        """
        # Load resources
        resources = self.resource_manager.get_all_resources()
        
        # Create feature prompt
        from ..types import FeatureExample, FeaturePrompt
        examples = []
        if feature_examples:
            examples = [FeatureExample(**ex) for ex in feature_examples]
        
        feature_prompt = FeaturePrompt(
            description=feature_description,
            feature_type=feature_type,
            examples=examples
        )
        
        # Classification step: Always use LLM-based classification to select relevant artifacts
        # This ensures intelligent selection based on feature description rather than keyword matching
        classification_result = None
        selected_context = None
        
        use_classifier = enable_classification if enable_classification is not None else self.use_classifier
        
        if include_all_context:
            # Include all context - no selection needed
            business_goals = resources["business_goals"]
            agent_guidelines = resources["agent_guidelines"]
            system_description = resources["system_description"] or SystemDescription()
            business_context = resources.get("business_context")
            selected_context = {
                "components": system_description.components if system_description else [],
                "infrastructure_sections": system_description.infrastructure.sections if system_description and system_description.infrastructure else [],
                "business_context_artifacts": business_context.artifacts if business_context else [],
                "include_infrastructure": True,
                "include_all_io_examples": True,
            }
            # Set classification_result to None since we're including all context
            classification_result = None
        elif self.classifier:
            # Always use LLM-based classification for artifact selection
            classification_result = self.classifier.classify_and_select(
                feature_description,
                resources
            )
            
            # Convert classification result to context format
            selected_artifacts = classification_result["selected_artifacts"]
            selected_context = {
                "components": selected_artifacts["components"],
                "infrastructure_sections": selected_artifacts["infrastructure_sections"],
                "business_context_artifacts": selected_artifacts.get("business_context_artifacts", []),
                "include_infrastructure": len(selected_artifacts["infrastructure_sections"]) > 0,
                "include_all_io_examples": selected_artifacts["include_system_io_examples"],
            }
            
            # Update prompt artifacts based on classification
            business_goals = None
            if selected_artifacts["include_business_goals"]:
                business_goals = resources["business_goals"]
            
            agent_guidelines = None
            if selected_artifacts["include_agent_guidelines"]:
                agent_guidelines = resources["agent_guidelines"]
            
            # Create system description with selected components
            system_description = resources["system_description"] or SystemDescription()
            if system_description:
                # Filter components based on classification
                if selected_artifacts["components"]:
                    system_description.components = selected_artifacts["components"]
                # Filter infrastructure sections
                if system_description.infrastructure and selected_artifacts["infrastructure_sections"]:
                    system_description.infrastructure.sections = selected_artifacts["infrastructure_sections"]
            
            # Create filtered business context with only selected artifacts
            business_context = None
            if selected_artifacts.get("business_context_artifacts"):
                from ..types import BusinessContext
                original_bc = resources.get("business_context")
                indexed_at = ""
                if original_bc:
                    indexed_at = original_bc.indexed_at if hasattr(original_bc, 'indexed_at') else ""
                business_context = BusinessContext(
                    artifacts=selected_artifacts["business_context_artifacts"],
                    indexed_at=indexed_at
                )
        else:
            # If classifier is not available, raise an error rather than falling back to keyword matching
            raise ValueError(
                "LLM-based artifact classification is required but classifier is not available. "
                "Please ensure OPENAI_API_KEY is set or provide classifier_api_key. "
                "Keyword matching fallback has been removed in favor of LLM-based selection."
            )
        
        # Create prompt artifacts
        prompt_artifacts = PromptArtifacts(
            business_goals=business_goals or BusinessGoals(
                purpose="Not specified",
                external_constraints=[]
            ),
            system_description=system_description,
            agent_guidelines=agent_guidelines or AgentGuidelines(),
            feature_prompt=feature_prompt,
            business_context=business_context
        )
        
        # Get formatter for model
        formatter = self.formatters.get(model, GPT4Formatter())
        
        # Build initial prompt
        initial_prompt = formatter.format(prompt_artifacts, selected_context)
        
        # Optimization step: Refine prompt for target model
        use_optimizer = enable_optimization if enable_optimization is not None else (self.use_optimizer or refine_with_model)
        optimized_prompt = initial_prompt
        
        if use_optimizer and self.optimizer:
            optimized_prompt = self.optimizer.optimize(
                initial_prompt,
                target_model=model,
                feature_description=feature_description
            )
        
        return {
            "prompt": optimized_prompt,
            "initial_prompt": initial_prompt if use_optimizer else None,
            "classification": classification_result,
            "model": model,
            "feature_type": feature_type,
            "optimized": use_optimizer,
            "classified": use_classifier
        }
    


class PromptBuilderConfig:
    """Configuration for prompt building."""
    
    def __init__(
        self,
        max_context_length: int = 8000,
        include_component_details: bool = True,
        include_infrastructure: bool = True,
        include_examples: bool = True
    ):
        self.max_context_length = max_context_length
        self.include_component_details = include_component_details
        self.include_infrastructure = include_infrastructure
        self.include_examples = include_examples


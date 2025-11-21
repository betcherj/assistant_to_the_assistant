"""LLM-based prompt optimizer for maximizing performance on specific model types."""
import logging
from typing import Optional, Dict, Any

from ..utils import BaseLLMClient, make_llm_call

logger = logging.getLogger(__name__)


class PromptOptimizer(BaseLLMClient):
    """Optimizes prompts for specific LLM model types."""
    
    # Model-specific optimization guidelines
    MODEL_GUIDELINES = {
        "gpt-4": {
            "preferred_format": "structured markdown with clear sections",
            "instruction_style": "direct and explicit",
            "context_handling": "can handle large context windows efficiently",
            "examples": "benefit from few-shot examples",
            "reasoning": "responds well to step-by-step reasoning prompts"
        },
        "gpt-4-turbo": {
            "preferred_format": "structured markdown with clear sections",
            "instruction_style": "direct and explicit",
            "context_handling": "excellent at handling large context windows",
            "examples": "benefit from few-shot examples",
            "reasoning": "responds well to step-by-step reasoning prompts"
        },
        "gpt-4-turbo-preview": {
            "preferred_format": "structured markdown with clear sections",
            "instruction_style": "direct and explicit",
            "context_handling": "excellent at handling large context windows",
            "examples": "benefit from few-shot examples",
            "reasoning": "responds well to step-by-step reasoning prompts"
        },
        "gpt-3.5-turbo": {
            "preferred_format": "concise structured format",
            "instruction_style": "clear and concise",
            "context_handling": "moderate context window",
            "examples": "benefit from examples but keep concise",
            "reasoning": "prefer simpler, more direct instructions"
        },
        "claude-3-opus": {
            "preferred_format": "natural language with clear structure",
            "instruction_style": "conversational but precise",
            "context_handling": "excellent at handling large context",
            "examples": "benefit from detailed examples",
            "reasoning": "responds well to detailed explanations"
        },
        "claude-3-sonnet": {
            "preferred_format": "natural language with clear structure",
            "instruction_style": "conversational but precise",
            "context_handling": "good at handling large context",
            "examples": "benefit from examples",
            "reasoning": "responds well to explanations"
        },
        "claude-3-haiku": {
            "preferred_format": "concise natural language",
            "instruction_style": "direct and concise",
            "context_handling": "moderate context window",
            "examples": "benefit from concise examples",
            "reasoning": "prefer simpler instructions"
        },
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        optimizer_model: str = "gpt-4-turbo-preview"
    ):
        """
        Initialize the prompt optimizer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            optimizer_model: Model to use for optimization (judge model)
        """
        super().__init__(api_key=api_key, model=optimizer_model)
        self.optimizer_model = self.model  # Alias for backward compatibility
    
    def optimize(
        self,
        prompt: str,
        target_model: str,
        feature_description: Optional[str] = None
    ) -> str:
        """
        Optimize a prompt for a specific target model.
        
        Args:
            prompt: Initial prompt to optimize
            target_model: Target model to optimize for
            feature_description: Optional feature description for context
        
        Returns:
            Optimized prompt
        """
        # Get model-specific guidelines
        model_guidelines = self.MODEL_GUIDELINES.get(
            target_model,
            self.MODEL_GUIDELINES["gpt-4-turbo-preview"]  # Default
        )
        
        # Use LLM to optimize the prompt
        optimized_prompt = self._llm_optimize(
            prompt,
            target_model,
            model_guidelines,
            feature_description
        )
        
        return optimized_prompt
    
    def _llm_optimize(
        self,
        prompt: str,
        target_model: str,
        model_guidelines: Dict[str, str],
        feature_description: Optional[str]
    ) -> str:
        """Use LLM to optimize the prompt."""
        
        optimization_prompt = self._build_optimization_prompt(
            prompt,
            target_model,
            model_guidelines,
            feature_description
        )
        
        system_message = (
            "You are an expert at optimizing prompts for LLM models. Your goal is to "
            "improve prompt clarity, structure, and effectiveness for the target model "
            "while preserving all essential information and context."
        )
        
        try:
            optimized = make_llm_call(
                client=self.client,
                model=self.optimizer_model,
                system_message=system_message,
                user_message=optimization_prompt,
                temperature=0.5  # Slightly higher for creativity in optimization
            )
            return optimized
            
        except Exception as e:
            logger.error(f"Error during prompt optimization: {e}", exc_info=True)
            # Return original prompt if optimization fails
            return prompt
    
    def _build_optimization_prompt(
        self,
        prompt: str,
        target_model: str,
        model_guidelines: Dict[str, str],
        feature_description: Optional[str]
    ) -> str:
        """Build prompt for optimization."""
        
        feature_context = ""
        if feature_description:
            feature_context = f"""
Feature Description:
{feature_description}
"""
        
        return f"""Optimize the following prompt for the target model: {target_model}

Target Model Guidelines:
- Preferred Format: {model_guidelines['preferred_format']}
- Instruction Style: {model_guidelines['instruction_style']}
- Context Handling: {model_guidelines['context_handling']}
- Examples: {model_guidelines['examples']}
- Reasoning: {model_guidelines['reasoning']}

{feature_context}
Current Prompt:
{prompt}

Optimization Goals:
1. Improve clarity and structure according to target model preferences
2. Ensure all essential context is preserved
3. Optimize formatting for better model comprehension
4. Enhance instruction clarity
5. Adjust detail level based on model capabilities
6. Improve organization and flow

Return the optimized prompt. Do not add explanations or comments, just return the improved prompt.
"""
    
    def optimize_with_feedback(
        self,
        prompt: str,
        target_model: str,
        feedback: Optional[str] = None
    ) -> str:
        """
        Optimize prompt with optional feedback from previous attempts.
        
        Args:
            prompt: Initial prompt
            target_model: Target model
            feedback: Optional feedback about prompt performance
        
        Returns:
            Optimized prompt
        """
        if feedback:
            optimization_prompt = f"""Optimize the following prompt for {target_model} based on this feedback:

Feedback:
{feedback}

Current Prompt:
{prompt}

Please improve the prompt addressing the feedback while maintaining all essential information.
"""
        else:
            return self.optimize(prompt, target_model)
        
        try:
            optimized = make_llm_call(
                client=self.client,
                model=self.optimizer_model,
                system_message="You are an expert at optimizing prompts based on performance feedback.",
                user_message=optimization_prompt,
                temperature=0.5
            )
            return optimized
            
        except Exception as e:
            logger.error(f"Error during feedback-based optimization: {e}", exc_info=True)
            return prompt


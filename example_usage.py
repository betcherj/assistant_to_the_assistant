"""Example usage of Assistant to the Assistant framework."""
from project_resources import ProjectResourceManager
from prompt_construction import PromptBuilder
from types import BusinessGoals, AgentGuidelines

def main():
    """Example usage."""
    # Initialize managers
    resource_manager = ProjectResourceManager()
    prompt_builder = PromptBuilder(resource_manager)
    
    # Set business goals
    business_goals = BusinessGoals(
        purpose="Build a REST API for managing user accounts",
        external_constraints=["Must comply with GDPR", "Must support 10k concurrent users"]
    )
    resource_manager.save_business_goals(business_goals)
    print("✓ Business goals saved")
    
    # Set agent guidelines
    agent_guidelines = AgentGuidelines(
        guardrails=[
            "Never commit API keys to code",
            "Always validate user input"
        ],
        best_practices=[
            "Use type hints",
            "Write docstrings for all functions",
            "Follow PEP 8 style guide"
        ],
        coding_standards=[
            "Use async/await for I/O operations",
            "Return Pydantic models from API endpoints"
        ]
    )
    resource_manager.save_agent_guidelines(agent_guidelines)
    print("✓ Agent guidelines saved")
    
    # Generate a prompt with classification and optimization
    result = prompt_builder.build_prompt(
        feature_description="Add user authentication endpoint that accepts email and password",
        feature_type="feature",
        model="gpt-4-turbo-preview",
        include_all_context=False,  # Use classification to select relevant context
        enable_classification=True,  # Enable LLM-based artifact classification
        enable_optimization=True     # Enable LLM-based prompt optimization
    )
    
    print("\n" + "="*80)
    print("GENERATED PROMPT:")
    print("="*80)
    print(result["prompt"])
    print("="*80)
    
    if result.get("classification"):
        print("\nClassification Results:")
        print(f"  Feature Category: {result['classification'].get('feature_category', 'unknown')}")
        print(f"  Complexity: {result['classification'].get('complexity', 'unknown')}")
        print(f"  Reasoning: {result['classification'].get('reasoning', 'N/A')}")
    
    print(f"\nOptimized: {result.get('optimized', False)}")
    print(f"Classified: {result.get('classified', False)}")

if __name__ == "__main__":
    main()



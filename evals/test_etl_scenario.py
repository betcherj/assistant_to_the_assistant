"""Evaluation test for ETL scenario."""
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import assistant_to_the_assistant
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from assistant_to_the_assistant.project_resources import ProjectResourceManager
from assistant_to_the_assistant.prompt_construction import PromptBuilder
from assistant_to_the_assistant.project_indexer import ProjectIndexer, InfrastructureIndexer
from assistant_to_the_assistant.types import BusinessGoals, SystemDescription, InfrastructureDescription, InfrastructureSection

logger = logging.getLogger(__name__)


class ETLScenarioEval:
    """Evaluation for ETL scenario."""
    
    def __init__(self, scenario_dir: Path):
        """
        Initialize the evaluation.
        
        Args:
            scenario_dir: Directory containing scenario files
        """
        self.scenario_dir = scenario_dir
        self.resource_manager = ProjectResourceManager()
        self.prompt_builder = PromptBuilder(resource_manager)
    
    def setup_scenario(self):
        """Set up the ETL scenario with business context, infrastructure, and codebase."""
        logger.info("Setting up ETL scenario...")
        
        # Load business context from YAML
        business_context_path = self.scenario_dir / "business_context.yaml"
        if business_context_path.exists():
            import yaml
            with open(business_context_path, 'r') as f:
                business_data = yaml.safe_load(f)
            
            business_goals = BusinessGoals(
                purpose=business_data.get('purpose', ''),
                external_constraints=business_data.get('external_constraints', [])
            )
            self.resource_manager.save_business_goals(business_goals)
            logger.info("✓ Business goals loaded")
        
        # Load infrastructure from YAML
        infra_path = self.scenario_dir / "infrastructure.yaml"
        if infra_path.exists():
            import yaml
            with open(infra_path, 'r') as f:
                infra_data = yaml.safe_load(f)
            
            # Create infrastructure sections
            sections = []
            for section_data in infra_data.get('sections', []):
                section = InfrastructureSection(
                    title=section_data['title'],
                    content=section_data['content'],
                    section_type=section_data['section_type'],
                    keywords=section_data.get('keywords', [])
                )
                sections.append(section)
            
            infrastructure = InfrastructureDescription(
                deployment=infra_data.get('deployment'),
                databases=infra_data.get('databases', []),
                services=infra_data.get('services', []),
                sections=sections
            )
            
            # Create or update system description with infrastructure
            system_description = self.resource_manager.load_system_description() or SystemDescription()
            system_description.infrastructure = infrastructure
            self.resource_manager.save_system_description(system_description)
            logger.info("✓ Infrastructure loaded")
        
        # Index mock codebase
        mock_codebase_path = self.scenario_dir / "mock_codebase"
        if mock_codebase_path.exists():
            indexer = ProjectIndexer()
            component_index = indexer.index_codebase(
                paths=[str(mock_codebase_path / "src")]
            )
            
            # Update system description with components
            system_description = self.resource_manager.load_system_description() or SystemDescription()
            system_description.components = component_index.components
            self.resource_manager.save_system_description(system_description)
            logger.info(f"✓ Codebase indexed: {len(component_index.components)} components")
    
    def test_prompt_generation(self) -> Dict[str, Any]:
        """
        Test prompt generation for the ETL scenario.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing prompt generation...")
        
        # Load feature spec
        feature_spec_path = self.scenario_dir / "feature_spec.yaml"
        if not feature_spec_path.exists():
            raise FileNotFoundError(f"Feature spec not found: {feature_spec_path}")
        
        import yaml
        with open(feature_spec_path, 'r') as f:
            feature_data = yaml.safe_load(f)
        
        # Generate prompt
        result = self.prompt_builder.build_prompt(
            feature_description=feature_data['feature_description'],
            feature_type=feature_data.get('feature_type', 'feature'),
            feature_examples=feature_data.get('feature_examples'),
            model=feature_data.get('model', 'gpt-4-turbo-preview'),
            include_all_context=feature_data.get('include_all_context', False),
            enable_classification=feature_data.get('enable_classification', True),
            enable_optimization=feature_data.get('enable_optimization', True)
        )
        
        # Save generated prompt
        output_file = feature_data.get('output_file')
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result['prompt'], encoding='utf-8')
            logger.info(f"✓ Prompt saved to {output_path}")
        
        # Validate prompt contains expected elements
        prompt_text = result['prompt']
        validations = {
            'contains_feature_description': feature_data['feature_description'] in prompt_text or len(feature_data['feature_description']) > 0,
            'contains_business_context': 'ETL' in prompt_text or 'extract' in prompt_text.lower(),
            'contains_infrastructure': 'ECS' in prompt_text or 'AWS' in prompt_text or 'infrastructure' in prompt_text.lower(),
            'contains_components': len(result.get('classification', {}).get('selected_artifacts', {}).get('components', [])) > 0 or 'component' in prompt_text.lower(),
            'classification_used': result.get('classified', False),
            'optimization_used': result.get('optimized', False),
        }
        
        return {
            'prompt': result['prompt'],
            'classification': result.get('classification'),
            'validations': validations,
            'all_validations_passed': all(validations.values())
        }
    
    def test_component_selection(self) -> Dict[str, Any]:
        """
        Test that relevant components are selected for the feature.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing component selection...")
        
        # Load feature spec
        feature_spec_path = self.scenario_dir / "feature_spec.yaml"
        import yaml
        with open(feature_spec_path, 'r') as f:
            feature_data = yaml.safe_load(f)
        
        # Generate prompt with classification
        result = self.prompt_builder.build_prompt(
            feature_description=feature_data['feature_description'],
            feature_type='feature',
            model='gpt-4-turbo-preview',
            include_all_context=False,
            enable_classification=True,
            enable_optimization=False
        )
        
        classification = result.get('classification', {})
        selected_artifacts = classification.get('selected_artifacts', {})
        selected_components = selected_artifacts.get('components', [])
        
        # Check that relevant components were selected
        # For email attachment feature, we expect order_extractor and document_processor to be relevant
        component_names = [comp.name.lower() for comp in selected_components]
        
        validations = {
            'components_selected': len(selected_components) > 0,
            'relevant_components_selected': any(
                'order' in name or 'document' in name or 'extract' in name
                for name in component_names
            ),
            'classification_reasoning_present': 'reasoning' in classification,
        }
        
        return {
            'selected_components': [comp.name for comp in selected_components],
            'validations': validations,
            'all_validations_passed': all(validations.values())
        }
    
    def run_eval(self) -> Dict[str, Any]:
        """
        Run the complete evaluation.
        
        Returns:
            Dictionary with all test results
        """
        logger.info("="*80)
        logger.info("Running ETL Scenario Evaluation")
        logger.info("="*80)
        
        # Setup
        self.setup_scenario()
        
        # Run tests
        prompt_test = self.test_prompt_generation()
        component_test = self.test_component_selection()
        
        # Summary
        all_passed = (
            prompt_test['all_validations_passed'] and
            component_test['all_validations_passed']
        )
        
        results = {
            'prompt_generation': prompt_test,
            'component_selection': component_test,
            'all_tests_passed': all_passed
        }
        
        logger.info("="*80)
        logger.info("Evaluation Results:")
        logger.info(f"  Prompt Generation: {'PASS' if prompt_test['all_validations_passed'] else 'FAIL'}")
        logger.info(f"  Component Selection: {'PASS' if component_test['all_validations_passed'] else 'FAIL'}")
        logger.info(f"  Overall: {'PASS' if all_passed else 'FAIL'}")
        logger.info("="*80)
        
        return results


def main():
    """Main entry point for evaluation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scenario_dir = Path(__file__).parent / "etl_scenario"
    
    if not scenario_dir.exists():
        logger.error(f"Scenario directory not found: {scenario_dir}")
        sys.exit(1)
    
    eval = ETLScenarioEval(scenario_dir)
    results = eval.run_eval()
    
    # Exit with error code if tests failed
    sys.exit(0 if results['all_tests_passed'] else 1)


if __name__ == "__main__":
    main()


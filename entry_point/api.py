"""FastAPI endpoints for Assistant to the Assistant."""
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..project_indexer import InfrastructureIndexer
from ..project_resources import ProjectResourceManager
from ..prompt_construction import PromptBuilder
from ..types import AgentGuidelines, BusinessGoals, FeatureExample, SystemDescription

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Assistant to the Assistant",
    description="Low code LLM assisted software development framework",
    version="0.1.0"
)


# Request/Response models
class IndexRequest(BaseModel):
    """Request model for indexing endpoint."""
    codebase_paths: List[str] = Field(..., description="Paths to codebase files/directories to index")
    config_paths: Optional[List[str]] = Field(None, description="Paths to configuration files")
    dockerfile_path: Optional[str] = Field(None, description="Path to Dockerfile")
    readme_path: Optional[str] = Field(None, description="Path to README")
    document_paths: Optional[List[str]] = Field(None, description="Paths to contextual documents")
    api_key: Optional[str] = Field(None, description="OpenAI API key (if not in env)")
    model: str = Field(default="gpt-4-turbo-preview", description="LLM model to use")


class InfrastructureIndexRequest(BaseModel):
    """Request model for infrastructure indexing endpoint."""
    repo_url: Optional[str] = Field(None, description="Repository URL (GitLab supported, files will be auto-discovered)")
    repo_token: Optional[str] = Field(None, description="Repository access token")
    repo_branch: Optional[str] = Field(None, description="Branch to clone (defaults to default branch)")
    tfstate_path: Optional[str] = Field(None, description="Path to Terraform state file (.tfstate) - remote, must be provided if needed")
    gitlab_ci_path: Optional[str] = Field(None, description="Path to .gitlab-ci.yml file (auto-discovered if repo_url provided)")
    dockerfile_path: Optional[str] = Field(None, description="Path to Dockerfile (auto-discovered if repo_url provided)")
    docker_compose_path: Optional[str] = Field(None, description="Path to docker-compose.yml (auto-discovered if repo_url provided)")
    ecs_task_def_path: Optional[str] = Field(None, description="Path to ECS task definition JSON (auto-discovered if repo_url provided)")
    cloudformation_path: Optional[str] = Field(None, description="Path to CloudFormation template (auto-discovered if repo_url provided)")
    gitlab_token: Optional[str] = Field(None, description="GitLab access token (deprecated, use repo_token)")
    gitlab_repo_url: Optional[str] = Field(None, description="GitLab repository URL (deprecated, use repo_url)")
    aws_access_key: Optional[str] = Field(None, description="AWS access key")
    aws_secret_key: Optional[str] = Field(None, description="AWS secret key")
    aws_region: Optional[str] = Field(None, description="AWS region")
    api_key: Optional[str] = Field(None, description="OpenAI API key (if not in env)")
    model: str = Field(default="gpt-4-turbo-preview", description="LLM model to use")


class BusinessGoalsRequest(BaseModel):
    """Request model for setting business goals."""
    purpose: str
    external_constraints: List[str] = Field(default_factory=list)


class SystemDescriptionRequest(BaseModel):
    """Request model for setting system description."""
    io_examples: List[Dict[str, str]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    infrastructure: Optional[Dict[str, Any]] = Field(None)


class AgentGuidelinesRequest(BaseModel):
    """Request model for setting agent guidelines."""
    guardrails: List[str] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)
    coding_standards: List[str] = Field(default_factory=list)


class FeatureExampleRequest(BaseModel):
    """Request model for feature example."""
    input_description: str
    output_description: str
    example: Optional[str] = None


class PromptRequest(BaseModel):
    """Request model for prompt generation."""
    feature_description: str = Field(..., description="Description of what to build/fix")
    feature_type: str = Field(default="feature", description="Type: feature, fix, or instance")
    feature_examples: Optional[List[Dict[str, str]]] = Field(None, description="Feature-level examples")
    model: str = Field(default="gpt-4-turbo-preview", description="Target LLM model")
    include_all_context: bool = Field(default=False, description="Include all context or select relevant")
    refine_with_model: bool = Field(default=False, description="Refine prompt using target model (deprecated, use enable_optimization)")
    enable_classification: Optional[bool] = Field(None, description="Enable LLM-based artifact classification (default: True)")
    enable_optimization: Optional[bool] = Field(None, description="Enable LLM-based prompt optimization (default: True)")
    return_metadata: bool = Field(default=True, description="Return classification and optimization metadata")


# Initialize managers
resource_manager = ProjectResourceManager()
prompt_builder = PromptBuilder(resource_manager)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Assistant to the Assistant API",
        "version": "0.1.0",
        "endpoints": [
            "/index",
            "/index-infrastructure",
            "/business-goals",
            "/system-description",
            "/agent-guidelines",
            "/prompt",
            "/resources"
        ]
    }


@app.post("/index")
async def index_project(request: IndexRequest):
    """
    Index project codebase, infrastructure, and documents.
    
    This endpoint accepts paths to resources and initializes the project background resources.
    """
    try:
        result = resource_manager.index_project(
            codebase_paths=request.codebase_paths,
            config_paths=request.config_paths,
            dockerfile_path=request.dockerfile_path,
            readme_path=request.readme_path,
            document_paths=request.document_paths,
            api_key=request.api_key,
            model=request.model
        )
        return JSONResponse(content={
            "status": "success",
            "message": "Project indexed successfully",
            "result": {
                "components_indexed": len(result["component_index"].components),
                "infrastructure_indexed": result["infrastructure"] is not None,
                "documents_indexed": len(result.get("document_summaries", {}))
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.post("/index-infrastructure")
async def index_infrastructure(request: InfrastructureIndexRequest):
    """
    Index infrastructure files and generate structured markdown documentation.
    
    Parses Terraform state files, GitLab CI configurations, Docker files, and AWS configurations
    to generate comprehensive infrastructure documentation broken into sections.
    
    If repo_url is provided, the endpoint will automatically discover infrastructure files
    by cloning and crawling the repository. Missing files are skipped gracefully.
    """
    try:
        indexer = InfrastructureIndexer(
            api_key=request.api_key,
            model=request.model
        )
        
        infrastructure = indexer.index_infrastructure(
            repo_url=request.repo_url,
            repo_token=request.repo_token,
            repo_branch=request.repo_branch,
            tfstate_path=request.tfstate_path,
            gitlab_ci_path=request.gitlab_ci_path,
            dockerfile_path=request.dockerfile_path,
            docker_compose_path=request.docker_compose_path,
            ecs_task_def_path=request.ecs_task_def_path,
            cloudformation_path=request.cloudformation_path,
            gitlab_token=request.gitlab_token,
            gitlab_repo_url=request.gitlab_repo_url,
            aws_access_key=request.aws_access_key,
            aws_secret_key=request.aws_secret_key,
            aws_region=request.aws_region,
        )
        
        # Save infrastructure to resources
        resource_manager.save_infrastructure(infrastructure)
        
        # Update system description with infrastructure
        system_description = resource_manager.load_system_description()
        if system_description:
            system_description.infrastructure = infrastructure
            resource_manager.save_system_description(system_description)
        else:
            from ..types import SystemDescription
            system_description = SystemDescription(infrastructure=infrastructure)
            resource_manager.save_system_description(system_description)
        
        # Build response with discovered files info
        response_data = {
            "status": "success",
            "message": "Infrastructure indexed successfully",
            "result": {
                "sections_generated": len(infrastructure.sections),
                "section_types": [s.section_type for s in infrastructure.sections],
                "markdown_length": len(infrastructure.markdown_document or ""),
            }
        }
        
        # Include discovered files info if repo_url was provided
        if request.repo_url:
            response_data["result"]["repo_url"] = request.repo_url
            response_data["result"]["auto_discovery"] = True
        
        # Include infrastructure data
        response_data["result"]["infrastructure"] = infrastructure.model_dump()
        
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Infrastructure indexing failed: {str(e)}")


@app.post("/business-goals")
async def set_business_goals(request: BusinessGoalsRequest):
    """Set business goals for the project."""
    try:
        business_goals = BusinessGoals(
            purpose=request.purpose,
            external_constraints=request.external_constraints
        )
        resource_manager.save_business_goals(business_goals)
        return {"status": "success", "message": "Business goals saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save business goals: {str(e)}")


@app.get("/business-goals")
async def get_business_goals():
    """Get current business goals."""
    business_goals = resource_manager.load_business_goals()
    if not business_goals:
        raise HTTPException(status_code=404, detail="Business goals not set")
    return business_goals.model_dump()


@app.post("/system-description")
async def set_system_description(request: SystemDescriptionRequest):
    """Set system description."""
    try:
        from ..types import SystemIOExample, Component, InfrastructureDescription
        
        io_examples = [
            SystemIOExample(**ex) for ex in request.io_examples
        ]
        
        components = [
            Component(**comp) for comp in request.components
        ]
        
        infrastructure = None
        if request.infrastructure:
            infrastructure = InfrastructureDescription(**request.infrastructure)
        
        system_description = SystemDescription(
            io_examples=io_examples,
            components=components,
            infrastructure=infrastructure or InfrastructureDescription()
        )
        resource_manager.save_system_description(system_description)
        return {"status": "success", "message": "System description saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save system description: {str(e)}")


@app.get("/system-description")
async def get_system_description():
    """Get current system description."""
    system_description = resource_manager.load_system_description()
    if not system_description:
        raise HTTPException(status_code=404, detail="System description not set")
    return system_description.model_dump()


@app.post("/agent-guidelines")
async def set_agent_guidelines(request: AgentGuidelinesRequest):
    """Set agent guidelines (guardrails and best practices)."""
    try:
        agent_guidelines = AgentGuidelines(
            guardrails=request.guardrails,
            best_practices=request.best_practices,
            coding_standards=request.coding_standards
        )
        resource_manager.save_agent_guidelines(agent_guidelines)
        return {"status": "success", "message": "Agent guidelines saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save agent guidelines: {str(e)}")


@app.get("/agent-guidelines")
async def get_agent_guidelines():
    """Get current agent guidelines."""
    agent_guidelines = resource_manager.load_agent_guidelines()
    if not agent_guidelines:
        raise HTTPException(status_code=404, detail="Agent guidelines not set")
    return agent_guidelines.model_dump()


@app.post("/prompt")
async def generate_prompt(request: PromptRequest):
    """
    Generate a formatted prompt for feature development.
    
    Combines stored project information and relevant business context.
    Uses LLM-based classification to select relevant artifacts and optimization
    to maximize performance for the target model.
    """
    try:
        result = prompt_builder.build_prompt(
            feature_description=request.feature_description,
            feature_type=request.feature_type,
            feature_examples=request.feature_examples,
            model=request.model,
            include_all_context=request.include_all_context,
            refine_with_model=request.refine_with_model,
            enable_classification=request.enable_classification,
            enable_optimization=request.enable_optimization
        )
        
        if request.return_metadata:
            return {
                "status": "success",
                "prompt": result["prompt"],
                "model": result["model"],
                "feature_type": result["feature_type"],
                "metadata": {
                    "classified": result.get("classified", False),
                    "optimized": result.get("optimized", False),
                    "classification": result.get("classification"),
                    "initial_prompt": result.get("initial_prompt")
                }
            }
        else:
            return {
                "status": "success",
                "prompt": result["prompt"],
                "model": result["model"],
                "feature_type": result["feature_type"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")


@app.get("/resources")
async def get_resources():
    """Get all project resources."""
    resources = resource_manager.get_all_resources()
    return {
        "business_goals": resources["business_goals"].model_dump() if resources["business_goals"] else None,
        "system_description": resources["system_description"].model_dump() if resources["system_description"] else None,
        "agent_guidelines": resources["agent_guidelines"].model_dump() if resources["agent_guidelines"] else None,
        "component_index": resources["component_index"].model_dump() if resources["component_index"] else None,
        "infrastructure": resources["infrastructure"].model_dump() if resources["infrastructure"] else None,
    }


# Export router for use in main app
router = app


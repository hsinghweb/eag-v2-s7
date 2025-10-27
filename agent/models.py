"""
Pydantic models for AI agent input and output validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


# Query and Response Models
class QueryInput(BaseModel):
    """Input model for agent queries"""
    query: str = Field(..., min_length=1, description="User query to process")


class AgentResponse(BaseModel):
    """Output model for agent responses"""
    result: str = Field(..., description="Final answer from the agent")
    success: bool = Field(default=True, description="Whether the operation was successful")
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Clean answer without formatting")
    full_response: str = Field(..., description="Full formatted response")


# Conversation History Models
class FunctionCallHistoryItem(BaseModel):
    """Model for function call history items"""
    type: Literal["function_call"] = "function_call"
    name: str = Field(..., description="Function name")
    args: Dict[str, Any] = Field(..., description="Function arguments")
    reasoning_type: str = Field(default="", description="Type of reasoning used")
    step: str = Field(default="", description="Step description")
    result: str = Field(..., description="Function result")


class SelfCheckHistoryItem(BaseModel):
    """Model for self-check history items"""
    type: Literal["self_check"] = "self_check"
    content: str = Field(..., description="Self-check content")


class FallbackHistoryItem(BaseModel):
    """Model for fallback reasoning history items"""
    type: Literal["fallback"] = "fallback"
    content: str = Field(..., description="Fallback content")


# Tool Information Models
class ToolParameter(BaseModel):
    """Model for tool parameter information"""
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None


class ToolInfo(BaseModel):
    """Model for tool information"""
    name: str
    description: str
    parameters: List[ToolParameter] = []


# LLM Response Parsing Models
class FunctionCallRequest(BaseModel):
    """Model for parsed function call requests"""
    name: str = Field(..., description="Function name to call")
    args: Any = Field(..., description="Function arguments (can be list or dict)")
    reasoning_type: str = Field(default="", description="Type of reasoning")
    step: str = Field(default="", description="Step description")


class FinalAnswer(BaseModel):
    """Model for final answer responses"""
    answer: str = Field(..., description="Final answer text")


# Iteration State Models
class IterationState(BaseModel):
    """Model for tracking iteration state"""
    iteration: int = Field(ge=0, le=5, description="Current iteration number")
    max_iterations: int = Field(default=5, ge=1, description="Maximum allowed iterations")
    responses: List[str] = Field(default_factory=list, description="Response history")
    last_response: Optional[Any] = Field(default=None, description="Last response received")


# Tool Execution Models
class ToolCallResult(BaseModel):
    """Model for tool execution results"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class ToolCallRequest(BaseModel):
    """Model for tool call requests"""
    func_name: str
    arguments: Dict[str, Any]
    reasoning_type: str = ""
    step_desc: str = ""


# Configuration Models
class AgentConfig(BaseModel):
    """Configuration for the AI agent"""
    max_iterations: int = Field(default=5, ge=1, le=10, description="Maximum iteration count")
    timeout: int = Field(default=10, ge=1, le=60, description="LLM timeout in seconds")
    model_name: str = Field(default="gemini-2.5-flash", description="LLM model name")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="DEBUG")


# Error Models
class AgentError(BaseModel):
    """Model for agent error responses"""
    success: bool = False
    error: str
    error_type: str
    query: Optional[str] = None


# Prompt Formatting Models
class PromptContext(BaseModel):
    """Model for prompt context data"""
    system_prompt: str
    conversation_history: List[Dict[str, Any]] = []
    query: str
    iteration_responses: List[str] = []
    last_response: Optional[Any] = None


class FormattedPrompt(BaseModel):
    """Model for formatted prompt ready for LLM"""
    content: str
    context: PromptContext


# ============================================================================
# YOUTUBE RAG MODELS
# ============================================================================

class YouTubeTranscriptChunk(BaseModel):
    """Model for a chunk of YouTube transcript with metadata"""
    video_id: str = Field(..., description="YouTube video ID")
    chunk_text: str = Field(..., description="Text content of the chunk")
    start_timestamp: float = Field(..., description="Start time in seconds")
    end_timestamp: float = Field(..., description="End time in seconds")
    chunk_index: int = Field(..., description="Index of this chunk in the video")


class IndexYouTubeInput(BaseModel):
    """Input model for indexing a YouTube video"""
    video_id: str = Field(..., min_length=11, max_length=11, description="YouTube video ID (11 characters)")
    video_url: Optional[str] = Field(None, description="Full YouTube URL (optional)")


class IndexYouTubeOutput(BaseModel):
    """Output model for YouTube indexing operation"""
    success: bool = Field(..., description="Whether indexing was successful")
    video_id: str = Field(..., description="YouTube video ID")
    chunks_indexed: int = Field(..., description="Number of chunks indexed")
    message: str = Field(..., description="Status message")


class AskYouTubeInput(BaseModel):
    """Input model for asking questions about YouTube content"""
    question: str = Field(..., min_length=1, description="Question about YouTube content")
    video_id: Optional[str] = Field(None, description="Optional: Restrict search to specific video")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of relevant chunks to retrieve")


class YouTubeContext(BaseModel):
    """Model for retrieved YouTube context"""
    video_id: str = Field(..., description="YouTube video ID")
    chunk_text: str = Field(..., description="Relevant text from transcript")
    timestamp: float = Field(..., description="Timestamp in seconds")
    relevance_score: float = Field(..., description="Similarity score")


class AskYouTubeOutput(BaseModel):
    """Output model for YouTube Q&A"""
    success: bool = Field(..., description="Whether the query was successful")
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    contexts: List[YouTubeContext] = Field(default_factory=list, description="Retrieved contexts with timestamps")
    youtube_links: List[str] = Field(default_factory=list, description="YouTube links with timestamps")


# ============================================================================
# COGNITIVE LAYERS MODELS
# ============================================================================

# 1. PERCEPTION LAYER MODELS
class ThoughtType(str):
    """Enum-like class for thought types"""
    PLANNING = "Planning"
    ANALYSIS = "Analysis"
    DECISION_MAKING = "Decision Making"
    PROBLEM_SOLVING = "Problem Solving"
    MEMORY_INTEGRATION = "Memory Integration"
    SELF_REFLECTION = "Self-Reflection"
    GOAL_SETTING = "Goal Setting"
    PRIORITIZATION = "Prioritization"


class SelfCheckPerception(BaseModel):
    """Self-check result from Perception Layer"""
    clarity_verified: bool = Field(..., description="Whether query clarity is verified")
    entities_complete: bool = Field(..., description="Whether all entities are identified")
    reasoning: str = Field(..., description="Reasoning for the self-check")


class FallbackPerception(BaseModel):
    """Fallback information from Perception Layer"""
    is_uncertain: bool = Field(..., description="Whether the perception is uncertain")
    uncertain_aspects: List[str] = Field(default_factory=list, description="Aspects that are uncertain")
    suggested_clarification: Optional[str] = Field(default="", description="Suggested clarification question for user")


class PerceptionOutput(BaseModel):
    """Output from the Perception Layer"""
    intent: str = Field(..., description="Primary intent of the user query")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities from the query")
    thought_type: str = Field(..., description="Type of cognitive thought involved")
    extracted_facts: List[str] = Field(default_factory=list, description="Facts extracted from the query")
    requires_tools: bool = Field(default=False, description="Whether the query requires tool execution")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in perception")
    self_check: Optional[SelfCheckPerception] = Field(default=None, description="Self-verification results")
    fallback: Optional[FallbackPerception] = Field(default=None, description="Fallback handling information")


# 2. MEMORY LAYER MODELS
class MemoryFact(BaseModel):
    """A single fact stored in memory"""
    content: str = Field(..., description="The fact content")
    timestamp: Optional[str] = Field(default=None, description="When the fact was stored")
    source: str = Field(default="user", description="Source of the fact (user, system, tool)")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score")


class MemoryState(BaseModel):
    """State of the agent's memory"""
    facts: List[MemoryFact] = Field(default_factory=list, description="Stored facts")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    context: Dict[str, Any] = Field(default_factory=dict, description="Current context information")
    conversation_summary: str = Field(default="", description="Summary of conversation so far")


class MemoryQuery(BaseModel):
    """Query to retrieve relevant memories"""
    query: str = Field(..., description="Query to search memories")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results")
    min_relevance: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum relevance score")


class MemoryRetrievalResult(BaseModel):
    """Result from memory retrieval"""
    relevant_facts: List[MemoryFact] = Field(default_factory=list, description="Retrieved facts")
    context: Dict[str, Any] = Field(default_factory=dict, description="Retrieved context")
    summary: str = Field(default="", description="Summary of retrieved information")


# 3. DECISION-MAKING LAYER MODELS
class ActionStep(BaseModel):
    """A single step in an action plan"""
    step_number: int = Field(..., ge=1, description="Step number in sequence")
    action_type: str = Field(..., description="Type of action (tool_call, response, query_memory, etc.)")
    description: str = Field(..., description="Description of the action")
    tool_name: Optional[str] = Field(default=None, description="Tool to call if action_type is tool_call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")
    reasoning: str = Field(default="", description="Reasoning behind this step")
    reasoning_type: str = Field(default="", description="Type of reasoning (arithmetic, logical, algebraic, etc.)")


class FallbackStep(BaseModel):
    """A single fallback step"""
    condition: str = Field(..., description="When to use this fallback")
    alternative_action: str = Field(..., description="What to do instead")
    tool_name: Optional[str] = Field(default=None, description="Alternative tool if applicable")


class SelfCheckDecision(BaseModel):
    """Self-check result from Decision Layer"""
    plan_verified: bool = Field(..., description="Whether the plan is verified")
    tools_available: bool = Field(..., description="Whether required tools are available")
    parameters_complete: bool = Field(..., description="Whether all parameters are complete")
    reasoning: str = Field(..., description="Reasoning for the self-check")


class FallbackPlan(BaseModel):
    """Fallback plan for Decision Layer"""
    has_fallback: bool = Field(..., description="Whether a fallback exists")
    fallback_steps: List[FallbackStep] = Field(default_factory=list, description="Fallback steps")
    error_handling: str = Field(default="", description="What to do if tools fail")


class DecisionOutput(BaseModel):
    """Output from the Decision-Making Layer"""
    action_plan: List[ActionStep] = Field(..., description="Sequence of actions to take")
    reasoning: str = Field(..., description="Overall reasoning for the decision")
    reasoning_type: str = Field(default="", description="Primary type of reasoning used (arithmetic, logical, algebraic, etc.)")
    expected_outcome: str = Field(default="", description="Expected outcome of the plan")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the decision")
    should_continue: bool = Field(default=True, description="Whether to continue with more iterations")
    self_check: Optional[SelfCheckDecision] = Field(default=None, description="Self-verification results")
    fallback_plan: Optional[FallbackPlan] = Field(default=None, description="Fallback plan for errors")


# 4. ACTION LAYER MODELS
class ActionInput(BaseModel):
    """Input for action execution"""
    action_step: ActionStep = Field(..., description="Action step to execute")
    available_tools: List[str] = Field(default_factory=list, description="List of available tool names")


class ActionResult(BaseModel):
    """Result from action execution"""
    success: bool = Field(..., description="Whether the action succeeded")
    result: Optional[Any] = Field(default=None, description="Result data from the action")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: float = Field(default=0.0, description="Time taken to execute")
    facts_to_remember: List[str] = Field(default_factory=list, description="New facts to store in memory")


# AGENT ORCHESTRATION MODELS
class CognitiveState(BaseModel):
    """Complete cognitive state of the agent"""
    perception: Optional[PerceptionOutput] = None
    memory: MemoryState = Field(default_factory=MemoryState)
    decision: Optional[DecisionOutput] = None
    action_results: List[ActionResult] = Field(default_factory=list)
    iteration: int = Field(default=0, ge=0)
    complete: bool = Field(default=False)

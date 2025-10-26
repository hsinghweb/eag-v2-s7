"""
AI Agent with Cognitive Layers Architecture

This module orchestrates the 4 cognitive layers:
👁️ Perception → 🧠 Memory → 🧭 Decision → 🎯 Action

The agent no longer functions as a single "Augmented LLM" but as a
structured, layered cognitive system with clear separation of concerns.
"""
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
import logging
from datetime import datetime
import traceback
from typing import Optional, Dict, Any

# Import cognitive layers
from .perception import PerceptionLayer
from .memory import MemoryLayer
from .decision import DecisionLayer
from .action import ActionLayer

# Import models
from .models import (
    AgentResponse,
    CognitiveState,
    MemoryQuery
)

# Load environment variables first
load_dotenv()

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"cognitive_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Get log level from environment variable, default to INFO
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
log_level = log_level_map.get(log_level_str, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Configure StreamHandler to use UTF-8 encoding
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
        handler.setStream(open(handler.stream.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False))
logger = logging.getLogger(__name__)

# Log the configured log level
logger.info(f"Logging configured with level: {logging.getLevelName(log_level)}")

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in .env file")
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Constants
MAX_ITERATIONS = 50  # Each LLM call or tool call counts as one iteration


class CognitiveAgent:
    """
    Cognitive Agent with 4-layer architecture.
    
    This agent processes queries through distinct cognitive layers:
    1. Perception: Understanding input
    2. Memory: Storing and retrieving context
    3. Decision: Planning actions
    4. Action: Executing the plan
    """
    
    def __init__(self, session: ClientSession, tools: list, preferences: Optional[Dict[str, Any]] = None, memory_file: Optional[str] = None):
        """
        Initialize the Cognitive Agent.
        
        Args:
            session: MCP client session
            tools: Available MCP tools
            preferences: User preferences (math ability, location, etc.)
            memory_file: Path to memory file (if None, creates a timestamped one)
        """
        self.session = session
        self.tools = tools
        self.preferences = preferences or {}
        
        # Create timestamped memory file if not provided
        if memory_file is None:
            memory_file = os.path.join(log_dir, f"agent_memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Initialize cognitive layers
        self.perception = PerceptionLayer(model, user_preferences=self.preferences)
        self.memory = MemoryLayer(memory_file=memory_file)
        self.decision = DecisionLayer(model, user_preferences=self.preferences)
        self.action = ActionLayer(session, tools)
        
        # Store user preferences in memory
        if self.preferences:
            self._store_preferences()
        
        # Initialize cognitive state
        self.state = CognitiveState()
        
        logger.info("[AGENT] Cognitive Agent initialized with 4 layers")
        logger.info(f"[AGENT] Memory file: {memory_file}")
        if self.preferences:
            logger.info(f"[AGENT] User preferences loaded: {self.preferences}")
    
    def _store_preferences(self):
        """
        Store user preferences in the Memory Layer.
        """
        # Store each preference as a fact
        for key, value in self.preferences.items():
            preference_text = f"User preference: {key} = {value}"
            self.memory.store_fact(
                content=preference_text,
                source="user_preferences",
                relevance_score=1.0
            )
        
        # Store in user_preferences dict (always update to ensure proper capture)
        for key, value in self.preferences.items():
            self.memory.memory_state.user_preferences[key] = value
        
        logger.info(f"[AGENT] Stored {len(self.preferences)} user preferences in memory")
    
    def _extract_value_from_result(self, result):
        """Extract numeric/boolean value from various result formats - generic approach."""
        import json
        import re
        
        if isinstance(result, (int, float, bool)):
            return result
        
        if not isinstance(result, str):
            return None
        
        try:
            parsed = json.loads(result)
            return self._extract_value_from_json(parsed)
        except (json.JSONDecodeError, KeyError):
            # Fallback: try to extract any number from the string
            num_match = re.search(r'-?\d+\.?\d*', result)
            if num_match:
                return float(num_match.group())
        
        return None
    
    def _format_result_as_string(self, extracted_value):
        """Format extracted value as string for email/text output."""
        if isinstance(extracted_value, bool):
            return "True" if extracted_value else "False"
        if isinstance(extracted_value, float) and extracted_value.is_integer():
            return str(int(extracted_value))
        return str(extracted_value)
    
    def _build_email_content(self, result_str):
        """Build formatted email content with query and result."""
        initial_query = self.memory.memory_state.context.get("initial_query", "")
        lines = [
            "AI Agent Result",
            "=" * 40,
            "",
        ]
        if initial_query:
            lines.extend([f"Query: {initial_query}", ""])
        lines.extend([
            f"Result: {result_str}",
            "",
            "=" * 40,
            "Computed by AI Agent"
        ])
        return "\n".join(lines)
    
    def _build_email_result_string(self, extracted):
        """Build result string for email content from computation results."""
        computation_results = []
        for i, ar in enumerate(self.state.action_results):
            if self._is_computation_result(i, ar):
                self._parse_tool_result(str(ar.result), computation_results)
        
        # Format based on whether operations are chained
        if len(computation_results) > 1 and self._has_chained_operations(computation_results):
            return self._format_result_as_string(computation_results[-1])
        elif len(computation_results) > 1:
            return ", ".join(str(v) for v in computation_results)
        elif computation_results:
            return self._format_result_as_string(computation_results[0])
        else:
            return self._format_result_as_string(extracted)
    
    def _replace_placeholder(self, value, param_name, results_map):
        """Replace a single placeholder value."""
        import re
        
        if not isinstance(value, str):
            return value
        
        match = re.search(r'RESULT_FROM_STEP_(\d+)', value)
        if not match:
            return value
        
        step_num = int(match.group(1))
        if step_num not in results_map:
            return value
        
        result = results_map[step_num]
        extracted = self._extract_value_from_result(result)
        
        if extracted is None:
            return result
        
        needs_string = param_name and param_name.lower() in ['content', 'text', 'message', 'body', 'description']
        
        if needs_string:
            result_str = self._build_email_result_string(extracted)
            return self._build_email_content(result_str)
        
        return extracted
    
    def _replace_result_placeholders(self, params: dict, results_map: dict) -> dict:
        """Replace result placeholders like 'RESULT_FROM_STEP_1' with actual values."""
        import copy
        
        def replace_recursive(value, param_name=None):
            if isinstance(value, str):
                return self._replace_placeholder(value, param_name, results_map)
            if isinstance(value, dict):
                return {k: replace_recursive(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [replace_recursive(item) for item in value]
            return value
        
        return replace_recursive(copy.deepcopy(params))
    
    def _execute_perception_layer(self, query: str):
        """Execute perception layer if not already done."""
        if self.state.perception is not None:
            return self.state.perception
        
        self.state.iteration += 1
        logger.info("\n" + "-" * 80)
        logger.info(f"[AGENT] ITERATION {self.state.iteration}/{MAX_ITERATIONS}: Perception Layer (LLM Call)")
        logger.info("-" * 80)
        
        perception = self.perception.perceive(query)
        self.state.perception = perception
        
        if perception.extracted_facts:
            self.memory.store_facts(perception.extracted_facts, source="perception")
        
        logger.info(f"[AGENT] ✓ Iteration {self.state.iteration} complete: Perception")
        return perception
    
    def _execute_decision_layer(self, perception, query):
        """Execute decision layer."""
        memory_query = MemoryQuery(query=query, max_results=5, min_relevance=0.3)
        memory_retrieval = self.memory.retrieve_relevant_facts(memory_query)
        
        available_tools = self.action.get_all_tools_info()
        
        self.state.iteration += 1
        logger.info("\n" + "-" * 80)
        logger.info(f"[AGENT] ITERATION {self.state.iteration}/{MAX_ITERATIONS}: Decision Layer (LLM Call)")
        logger.info("-" * 80)
        
        decision = self.decision.decide(
            perception=perception,
            memory=memory_retrieval,
            available_tools=available_tools,
            previous_actions=None
        )
        self.state.decision = decision
        logger.info(f"[AGENT] ✓ Iteration {self.state.iteration} complete: Decision ({len(decision.action_plan)} actions planned)")
        return decision
    
    async def _execute_action_step(self, action_step, action_results_map):
        """Execute a single action step."""
        if action_step.action_type == "tool_call":
            self.state.iteration += 1
            logger.info("\n" + "-" * 80)
            logger.info(f"[AGENT] ITERATION {self.state.iteration}/{MAX_ITERATIONS}: Action Step {action_step.step_number} - {action_step.tool_name}")
            logger.info("-" * 80)
        else:
            logger.info(f"\n[AGENT] Executing action {action_step.step_number}: {action_step.description} (no iteration count)")
        
        if action_step.parameters:
            action_step.parameters = self._replace_result_placeholders(
                action_step.parameters, 
                action_results_map
            )
        
        action_result = await self.action.execute(action_step)
        self.state.action_results.append(action_result)
        
        if action_step.action_type == "tool_call":
            logger.info(f"[AGENT] ✓ Iteration {self.state.iteration} complete: {action_step.tool_name}")
        
        if action_result.success and action_result.result is not None:
            action_results_map[action_step.step_number] = action_result.result
        
        if action_result.success and action_result.facts_to_remember:
            self.memory.store_facts(action_result.facts_to_remember, source="action")
        
        # Don't return response action results - they're just descriptions
        # The actual results will be extracted in _finalize_result
        return None
    
    def _is_computation_result(self, i, ar):
        """
        Check if action result contains a computational result (vs status message).
        Uses heuristics: looks for numeric results or structured data.
        """
        if not (ar.success and ar.result is not None):
            return False
        
        if not (self.state.decision and self.state.decision.action_plan):
            return False
        
        if i >= len(self.state.decision.action_plan):
            return False
        
        action_step = self.state.decision.action_plan[i]
        if action_step.action_type != "tool_call":
            return False
        
        # Heuristic: check if result looks like a status message
        result_str = str(ar.result).lower()
        if any(word in result_str for word in ['sent', 'created', 'added', 'successfully', 'failed']):
            return False
        
        # If it's a JSON with computational values (numbers, booleans, lists), treat as computation
        import json
        import re
        try:
            parsed = json.loads(str(ar.result))
            return isinstance(parsed, dict) and any(isinstance(v, (int, float, bool, list)) for v in parsed.values())
        except json.JSONDecodeError:
            # Check if string contains numbers or boolean keywords
            return bool(re.search(r'\d', result_str)) or result_str in ['true', 'false']
        
        return True
    
    def _process_action_result(self, i, ar, computation_results):
        """Process a single action result and return status message if applicable."""
        if not (ar.success and ar.result is not None and i < len(self.state.decision.action_plan)):
            return None
        
        action_step = self.state.decision.action_plan[i]
        
        if action_step.action_type != "tool_call":
            return None
        
        result_str = str(ar.result)
        
        # Check for status messages (email sent, file created, etc.)
        if any(word in result_str.lower() for word in ['sent', 'created', 'added', 'successfully']):
            return result_str
        
        # Otherwise treat as computation result
        if self._is_computation_result(i, ar):
            self._parse_tool_result(result_str, computation_results)
        
        return None
    
    def _has_chained_operations(self, computation_results):
        """
        Check if computation results are from chained operations.
        
        Heuristic: If there are 3+ computational results, it's likely a chained operation
        (e.g., factorial -> fibonacci -> multiply). If there are exactly 2 results, they're
        likely independent answers (e.g., two consecutive numbers).
        """
        return len(computation_results) >= 3
    
    def _finalize_result(self):
        """Extract and format final result from tool executions."""
        if not (self.state.decision and self.state.decision.action_plan):
            return None
        
        computation_results = []
        status_message = None
        
        for i, ar in enumerate(self.state.action_results):
            status = self._process_action_result(i, ar, computation_results)
            if status:
                status_message = status
        
        # Return computed results for display (no status messages)
        if computation_results:
            # For chained operations (A -> B -> C), show only the final result
            # For independent results (like two separate numbers), show all
            if len(computation_results) > 1 and self._has_chained_operations(computation_results):
                # Chained operations: show only final result
                return str(computation_results[-1])
            elif len(computation_results) > 1:
                # Independent results: show all (e.g., two consecutive numbers)
                return ", ".join(str(v) for v in computation_results)
            else:
                # Single result
                return str(computation_results[0])
        
        # If no computation result but there's a status message, return it
        if status_message:
            return status_message
        
        return None
    
    def _format_value(self, value):
        """Format a value for output."""
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return float(value)
        return None
    
    def _extract_from_common_keys(self, parsed_json):
        """Extract value from common result keys."""
        for key in ['result', 'value', 'answer', 'solution', 'salary', 'output']:
            if key in parsed_json and parsed_json[key] is not None:
                return self._format_value(parsed_json[key])
        return None
    
    def _extract_from_lists(self, parsed_json):
        """Extract last element from any list of numbers."""
        for value in parsed_json.values():
            if isinstance(value, list) and value and isinstance(value[-1], (int, float)):
                return float(value[-1])
        return None
    
    def _extract_any_numeric(self, parsed_json):
        """Extract any numeric value from the dict."""
        for value in parsed_json.values():
            formatted = self._format_value(value)
            if formatted is not None:
                return formatted
        return None
    
    def _extract_value_from_json(self, parsed_json):
        """
        Extract meaningful value from parsed JSON - generic approach.
        Uses priority: common keys > lists > any numeric value.
        """
        if not isinstance(parsed_json, dict):
            return None
        
        # Try extraction strategies in priority order
        for strategy in [self._extract_from_common_keys, 
                        self._extract_from_lists, 
                        self._extract_any_numeric]:
            result = strategy(parsed_json)
            if result is not None:
                return result
        
        return None
    
    def _parse_tool_result(self, result_str, parsed_list):
        """Parse a tool result and append to parsed_list."""
        import json
        import re
        
        try:
            if result_str.strip().startswith('{'):
                parsed = json.loads(result_str)
                extracted = self._extract_value_from_json(parsed)
                if extracted is not None:
                    parsed_list.append(extracted)
            else:
                num_match = re.search(r'-?\d+\.?\d*', result_str)
                if num_match:
                    parsed_list.append(float(num_match.group()))
        except ValueError:
            pass
    
    async def _run_cognitive_loop(self, query: str):
        """Run a single cognitive loop and return final_result if found."""
        perception = self._execute_perception_layer(query)
        
        if self.state.iteration >= MAX_ITERATIONS:
            return None, True  # result, should_stop
        
        # Check for out-of-scope queries (fallback mechanism)
        if perception.intent == "out_of_scope" or (
            perception.fallback and 
            perception.fallback.is_uncertain and 
            perception.fallback.suggested_clarification
        ):
            logger.info("[AGENT] Query is out of scope - triggering fallback mechanism")
            fallback_message = (
                perception.fallback.suggested_clarification if perception.fallback 
                else "I apologize, but this query is outside my mathematical capabilities. I can help with arithmetic, algebra, geometry, statistics, and logical reasoning."
            )
            logger.info(f"[AGENT] Fallback message: {fallback_message}")
            return fallback_message, True  # Return fallback message and stop
        
        decision = self._execute_decision_layer(perception, query)
        
        if self.state.iteration >= MAX_ITERATIONS:
            return None, True
        
        # Execute action plan
        action_results_map = {}
        final_result = None
        
        for action_step in decision.action_plan:
            if self.state.iteration >= MAX_ITERATIONS:
                logger.warning(f"[AGENT] Reached MAX_ITERATIONS limit before action {action_step.step_number}")
                return final_result, True
            
            step_result = await self._execute_action_step(action_step, action_results_map)
            if step_result is not None:
                final_result = step_result
                logger.info(f"[AGENT] Final result obtained: {final_result}")
        
        # Check if should continue
        should_stop = not decision.should_continue or final_result is not None
        return final_result, should_stop
    
    async def process_query(self, query: str) -> AgentResponse:
        """Process a user query through the cognitive layers."""
        logger.info("=" * 80)
        logger.info(f"[AGENT] Starting cognitive processing for: {query}")
        logger.info(f"[AGENT] Max iterations allowed: {MAX_ITERATIONS} (each LLM call or tool call = 1 iteration)")
        logger.info("=" * 80)
        
        try:
            self.state = CognitiveState()
            self.memory.update_context("initial_query", query)
            final_result = None
            
            cognitive_loop_count = 0
            while self.state.iteration < MAX_ITERATIONS:
                cognitive_loop_count += 1
                logger.info("\n" + "=" * 80)
                logger.info(f"[AGENT] COGNITIVE LOOP {cognitive_loop_count}")
                logger.info("=" * 80)
                
                final_result, should_stop = await self._run_cognitive_loop(query)
                
                if should_stop:
                    self.state.complete = True
                    logger.info("\n" + "=" * 80)
                    logger.info(f"[AGENT] Cognitive processing complete after {self.state.iteration} iterations")
                    logger.info("=" * 80)
                    break
                
                logger.info("[AGENT] Continuing to next cognitive loop...")
            
            # Finalize result
            if final_result is None:
                final_result = self._finalize_result()
                if final_result:
                    logger.info(f"[AGENT] Using computed result: {final_result}")
                else:
                    final_result = "Task completed"
            
            # Save memory to disk
            self.memory.save_memory()
            
            # Create response
            response = AgentResponse(
                result=final_result,
                success=True,
                query=query,
                answer=final_result,
                full_response=f"Query: {query}\nResult: {final_result}"
            )
            
            # Count breakdown
            llm_calls = self.state.iteration - len([ar for i, ar in enumerate(self.state.action_results) 
                                                    if i < len(self.state.decision.action_plan) and 
                                                    self.state.decision.action_plan[i].action_type == "tool_call"])
            tool_calls = self.state.iteration - llm_calls
            
            logger.info("=" * 80)
            logger.info("[AGENT] Processing completed successfully")
            logger.info(f"Total Iterations: {self.state.iteration}")
            logger.info(f"  - LLM calls: {llm_calls}")
            logger.info(f"  - Tool calls: {tool_calls}")
            logger.info(f"Final Result: {final_result}")
            logger.info("=" * 80 + "\n")
            
            return response
            
        except Exception as e:
            logger.error(f"[AGENT] Error in cognitive processing: {e}")
            logger.error(traceback.format_exc())
            
            # Return error response
            return AgentResponse(
                result=f"Error: {str(e)}",
                success=False,
                query=query,
                answer=f"I encountered an error: {str(e)}",
                full_response=f"Query: {query}\nError: {str(e)}"
            )


async def main(query: str, preferences: Optional[Dict[str, Any]] = None):
    """
    Main entry point for the cognitive agent.
    
    Args:
        query: User query string
        preferences: Dictionary of user preferences (e.g., math ability, location, etc.)
        
    Returns:
        JSON string with agent response
    """
    logger.info(f"Starting cognitive agent with query: {query}")
    if preferences:
        logger.info(f"User preferences: {preferences}")
    
    try:
        # Establish MCP connection
        logger.info("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["server_mcp/mcp_server.py", "dev"]
        )

        async with stdio_client(server_params) as (read, write):
            logger.info("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                logger.info("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                logger.info("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logger.info(f"Successfully retrieved {len(tools)} tools")
                
                # Create cognitive agent
                agent = CognitiveAgent(session, tools, preferences=preferences)
                
                # Process query
                response = await agent.process_query(query)
                
                # Return JSON response
                return response.model_dump_json(indent=2)
                
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    query = input("Enter your query: ").strip()
    if not query:
        logger.error("No query provided by user")
        print("Error: Please provide a valid query")
    else:
        logger.info(f"User provided query: {query}")
        result = asyncio.run(main(query))
        if result:
            print(f"\n{'='*80}")
            print("RESULT:")
            print(result)
            print(f"{'='*80}")

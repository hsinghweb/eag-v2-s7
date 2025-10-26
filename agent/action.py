"""
Action Layer - Do the Thing™

This module handles the action layer of the cognitive architecture.
It executes decisions by calling tools or generating responses.
"""
import logging
import time
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from .models import ActionStep, ActionResult

logger = logging.getLogger(__name__)


class ActionLayer:
    """
    The Action Layer executes decisions.
    
    🎯 ACT: Execute the plan
    
    This layer handles:
    - Calling external APIs/MCP tools
    - Generating responses
    - Writing to files (future)
    - Any other execution tasks
    """
    
    def __init__(self, session: ClientSession, tools: List[Any]):
        """
        Initialize the Action Layer.
        
        Args:
            session: MCP client session for tool execution
            tools: List of available MCP tools
        """
        self.session = session
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
        logger.info(f"[ACTION] Action Layer initialized with {len(tools)} tools")
    
    async def execute(self, action_step: ActionStep) -> ActionResult:
        """
        Execute a single action step.
        
        Args:
            action_step: Action step to execute
            
        Returns:
            ActionResult: Result of the action execution
        """
        logger.info(f"[ACTION] EXECUTING: Step {action_step.step_number} - {action_step.description}")
        start_time = time.time()
        
        try:
            if action_step.action_type == "tool_call":
                result = await self._execute_tool_call(action_step)
            elif action_step.action_type == "response":
                result = self._generate_response(action_step)
            elif action_step.action_type == "query_memory":
                result = self._query_memory(action_step)
            else:
                raise ValueError(f"Unknown action type: {action_step.action_type}")
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            logger.info(f"[ACTION] Completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"[ACTION] Failed: {e}")
            
            return ActionResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                facts_to_remember=[f"Action failed: {action_step.description} - Error: {str(e)}"]
            )
    
    async def _execute_tool_call(self, action_step: ActionStep) -> ActionResult:
        """
        Execute an MCP tool call.
        
        Args:
            action_step: Action step with tool call details
            
        Returns:
            ActionResult from tool execution
        """
        tool_name = action_step.tool_name
        parameters = action_step.parameters
        
        if not tool_name:
            raise ValueError("tool_name is required for tool_call action type")
        
        if tool_name not in self.tool_map:
            available = ', '.join(self.tool_map.keys())
            raise ValueError(f"Tool '{tool_name}' not found. Available: {available}")
        
        logger.debug(f"Calling tool: {tool_name} with params: {parameters}")
        
        # Execute the tool via MCP
        result = await self.session.call_tool(tool_name, arguments=parameters)
        
        # Extract result content
        result_content = self._extract_result_content(result)
        
        # Create facts to remember
        facts_to_remember = [
            f"Called tool {tool_name}",
            f"Parameters: {parameters}",
            f"Result: {result_content}"
        ]
        
        return ActionResult(
            success=True,
            result=result_content,
            error=None,
            execution_time=0.0,  # Will be set by execute()
            facts_to_remember=facts_to_remember
        )
    
    def _generate_response(self, action_step: ActionStep) -> ActionResult:
        """
        Generate a text response.
        
        Args:
            action_step: Action step with response details
            
        Returns:
            ActionResult with generated response
        """
        message = action_step.parameters.get("message", action_step.description)
        
        logger.debug(f"Generating response: {message}")
        
        return ActionResult(
            success=True,
            result=message,
            error=None,
            execution_time=0.0,
            facts_to_remember=[f"Generated response: {message}"]
        )
    
    def _query_memory(self, _action_step: ActionStep) -> ActionResult:
        """
        Query memory (placeholder for future implementation).
        
        Args:
            _action_step: Action step with memory query
            
        Returns:
            ActionResult with memory query result
        """
        logger.warning("Memory query not yet implemented")
        
        return ActionResult(
            success=False,
            result=None,
            error="Memory query not yet implemented",
            execution_time=0.0,
            facts_to_remember=[]
        )
    
    def _extract_result_content(self, result: Any) -> str:
        """
        Extract content from MCP tool result.
        
        Args:
            result: Raw result from MCP tool
            
        Returns:
            String representation of result
        """
        if hasattr(result, 'content'):
            if isinstance(result.content, list):
                # Extract text from list of content items
                return ', '.join([
                    item.text if hasattr(item, 'text') else str(item)
                    for item in result.content
                ])
            else:
                return str(result.content)
        else:
            return str(result)
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tool_map.keys())
    
    def tool_exists(self, tool_name: str) -> bool:
        """
        Check if a tool exists.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            Boolean indicating if tool exists
        """
        return tool_name in self.tool_map
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool information, or None if not found
        """
        if tool_name not in self.tool_map:
            return None
        
        tool = self.tool_map[tool_name]
        schema = tool.inputSchema
        
        # Extract actual parameters from nested schema
        parameters = {}
        
        # Check if there's an 'input' property with a $ref
        props = schema.get('properties', {})
        if 'input' in props:
            input_prop = props['input']
            # Follow $ref to get actual parameters
            if '$ref' in input_prop:
                ref_path = input_prop['$ref']  # e.g., "#/$defs/TwoNumberInput"
                if ref_path.startswith('#/$defs/'):
                    def_name = ref_path.split('/')[-1]
                    defs = schema.get('$defs', {})
                    if def_name in defs:
                        parameters = defs[def_name].get('properties', {})
        
        return {
            "name": tool.name,
            "description": getattr(tool, 'description', 'No description'),
            "parameters": parameters
        }
    
    def get_all_tools_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all available tools.
        
        Returns:
            List of dictionaries with tool information
        """
        tools_info = []
        for tool_name in self.tool_map.keys():
            info = self.get_tool_info(tool_name)
            if info:
                tools_info.append(info)
        return tools_info


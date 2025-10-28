"""
Action Layer - Do the Thing™

This module handles the action layer of the cognitive architecture.
It executes decisions by calling tools or generating responses.
"""
import logging
import time
import numpy as np
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from .models import ActionStep, ActionResult, YouTubeDecisionOutput, YouTubeActionResult, YouTubeContext
from .memory import MemoryLayer
from tools.tools_youtube import get_ollama_embedding, create_youtube_link
import google.generativeai as genai

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

    def execute_youtube_question(
        self,
        decision: YouTubeDecisionOutput,
        memory_layer: MemoryLayer,
        gemini_model: genai.GenerativeModel,
        original_question: str
    ) -> YouTubeActionResult:
        """
        Execute YouTube question answering based on decision plan.
        
        Args:
            decision: YouTube decision plan
            memory_layer: Memory layer with FAISS index
            gemini_model: Gemini model for answer generation
            original_question: Original user question
            
        Returns:
            YouTubeActionResult: Result of the YouTube question answering
        """
        logger.info("[ACTION] Executing YouTube question answering")
        
        try:
            # Step 1: Get embedding for search query
            logger.debug(f"Getting embedding for search query: {decision.search_query}")
            search_embedding = get_ollama_embedding(decision.search_query)
            
            # Step 2: Search FAISS index
            logger.debug(f"Searching FAISS index with top_k={decision.top_k}")
            contexts = memory_layer.search_youtube_content(
                query_embedding=search_embedding,
                top_k=decision.top_k,
                video_id_filter=None  # Search across all videos
            )
            
            if not contexts:
                return YouTubeActionResult(
                    success=False,
                    answer="No relevant content found in indexed videos.",
                    contexts=[],
                    youtube_links=[],
                    confidence=0.0,
                    reasoning="No matching content found in FAISS index"
                )
            
            # Step 3: Expand context if requested
            if decision.context_expansion:
                logger.debug("Expanding context with surrounding chunks")
                expanded_contexts = self._expand_context_with_surrounding_chunks(contexts, memory_layer)
            else:
                expanded_contexts = contexts
            
            # Step 4: Generate answer using Gemini
            logger.debug("Generating answer using Gemini")
            context_text = "\n\n".join([
                f"[Video {ctx.video_id} at {int(ctx.timestamp)}s]\n{ctx.chunk_text}"
                for ctx in expanded_contexts
            ])
            
            prompt = f"""You are a helpful assistant that answers questions about YouTube videos based on their transcripts.

Context from video transcript(s):
{context_text}

Question: {original_question}

Please provide a detailed answer based on the context above. If the context doesn't contain enough information to fully answer the question, say so."""
            
            response = gemini_model.generate_content(prompt)
            answer = response.text.strip()
            
            # Step 5: Create YouTube links for original contexts (not expanded)
            youtube_links = [
                create_youtube_link(ctx.video_id, ctx.timestamp)
                for ctx in contexts  # Use original contexts for links
            ]
            
            logger.info("[ACTION] YouTube question answered successfully")
            logger.debug(f"Answer generated with {len(expanded_contexts)} expanded contexts")
            
            return YouTubeActionResult(
                success=True,
                answer=answer,
                contexts=contexts,  # Return original contexts for display
                youtube_links=youtube_links,
                confidence=0.9,  # High confidence for successful execution
                reasoning=f"Successfully executed plan: {decision.plan}"
            )
            
        except Exception as e:
            logger.error(f"Error executing YouTube question: {e}")
            return YouTubeActionResult(
                success=False,
                answer=f"Error answering question: {str(e)}",
                contexts=[],
                youtube_links=[],
                confidence=0.0,
                reasoning=f"Execution failed: {str(e)}"
            )
    
    def _expand_context_with_surrounding_chunks(
        self, 
        top_contexts: List[YouTubeContext], 
        memory_layer: MemoryLayer
    ) -> List[YouTubeContext]:
        """
        Expand the top matching chunks with their previous and next chunks for better context.
        """
        expanded_contexts = []
        processed_chunks = set()
        
        logger.debug("🔍 Expanding context with surrounding chunks...")
        
        for ctx in top_contexts:
            # Add the original chunk if not already processed
            chunk_key = f"{ctx.video_id}_{ctx.timestamp}"
            if chunk_key not in processed_chunks:
                expanded_contexts.append(ctx)
                processed_chunks.add(chunk_key)
                logger.debug(f"✅ Added original chunk: [{ctx.timestamp:.1f}s] {ctx.chunk_text[:50]}...")
            
            # Find previous and next chunks for this video
            video_chunks = []
            for metadata in memory_layer.youtube_metadata:
                if metadata['video_id'] == ctx.video_id:
                    video_chunks.append(metadata)
            
            # Sort chunks by timestamp
            video_chunks.sort(key=lambda x: x['start_timestamp'])
            
            # Find current chunk index
            current_idx = None
            for i, chunk in enumerate(video_chunks):
                if abs(chunk['start_timestamp'] - ctx.timestamp) < 1.0:  # Within 1 second
                    current_idx = i
                    break
            
            if current_idx is not None:
                # Add previous chunk
                if current_idx > 0:
                    prev_chunk = video_chunks[current_idx - 1]
                    prev_key = f"{prev_chunk['video_id']}_{prev_chunk['start_timestamp']}"
                    if prev_key not in processed_chunks:
                        prev_context = YouTubeContext(
                            video_id=prev_chunk['video_id'],
                            chunk_text=prev_chunk['chunk_text'],
                            timestamp=prev_chunk['start_timestamp'],
                            relevance_score=0.5  # Lower relevance for context chunks
                        )
                        expanded_contexts.append(prev_context)
                        processed_chunks.add(prev_key)
                        logger.debug(f"📝 Added previous chunk: [{prev_chunk['start_timestamp']:.1f}s] {prev_chunk['chunk_text'][:50]}...")
                
                # Add next chunk
                if current_idx < len(video_chunks) - 1:
                    next_chunk = video_chunks[current_idx + 1]
                    next_key = f"{next_chunk['video_id']}_{next_chunk['start_timestamp']}"
                    if next_key not in processed_chunks:
                        next_context = YouTubeContext(
                            video_id=next_chunk['video_id'],
                            chunk_text=next_chunk['chunk_text'],
                            timestamp=next_chunk['start_timestamp'],
                            relevance_score=0.5  # Lower relevance for context chunks
                        )
                        expanded_contexts.append(next_context)
                        processed_chunks.add(next_key)
                        logger.debug(f"📝 Added next chunk: [{next_chunk['start_timestamp']:.1f}s] {next_chunk['chunk_text'][:50]}...")
        
        # Sort expanded contexts by timestamp for better readability
        expanded_contexts.sort(key=lambda x: x.timestamp)
        
        logger.info(f"🔍 Context expansion: {len(top_contexts)} → {len(expanded_contexts)} chunks")
        
        return expanded_contexts


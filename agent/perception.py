"""
Perception Layer - Understanding Input

This module handles the perception layer of the cognitive architecture.
It translates raw user input into structured information using an LLM.
"""
import logging
import json
import google.generativeai as genai
from .models import PerceptionOutput
from .prompts import PERCEPTION_PROMPT

logger = logging.getLogger(__name__)


class PerceptionLayer:
    """
    The Perception Layer extracts structured information from user queries.
    
    👁️ PERCEIVE: Raw input → Structured understanding
    """
    
    def __init__(self, model: genai.GenerativeModel, user_preferences: dict = None):
        """
        Initialize the Perception Layer.
        
        Args:
            model: Google Gemini model instance
            user_preferences: Dictionary of user preferences
        """
        self.model = model
        self.user_preferences = user_preferences or {}
        logger.info("Perception Layer initialized")
    
    def perceive(self, query: str) -> PerceptionOutput:
        """
        Analyze user query and extract structured information.
        
        Args:
            query: Raw user input string
            
        Returns:
            PerceptionOutput: Structured perception with intent, entities, facts
            
        Raises:
            ValueError: If perception fails or produces invalid output
        """
        logger.info(f"[PERCEIVE] Analyzing query: {query}")
        
        try:
            # Format user preferences for prompt
            if self.user_preferences:
                prefs_text = "\n".join([f"- {k}: {v}" for k, v in self.user_preferences.items()])
            else:
                prefs_text = "No preferences set"
            
            # Format the perception prompt with the user query and preferences
            prompt = PERCEPTION_PROMPT.format(
                user_preferences=prefs_text,
                query=query
            )
            
            # DEBUG: Print the final prompt being sent to LLM
            logger.debug("=" * 80)
            logger.debug("PERCEPTION_PROMPT (Final prompt being sent to LLM):")
            logger.debug("=" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)
            
            # Call LLM to extract structured information
            logger.debug("Calling LLM for perception...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.debug(f"Perception LLM response: {response_text}")
            
            # Parse JSON response
            # Handle markdown code blocks if present
            if response_text.startswith("```"):
                # Remove markdown code blocks
                lines = response_text.split('\n')
                # Find lines that are not ``` or ```json
                json_lines = [line for line in lines if line.strip() and not line.strip().startswith('```')]
                response_text = '\n'.join(json_lines)
            
            perception_data = json.loads(response_text)
            
            # Validate and create Pydantic model
            perception = PerceptionOutput(**perception_data)
            
            logger.info(f"[PERCEIVE] Complete - Intent: {perception.intent}, Thought: {perception.thought_type}")
            logger.debug(f"Extracted facts: {perception.extracted_facts}")
            
            return perception
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse perception JSON: {e}")
            logger.error(f"Raw response: {response_text}")
            
            # Fallback: create a basic perception output
            logger.warning("Using fallback perception")
            return PerceptionOutput(
                intent="unknown",
                entities={},
                thought_type="Analysis",
                extracted_facts=[f"User query: {query}"],
                requires_tools=True,
                confidence=0.5
            )
            
        except Exception as e:
            logger.error(f"Error in perception layer: {e}")
            raise ValueError(f"Perception failed: {str(e)}")
    
    def extract_facts_from_result(self, result: str, operation: str) -> list[str]:
        """
        Extract facts from tool execution results.
        
        Args:
            result: Result from tool execution
            operation: Description of the operation performed
            
        Returns:
            List of facts to store in memory
        """
        facts = [
            f"Performed operation: {operation}",
            f"Result obtained: {result}"
        ]
        return facts


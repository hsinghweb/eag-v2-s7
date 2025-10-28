"""
Perception Layer - Understanding Input

This module handles the perception layer of the cognitive architecture.
It translates raw user input into structured information using an LLM.
"""
import logging
import json
import google.generativeai as genai
from .models import PerceptionOutput, YouTubePerceptionOutput
from .prompts import PERCEPTION_PROMPT, YOUTUBE_PERCEPTION_PROMPT

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

    def perceive_youtube_question(self, question: str, indexed_videos: list = None) -> YouTubePerceptionOutput:
        """
        Analyze YouTube question and extract structured information.
        
        Args:
            question: User's question about YouTube content
            indexed_videos: List of available indexed video IDs
            
        Returns:
            YouTubePerceptionOutput: Structured perception with question analysis
        """
        logger.info(f"[PERCEIVE] Analyzing YouTube question: {question}")
        
        try:
            # Format indexed videos for context
            if indexed_videos:
                videos_text = "\n".join([f"- {video_id}" for video_id in indexed_videos])
            else:
                videos_text = "No videos indexed yet"
            
            # Format the YouTube perception prompt
            prompt = YOUTUBE_PERCEPTION_PROMPT.format(
                question=question,
                indexed_videos=videos_text
            )
            
            logger.debug("=" * 80)
            logger.debug("YOUTUBE_PERCEPTION_PROMPT:")
            logger.debug("=" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)
            
            # Call LLM for perception
            logger.debug("Calling LLM for YouTube question perception...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.debug(f"YouTube perception LLM response: {response_text}")
            
            # Parse JSON response
            if response_text.startswith("```"):
                lines = response_text.split('\n')
                json_lines = [line for line in lines if line.strip() and not line.strip().startswith('```')]
                response_text = '\n'.join(json_lines)
            
            perception_data = json.loads(response_text)
            
            # Validate and create Pydantic model
            perception = YouTubePerceptionOutput(**perception_data)
            
            logger.info(f"[PERCEIVE] YouTube question analyzed - Intent: {perception.intent}, Type: {perception.question_type}")
            logger.debug(f"Extracted concepts: {perception.extracted_concepts}")
            
            return perception
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse YouTube perception JSON: {e}")
            logger.error(f"Raw response: {response_text}")
            
            # Return fallback perception
            return YouTubePerceptionOutput(
                intent="answer_question",
                question_type="general",
                extracted_concepts=[question],
                context_needed="general",
                search_strategy="semantic_search",
                confidence=0.5,
                reasoning=f"Fallback perception due to JSON parsing error: {e}"
            )
            
        except Exception as e:
            logger.error(f"Error in YouTube perception: {e}")
            raise ValueError(f"Perception failed: {e}")


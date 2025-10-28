"""
Decision-Making Layer - Planning Next Step

This module handles the decision-making layer of the cognitive architecture.
It decides what actions to take based on perception and memory.
"""
import logging
import json
import google.generativeai as genai
from typing import List, Dict
from .models import (
    PerceptionOutput,
    MemoryRetrievalResult,
    DecisionOutput,
    ActionStep,
    YouTubePerceptionOutput,
    YouTubeDecisionOutput
)
from .prompts import DECISION_PROMPT, YOUTUBE_DECISION_PROMPT

logger = logging.getLogger(__name__)


class DecisionLayer:
    """
    The Decision Layer plans what actions to take.
    
    🧭 DECIDE: Perception + Memory → Action Plan
    
    This is where the agent starts thinking - reasoning about options,
    considering memory, and picking an action plan.
    """
    
    def __init__(self, model: genai.GenerativeModel, user_preferences: dict = None):
        """
        Initialize the Decision Layer.
        
        Args:
            model: Google Gemini model instance
            user_preferences: Dictionary of user preferences
        """
        self.model = model
        self.user_preferences = user_preferences or {}
        logger.info("[DECISION] Decision Layer initialized")
    
    def decide(
        self, 
        perception: PerceptionOutput,
        memory: MemoryRetrievalResult,
        available_tools: List[Dict],
        previous_actions: List[ActionStep] = None
    ) -> DecisionOutput:
        """
        Create an action plan based on perception and memory.
        
        Args:
            perception: Output from the perception layer
            memory: Retrieved memory information
            available_tools: List of tool schemas (name, description, parameters)
            previous_actions: Previous actions taken (for iteration)
            
        Returns:
            DecisionOutput: Action plan with reasoning
            
        Raises:
            ValueError: If decision-making fails
        """
        logger.info("[DECISION] Creating action plan...")
        
        try:
            # Format the decision prompt
            perception_summary = {
                "intent": perception.intent,
                "entities": perception.entities,
                "thought_type": perception.thought_type,
                "facts": perception.extracted_facts,
                "requires_tools": perception.requires_tools
            }
            
            memory_summary = {
                "relevant_facts": [f.content for f in memory.relevant_facts],
                "context": memory.context,
                "summary": memory.summary
            }
            
            # Format tool schemas for the prompt
            tools_text = []
            for tool in available_tools[:50]:  # Limit to first 50 tools to avoid token overflow
                params_dict = tool.get('parameters', {})
                if params_dict:
                    # Format parameters with types
                    params_list = []
                    for param_name, param_info in params_dict.items():
                        param_type = param_info.get('type', 'any')
                        params_list.append(f"{param_name}: {param_type}")
                    params_str = ", ".join(params_list)
                else:
                    params_str = ""
                tools_text.append(f"- {tool['name']}({params_str}): {tool.get('description', '')}")
            tools_list = "\n".join(tools_text) if tools_text else "No tools available"
            
            # Format user preferences for prompt
            if self.user_preferences:
                prefs_text = "\n".join([f"- {k}: {v}" for k, v in self.user_preferences.items()])
            else:
                prefs_text = "No preferences set"
            
            prompt = DECISION_PROMPT.format(
                user_preferences=prefs_text,
                perception=json.dumps(perception_summary, indent=2),
                memory=json.dumps(memory_summary, indent=2),
                available_tools=tools_list
            )
            
            # Add previous actions context if available
            if previous_actions:
                actions_summary = [
                    f"Step {a.step_number}: {a.description} (completed)"
                    for a in previous_actions
                ]
                prompt += "\n\nPrevious actions completed:\n" + "\n".join(actions_summary)
                prompt += "\n\nContinue from where you left off."
            
            # DEBUG: Print the final prompt being sent to LLM
            logger.debug("=" * 80)
            logger.debug("DECISION_PROMPT (Final prompt being sent to LLM):")
            logger.debug("=" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)
            
            # Call LLM to create action plan
            logger.debug("Calling LLM for decision-making...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.debug(f"Decision LLM response: {response_text}")
            
            # Parse JSON response
            # Handle markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split('\n')
                json_lines = [line for line in lines if line.strip() and not line.strip().startswith('```')]
                response_text = '\n'.join(json_lines)
            
            decision_data = json.loads(response_text)
            
            # Validate and create Pydantic model
            decision = DecisionOutput(**decision_data)
            
            logger.info(f"[DECISION] Complete - {len(decision.action_plan)} steps planned")
            logger.debug(f"Reasoning: {decision.reasoning}")
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse decision JSON: {e}")
            logger.error(f"Raw response: {response_text}")
            
            # Fallback: create a simple response action
            logger.warning("Using fallback decision - direct response")
            return DecisionOutput(
                action_plan=[
                    ActionStep(
                        step_number=1,
                        action_type="response",
                        description="Provide direct response to user",
                        tool_name=None,
                        parameters={},
                        reasoning="Fallback due to decision parsing error"
                    )
                ],
                reasoning="Unable to create detailed plan, providing direct response",
                expected_outcome="User receives acknowledgment",
                confidence=0.5,
                should_continue=False
            )
            
        except Exception as e:
            logger.error(f"Error in decision layer: {e}")
            raise ValueError(f"Decision-making failed: {str(e)}")
    
    def should_continue_iteration(self, decision: DecisionOutput) -> bool:
        """
        Determine if agent should continue iterating.
        
        Args:
            decision: Current decision output
            
        Returns:
            Boolean indicating whether to continue
        """
        return decision.should_continue
    
    def get_next_action(self, decision: DecisionOutput) -> ActionStep:
        """
        Get the next action to execute from the plan.
        
        Args:
            decision: Decision output with action plan
            
        Returns:
            Next ActionStep to execute
        """
        if not decision.action_plan:
            raise ValueError("No actions in plan")
        
        # Return the first action (we'll track completed actions separately)
        return decision.action_plan[0]
    
    def create_simple_response_decision(self, message: str) -> DecisionOutput:
        """
        Create a simple decision that just responds to the user.
        
        Args:
            message: Message to respond with
            
        Returns:
            DecisionOutput with single response action
        """
        return DecisionOutput(
            action_plan=[
                ActionStep(
                    step_number=1,
                    action_type="response",
                    description=f"Respond: {message}",
                    tool_name=None,
                    parameters={"message": message},
                    reasoning="Direct response"
                )
            ],
            reasoning="Simple response decision",
            expected_outcome=message,
            confidence=1.0,
            should_continue=False
        )

    def decide_youtube_question(
        self,
        perception: YouTubePerceptionOutput,
        indexed_videos: List[str] = None
    ) -> YouTubeDecisionOutput:
        """
        Plan execution for YouTube question answering.
        
        Args:
            perception: YouTube perception analysis
            indexed_videos: List of available indexed video IDs
            
        Returns:
            YouTubeDecisionOutput: Execution plan for answering the question
        """
        logger.info("[DECISION] Planning YouTube question execution")
        
        try:
            # Format indexed videos for context
            if indexed_videos:
                videos_text = "\n".join([f"- {video_id}" for video_id in indexed_videos])
            else:
                videos_text = "No videos indexed yet"
            
            # Format the YouTube decision prompt
            prompt = YOUTUBE_DECISION_PROMPT.format(
                intent=perception.intent,
                question_type=perception.question_type,
                extracted_concepts=", ".join(perception.extracted_concepts),
                context_needed=perception.context_needed,
                search_strategy=perception.search_strategy,
                confidence=perception.confidence,
                indexed_videos=videos_text
            )
            
            logger.debug("=" * 80)
            logger.debug("YOUTUBE_DECISION_PROMPT:")
            logger.debug("=" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)
            
            # Call LLM for decision planning
            logger.debug("Calling LLM for YouTube decision planning...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.debug(f"YouTube decision LLM response: {response_text}")
            
            # Parse JSON response
            if response_text.startswith("```"):
                lines = response_text.split('\n')
                json_lines = [line for line in lines if line.strip() and not line.strip().startswith('```')]
                response_text = '\n'.join(json_lines)
            
            decision_data = json.loads(response_text)
            
            # Validate and create Pydantic model
            decision = YouTubeDecisionOutput(**decision_data)
            
            logger.info(f"[DECISION] YouTube execution plan created - Plan: {decision.plan}")
            logger.debug(f"Execution steps: {decision.steps}")
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse YouTube decision JSON: {e}")
            logger.error(f"Raw response: {response_text}")
            
            # Return fallback decision
            return YouTubeDecisionOutput(
                plan="Answer question using semantic search",
                steps=[
                    "Search FAISS index with question",
                    "Retrieve top 3 relevant chunks",
                    "Expand context with surrounding chunks",
                    "Generate answer using Gemini"
                ],
                search_query=perception.extracted_concepts[0] if perception.extracted_concepts else "general question",
                top_k=3,
                context_expansion=True,
                reasoning=f"Fallback decision due to JSON parsing error: {e}"
            )
            
        except Exception as e:
            logger.error(f"Error in YouTube decision planning: {e}")
            raise ValueError(f"Decision planning failed: {e}")


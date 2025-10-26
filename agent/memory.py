"""
Memory Layer - Remembering Stuff

This module handles the memory layer of the cognitive architecture.
It stores and retrieves facts, user preferences, and context information.
"""
import logging
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from .models import (
    MemoryState, 
    MemoryFact, 
    MemoryQuery, 
    MemoryRetrievalResult
)

logger = logging.getLogger(__name__)

# Memory file rotation settings
MAX_MEMORY_SIZE_MB = 5  # Maximum size before rotation
MAX_ROTATED_FILES = 10  # Keep only the last N rotated files


class MemoryLayer:
    """
    The Memory Layer stores facts and context for future reasoning.
    
    🧠 REMEMBER: Store observations → Retrieve relevant context
    
    This mimics human memory: remembering facts and retrieving relevant info later.
    """
    
    def __init__(self, memory_file: Optional[str] = None, load_existing: bool = False):
        """
        Initialize the Memory Layer.
        
        Args:
            memory_file: Optional path to JSON file for persistent memory
            load_existing: If True, load existing memory file; otherwise start fresh
        """
        self.memory_state = MemoryState()
        self.memory_file = memory_file
        
        # Load existing memory only if explicitly requested and file exists
        if load_existing and memory_file and Path(memory_file).exists():
            self.load_memory()
        
        logger.info("[MEMORY] Memory Layer initialized")
    
    def store_fact(self, content: str, source: str = "user", relevance_score: float = 1.0):
        """
        Store a single fact in memory.
        
        Args:
            content: The fact to store
            source: Source of the fact (user, system, tool)
            relevance_score: Relevance score (0.0 to 1.0)
        """
        fact = MemoryFact(
            content=content,
            timestamp=datetime.now().isoformat(),
            source=source,
            relevance_score=relevance_score
        )
        self.memory_state.facts.append(fact)
        logger.info(f"[MEMORY] Stored fact: {content[:50]}...")
    
    def store_facts(self, facts: List[str], source: str = "perception"):
        """
        Store multiple facts in memory.
        
        Args:
            facts: List of facts to store
            source: Source of the facts
        """
        for fact in facts:
            self.store_fact(fact, source=source)
        logger.info(f"[MEMORY] Stored {len(facts)} facts from {source}")
    
    def update_context(self, key: str, value: Any):
        """
        Update context information.
        
        Args:
            key: Context key
            value: Context value
        """
        self.memory_state.context[key] = value
        logger.debug(f"Updated context: {key} = {value}")
    
    def update_preference(self, key: str, value: Any):
        """
        Update user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.memory_state.user_preferences[key] = value
        logger.info(f"Updated preference: {key} = {value}")
    
    def retrieve_relevant_facts(self, query: MemoryQuery) -> MemoryRetrievalResult:
        """
        Retrieve facts relevant to a query.
        
        Currently uses simple keyword matching. In Session 7, this will be
        replaced with vector database semantic search.
        
        Args:
            query: Memory query with search parameters
            
        Returns:
            MemoryRetrievalResult with relevant facts and context
        """
        logger.info(f"[MEMORY] Retrieving memories for: {query.query}")
        
        # Simple keyword-based retrieval (will be upgraded to vector search later)
        query_words = set(query.query.lower().split())
        relevant_facts = []
        
        for fact in self.memory_state.facts:
            fact_words = set(fact.content.lower().split())
            # Calculate simple overlap score
            overlap = len(query_words.intersection(fact_words))
            
            if overlap > 0:
                # Update relevance score based on overlap
                score = overlap / len(query_words)
                if score >= query.min_relevance:
                    relevant_facts.append(fact)
        
        # Sort by relevance score and limit results
        relevant_facts.sort(key=lambda f: f.relevance_score, reverse=True)
        relevant_facts = relevant_facts[:query.max_results]
        
        # Create summary
        summary = f"Retrieved {len(relevant_facts)} relevant facts"
        if relevant_facts:
            summary += f": {', '.join([f.content[:30] + '...' for f in relevant_facts[:3]])}"
        
        result = MemoryRetrievalResult(
            relevant_facts=relevant_facts,
            context=self.memory_state.context.copy(),
            summary=summary
        )
        
        logger.info(f"[MEMORY] Retrieved {len(relevant_facts)} relevant facts")
        return result
    
    def get_all_facts(self) -> List[MemoryFact]:
        """
        Get all stored facts.
        
        Returns:
            List of all memory facts
        """
        return self.memory_state.facts.copy()
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get current context.
        
        Returns:
            Dictionary of context information
        """
        return self.memory_state.context.copy()
    
    def get_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Returns:
            Dictionary of user preferences
        """
        return self.memory_state.user_preferences.copy()
    
    def update_summary(self, summary: str):
        """
        Update conversation summary.
        
        Args:
            summary: New conversation summary
        """
        self.memory_state.conversation_summary = summary
        logger.info("Updated conversation summary")
    
    def clear_memory(self):
        """Clear all memory (useful for testing or reset)."""
        self.memory_state = MemoryState()
        logger.warning("[MEMORY] Memory cleared")
    
    def _rotate_memory_file(self):
        """
        Rotate memory file if it exceeds size limit.
        Renames current file with timestamp and creates a new one.
        """
        try:
            # Check if file exists and its size
            if not os.path.exists(self.memory_file):
                return
            
            file_size_mb = os.path.getsize(self.memory_file) / (1024 * 1024)
            
            if file_size_mb < MAX_MEMORY_SIZE_MB:
                return  # No rotation needed
            
            # Create rotated filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_path = Path(self.memory_file)
            rotated_file = base_path.parent / f"{base_path.stem}_{timestamp}{base_path.suffix}"
            
            # Rename current file
            os.rename(self.memory_file, rotated_file)
            logger.info(f"[MEMORY] Rotated memory file to {rotated_file.name} (size: {file_size_mb:.2f}MB)")
            
            # Clean up old rotated files (keep only last N)
            self._cleanup_rotated_files()
            
        except Exception as e:
            logger.error(f"Failed to rotate memory file: {e}")
    
    def _cleanup_rotated_files(self):
        """
        Keep only the last MAX_ROTATED_FILES rotated memory files.
        Deletes older ones.
        """
        try:
            base_path = Path(self.memory_file)
            parent_dir = base_path.parent
            stem = base_path.stem
            suffix = base_path.suffix
            
            # Find all rotated files matching pattern
            pattern = f"{stem}_*{suffix}"
            rotated_files = sorted(parent_dir.glob(pattern), key=os.path.getmtime, reverse=True)
            
            # Delete files beyond the limit
            for old_file in rotated_files[MAX_ROTATED_FILES:]:
                os.remove(old_file)
                logger.info(f"[MEMORY] Deleted old rotated file: {old_file.name}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup rotated files: {e}")
    
    def save_memory(self):
        """
        Save memory to JSON file for persistence.
        Automatically rotates the file if it exceeds size limit.
        """
        if not self.memory_file:
            logger.warning("No memory file specified, cannot save")
            return
        
        try:
            # Check if rotation is needed before saving
            self._rotate_memory_file()
            
            # Save memory to file
            memory_dict = self.memory_state.model_dump()
            with open(self.memory_file, 'w') as f:
                json.dump(memory_dict, f, indent=2)
            
            # Log file size
            file_size_kb = os.path.getsize(self.memory_file) / 1024
            logger.info(f"[MEMORY] Memory saved to {self.memory_file} (size: {file_size_kb:.1f}KB)")
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def load_memory(self):
        """
        Load memory from JSON file.
        """
        if not self.memory_file:
            logger.warning("No memory file specified, cannot load")
            return
        
        try:
            with open(self.memory_file, 'r') as f:
                memory_dict = json.load(f)
            self.memory_state = MemoryState(**memory_dict)
            logger.info(f"[MEMORY] Memory loaded from {self.memory_file}")
            logger.info(f"Loaded {len(self.memory_state.facts)} facts")
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
    
    def get_summary(self) -> str:
        """
        Get a summary of current memory state.
        
        Returns:
            String summary of memory
        """
        summary = "Memory State:\n"
        summary += f"- Facts: {len(self.memory_state.facts)}\n"
        summary += f"- Preferences: {len(self.memory_state.user_preferences)}\n"
        summary += f"- Context items: {len(self.memory_state.context)}\n"
        
        if self.memory_state.conversation_summary:
            summary += f"- Summary: {self.memory_state.conversation_summary}\n"
        
        return summary


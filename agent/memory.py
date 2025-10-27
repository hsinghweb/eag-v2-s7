"""
Memory Layer - YouTube RAG Memory with FAISS

This module handles the memory layer with FAISS vector store for YouTube transcripts.
Stores and retrieves YouTube video chunks using semantic search.
"""
import logging
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import numpy as np
import faiss
import pickle

from .models import (
    MemoryState, 
    MemoryFact, 
    MemoryQuery, 
    MemoryRetrievalResult,
    YouTubeTranscriptChunk,
    YouTubeContext
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
        Initialize the Memory Layer with FAISS vector store for YouTube.
        
        Args:
            memory_file: Optional path to JSON file for persistent memory
            load_existing: If True, load existing memory file; otherwise start fresh
        """
        self.memory_state = MemoryState()
        self.memory_file = memory_file
        
        # Initialize YouTube FAISS vector store
        self.youtube_index: Optional[faiss.Index] = None
        self.youtube_metadata: List[Dict[str, Any]] = []
        self.youtube_dimension = 768  # nomic-embed-text dimension
        
        # Paths for FAISS persistence
        if memory_file:
            base_path = Path(memory_file).parent
            self.youtube_index_file = base_path / "youtube_faiss.index"
            self.youtube_metadata_file = base_path / "youtube_metadata.pkl"
        else:
            self.youtube_index_file = None
            self.youtube_metadata_file = None
        
        # Load existing memory only if explicitly requested and file exists
        if load_existing and memory_file and Path(memory_file).exists():
            self.load_memory()
            self.load_youtube_index()
        
        logger.info("[MEMORY] Memory Layer initialized with YouTube FAISS")
        logger.info(f"[MEMORY] YouTube vector store ready (dimension: {self.youtube_dimension})")
    
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
        Also saves YouTube FAISS index.
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
            
            # Save YouTube index
            self.save_youtube_index()
            
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
        
        # Add YouTube index stats
        if self.youtube_index:
            summary += f"- YouTube chunks indexed: {self.youtube_index.ntotal}\n"
        
        return summary
    
    # ============================================================================
    # YOUTUBE FAISS VECTOR STORE METHODS
    # ============================================================================
    
    def add_youtube_chunks(
        self, 
        chunks: List[YouTubeTranscriptChunk],
        embeddings: np.ndarray
    ) -> int:
        """
        Add YouTube transcript chunks to FAISS vector store.
        
        Args:
            chunks: List of YouTube transcript chunks with metadata
            embeddings: Numpy array of embeddings (shape: [n_chunks, dimension])
            
        Returns:
            Number of chunks added
        """
        if embeddings.shape[0] != len(chunks):
            raise ValueError("Number of embeddings must match number of chunks")
        
        if embeddings.shape[1] != self.youtube_dimension:
            raise ValueError(f"Embedding dimension mismatch: expected {self.youtube_dimension}, got {embeddings.shape[1]}")
        
        # Initialize index if not exists
        if self.youtube_index is None:
            self.youtube_index = faiss.IndexFlatL2(self.youtube_dimension)
            logger.info(f"[MEMORY] Created new FAISS index with dimension {self.youtube_dimension}")
        
        # Add embeddings to FAISS
        self.youtube_index.add(embeddings.astype(np.float32))
        
        # Store metadata
        for chunk in chunks:
            self.youtube_metadata.append({
                'video_id': chunk.video_id,
                'chunk_text': chunk.chunk_text,
                'start_timestamp': chunk.start_timestamp,
                'end_timestamp': chunk.end_timestamp,
                'chunk_index': chunk.chunk_index
            })
        
        logger.info(f"[MEMORY] Added {len(chunks)} YouTube chunks to vector store")
        logger.info(f"[MEMORY] Total chunks in index: {self.youtube_index.ntotal}")
        
        return len(chunks)
    
    def search_youtube_content(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
        video_id_filter: Optional[str] = None
    ) -> List[YouTubeContext]:
        """
        Search YouTube content using semantic similarity.
        
        Args:
            query_embedding: Query embedding vector (shape: [dimension])
            top_k: Number of results to return
            video_id_filter: Optional video ID to filter results
            
        Returns:
            List of YouTubeContext objects with relevant chunks
        """
        if self.youtube_index is None or self.youtube_index.ntotal == 0:
            logger.warning("[MEMORY] No YouTube content indexed yet")
            return []
        
        # Reshape query for FAISS
        query_vector = query_embedding.reshape(1, -1).astype(np.float32)
        
        # Search in FAISS - get more results if filtering by video_id
        search_k = top_k * 3 if video_id_filter else top_k
        distances, indices = self.youtube_index.search(query_vector, min(search_k, self.youtube_index.ntotal))
        
        # Retrieve metadata and create contexts
        contexts = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.youtube_metadata):
                continue
            
            metadata = self.youtube_metadata[idx]
            
            # Apply video ID filter if specified
            if video_id_filter and metadata['video_id'] != video_id_filter:
                continue
            
            # Convert L2 distance to similarity score (inverse)
            # Smaller distance = higher similarity
            similarity_score = 1.0 / (1.0 + float(dist))
            
            context = YouTubeContext(
                video_id=metadata['video_id'],
                chunk_text=metadata['chunk_text'],
                timestamp=metadata['start_timestamp'],
                relevance_score=similarity_score
            )
            contexts.append(context)
            
            # Stop if we have enough results
            if len(contexts) >= top_k:
                break
        
        logger.info(f"[MEMORY] Found {len(contexts)} relevant YouTube chunks")
        return contexts
    
    def save_youtube_index(self):
        """Save FAISS index and metadata to disk."""
        if self.youtube_index is None or self.youtube_index_file is None:
            logger.debug("[MEMORY] No YouTube index to save")
            return
        
        try:
            # Ensure directory exists
            os.makedirs(self.youtube_index_file.parent, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.youtube_index, str(self.youtube_index_file))
            
            # Save metadata
            with open(self.youtube_metadata_file, 'wb') as f:
                pickle.dump(self.youtube_metadata, f)
            
            logger.info(f"[MEMORY] Saved YouTube index: {self.youtube_index.ntotal} chunks")
            logger.info(f"[MEMORY] Index file: {self.youtube_index_file}")
            
        except Exception as e:
            logger.error(f"[MEMORY] Failed to save YouTube index: {e}")
    
    def load_youtube_index(self):
        """Load FAISS index and metadata from disk."""
        if self.youtube_index_file is None or not Path(self.youtube_index_file).exists():
            logger.info("[MEMORY] No existing YouTube index found")
            return
        
        try:
            # Load FAISS index
            self.youtube_index = faiss.read_index(str(self.youtube_index_file))
            
            # Load metadata
            with open(self.youtube_metadata_file, 'rb') as f:
                self.youtube_metadata = pickle.load(f)
            
            logger.info(f"[MEMORY] Loaded YouTube index: {self.youtube_index.ntotal} chunks")
            
        except Exception as e:
            logger.error(f"[MEMORY] Failed to load YouTube index: {e}")
            # Initialize empty index on failure
            self.youtube_index = None
            self.youtube_metadata = []
    
    def get_youtube_stats(self) -> Dict[str, Any]:
        """
        Get statistics about indexed YouTube content.
        
        Returns:
            Dictionary with stats
        """
        if self.youtube_index is None:
            return {
                'total_chunks': 0,
                'unique_videos': 0,
                'video_ids': []
            }
        
        # Count unique videos
        video_ids = set(meta['video_id'] for meta in self.youtube_metadata)
        
        return {
            'total_chunks': self.youtube_index.ntotal,
            'unique_videos': len(video_ids),
            'video_ids': list(video_ids)
        }


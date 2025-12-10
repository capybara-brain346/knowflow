import os
from typing import List, Dict, Any, Optional
from mem0 import Memory

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger

os.environ["OPENAI_API_KEY"] = "NONE"


class MemoryService:
    def __init__(self):
        try:
            config = {
                "graph_store": {
                    "provider": "neo4j",
                    "config": {
                        "url": settings.NEO4J_URI,
                        "username": settings.NEO4J_USER,
                        "password": settings.NEO4J_PASSWORD,
                        "database": "neo4j",
                    },
                },
                "llm": {
                    "provider": "gemini",
                    "config": {
                        "model": "gemini-2.5-flash-lite",
                        "temperature": 0.2,
                        "max_tokens": 2000,
                        "top_p": 0.7,
                    },
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "all-MiniLM-L6-v2",
                        "model_kwargs": {"device": "cpu"},
                    },
                },
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": "mem0_memories",
                        "path": "./chroma_mem0_data",
                    },
                },
            }

            self.memory = Memory.from_config(config_dict=config)
            logger.info("MemoryService initialized successfully with Mem0")
        except Exception as e:
            logger.error(
                f"Failed to initialize MemoryService: {str(e)}",
                exc_info=True,
            )
            raise ExternalServiceException(
                message="Failed to initialize memory service",
                service_name="MemoryService",
                extra={"error": str(e)},
            )

    def add_document_memory(
        self,
        doc_id: str,
        content: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            conversation = [
                {"role": "user", "content": f"Document content: {content}"},
                {
                    "role": "assistant",
                    "content": "Understood. I've processed and stored the document content.",
                },
            ]

            result = self.memory.add(
                conversation,
                user_id=user_id,
                metadata={"doc_id": doc_id, "type": "document", **(metadata or {})},
            )

            logger.info(f"Successfully added document memory for doc_id: {doc_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding document memory: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to add document memory",
                service_name="MemoryService",
                extra={"error": str(e), "doc_id": doc_id},
            )

    def add_conversation_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            result = self.memory.add(
                messages,
                user_id=user_id,
                metadata={
                    "session_id": session_id,
                    "type": "conversation",
                    **(metadata or {}),
                },
            )

            logger.info(f"Successfully added conversation memory for user: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding conversation memory: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to add conversation memory",
                service_name="MemoryService",
                extra={"error": str(e), "user_id": user_id},
            )

    def search_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        rerank: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            results = self.memory.search(
                query, user_id=user_id, limit=limit, rerank=rerank, filters=filters
            )

            logger.info(f"Found {len(results.get('results', []))} memories for query")
            return results
        except Exception as e:
            logger.error(f"Error searching memory: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to search memory",
                service_name="MemoryService",
                extra={"error": str(e), "query": query},
            )

    def get_all_memories(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            memories = self.memory.get_all(user_id=user_id, limit=limit)
            logger.info(f"Retrieved {len(memories)} memories for user: {user_id}")
            return memories
        except Exception as e:
            logger.error(f"Error getting all memories: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to get all memories",
                service_name="MemoryService",
                extra={"error": str(e), "user_id": user_id},
            )

    def delete_memory(self, memory_id: str, user_id: str) -> Dict[str, Any]:
        try:
            result = self.memory.delete(memory_id=memory_id, user_id=user_id)
            logger.info(f"Deleted memory: {memory_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to delete memory",
                service_name="MemoryService",
                extra={"error": str(e), "memory_id": memory_id},
            )

    def delete_all_memories(self, user_id: str) -> Dict[str, Any]:
        try:
            result = self.memory.delete_all(user_id=user_id)
            logger.info(f"Deleted all memories for user: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting all memories: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to delete all memories",
                service_name="MemoryService",
                extra={"error": str(e), "user_id": user_id},
            )

    def update_memory(
        self,
        memory_id: str,
        data: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            result = self.memory.update(
                memory_id=memory_id, data=data, user_id=user_id, metadata=metadata
            )
            logger.info(f"Updated memory: {memory_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to update memory",
                service_name="MemoryService",
                extra={"error": str(e), "memory_id": memory_id},
            )

    def get_memory_history(self, memory_id: str, user_id: str) -> List[Dict[str, Any]]:
        try:
            history = self.memory.history(memory_id=memory_id, user_id=user_id)
            logger.info(f"Retrieved history for memory: {memory_id}")
            return history
        except Exception as e:
            logger.error(f"Error getting memory history: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to get memory history",
                service_name="MemoryService",
                extra={"error": str(e), "memory_id": memory_id},
            )

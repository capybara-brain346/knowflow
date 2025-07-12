from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.request import FollowUpChatRequest
from src.models.response import FollowUpChatResponse
from src.models.database import ChatSession
from datetime import datetime, timezone
from neo4j import GraphDatabase

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.services.graph_service import GraphService
from src.services.auth_service import AuthService
from fastapi import status
from src.models.database import Document
from src.models.database import DocumentChunk
from src.models.database import DocumentStatus


class ChatService:
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.auth_service = AuthService(self.db)
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )

            self.vector_store = PGVector(
                connection=settings.DATABASE_URL,
                embeddings=self.embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
            )

            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL_NAME
            )

            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            self.graph_service = GraphService()

            logger.info("ChatService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatService: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to initialize chat service",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    def _get_vector_results(self, query: str, current_user_id: int) -> List[str]:
        try:
            logger.debug(f"Starting vector search for user_id: {current_user_id}")

            user_docs = (
                self.db.query(Document)
                .filter(
                    Document.user_id == current_user_id,
                    Document.status == DocumentStatus.INDEXED,
                )
                .all()
            )

            logger.debug(f"Found {len(user_docs)} indexed documents for user")

            if not user_docs:
                logger.info("No indexed documents found for user")
                return []

            doc_chunks = (
                self.db.query(DocumentChunk)
                .join(Document, Document.id == DocumentChunk.document_id)
                .filter(Document.user_id == current_user_id)
                .all()
            )

            logger.debug(f"Found {len(doc_chunks)} chunks for user's documents")

            if not doc_chunks:
                logger.info("No document chunks found")
                return []

            docs = self.vector_store.similarity_search(query, k=settings.TOP_K_RESULTS)

            logger.debug(f"Vector search returned {len(docs)} results")

            results = []
            for doc in docs:
                try:
                    metadata = doc.metadata
                    logger.debug(f"Processing result metadata: {metadata}")

                    chunk_doc = (
                        self.db.query(Document)
                        .join(DocumentChunk, Document.id == DocumentChunk.document_id)
                        .filter(
                            Document.user_id == current_user_id,
                            DocumentChunk.document_id == metadata.get("document_id"),
                        )
                        .first()
                    )

                    if chunk_doc:
                        results.append(doc.page_content)
                        logger.debug(f"Added result from document {chunk_doc.doc_id}")
                except Exception as e:
                    logger.warning(f"Error processing vector search result: {str(e)}")
                    continue

            logger.info(f"Found {len(results)} authorized results in vector store")
            return results

        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to search vector store",
                service_name="VectorStore",
                extra={"error": str(e)},
            )

    def _get_graph_results(self, query: str) -> List[Dict[str, Any]]:
        try:
            logger.debug("Querying graph database")
            results = self.graph_service.query_graph(query)
            logger.info(f"Found {len(results)} relevant results in graph")
            return results
        except Exception as e:
            logger.error(f"Error querying graph: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to query graph",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def _merge_results(
        self, vector_results: List[str], graph_results: List[Dict[str, Any]]
    ) -> str:
        try:
            graph_texts = []
            for result in graph_results:
                text = f"Type: {result.get('type', 'Unknown')}\n"
                text += f"Properties: {', '.join([f'{k}: {v}' for k, v in result.get('properties', {}).items()])}\n"
                if "relationships" in result:
                    text += f"Relationships: {', '.join([r['type'] for r in result['relationships']])}"
                graph_texts.append(text)

            all_texts = vector_results[:3] + graph_texts[:3]
            return "\n\n".join(all_texts)
        except Exception as e:
            logger.error(f"Error merging results: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to merge results",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    async def process_query(
        self, query: str, session_id: str, current_user_id: int
    ) -> Dict[str, Any]:
        try:
            if session_id:
                session = (
                    self.db.query(ChatSession)
                    .filter(
                        ChatSession.id == session_id,
                        ChatSession.user_id == current_user_id,
                    )
                    .first()
                )
                if not session:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to this chat session",
                    )

            vector_results = self._get_vector_results(query, current_user_id)
            graph_results = self._get_graph_results(query)

            context = self._merge_results(vector_results, graph_results)

            logger.debug("Building prompt with merged context")
            system_prompt = f"""You are a helpful AI assistant. Answer the user's question based on the following context.
                The context includes both semantic search results and structured knowledge graph information.
                If you cannot find the answer in the context, say so.

                Context:
                {context}"""
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query),
            ]

            response = self.llm.invoke(messages)
            logger.info("Successfully generated response")

            return {
                "message": response.content,
                "context_used": {
                    "context": context,
                    "vector_results": vector_results,
                    "graph_results": graph_results,
                },
                "session_id": session_id if session_id else None,
            }
        except Exception as e:
            logger.error(f"Error processing chat query: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to process chat query",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    async def follow_up_chat(
        self, session_id: str, request: FollowUpChatRequest, current_user_id: int
    ) -> FollowUpChatResponse:
        session = self._get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session",
            )

        context_nodes = await self._get_context_nodes(
            request.referenced_node_ids or session.recent_node_ids,
            request.context_window,
        )

        self._update_session(session, context_nodes)

        response = await self._generate_response_with_context(
            request.message, context_nodes, session.memory_context
        )

        return FollowUpChatResponse(
            response=response["text"],
            context_nodes=context_nodes,
            memory_context=session.memory_context,
            referenced_entities=response["referenced_entities"],
        )

    def _get_session(self, session_id: str) -> ChatSession:
        return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()

    async def _get_context_nodes(
        self, node_ids: List[str], context_window: int
    ) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            query = """
            MATCH path = (start)-[*..{context_window}]-(related)
            WHERE start.id IN $node_ids
            RETURN DISTINCT related
            """
            result = session.run(
                query, node_ids=node_ids, context_window=context_window
            )
            return [dict(record["related"]) for record in result]

    def _update_session(
        self, session: ChatSession, context_nodes: List[Dict[str, Any]]
    ) -> None:
        new_node_ids = [node["id"] for node in context_nodes if "id" in node]

        session.recent_node_ids = list(
            dict.fromkeys(new_node_ids + session.recent_node_ids)
        )[:10]
        session.last_activity = datetime.now(timezone.utc)

        self.db.commit()

    async def _generate_response_with_context(
        self, message: str, context_nodes: List[Dict[str, Any]], memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "text": "Placeholder response",
            "referenced_entities": [
                node["id"] for node in context_nodes if "id" in node
            ],
        }

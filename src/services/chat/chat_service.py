from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from langchain.schema import HumanMessage, SystemMessage
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from neo4j import GraphDatabase

from src.core.database import get_db
from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.models.request import FollowUpChatRequest
from src.models.response import FollowUpChatResponse
from src.models.database import ChatSession
from src.models.database import Message
from src.services.graph_service import GraphService
from src.services.auth_service import AuthService
from src.services.base_client import BaseLLMClient
from src.services.chat.query_decomposition import QueryDecompositionService
from src.services.chat.retrieval_evaluation import RetrievalEvaluationService


class ChatService(BaseLLMClient):
    def __init__(self, db: Session = None):
        super().__init__("ChatService")
        try:
            self.db = db or next(get_db())
            self.auth_service = AuthService(self.db)

            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            self.graph_service = GraphService()

            self._query_decomposition_service = None
            self._retrieval_evaluation_service = None

            logger.info("ChatService core dependencies initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize ChatService dependencies: {str(e)}",
                exc_info=True,
            )
            raise ExternalServiceException(
                message="Failed to initialize chat service dependencies",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    @property
    def query_decomposition_service(self):
        if self._query_decomposition_service is None:
            self._query_decomposition_service = QueryDecompositionService()
        return self._query_decomposition_service

    @property
    def retrieval_evaluation_service(self):
        if self._retrieval_evaluation_service is None:
            self._retrieval_evaluation_service = RetrievalEvaluationService()
        return self._retrieval_evaluation_service

    async def process_query(
        self,
        query: str,
        session_id: str,
        current_user_id: int,
        document_ids: Optional[List[str]] = None,
        use_query_decomposition: bool = True,
        use_retrieval_evaluation: bool = True,
    ) -> Dict[str, Any]:
        try:
            if use_query_decomposition:
                sub_questions = self.query_decomposition_service.decompose_query(query)
                if len(sub_questions) > 1:
                    responses = await self._process_multiple_queries(
                        sub_questions,
                        current_user_id,
                        document_ids,
                        use_retrieval_evaluation,
                    )
                    return self._synthesize_responses(query, responses)

            return await self._process_single_query(
                query, current_user_id, document_ids, use_retrieval_evaluation
            )

        except Exception as e:
            logger.error(f"Error in process_query: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to process query",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    async def _process_multiple_queries(
        self,
        queries: List[str],
        current_user_id: int,
        document_ids: Optional[List[str]],
        use_retrieval_evaluation: bool,
    ) -> List[Dict[str, Any]]:
        responses = []
        for query in queries:
            response = await self._process_single_query(
                query, current_user_id, document_ids, use_retrieval_evaluation
            )
            responses.append(response)
        return responses

    async def _process_single_query(
        self,
        query: str,
        current_user_id: int,
        document_ids: Optional[List[str]],
        use_retrieval_evaluation: bool,
    ) -> Dict[str, Any]:
        try:
            vector_results = self._get_vector_results(
                query, current_user_id, document_ids
            )
            graph_results = self._get_graph_results(query)

            if use_retrieval_evaluation:
                vector_results = await self._apply_retrieval_evaluation(
                    query, vector_results, current_user_id, document_ids
                )

            context = self._merge_results(vector_results, graph_results)
            response = await self._generate_llm_response(query, context)

            return {
                "message": response,
                "context_used": {
                    "vector_results": vector_results,
                    "graph_results": graph_results,
                },
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to process query",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    async def _apply_retrieval_evaluation(
        self,
        query: str,
        initial_results: List[str],
        current_user_id: int,
        document_ids: Optional[List[str]],
    ) -> List[str]:
        results = initial_results.copy()
        evaluation = self.retrieval_evaluation_service.evaluate_retrieval_quality(
            query, results
        )

        attempt = 0
        while evaluation.get("needs_improvement", False) and attempt < 2:
            alternative_queries = self.retrieval_evaluation_service._improve_retrieval(
                query, evaluation
            )
            for alt_query in alternative_queries:
                additional_results = self._get_vector_results(
                    alt_query, current_user_id, document_ids
                )
                results.extend(additional_results)

            evaluation = self.retrieval_evaluation_service.evaluate_retrieval_quality(
                query, results
            )
            attempt += 1

        return results

    async def _generate_llm_response(self, query: str, context: str) -> str:
        """Generate LLM response with given context"""
        system_prompt = f"""
        You are a helpful, reasoning assistant. Answer the user's question based primarily on the provided context. You are allowed to:
        - Rephrase, summarize, or logically infer information from the context.
        - Use reasoning to clarify or structure the answer when necessary.

        However:
        - Do not fabricate facts not supported by the context.
        - If the answer cannot reasonably be inferred from the context, reply: "The answer is not available in the provided context."

        Context:
        {context}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]

        response = self.llm.invoke(messages)
        return response.content

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

    async def rename_chat_session(
        self, session_id: str, new_title: str, current_user_id: int
    ) -> Dict[str, Any]:
        try:
            session = self._get_session(session_id)

            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")

            if session.user_id != current_user_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this chat session"
                )

            session.title = new_title
            session.updated_at = datetime.now(timezone.utc)
            self.db.commit()

            return {"session_id": session_id, "title": new_title}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error renaming chat session: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to rename chat session",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    async def delete_chat_session(
        self, session_id: str, current_user_id: int
    ) -> Dict[str, Any]:
        try:
            session = self._get_session(session_id)

            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")

            if session.user_id != current_user_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this chat session"
                )

            self.db.query(Message).filter(
                Message.chat_session_id == session_id
            ).delete()

            self.db.query(ChatSession).filter(
                ChatSession.id == session_id, ChatSession.user_id == current_user_id
            ).delete()

            self.db.commit()

            return {"session_id": session_id, "status": "deleted"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting chat session: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to delete chat session",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    def _get_vector_results(
        self, query: str, current_user_id: int, document_ids: Optional[List[str]] = None
    ) -> List[str]:
        try:
            filter_dict = {
                "user_id": current_user_id,
            }
            if document_ids:
                filter_dict["doc_id"] = {"$in": document_ids}

            query_embedding = self.embeddings.embed_query(query)

            docs_and_scores = self.vector_store.similarity_search_with_score_by_vector(
                embedding=query_embedding,
                k=settings.TOP_K_RESULTS,
                filter=filter_dict,
            )

            results = [doc.page_content for doc, score in docs_and_scores]

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

    def _synthesize_responses(
        self, original_query: str, sub_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            combined_contexts = "\n\n".join(
                [f"Sub-question result:\n{r['message']}" for r in sub_responses]
            )

            messages = [
                SystemMessage(
                    content="""Synthesize a comprehensive response from the sub-question results.
                The response should:
                1. Flow naturally and be coherent
                2. Address all aspects of the original question
                3. Maintain technical accuracy
                4. Be concise but complete"""
                ),
                HumanMessage(
                    content=f"""Original question: {original_query}

                Sub-question results:
                {combined_contexts}"""
                ),
            ]

            response = self.llm.invoke(messages)

            all_contexts = {
                "sub_responses": sub_responses,
                "synthesized_response": response.content,
            }

            return {"message": response.content, "context_used": all_contexts}
        except Exception as e:
            logger.error(f"Error synthesizing responses: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to synthesize responses",
                service_name="ChatService",
                extra={"error": str(e)},
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

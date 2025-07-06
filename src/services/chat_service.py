from typing import List, Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.services.graph_service import GraphService


class ChatService:
    def __init__(self):
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

            self.graph_service = GraphService()

            logger.info("ChatService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatService: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to initialize chat service",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    def _get_vector_results(self, query: str) -> List[str]:
        try:
            logger.debug("Searching vector store")
            docs = self.vector_store.similarity_search(query, k=settings.TOP_K_RESULTS)
            logger.info(f"Found {len(docs)} relevant documents in vector store")
            return [doc.page_content for doc in docs]
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

    async def process_query(self, query: str) -> str:
        try:
            vector_results = self._get_vector_results(query)
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

            return response.content
        except Exception as e:
            logger.error(f"Error processing chat query: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to process chat query",
                service_name="ChatService",
                extra={"error": str(e)},
            )

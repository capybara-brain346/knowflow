import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger


class ChatService:
    def __init__(self):
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )

            self.vector_store = PGVector.from_existing_index(
                embedding=self.embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
                connection_string=settings.DATABASE_URL,
            )

            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL_NAME
            )
            logger.info("ChatService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatService: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to initialize chat service",
                service_name="ChatService",
                extra={"error": str(e)},
            )

    async def process_query(self, query: str) -> str:
        try:
            logger.debug("Searching for relevant documents")
            docs = self.vector_store.similarity_search(query, k=settings.TOP_K_RESULTS)
            logger.info(f"Found {len(docs)} relevant documents")

            context = "\n\n".join([doc.page_content for doc in docs])

            logger.debug("Building prompt with context")
            messages = [
                SystemMessage(
                    content=f"""You are a helpful AI assistant. Answer the user's question based on the following context. 
                If you cannot find the answer in the context, say so.
                
                Context:
                {context}"""
                ),
                HumanMessage(content=query),
            ]

            logger.debug("Generating response using Groq")
            response = self.llm(messages)
            logger.info("Successfully generated response")

            return response.content
        except Exception as e:
            logger.error(f"Error processing chat query: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to process chat query",
                service_name="ChatService",
                extra={"error": str(e)},
            )

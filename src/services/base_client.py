from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger


class BaseLLMClient:
    def __init__(self, service_name: str):
        self.service_name = service_name
        try:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=settings.GOOGLE_API_KEY,
                model=settings.GEMINI_MODEL_NAME,
                convert_system_message_to_human=True,
            )

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
            )

            self.vector_store = PGVector(
                connection=settings.DATABASE_URL,
                embeddings=self.embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
            )

            logger.info(f"{service_name} initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize {service_name}: {str(e)}", exc_info=True
            )
            raise ExternalServiceException(
                message=f"Failed to initialize {service_name.lower()}",
                service_name=service_name,
                extra={"error": str(e)},
            )

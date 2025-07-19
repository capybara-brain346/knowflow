from typing import List
from langchain.schema import HumanMessage, SystemMessage

from src.core.logging import logger
from src.services.base_client import BaseLLMClient


class QueryDecompositionService(BaseLLMClient):
    def __init__(self):
        super().__init__("QueryDecompositionService")

    def decompose_query(self, query: str) -> List[str]:
        try:
            logger.debug(f"Decomposing query: {query}")
            messages = [
                SystemMessage(
                    content="""You are a query decomposition assistant. Break down complex queries into 2-3 simpler sub-questions.
                Rules:
                1. If the query is already simple, return it as a single question
                2. Each sub-question should be self-contained
                3. Maximum 3 sub-questions
                4. Return only the sub-questions, nothing else"""
                ),
                HumanMessage(content=query),
            ]

            response = self.llm.invoke(messages)
            sub_questions = [
                q.strip() for q in response.content.split("\n") if q.strip()
            ]

            logger.info(f"Query decomposed into {len(sub_questions)} sub-questions")
            return sub_questions
        except Exception as e:
            logger.error(f"Error decomposing query: {str(e)}", exc_info=True)
            return [query]

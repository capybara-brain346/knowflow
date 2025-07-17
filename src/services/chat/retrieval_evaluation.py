import json
from typing import List, Dict, Any
from langchain.schema import HumanMessage, SystemMessage

from src.core.logging import logger
from src.services.base_service import BaseLLMService
from src.utils.utils import clean_llm_response


class RetrievalEvaluationService(BaseLLMService):
    def __init__(self):
        super().__init__("RetrievalEvaluationService")

    def evaluate_retrieval_quality(
        self,
        query: str,
        retrieved_chunks: List[str],
    ) -> Dict[str, Any]:
        try:
            evaluation_prompt = f"""Evaluate the quality of retrieved context for the given query.
            
            Query: {query}
            
            Retrieved Context Chunks:
            {retrieved_chunks}
            
            Analyze the retrieval quality and return a JSON object with the following structure:
            {{
                "chunk_scores": [
                    {{"chunk": "chunk text", "relevance_score": 0-10, "reasoning": "why this score"}}
                ],
                "missing_aspects": ["list of query aspects not covered"],
                "redundant_information": ["list of redundant content"],
                "suggested_improvements": {{
                    "additional_info_needed": ["list of missing information"],
                    "alternative_search_terms": ["list of suggested search terms"]
                }},
                "overall_quality_score": 0-10,
                "quality_summary": "brief evaluation summary"
            }}
            
            Return ONLY valid JSON, no other text."""

            messages = [
                SystemMessage(
                    content="You are a retrieval quality evaluation expert. You must return only valid JSON."
                ),
                HumanMessage(content=evaluation_prompt),
            ]

            evaluation = self.llm.invoke(messages)
            cleaned_response = clean_llm_response(evaluation.content)

            try:
                evaluation_data = json.loads(cleaned_response)
                evaluation_data["needs_improvement"] = (
                    evaluation_data["overall_quality_score"] < 7
                )
                return evaluation_data
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse evaluation JSON: {str(e)}", exc_info=True
                )
                return {"overall_quality_score": 0, "needs_improvement": True}

        except Exception as e:
            logger.error(f"Error evaluating retrieval quality: {str(e)}", exc_info=True)
            return {"overall_quality_score": 0, "needs_improvement": True}

    def _improve_retrieval(
        self,
        query: str,
        evaluation: Dict[str, Any],
    ) -> List[str]:
        try:
            if not evaluation.get("needs_improvement", False):
                return []

            alternative_queries = []

            if "missing_aspects" in evaluation:
                alternative_queries.extend(
                    [f"{query} {aspect}" for aspect in evaluation["missing_aspects"]]
                )

            if "suggested_improvements" in evaluation:
                if "alternative_search_terms" in evaluation["suggested_improvements"]:
                    alternative_queries.extend(
                        evaluation["suggested_improvements"]["alternative_search_terms"]
                    )

            return alternative_queries
        except Exception as e:
            logger.error(
                f"Error generating alternative queries: {str(e)}", exc_info=True
            )
            return []

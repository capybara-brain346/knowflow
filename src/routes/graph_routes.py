from fastapi import APIRouter, status
from typing import Dict, Any, List
from pydantic import BaseModel

from src.services.graph_service import GraphService
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger

router = APIRouter()
graph_service = GraphService()


class GraphQueryRequest(BaseModel):
    query: str


@router.get("/query", status_code=status.HTTP_200_OK)
async def query_graph(query_id: str) -> Dict[str, List[Dict[str, Any]]]:
    try:
        logger.info(f"Processing graph query: {query_id}")
        results = graph_service.query_graph(query_id)
        logger.info("Graph query processed successfully")
        return {"results": results}
    except ExternalServiceException as e:
        logger.error(f"External service error during graph query: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during graph query: {str(e)}", exc_info=True)
        raise ExternalServiceException(
            message="Failed to process graph query",
            service_name="GraphService",
            extra={"error": str(e)},
        )

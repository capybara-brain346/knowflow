from fastapi import APIRouter, status, Depends
from typing import Dict, Any, List, Optional
from src.services.graph_service import GraphService
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.models.request import GraphQueryRequest
from src.models.response import (
    GraphQueryResponse,
    GraphNodeResponse,
    GraphRelationResponse,
)
from src.core.auth import get_current_user
from src.models.database import User

router = APIRouter()
graph_service = GraphService()


@router.post("/query", response_model=GraphQueryResponse)
async def query_graph(
    request: GraphQueryRequest,
    current_user: User = Depends(get_current_user),
) -> GraphQueryResponse:
    try:
        logger.info(f"Processing graph query: {request.query}")
        results = await graph_service.query_graph(request.query, request.params)
        logger.info("Graph query processed successfully")

        return GraphQueryResponse(
            nodes=[GraphNodeResponse(**node) for node in results.get("nodes", [])],
            relations=[
                GraphRelationResponse(**rel) for rel in results.get("relations", [])
            ],
            metadata=results.get("metadata"),
        )
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

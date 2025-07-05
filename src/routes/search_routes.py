from fastapi import APIRouter, Query
from typing import Optional

from src.models.request import SearchParams, SearchSuggestionParams, RecentSearchParams
from src.models.response import (
    SearchResponse,
    SearchSuggestionResponse,
    RecentSearchResponse,
)

router = APIRouter()


@router.get("/", response_model=SearchResponse)
async def search(search_params: SearchParams):
    return {
        "results": [
            {
                "id": 1,
                "title": "Sample Result",
                "content": "Sample content matching query",
                "relevance_score": 0.95,
            }
        ],
        "total_count": 1,
        "page": search_params.page,
        "page_size": search_params.page_size,
    }


@router.get("/suggestions", response_model=SearchSuggestionResponse)
async def get_search_suggestions(suggestion_params: SearchSuggestionParams):
    return {
        "suggestions": [
            f"{suggestion_params.query} suggestion 1",
            f"{suggestion_params.query} suggestion 2",
        ]
    }


@router.get("/recent", response_model=RecentSearchResponse)
async def get_recent_searches(recent_params: RecentSearchParams):
    return {"recent_searches": ["recent search 1", "recent search 2"]}

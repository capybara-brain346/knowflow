from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class NodeProperties(BaseModel):
    name: str = Field(description="Name or title of the node")
    content: Optional[str] = Field(description="Content or description", default=None)
    created_at: str = Field(description="Creation timestamp in ISO format")


class Node(BaseModel):
    id: str = Field(description="Unique string identifier for the node")
    label: str = Field(description="Type/category of the node")
    properties: NodeProperties

    @field_validator("label")
    def validate_label(cls, v):
        valid_labels = {
            "Document",
            "Section",
            "Entity",
            "Concept",
            "Tag",
        }
        if v not in valid_labels:
            raise ValueError(f"Invalid label. Must be one of: {valid_labels}")
        return v


class RelationshipProperties(BaseModel):
    context: Optional[str] = Field(
        description="Description of relationship context", default=None
    )
    extracted_at: str = Field(description="Timestamp when relationship was extracted")


class Relationship(BaseModel):
    start_node: str = Field(description="ID of the starting node")
    end_node: str = Field(description="ID of the ending node")
    type: str = Field(description="Type of relationship")
    properties: RelationshipProperties

    @field_validator("type")
    def validate_type(cls, v):
        valid_types = {
            "CONTAINS",
            "RELATED_TO",
            "MENTIONS",
            "HAS_TAG",
        }
        if v not in valid_types:
            raise ValueError(
                f"Invalid relationship type. Must be one of: {valid_types}"
            )
        return v


class GraphKnowledge(BaseModel):
    nodes: List[Node] = Field(description="List of nodes in the knowledge graph")
    relationships: List[Relationship] = Field(
        description="List of relationships between nodes"
    )

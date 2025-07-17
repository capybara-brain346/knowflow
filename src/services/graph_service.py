from typing import List, Dict, Any, Optional
import json
from neo4j import GraphDatabase, Session
from langchain.schema import HumanMessage, SystemMessage

from src.core.config import settings
from src.models.graph import GraphKnowledge
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.utils.utils import clean_llm_response
from src.services.base_service import BaseLLMService


class GraphService(BaseLLMService):
    def __init__(self):
        super().__init__("GraphService")
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info("GraphService connections initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize GraphService connections: {str(e)}",
                exc_info=True,
            )
            raise ExternalServiceException(
                message="Failed to initialize graph service connections",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def close(self) -> None:
        self.driver.close()

    def _get_knowledge_extraction_prompt(self) -> str:
        return """You are a knowledge graph extraction assistant. Extract entities and their relationships from the given text.
                Return ONLY a raw JSON object (no markdown, no explanation) with nodes and relationships following this exact structure.
                
                IMPORTANT: Keep the graph simple and focused on key concepts.
                
                NODE LABELS EXPLAINED:
                - Document: The main document being processed
                - Section: A distinct part or segment of a document
                - Entity: A specific named thing (person, place, product, etc.)
                - Concept: An abstract idea or topic discussed
                - Tag: A classification or category label
                
                RELATIONSHIP TYPES EXPLAINED:
                - HAS_SECTION: Links a document to its sections/parts
                - MENTIONS: Shows when a section/document refers to an entity/concept
                - HAS_TAG: Connects content to its classification tags
                - RELATED_TO: Shows a general connection between two nodes
                
                {
                    "nodes": [
                        {
                            "id": "unique_string_id",  # Unique identifier for the node
                            "label": "MUST BE ONE OF: Document, Section, Entity, Concept, Tag",
                            "properties": {
                                "name": "string",      # Short, descriptive name of the node
                                "content": null,       # Optional detailed text content
                                "created_at": "2024-03-20T10:00:00Z"  # Creation timestamp
                            }
                        }
                    ],
                    "relationships": [
                        {
                            "start_node": "start_node_id",  # ID of the source node
                            "end_node": "end_node_id",      # ID of the target node
                            "type": "MUST BE ONE OF VALID TYPES",
                            "properties": {
                                "context": null,      # Optional explanation of the relationship
                                "extracted_at": "2024-03-20T10:00:00Z"  # When this connection was found
                            }
                        }
                    ]
                }
                
                DO NOT GENERATE MARKDOWN. ONLY GENERATE JSON.
                FOCUS ON KEY CONCEPTS AND KEEP THE GRAPH SIMPLE.
                ENSURE ALL TIMESTAMPS ARE IN ISO FORMAT.
                """

    def _get_cypher_generation_prompt(self) -> str:
        return """You are a Cypher query generator. Convert the given natural language query into a Cypher query.
                Available node labels: Document, Section, Entity, Concept, Keyword, Tag, Author, Department, FAQ, UserQuery
                Available relationship types: HAS_SECTION, MENTIONS, HAS_TAG, WRITTEN_BY, BELONGS_TO, REFERS_TO, RELATED_TO, ANSWERED_BY, SOURCE_OF
                
                Requirements:
                1. Return ONLY the raw Cypher query without any markdown formatting, quotes, or explanation
                2. Do not use any backticks (`) or code block markers
                3. Use only the specified node labels and relationship types
                4. Each query must start with a valid Cypher command (MATCH, CREATE, etc.)
                5. Use proper Cypher syntax for labels (:Label) and relationships ([:TYPE])
                6. For new/empty databases, use OPTIONAL MATCH to handle missing nodes gracefully
                7. Avoid using WHERE clauses with properties that might not exist
                8. Return null for non-existent paths/properties
                """

    def _parse_knowledge_json(
        self, raw_response: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        try:
            raw_json = json.loads(raw_response)
            knowledge = GraphKnowledge.model_validate(raw_json)
            return knowledge.model_dump()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {"nodes": [], "relationships": []}
        except Exception as e:
            logger.error(f"Failed to validate response structure: {e}")
            return {"nodes": [], "relationships": []}

    def _extract_graph_knowledge(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        try:
            messages = [
                SystemMessage(content=self._get_knowledge_extraction_prompt()),
                HumanMessage(content=text),
            ]

            raw_response = self.llm.invoke(messages).content.strip()
            cleaned_response = clean_llm_response(raw_response)
            print("Raw LLM Response:", cleaned_response)

            return self._parse_knowledge_json(cleaned_response)
        except Exception as e:
            logger.error(f"Error extracting graph knowledge: {str(e)}")
            return {"nodes": [], "relationships": []}

    def _create_document_node(self, session: Session, doc_id: str) -> None:
        session.run(
            """
            MERGE (d:Document {id: $doc_id})
            SET d.created_at = datetime()
            """,
            doc_id=doc_id,
        )

    def _create_knowledge_node(
        self, session: Session, node: Dict[str, Any], doc_id: str
    ) -> None:
        if node["label"] == "Document" and node["id"] == doc_id:
            return

        session.run(
            """
            MERGE (n:`{label}` {id: $id})
            SET n += $properties
            SET n.doc_id = $doc_id
            """,
            label=node["label"],
            id=node["id"],
            properties=node["properties"],
            doc_id=doc_id,
        )

    def _create_relationship(self, session: Session, rel: Dict[str, Any]) -> None:
        session.run(
            """
            MATCH (start {id: $start_id})
            MATCH (end {id: $end_id})
            MERGE (start)-[r:`{type}`]->(end)
            SET r += $properties
            SET r.created_at = datetime()
            """,
            start_id=rel["start_node"],
            end_id=rel["end_node"],
            type=rel["type"],
            properties=rel["properties"],
        )

    def store_graph_knowledge(self, doc_id: str, text: str) -> None:
        try:
            knowledge = self._extract_graph_knowledge(text)

            with self.driver.session() as session:
                self._create_document_node(session, doc_id)

                for node in knowledge["nodes"]:
                    self._create_knowledge_node(session, node, doc_id)

                for rel in knowledge["relationships"]:
                    self._create_relationship(session, rel)

            logger.info(f"Successfully stored graph knowledge for doc_id: {doc_id}")
        except Exception as e:
            logger.error(f"Error storing graph knowledge: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to store graph knowledge",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def _validate_cypher_query(self, query: str) -> bool:
        valid_starts = [
            "MATCH",
            "CREATE",
            "MERGE",
            "RETURN",
            "WITH",
            "UNWIND",
            "CALL",
            "OPTIONAL",
        ]
        return any(query.upper().startswith(cmd) for cmd in valid_starts)

    def _generate_cypher_query(self, query: str) -> str:
        messages = [
            SystemMessage(content=self._get_cypher_generation_prompt()),
            HumanMessage(content=query),
        ]

        cypher_query = self.llm.invoke(messages).content.strip()
        cypher_query = clean_llm_response(cypher_query)

        if not self._validate_cypher_query(cypher_query):
            raise ExternalServiceException(
                message="Invalid Cypher query: must start with a valid Cypher command",
                service_name="GraphService",
                extra={"query": cypher_query},
            )

        return cypher_query

    def query_graph(self, query: str) -> List[Dict[str, Any]]:
        try:
            cypher_query = self._generate_cypher_query(query)
            logger.debug(f"Generated Cypher query: {cypher_query}")

            with self.driver.session() as session:
                result = session.run(cypher_query)
                records = [dict(record) for record in result]
                logger.info(f"Found {len(records)} relevant results in graph")
                return records
        except Exception as e:
            logger.error(f"Error querying graph: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to query graph",
                service_name="GraphService",
                extra={"error": str(e)},
            )

import json
from typing import List, Dict, Any
from neo4j import GraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from datetime import datetime, timezone

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger


class GraphService:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            self.llm = ChatGoogleGenerativeAI(
                google_api_key=settings.GOOGLE_API_KEY,
                model=settings.GEMINI_MODEL_NAME,
                convert_system_message_to_human=True,
            )

            logger.info("GraphService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GraphService: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to initialize graph service",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def close(self):
        self.driver.close()

    def _extract_graph_knowledge(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        try:
            messages = [
                SystemMessage(
                    content="""You are a knowledge graph extraction assistant. Extract entities and their relationships from the given text.
                Return ONLY a raw JSON object (no markdown, no ```json, no backticks) with this structure:
                {
                    "nodes": [
                        {
                            "id": "unique_string_id",
                            "label": "MUST BE ONE OF: Document, Section, Entity, Concept, Keyword, Tag, Author, Department, FAQ, UserQuery",
                            "properties": {
                                "name": "string",
                                "content": "string",
                                "created_at": "timestamp",
                                "last_updated": "timestamp",
                                // Additional properties based on node type
                            }
                        }
                    ],
                    "relationships": [
                        {
                            "start_node": "start_node_id",
                            "end_node": "end_node_id",
                            "type": "MUST BE ONE OF: HAS_SECTION, MENTIONS, HAS_TAG, WRITTEN_BY, BELONGS_TO, REFERS_TO, RELATED_TO, ANSWERED_BY, SOURCE_OF",
                            "properties": {
                                "confidence": "float between 0 and 1",
                                "context": "string describing relationship context"
                            }
                        }
                    ]
                }
                
                Strict Requirements:
                1. Node labels MUST be one of: Document, Section, Entity, Concept, Keyword, Tag, Author, Department, FAQ, UserQuery
                2. Relationship types MUST be one of: HAS_SECTION, MENTIONS, HAS_TAG, WRITTEN_BY, BELONGS_TO, REFERS_TO, RELATED_TO, ANSWERED_BY, SOURCE_OF
                3. All strings must be properly quoted
                4. Return ONLY the raw JSON object - no markdown formatting, no code blocks
                5. All IDs referenced in relationships must exist in nodes
                6. Do not infer relationships unless there's clear evidence in the text
                7. If no valid nodes or relationships can be extracted, return {"nodes": [], "relationships": []}
                8. ALWAYS return valid JSON - test your response before returning
                """
                ),
                HumanMessage(content=text),
            ]

            response = self.llm.invoke(messages)
            content = response.content.strip()

            if content.startswith("```"):
                content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("\n", 1)[0]
            content = content.strip()

            try:
                knowledge = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse LLM response as JSON")
                return {"nodes": [], "relationships": []}

            if (
                not isinstance(knowledge, dict)
                or "nodes" not in knowledge
                or "relationships" not in knowledge
            ):
                logger.error("Invalid knowledge graph structure")
                return {"nodes": [], "relationships": []}

            valid_labels = {
                "Document",
                "Section",
                "Entity",
                "Concept",
                "Keyword",
                "Tag",
                "Author",
                "Department",
                "FAQ",
                "UserQuery",
            }
            valid_types = {
                "HAS_SECTION",
                "MENTIONS",
                "HAS_TAG",
                "WRITTEN_BY",
                "BELONGS_TO",
                "REFERS_TO",
                "RELATED_TO",
                "ANSWERED_BY",
                "SOURCE_OF",
            }

            node_ids = {node["id"] for node in knowledge["nodes"]}

            valid_nodes = []
            for node in knowledge["nodes"]:
                if node["label"] not in valid_labels:
                    logger.warning(f"Invalid node label: {node['label']}")
                    continue
                if "properties" not in node:
                    node["properties"] = {}
                if "created_at" not in node["properties"]:
                    node["properties"]["created_at"] = datetime.now(
                        timezone.utc
                    ).isoformat()
                valid_nodes.append(node)

            valid_relationships = []
            for rel in knowledge["relationships"]:
                if rel["type"] not in valid_types:
                    logger.warning(f"Invalid relationship type: {rel['type']}")
                    continue
                if rel["start_node"] not in node_ids or rel["end_node"] not in node_ids:
                    logger.warning("Relationship references non-existent node")
                    continue
                if "properties" not in rel:
                    rel["properties"] = {}
                if "confidence" not in rel["properties"]:
                    rel["properties"]["confidence"] = 1.0
                valid_relationships.append(rel)

            return {"nodes": valid_nodes, "relationships": valid_relationships}

        except Exception as e:
            logger.error(f"Error extracting graph knowledge: {str(e)}")
            return {"nodes": [], "relationships": []}

    def store_graph_knowledge(self, doc_id: str, text: str) -> None:
        try:
            knowledge = self._extract_graph_knowledge(text)

            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (d:Document {id: $doc_id})
                    SET d.created_at = datetime(),
                        d.last_updated = datetime()
                    """,
                    doc_id=doc_id,
                )

                for node in knowledge["nodes"]:
                    if node["label"] == "Document" and node["id"] == doc_id:
                        continue

                    session.run(
                        """
                        MERGE (n:`{label}` {id: $id})
                        SET n += $properties
                        SET n.doc_id = $doc_id
                        SET n.last_updated = datetime()
                        """,
                        label=node["label"],
                        id=node["id"],
                        properties=node["properties"],
                        doc_id=doc_id,
                    )

                for rel in knowledge["relationships"]:
                    session.run(
                        """
                        MATCH (start {id: $start_id})
                        MATCH (end {id: $end_id})
                        MERGE (start)-[r:`{type}`]->(end)
                        SET r += $properties
                        SET r.created_at = CASE WHEN r.created_at IS NULL 
                                          THEN datetime() 
                                          ELSE r.created_at END
                        SET r.last_updated = datetime()
                        """,
                        start_id=rel["start_node"],
                        end_id=rel["end_node"],
                        type=rel["type"],
                        properties=rel["properties"],
                    )

            logger.info(f"Successfully stored graph knowledge for doc_id: {doc_id}")
        except Exception as e:
            logger.error(f"Error storing graph knowledge: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to store graph knowledge",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def query_graph(self, query: str) -> List[Dict[str, Any]]:
        try:
            messages = [
                SystemMessage(
                    content="""You are a Cypher query generator. Convert the given natural language query into a Cypher query.
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
                
                Example input: "Find all documents about password reset"
                Example output: MATCH (d:Document)-[:HAS_SECTION]->(s:Section)-[:MENTIONS]->(c:Concept {name: 'Password Reset'}) RETURN d, s
                
                Example input: "Find FAQs related to security"
                Example output: MATCH (f:FAQ)-[:MENTIONS]->(c:Concept {name: 'Security'}) RETURN f
                """
                ),
                HumanMessage(content=query),
            ]

            cypher_query = self.llm.invoke(messages).content.strip()

            cypher_query = (
                cypher_query.replace("```cypher", "")
                .replace("```", "")
                .replace("`", "")
                .strip()
            )

            if not any(
                cypher_query.upper().startswith(cmd)
                for cmd in [
                    "MATCH",
                    "CREATE",
                    "MERGE",
                    "RETURN",
                    "WITH",
                    "UNWIND",
                    "CALL",
                    "OPTIONAL",
                ]
            ):
                raise ExternalServiceException(
                    message="Invalid Cypher query: must start with a valid Cypher command",
                    service_name="GraphService",
                    extra={"query": cypher_query},
                )

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

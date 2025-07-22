import re
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
from neo4j import GraphDatabase, Session
from langchain.schema import HumanMessage, SystemMessage

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger
from src.models.graph import GraphKnowledge
from src.services.base_client import BaseLLMClient
from src.utils.utils import clean_llm_response


class GraphService(BaseLLMClient):
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

    def query_graph(self, query: str) -> List[Dict[str, Any]]:
        try:
            cypher_query = self._generate_cypher_query(query)
            logger.debug(f"Generated Cypher query: {cypher_query}")

            search_text = query.lower()
            params = {
                "text": search_text,
                "text_pattern": f"(?i).*{search_text}.*",
            }

            with self.driver.session() as session:
                result = session.run(cypher_query, params)
                records = []
                for record in result:
                    record_dict = {}
                    for key, value in dict(record).items():
                        if hasattr(value, "items"):
                            record_dict[key] = {
                                "id": value.get("id", ""),
                                "name": value.get("name", ""),
                                "content": value.get("content", ""),
                                "labels": list(value.labels)
                                if hasattr(value, "labels")
                                else [],
                            }
                        elif isinstance(value, list):
                            record_dict[key] = [str(v) for v in value]
                        else:
                            record_dict[key] = str(value) if value is not None else None
                    records.append(record_dict)

                logger.info(f"Found {len(records)} relevant results in graph")
                return records
        except Exception as e:
            logger.error(f"Error querying graph: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to query graph",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def query_graph_with_context(
        self, query: str, max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        try:
            base_query = self._generate_cypher_query(query)

            context_query = f"""
            {base_query}
            WITH *, relationships(path) as rels, nodes(path) as nodes
            RETURN 
                [n in nodes | {{
                    id: n.id,
                    label: labels(n)[0],
                    properties: properties(n)
                }}] as nodes,
                [r in rels | {{
                    type: type(r),
                    context: r.context,
                    confidence: r.confidence,
                    properties: properties(r)
                }}] as relationships
            """

            with self.driver.session() as session:
                result = session.run(context_query)
                records = []
                for record in result:
                    record_dict = {
                        "nodes": record["nodes"],
                        "relationships": record["relationships"],
                    }
                    records.append(record_dict)

                logger.info(
                    f"Found {len(records)} relevant results with context in graph"
                )
                return records

        except Exception as e:
            logger.error(f"Error querying graph with context: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to query graph with context",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def close(self) -> None:
        self.driver.close()

    def _get_knowledge_extraction_prompt(self) -> str:
        return """Extract key concepts and structure from the text into a knowledge graph.
            Return ONLY a JSON object with nodes and relationships.
            
            NODE TYPES:
            - Document: The main document
            - Section: Major parts of the document
            - Entity: Named things (people, places, products)
            - Concept: Key ideas or terms
            - Tag: Categories or classifications
            
            RELATIONSHIP TYPES:
            - CONTAINS: Shows hierarchy (Document contains Sections)
            - RELATED_TO: Shows general connections
            - MENTIONS: Shows references
            - HAS_TAG: Shows classifications
            
            Example format:
            {
                "nodes": [
                    {
                        "id": "unique_id",
                        "label": "ONE OF: Document, Section, Entity, Concept, Tag",
                        "properties": {
                            "name": "Short name or title",
                            "content": "Main text content",
                            "created_at": "2024-03-20T10:00:00Z"
                        }
                    }
                ],
                "relationships": [
                    {
                        "start_node": "id_of_source",
                        "end_node": "id_of_target",
                        "type": "ONE OF: CONTAINS, RELATED_TO, MENTIONS, HAS_TAG",
                        "properties": {
                            "context": "Brief explanation",
                            "extracted_at": "2024-03-20T10:00:00Z"
                        }
                    }
                ]
            }
            
            GUIDELINES:
            1. Keep it simple - focus on main concepts and clear relationships
            2. Use CONTAINS for document structure
            3. Use MENTIONS for references
            4. Use RELATED_TO for general connections
            5. Use HAS_TAG for categories
            
            Return ONLY valid JSON, no other text."""

    def _get_cypher_generation_prompt(self) -> str:
        return """Convert natural language queries into Cypher queries for our knowledge graph.
                
                Available Node Labels:
                - Document: Main documents
                - Section: Document sections
                - Entity: Named things
                - Concept: Key ideas
                - Tag: Categories
                
                Available Relationships:
                - CONTAINS: Shows hierarchy
                - RELATED_TO: Shows connections
                - MENTIONS: Shows references
                - HAS_TAG: Shows categories
                
                Query Guidelines:
                1. Basic document search:
                   MATCH (d:Document)
                   WHERE d.name CONTAINS $text OR d.content CONTAINS $text
                   RETURN d
                
                2. Find related entities:
                   MATCH (d:Document)-[:CONTAINS]->(s:Section)
                   MATCH (s)-[:MENTIONS]->(e:Entity)
                   RETURN d.name, collect(e.name)
                
                3. Find concepts and their tags:
                   MATCH (c:Concept)
                   OPTIONAL MATCH (c)-[:HAS_TAG]->(t:Tag)
                   RETURN c.name, collect(t.name)
                
                4. Find connected nodes:
                   MATCH (n)-[r]-(m)
                   WHERE n.name CONTAINS $text
                   RETURN n, type(r), m
                
                5. Return properties:
                   Always include relevant node properties like:
                   - name
                   - content
                   - context (for relationships)
                
                6. Use simple patterns:
                   - Avoid complex path patterns
                   - Use OPTIONAL MATCH for optional patterns
                   - Use WHERE for filtering
                   - Use basic string matching with CONTAINS
                
                Return ONLY the Cypher query, no explanation."""

    def _parse_knowledge_json(
        self, raw_response: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        try:
            try:
                raw_json = json.loads(raw_response)
            except json.JSONDecodeError as e:
                logger.error(f"Initial JSON parsing failed: {e}")
                fixed_response = self._fix_json_response(raw_response)
                raw_json = json.loads(fixed_response)

            if not isinstance(raw_json, dict):
                raise ValueError("Response must be a JSON object")
            if "nodes" not in raw_json or "relationships" not in raw_json:
                raise ValueError(
                    "Response must contain 'nodes' and 'relationships' keys"
                )

            try:
                knowledge = GraphKnowledge.model_validate(raw_json)
                return knowledge.model_dump()
            except Exception as e:
                logger.error(f"Failed to validate knowledge structure: {e}")
                fixed_json = self._fix_knowledge_structure(raw_json)
                knowledge = GraphKnowledge.model_validate(fixed_json)
                return knowledge.model_dump()

        except Exception as e:
            logger.error(f"Failed to parse knowledge JSON: {e}", exc_info=True)
            return {
                "nodes": [
                    {
                        "id": "error_node",
                        "label": "Document",
                        "properties": {
                            "name": "Error Node",
                            "content": f"Failed to parse knowledge: {str(e)}",
                            "created_at": datetime.now().isoformat(),
                        },
                    }
                ],
                "relationships": [],
            }

    def _fix_json_response(self, response: str) -> str:
        response = re.sub(r",(\s*[}\]])", r"\1", response)
        response = re.sub(r"(\w+)(?=\s*:)", r'"\1"', response)
        response = re.sub(
            r':\s*([^"{}\[\],\s][^,}\]]*?)(?=[,}\]])', r': "\1"', response
        )

        return response

    def _fix_knowledge_structure(self, data: Dict) -> Dict:
        fixed = {"nodes": [], "relationships": []}

        if "nodes" in data and isinstance(data["nodes"], list):
            for node in data["nodes"]:
                if isinstance(node, dict):
                    fixed_node = {
                        "id": node.get("id", str(uuid.uuid4())),
                        "label": node.get("label", "Document"),
                        "properties": {},
                    }
                    props = node.get("properties", {})
                    if isinstance(props, dict):
                        fixed_node["properties"] = {
                            "name": props.get("name", ""),
                            "content": props.get("content", ""),
                            "summary": props.get("summary", ""),
                            "importance": float(props.get("importance", 0.5)),
                            "created_at": props.get(
                                "created_at", datetime.now().isoformat()
                            ),
                        }
                    fixed["nodes"].append(fixed_node)

        if "relationships" in data and isinstance(data["relationships"], list):
            for rel in data["relationships"]:
                if isinstance(rel, dict):
                    fixed_rel = {
                        "start_node": rel.get("start_node", ""),
                        "end_node": rel.get("end_node", ""),
                        "type": rel.get("type", "RELATED_TO"),
                        "properties": {},
                    }
                    props = rel.get("properties", {})
                    if isinstance(props, dict):
                        fixed_rel["properties"] = {
                            "context": props.get("context", ""),
                            "confidence": float(props.get("confidence", 0.5)),
                            "extracted_at": props.get(
                                "extracted_at", datetime.now().isoformat()
                            ),
                        }
                    fixed["relationships"].append(fixed_rel)

        return fixed

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
            CREATE (d:Document {
                id: $doc_id,
                type: 'Document',
                created_at: datetime(),
                name: $doc_id,
                importance: 1.0
            })
            """,
            doc_id=doc_id,
        )

    VALID_NODE_LABELS = {
        "Document",
        "Section",
        "Entity",
        "Concept",
        "Tag",
    }

    VALID_RELATIONSHIP_TYPES = {
        "CONTAINS",
        "RELATED_TO",
        "MENTIONS",
        "HAS_TAG",
    }

    def _validate_node_label(self, label: str) -> bool:
        if label not in self.VALID_NODE_LABELS:
            logger.warning(f"Invalid node label: {label}")
            return False
        return True

    def _validate_relationship_type(self, rel_type: str) -> bool:
        if rel_type not in self.VALID_RELATIONSHIP_TYPES:
            logger.warning(f"Invalid relationship type: {rel_type}")
            return False
        return True

    def _create_knowledge_node(
        self, session: Session, node: Dict[str, Any], doc_id: str
    ) -> None:
        if node["label"] == "Document" and node["id"] == doc_id:
            return

        if not self._validate_node_label(node["label"]):
            logger.error(
                f"Skipping node creation due to invalid label: {node['label']}"
            )
            return

        session.run(
            """
            CREATE (n:`$node_label` {
                id: $id,
                doc_id: $doc_id,
                name: $name,
                content: $content,
                summary: $summary,
                importance: $importance,
                created_at: datetime()
            })
            """,
            node_label=node["label"],
            id=node["id"],
            doc_id=doc_id,
            name=node["properties"].get("name", ""),
            content=node["properties"].get("content", ""),
            summary=node["properties"].get("summary", ""),
            importance=node["properties"].get("importance", 0.5),
        )

    def _create_relationship(self, session: Session, rel: Dict[str, Any]) -> None:
        if not self._validate_relationship_type(rel["type"]):
            logger.error(
                f"Skipping relationship creation due to invalid type: {rel['type']}"
            )
            return

        session.run(
            """
            MATCH (start) WHERE start.id = $start_id
            MATCH (end) WHERE end.id = $end_id
            CREATE (start)-[r:`$rel_type` {
                context: $context,
                confidence: $confidence,
                created_at: datetime()
            }]->(end)
            """,
            start_id=rel["start_node"],
            end_id=rel["end_node"],
            rel_type=rel["type"],
            context=rel["properties"].get("context", ""),
            confidence=rel["properties"].get("confidence", 0.5),
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

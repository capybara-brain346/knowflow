import json
from typing import List, Dict, Any
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

from src.core.config import settings
from src.core.exceptions import ExternalServiceException
from src.core.logging import logger


class GraphService:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL_NAME
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
                            "label": "MUST BE EXACTLY ONE OF: Issue, Step, Doc, FAQ (no other values allowed)",
                            "properties": {"key1": "value1", "key2": "value2"}
                        }
                    ],
                    "relationships": [
                        {
                            "start_node": "start_node_id",
                            "end_node": "end_node_id",
                            "type": "MUST BE EXACTLY ONE OF: HAS_SOLUTION, FOLLOWS, MENTIONS (no other values allowed)",
                            "properties": {"key1": "value1"}
                        }
                    ]
                }
                
                Strict Requirements:
                1. Node labels MUST be exactly one of: Issue, Step, Doc, FAQ - no variations or other values allowed
                2. Relationship types MUST be exactly one of: HAS_SOLUTION, FOLLOWS, MENTIONS - no variations or other values allowed
                3. All strings must be properly quoted
                4. Return ONLY the raw JSON object - no markdown formatting, no code blocks, no backticks
                5. All IDs referenced in relationships must exist in nodes
                6. Do not infer or create relationships unless explicitly stated in the text
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

            valid_labels = {"Issue", "Step", "Doc", "FAQ"}
            valid_types = {"HAS_SOLUTION", "FOLLOWS", "MENTIONS"}

            node_ids = {node["id"] for node in knowledge["nodes"]}

            valid_nodes = []
            for node in knowledge["nodes"]:
                if node["label"] not in valid_labels:
                    logger.warning(f"Invalid node label: {node['label']}")
                    continue
                valid_nodes.append(node)

            valid_relationships = []
            for rel in knowledge["relationships"]:
                if rel["type"] not in valid_types:
                    logger.warning(f"Invalid relationship type: {rel['type']}")
                    continue
                if rel["start_node"] not in node_ids or rel["end_node"] not in node_ids:
                    logger.warning("Relationship references non-existent node")
                    continue
                valid_relationships.append(rel)

            return {"nodes": valid_nodes, "relationships": valid_relationships}

        except Exception as e:
            logger.error(f"Error extracting graph knowledge: {str(e)}")
            return {"nodes": [], "relationships": []}

    def store_graph_knowledge(self, doc_id: str, text: str) -> None:
        try:
            knowledge = self._extract_graph_knowledge(text)

            with self.driver.session() as session:
                for node in knowledge["nodes"]:
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

                for rel in knowledge["relationships"]:
                    session.run(
                        """
                        MATCH (start {id: $start_id})
                        MATCH (end {id: $end_id})
                        MERGE (start)-[r:`{type}`]->(end)
                        SET r += $properties
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
                Available node labels: Issue, Step, Doc, FAQ
                Available relationship types: HAS_SOLUTION, FOLLOWS, MENTIONS
                
                Requirements:
                1. Return ONLY the raw Cypher query without any markdown formatting, quotes, or explanation
                2. Do not use any backticks (`) or code block markers
                3. Use only the specified node labels and relationship types
                4. Each query must start with a valid Cypher command (MATCH, CREATE, etc.)
                5. Use proper Cypher syntax for labels (:Label) and relationships ([:TYPE])
                6. For new/empty databases, use OPTIONAL MATCH to handle missing nodes gracefully
                7. Avoid using WHERE clauses with properties that might not exist
                8. Return null for non-existent paths/properties
                
                Example input: "Find all issues"
                Example output: OPTIONAL MATCH (i:Issue) RETURN i
                
                Example input: "Find steps that follow issue X"
                Example output: OPTIONAL MATCH (i:Issue)-[:FOLLOWS]->(s:Step) RETURN s
                
                Example input: "Find support tickets"
                Example output: OPTIONAL MATCH (i:Issue) RETURN i
                
                Example input: "Find issues with specific type"
                Example output: OPTIONAL MATCH (i:Issue) RETURN i, i.properties
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

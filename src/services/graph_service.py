from typing import List, Dict, Any
from neo4j import GraphDatabase
from langchain.chat_models import ChatGroq
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
                Format the output as a dictionary with two keys:
                - nodes: list of dictionaries with 'id', 'label', and 'properties'
                - relationships: list of dictionaries with 'start_node', 'end_node', 'type', and 'properties'
                
                Node labels should be one of: Issue, Step, Doc, FAQ
                Relationship types should be one of: HAS_SOLUTION, FOLLOWS, MENTIONS
                """
                ),
                HumanMessage(content=text),
            ]

            response = self.llm(messages)
            return eval(response.content)  # Safe since we control the LLM prompt
        except Exception as e:
            logger.error(f"Error extracting graph knowledge: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to extract graph knowledge",
                service_name="GraphService",
                extra={"error": str(e)},
            )

    def store_graph_knowledge(self, doc_id: str, text: str) -> None:
        try:
            knowledge = self._extract_graph_knowledge(text)

            with self.driver.session() as session:
                # Create nodes
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

                # Create relationships
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
            # Generate Cypher query using LLM
            messages = [
                SystemMessage(
                    content="""You are a Cypher query generator. Convert the given natural language query into a Cypher query.
                Available node labels: Issue, Step, Doc, FAQ
                Available relationship types: HAS_SOLUTION, FOLLOWS, MENTIONS
                
                Return only the Cypher query without any explanation."""
                ),
                HumanMessage(content=query),
            ]

            cypher_query = self.llm(messages).content

            # Execute query
            with self.driver.session() as session:
                result = session.run(cypher_query)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error querying graph: {str(e)}", exc_info=True)
            raise ExternalServiceException(
                message="Failed to query graph",
                service_name="GraphService",
                extra={"error": str(e)},
            )

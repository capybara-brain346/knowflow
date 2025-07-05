# AI Architecture for Hybrid Retrieval-Augmented Generation (RAG) with Knowledge Graph

This document details the AI subsystems of the project, combining Retrieval-Augmented Generation (RAG) with structured Knowledge Graph (KG)-based retrieval. It is inspired by enterprise implementations like LinkedIn’s support pipeline and builds on open-source tooling such as LangChain, Neo4j, Qdrant, and OpenAI.

---

## 1. Overview: What is Hybrid RAG + KG?

Traditional RAG combines neural retrieval with LLMs by embedding a user query and searching a vector database for relevant chunks of unstructured text. However, this approach lacks structure and reasoning. This project enhances the standard RAG architecture with a **Knowledge Graph**, allowing retrieval over both:

* **Dense semantic embeddings** (via vector DB)
* **Structured graph traversal** (via graph DB like Neo4j or TigerGraph)

The hybrid approach enables:

* More accurate retrieval of long or structured content
* Multi-hop reasoning over connected concepts
* Explainability through graph node tracing
* Semantic + relational retrieval synergy

---

## 2. Core Pipeline Architecture

### Indexing Phase (Preprocessing)

1. **Document Ingestion**

   * Load documents (tickets, FAQs, etc.) using LangChain `DocumentLoader`.
   * Chunk large documents using `RecursiveCharacterTextSplitter` or custom chunkers.

2. **Graph Construction**

   * Use `LLMGraphTransformer` (LangChain) to extract structured fields, relations, and entities.
   * Build a hierarchical intra-document graph (e.g. sections of a support ticket).
   * Add inter-document edges via metadata (e.g. "cloned from") or embedding similarity.

3. **Embedding Storage**

   * Embed text of graph nodes (e.g. ticket summaries, steps) using models like `OpenAIEmbeddings` or `E5`.
   * Store embeddings in a vector DB (e.g. Qdrant, FAISS).

4. **Graph Storage**

   * Insert nodes and edges into a graph database (`Neo4jGraph.add_graph_documents()`).
   * Optionally use `Neo4jVector.from_existing_graph()` to create vector indexes over graph content.

---

### Query-Time Phase (Retrieval + Generation)

1. **Query Understanding**

   * Perform Named Entity Recognition (NER) or LLM parsing to extract:

     * Entities (e.g. issue = "login error")
     * Intent (e.g. fix instructions)
   * Used to construct filters and match against KG nodes.

2. **Hybrid Retrieval**

   * **Vector Search**: Query embedding retrieves top-K nodes based on semantic similarity.
   * **Graph Traversal**: Query is transformed into a graph query (e.g. Cypher) to extract exact subgraphs or fields (e.g. “steps to reproduce” for Ticket X).
   * **Combined**: Merge results from both strategies for richer context.

3. **Answer Generation**

   * Pass retrieved graph fields and vector chunks to an LLM (e.g. GPT-4) via a prompt template.
   * If graph fails or yields low-confidence results, fallback to pure vector-based RAG.

---

## 3. Key LangChain Components

| Task                       | LangChain Tool                                           |
| -------------------------- | -------------------------------------------------------- |
| Document Loading           | `CSVLoader`, `JSONLoader`, `PDFLoader`                   |
| Chunking                   | `RecursiveCharacterTextSplitter`                         |
| Graph Extraction           | `LLMGraphTransformer`                                    |
| Embedding & Indexing       | `OpenAIEmbeddings`, `Qdrant` or `FAISS`                  |
| Graph DB Connector         | `Neo4jGraph`, `TigerGraph`                               |
| Vector Retriever           | `.as_retriever()` on `VectorStore`                       |
| Graph Retriever            | `graph.query(cypher_query)`                              |
| LLM Interaction            | `RetrievalQA`, `ConversationalRetrievalQA`, `ChatOpenAI` |
| Hybrid Chain Orchestration | `SequentialChain`, custom merge logic                    |

---

## 4. Sample Code Snippet

```python
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain_neo4j import Neo4jGraph

# Initialize vector retriever
embeddings = OpenAIEmbeddings()
vector_store = FAISS.load_local("faiss_index", embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# LLM for final QA
qa = RetrievalQA.from_chain_type(llm=ChatOpenAI(temperature=0), retriever=retriever)

# Graph query step
graph = Neo4jGraph(uri="bolt://localhost:7687", user="neo4j", password="pw")
cypher = "MATCH (t:Ticket {id: 'ENT-22970'})-[:HAS_SOLUTION]->(s) RETURN s.value"
graph_answer = graph.query(cypher)[0]['s.value']

# Final output
query = "How to fix the login issue where users can't log in?"
response = qa.run(query)
print(graph_answer + "\n\n" + response)
```

---

## 5. Best Practices for Enterprise Use

* **Freshness**: Integrate ingestion pipelines or webhooks (e.g. Jira or CRM) to keep KG updated.
* **Fallback Mechanism**: Always support pure RAG fallback if graph-based query fails.
* **Monitoring**: Track retrieval scores (e.g. MRR) and token-level generation quality (e.g. BLEU).
* **Explainability**: Return graph node IDs or paths used for answer generation.
* **Guardrails**: Use KG to constrain LLM outputs with known facts (e.g. only generate answers with cited nodes).
* **Scaling**: Shard vector stores (e.g. Qdrant cluster) and graph DBs for large orgs.

---

## 6. Summary

This AI subsystem combines the semantic breadth of vector-based RAG with the precision and reasoning capabilities of Knowledge Graphs. It enables:

* Multi-hop retrieval across structured data
* Better alignment with enterprise knowledge
* Enhanced trust through explainable sources

By using LangChain’s modular tooling, this architecture remains flexible, debuggable, and production-ready.


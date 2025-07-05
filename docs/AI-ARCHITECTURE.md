# AI Architecture for Hybrid Retrieval-Augmented Generation (RAG) with Knowledge Graph

This document details the AI subsystems of the project, combining Retrieval-Augmented Generation (RAG) with structured Knowledge Graph (KG)-based retrieval. It is inspired by enterprise implementations like LinkedIn’s support pipeline and builds on open-source tooling such as LangChain, Neo4j, Qdrant, and OpenAI.

---

## 1. Overview: What is Hybrid RAG + KG?

Traditional RAG combines neural retrieval with LLMs by embedding a user query and searching a vector database for relevant chunks of unstructured text. However, this approach lacks structure and reasoning. This project enhances the standard RAG architecture with a **Knowledge Graph**, allowing retrieval over both:

- **Dense semantic embeddings** (via vector DB)
- **Structured graph traversal** (via graph DB like Neo4j or TigerGraph)

The hybrid approach enables:

- More accurate retrieval of long or structured content
- Multi-hop reasoning over connected concepts
- Explainability through graph node tracing
- Semantic + relational retrieval synergy

---

## 2. Core Pipeline Architecture

### Indexing Phase (Preprocessing)

1. **Document Ingestion**

   - Load documents (tickets, FAQs, etc.) using LangChain `DocumentLoader`.
   - Chunk large documents using `RecursiveCharacterTextSplitter` or custom chunkers.

2. **Graph Construction**

   - Use `LLMGraphTransformer` (LangChain) to extract structured fields, relations, and entities.
   - Build a hierarchical intra-document graph (e.g. sections of a support ticket).
   - Add inter-document edges via metadata (e.g. "cloned from") or embedding similarity.

3. **Embedding Storage**

   - Embed text of graph nodes (e.g. ticket summaries, steps) using models like `OpenAIEmbeddings` or `E5`.
   - Store embeddings in a vector DB (e.g. Qdrant, FAISS).

4. **Graph Storage**

   - Insert nodes and edges into a graph database (`Neo4jGraph.add_graph_documents()`).
   - Optionally use `Neo4jVector.from_existing_graph()` to create vector indexes over graph content.

---

### Query-Time Phase (Retrieval + Generation)

1. **Query Understanding**

   - Perform Named Entity Recognition (NER) or LLM parsing to extract:

     - Entities (e.g. issue = "login error")
     - Intent (e.g. fix instructions)

   - Used to construct filters and match against KG nodes.

2. **Hybrid Retrieval**

   - **Vector Search**: Query embedding retrieves top-K nodes based on semantic similarity.
   - **Graph Traversal**: Query is transformed into a graph query (e.g. Cypher) to extract exact subgraphs or fields (e.g. “steps to reproduce” for Ticket X).
   - **Combined**: Merge results from both strategies for richer context.

3. **Answer Generation**

   - Pass retrieved graph fields and vector chunks to an LLM (e.g. GPT-4) via a prompt template.
   - If graph fails or yields low-confidence results, fallback to pure vector-based RAG.

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

## 4. Advanced Features

### 4.1 Explainability Mode ("Why this answer?")

To increase trust and transparency, the system supports an explainability feature that reveals the inner workings of the AI pipeline.

**What it includes:**

- List of graph nodes and vector chunks used
- Vector similarity scores (e.g., cosine distance)
- Graph paths or Cypher queries executed
- The exact prompt fed into the LLM, including retrieved context

This mode helps users understand why a particular answer was given, supports debugging and validation, and makes the system suitable for high-assurance environments.

### 4.2 Conversational Memory with Graph Context

The system maintains conversational memory with awareness of previously mentioned graph entities.

**How it works:**

- Stores the history of referenced KG nodes per session (e.g., a specific support ticket ID)
- For follow-up queries, reuses and prioritizes nodes and their neighbors (e.g., next steps, causes, resolutions)
- Retrieval is guided not only by semantic similarity but also by graph relationships to the prior context

This creates a more natural, multi-turn conversation experience grounded in structured knowledge.

---

## 5. Best Practices for Enterprise Use

- **Freshness**: Integrate ingestion pipelines or webhooks (e.g. Jira or CRM) to keep KG updated.
- **Fallback Mechanism**: Always support pure RAG fallback if graph-based query fails.
- **Monitoring**: Track retrieval scores (e.g. MRR) and token-level generation quality (e.g. BLEU).
- **Explainability**: Return graph node IDs or paths used for answer generation.
- **Guardrails**: Use KG to constrain LLM outputs with known facts (e.g. only generate answers with cited nodes).
- **Scaling**: Shard vector stores (e.g. Qdrant cluster) and graph DBs for large orgs.

---

## 6. Summary

This AI subsystem combines the semantic breadth of vector-based RAG with the precision and reasoning capabilities of Knowledge Graphs. It enables:

- Multi-hop retrieval across structured data
- Better alignment with enterprise knowledge
- Enhanced trust through explainable sources

By using LangChain’s modular tooling, this architecture remains flexible, debuggable, and production-ready.

```

```

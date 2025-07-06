PGVector
class langchain_community.vectorstores.pgvector.PGVector(
connection_string: str,
embedding_function: Embeddings,
embedding_length: int | None = None,
collection_name: str = 'langchain',
collection_metadata: dict | None = None,
distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
pre_delete_collection: bool = False,
logger: Logger | None = None,
relevance_score_fn: Callable[[float], float] | None = None,
\*,
connection: Connection | None = None,
engine_args: dict[str, Any] | None = None,
use_jsonb: bool = False,
create_extension: bool = True,
)[source]
Deprecated since version 0.0.31: This class is pending deprecation and may be removed in a future version. You can swap to using the PGVector implementation in langchain_postgres. Please read the guidelines in the doc-string of this class to follow prior to migrating as there are some differences between the implementations. See <langchain-ai/langchain-postgres> for details about the new implementation. Use from langchain_postgres import PGVector; instead.

Postgres/PGVector vector store.

DEPRECATED: This class is pending deprecation and will likely receive
no updates. An improved version of this class is available in langchain_postgres as PGVector. Please use that class instead.

When migrating please keep in mind that:
The new implementation works with psycopg3, not with psycopg2 (This implementation does not work with psycopg3).

Filtering syntax has changed to use $ prefixed operators for JSONB metadata fields. (New implementation only uses JSONB field for metadata)

The new implementation made some schema changes to address issues with the existing implementation. So you will need to re-create your tables and re-index your data or else carry out a manual migration.

To use, you should have the pgvector python package installed.

Parameters
:
connection_string (str) – Postgres connection string.

embedding_function (Embeddings) – Any embedding function implementing langchain.embeddings.base.Embeddings interface.

embedding_length (Optional[int]) – The length of the embedding vector. (default: None) NOTE: This is not mandatory. Defining it will prevent vectors of any other size to be added to the embeddings table but, without it, the embeddings can’t be indexed.

collection_name (str) – The name of the collection to use. (default: langchain) NOTE: This is not the name of the table, but the name of the collection. The tables will be created when initializing the store (if not exists) So, make sure the user has the right permissions to create tables.

distance_strategy (DistanceStrategy) – The distance strategy to use. (default: COSINE)

pre_delete_collection (bool) – If True, will delete the collection if it exists. (default: False). Useful for testing.

engine_args (Optional[dict[str, Any]]) – SQLAlchemy’s create engine arguments.

use_jsonb (bool) – Use JSONB instead of JSON for metadata. (default: True) Strongly discouraged from using JSON as it’s not as efficient for querying. It’s provided here for backwards compatibility with older versions, and will be removed in the future.

create_extension (bool) – If True, will create the vector extension if it doesn’t exist. disabling creation is useful when using ReadOnly Databases.

collection_metadata (Optional[dict])

logger (Optional[logging.Logger])

relevance_score_fn (Optional[Callable[[float], float]])

connection (Optional[sqlalchemy.engine.Connection])

Example

from langchain_community.vectorstores import PGVector
from langchain_community.embeddings.openai import OpenAIEmbeddings
CONNECTION_STRING = "postgresql+psycopg2://hwc@localhost:5432/test3"
COLLECTION_NAME = "state_of_the_union_test"
embeddings = OpenAIEmbeddings()
vectorestore = PGVector.from_documents(
embedding=embeddings,
documents=docs,
collection_name=COLLECTION_NAME,
connection_string=CONNECTION_STRING,
use_jsonb=True,
Initialize the PGVector store.

Attributes

distance_strategy

embeddings

Access the query embedding object if available.

Methods

**init**(connection_string, embedding_function)

Initialize the PGVector store.

aadd_documents(documents, \*\*kwargs)

Async run more documents through the embeddings and add to the vectorstore.

aadd_texts(texts[, metadatas, ids])

Async run more texts through the embeddings and add to the vectorstore.

add_documents(documents, \*\*kwargs)

Add or update documents in the vectorstore.

add_embeddings(texts, embeddings[, ...])

Add embeddings to the vectorstore.

add_texts(texts[, metadatas, ids])

Run more texts through the embeddings and add to the vectorstore.

adelete([ids])

Async delete by vector ID or other criteria.

afrom_documents(documents, embedding, \*\*kwargs)

Async return VectorStore initialized from documents and embeddings.

afrom_texts(texts, embedding[, metadatas, ids])

Async return VectorStore initialized from texts and embeddings.

aget_by_ids(ids, /)

Async get documents by their IDs.

amax_marginal_relevance_search(query[, k, ...])

Async return docs selected using the maximal marginal relevance.

amax_marginal_relevance_search_by_vector(...)

Return docs selected using the maximal marginal relevance.

as_retriever(\*\*kwargs)

Return VectorStoreRetriever initialized from this VectorStore.

asearch(query, search_type, \*\*kwargs)

Async return docs most similar to query using a specified search type.

asimilarity_search(query[, k])

Async return docs most similar to query.

asimilarity_search_by_vector(embedding[, k])

Async return docs most similar to embedding vector.

asimilarity_search_with_relevance_scores(query)

Async return docs and relevance scores in the range [0, 1].

asimilarity_search_with_score(\*args, \*\*kwargs)

Async run similarity search with distance.

connection_string_from_db_params(driver, ...)

Return connection string from database parameters.

create_collection()

create_tables_if_not_exists()

create_vector_extension()

delete([ids, collection_only])

Delete vectors by ids or uuids.

delete_collection()

drop_tables()

from_documents(documents, embedding[, ...])

Return VectorStore initialized from documents and embeddings.

from_embeddings(text_embeddings, embedding)

Construct PGVector wrapper from raw documents and pre- generated embeddings.

from_existing_index(embedding[, ...])

Get instance of an existing PGVector store.This method will return the instance of the store without inserting any new embeddings

from_texts(texts, embedding[, metadatas, ...])

Return VectorStore initialized from texts and embeddings.

get_by_ids(ids, /)

Get documents by their IDs.

get_collection(session)

get_connection_string(kwargs)

max_marginal_relevance_search(query[, k, ...])

Return docs selected using the maximal marginal relevance.

max_marginal_relevance_search_by_vector(...)

Return docs selected using the maximal marginal relevance

max_marginal_relevance_search_with_score(query)

Return docs selected using the maximal marginal relevance with score.

max_marginal_relevance_search_with_score_by_vector(...)

Return docs selected using the maximal marginal relevance with score

search(query, search_type, \*\*kwargs)

Return docs most similar to query using a specified search type.

similarity_search(query[, k, filter])

Run similarity search with PGVector with distance.

similarity_search_by_vector(embedding[, k, ...])

Return docs most similar to embedding vector.

similarity_search_with_relevance_scores(query)

Return docs and relevance scores in the range [0, 1].

similarity_search_with_score(query[, k, filter])

Return docs most similar to query.

similarity_search_with_score_by_vector(embedding)

**init**(
connection_string: str,
embedding_function: Embeddings,
embedding_length: int | None = None,
collection_name: str = 'langchain',
collection_metadata: dict | None = None,
distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
pre_delete_collection: bool = False,
logger: Logger | None = None,
relevance_score_fn: Callable[[float], float] | None = None,
\*,
connection: Connection | None = None,
engine_args: dict[str, Any] | None = None,
use_jsonb: bool = False,
create_extension: bool = True,
) → None[source]
Initialize the PGVector store.

Parameters
:
connection_string (str)

embedding_function (Embeddings)

embedding_length (int | None)

collection_name (str)

collection_metadata (dict | None)

distance_strategy (DistanceStrategy)

pre_delete_collection (bool)

logger (Logger | None)

relevance_score_fn (Callable[[float], float] | None)

connection (Connection | None)

engine_args (dict[str, Any] | None)

use_jsonb (bool)

create_extension (bool)

Return type
:
None

async aadd_documents(
documents: list[Document],
\*\*kwargs: Any,
) → list[str]
Async run more documents through the embeddings and add to the vectorstore.

Parameters
:
documents (list[Document]) – Documents to add to the vectorstore.

kwargs (Any) – Additional keyword arguments.

Returns
:
List of IDs of the added texts.

Raises
:
ValueError – If the number of IDs does not match the number of documents.

Return type
:
list[str]

async aadd_texts(
texts: Iterable[str],
metadatas: list[dict] | None = None,
\*,
ids: list[str] | None = None,
\*\*kwargs: Any,
) → list[str]
Async run more texts through the embeddings and add to the vectorstore.

Parameters
:
texts (Iterable[str]) – Iterable of strings to add to the vectorstore.

metadatas (Optional[list[dict]]) – Optional list of metadatas associated with the texts. Default is None.

ids (Optional[list[str]]) – Optional list

\*\*kwargs (Any) – vectorstore specific parameters.

Returns
:
List of ids from adding the texts into the vectorstore.

Raises
:
ValueError – If the number of metadatas does not match the number of texts.

ValueError – If the number of ids does not match the number of texts.

Return type
:
list[str]

add_documents(
documents: list[Document],
\*\*kwargs: Any,
) → list[str]
Add or update documents in the vectorstore.

Parameters
:
documents (list[Document]) – Documents to add to the vectorstore.

kwargs (Any) – Additional keyword arguments. if kwargs contains ids and documents contain ids, the ids in the kwargs will receive precedence.

Returns
:
List of IDs of the added texts.

Raises
:
ValueError – If the number of ids does not match the number of documents.

Return type
:
list[str]

add_embeddings(
texts: Iterable[str],
embeddings: List[List[float]],
metadatas: List[dict] | None = None,
ids: List[str] | None = None,
\*\*kwargs: Any,
) → List[str][source]
Add embeddings to the vectorstore.

Parameters
:
texts (Iterable[str]) – Iterable of strings to add to the vectorstore.

embeddings (List[List[float]]) – List of list of embedding vectors.

metadatas (List[dict] | None) – List of metadatas associated with the texts.

kwargs (Any) – vectorstore specific parameters

ids (List[str] | None)

Return type
:
List[str]

add_texts(
texts: Iterable[str],
metadatas: List[dict] | None = None,
ids: List[str] | None = None,
\*\*kwargs: Any,
) → List[str][source]
Run more texts through the embeddings and add to the vectorstore.

Parameters
:
texts (Iterable[str]) – Iterable of strings to add to the vectorstore.

metadatas (List[dict] | None) – Optional list of metadatas associated with the texts.

kwargs (Any) – vectorstore specific parameters

ids (List[str] | None)

Returns
:
List of ids from adding the texts into the vectorstore.

Return type
:
List[str]

async adelete(
ids: list[str] | None = None,
\*\*kwargs: Any,
) → bool | None
Async delete by vector ID or other criteria.

Parameters
:
ids (list[str] | None) – List of ids to delete. If None, delete all. Default is None.

\*\*kwargs (Any) – Other keyword arguments that subclasses might use.

Returns
:
True if deletion is successful, False otherwise, None if not implemented.

Return type
:
Optional[bool]

async classmethod afrom_documents(
documents: list[Document],
embedding: Embeddings,
\*\*kwargs: Any,
) → Self
Async return VectorStore initialized from documents and embeddings.

Parameters
:
documents (list[Document]) – List of Documents to add to the vectorstore.

embedding (Embeddings) – Embedding function to use.

kwargs (Any) – Additional keyword arguments.

Returns
:
VectorStore initialized from documents and embeddings.

Return type
:
VectorStore

async classmethod afrom_texts(
texts: list[str],
embedding: Embeddings,
metadatas: list[dict] | None = None,
\*,
ids: list[str] | None = None,
\*\*kwargs: Any,
) → Self
Async return VectorStore initialized from texts and embeddings.

Parameters
:
texts (list[str]) – Texts to add to the vectorstore.

embedding (Embeddings) – Embedding function to use.

metadatas (list[dict] | None) – Optional list of metadatas associated with the texts. Default is None.

ids (list[str] | None) – Optional list of IDs associated with the texts.

kwargs (Any) – Additional keyword arguments.

Returns
:
VectorStore initialized from texts and embeddings.

Return type
:
VectorStore

async aget_by_ids(
ids: Sequence[str],
/,
) → list[Document]
Async get documents by their IDs.

The returned documents are expected to have the ID field set to the ID of the document in the vector store.

Fewer documents may be returned than requested if some IDs are not found or if there are duplicated IDs.

Users should not assume that the order of the returned documents matches the order of the input IDs. Instead, users should rely on the ID field of the returned documents.

This method should NOT raise exceptions if no documents are found for some IDs.

Parameters
:
ids (Sequence[str]) – List of ids to retrieve.

Returns
:
List of Documents.

Return type
:
list[Document]

Added in version 0.2.11.

async amax_marginal_relevance_search(
query: str,
k: int = 4,
fetch_k: int = 20,
lambda_mult: float = 0.5,
\*\*kwargs: Any,
) → list[Document]
Async return docs selected using the maximal marginal relevance.

Maximal marginal relevance optimizes for similarity to query AND diversity among selected documents.

Parameters
:
query (str) – Text to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

fetch_k (int) – Number of Documents to fetch to pass to MMR algorithm. Default is 20.

lambda_mult (float) – Number between 0 and 1 that determines the degree of diversity among the results with 0 corresponding to maximum diversity and 1 to minimum diversity. Defaults to 0.5.

\*\*kwargs (Any) – Arguments to pass to the search method.

Returns
:
List of Documents selected by maximal marginal relevance.

Return type
:
list[Document]

async amax_marginal_relevance_search_by_vector(
embedding: List[float],
k: int = 4,
fetch_k: int = 20,
lambda_mult: float = 0.5,
filter: Dict[str, str] | None = None,
\*\*kwargs: Any,
) → List[Document][source]
Return docs selected using the maximal marginal relevance.

Parameters
:
embedding (List[float])

k (int)

fetch_k (int)

lambda_mult (float)

filter (Dict[str, str] | None)

kwargs (Any)

Return type
:
List[Document]

as_retriever(
\*\*kwargs: Any,
) → VectorStoreRetriever
Return VectorStoreRetriever initialized from this VectorStore.

Parameters
:
\*\*kwargs (Any) –

Keyword arguments to pass to the search function. Can include: search_type (Optional[str]): Defines the type of search that

the Retriever should perform. Can be “similarity” (default), “mmr”, or “similarity_score_threshold”.

search_kwargs (Optional[Dict]): Keyword arguments to pass to the
search function. Can include things like:
k: Amount of documents to return (Default: 4) score_threshold: Minimum relevance threshold

for similarity_score_threshold

fetch_k: Amount of documents to pass to MMR algorithm
(Default: 20)

lambda_mult: Diversity of results returned by MMR;
1 for minimum diversity and 0 for maximum. (Default: 0.5)

filter: Filter by document metadata

Returns
:
Retriever class for VectorStore.

Return type
:
VectorStoreRetriever

Examples:

# Retrieve more documents with higher diversity

# Useful if your dataset has many similar documents

docsearch.as_retriever(
search_type="mmr",
search_kwargs={'k': 6, 'lambda_mult': 0.25}
)

# Fetch more documents for the MMR algorithm to consider

# But only return the top 5

docsearch.as_retriever(
search_type="mmr",
search_kwargs={'k': 5, 'fetch_k': 50}
)

# Only retrieve documents that have a relevance score

# Above a certain threshold

docsearch.as_retriever(
search_type="similarity_score_threshold",
search_kwargs={'score_threshold': 0.8}
)

# Only get the single most similar document from the dataset

docsearch.as_retriever(search_kwargs={'k': 1})

# Use a filter to only retrieve documents from a specific paper

docsearch.as_retriever(
search_kwargs={'filter': {'paper_title':'GPT-4 Technical Report'}}
)
async asearch(
query: str,
search_type: str,
\*\*kwargs: Any,
) → list[Document]
Async return docs most similar to query using a specified search type.

Parameters
:
query (str) – Input text.

search_type (str) – Type of search to perform. Can be “similarity”, “mmr”, or “similarity_score_threshold”.

\*\*kwargs (Any) – Arguments to pass to the search method.

Returns
:
List of Documents most similar to the query.

Raises
:
ValueError – If search_type is not one of “similarity”, “mmr”, or “similarity_score_threshold”.

Return type
:
list[Document]

async asimilarity_search(
query: str,
k: int = 4,
\*\*kwargs: Any,
) → list[Document]
Async return docs most similar to query.

Parameters
:
query (str) – Input text.

k (int) – Number of Documents to return. Defaults to 4.

\*\*kwargs (Any) – Arguments to pass to the search method.

Returns
:
List of Documents most similar to the query.

Return type
:
list[Document]

async asimilarity_search_by_vector(
embedding: list[float],
k: int = 4,
\*\*kwargs: Any,
) → list[Document]
Async return docs most similar to embedding vector.

Parameters
:
embedding (list[float]) – Embedding to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

\*\*kwargs (Any) – Arguments to pass to the search method.

Returns
:
List of Documents most similar to the query vector.

Return type
:
list[Document]

async asimilarity_search_with_relevance_scores(
query: str,
k: int = 4,
\*\*kwargs: Any,
) → list[tuple[Document, float]]
Async return docs and relevance scores in the range [0, 1].

0 is dissimilar, 1 is most similar.

Parameters
:
query (str) – Input text.

k (int) – Number of Documents to return. Defaults to 4.

\*\*kwargs (Any) –

kwargs to be passed to similarity search. Should include: score_threshold: Optional, a floating point value between 0 to 1 to

filter the resulting set of retrieved docs

Returns
:
List of Tuples of (doc, similarity_score)

Return type
:
list[tuple[Document, float]]

async asimilarity_search_with_score(
\*args: Any,
\*\*kwargs: Any,
) → list[tuple[Document, float]]
Async run similarity search with distance.

Parameters
:
\*args (Any) – Arguments to pass to the search method.

\*\*kwargs (Any) – Arguments to pass to the search method.

Returns
:
List of Tuples of (doc, similarity_score).

Return type
:
list[tuple[Document, float]]

classmethod connection_string_from_db_params(
driver: str,
host: str,
port: int,
database: str,
user: str,
password: str,
) → str[source]
Return connection string from database parameters.

Parameters
:
driver (str)

host (str)

port (int)

database (str)

user (str)

password (str)

Return type
:
str

create_collection() → None[source]
Return type
:
None

create_tables_if_not_exists() → None[source]
Return type
:
None

create_vector_extension() → None[source]
Return type
:
None

delete(
ids: List[str] | None = None,
collection_only: bool = False,
\*\*kwargs: Any,
) → None[source]
Delete vectors by ids or uuids.

Parameters
:
ids (List[str] | None) – List of ids to delete.

collection_only (bool) – Only delete ids in the collection.

kwargs (Any)

Return type
:
None

delete_collection() → None[source]
Return type
:
None

drop_tables() → None[source]
Return type
:
None

classmethod from_documents(
documents: List[Document],
embedding: Embeddings,
collection_name: str = 'langchain',
distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
ids: List[str] | None = None,
pre_delete_collection: bool = False,
\*,
use_jsonb: bool = False,
\*\*kwargs: Any,
) → PGVector[source]
Return VectorStore initialized from documents and embeddings. Postgres connection string is required “Either pass it as a parameter or set the PGVECTOR_CONNECTION_STRING environment variable.

Parameters
:
documents (List[Document])

embedding (Embeddings)

collection_name (str)

distance_strategy (DistanceStrategy)

ids (List[str] | None)

pre_delete_collection (bool)

use_jsonb (bool)

kwargs (Any)

Return type
:
PGVector

classmethod from_embeddings(
text_embeddings: List[Tuple[str, List[float]]],
embedding: Embeddings,
metadatas: List[dict] | None = None,
collection_name: str = 'langchain',
distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
ids: List[str] | None = None,
pre_delete_collection: bool = False,
\*\*kwargs: Any,
) → PGVector[source]
Construct PGVector wrapper from raw documents and pre- generated embeddings.

Return VectorStore initialized from documents and embeddings. Postgres connection string is required “Either pass it as a parameter or set the PGVECTOR_CONNECTION_STRING environment variable.

Example

from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()
text_embeddings = embeddings.embed_documents(texts)
text_embedding_pairs = list(zip(texts, text_embeddings))
faiss = PGVector.from_embeddings(text_embedding_pairs, embeddings)
Parameters
:
text_embeddings (List[Tuple[str, List[float]]])

embedding (Embeddings)

metadatas (List[dict] | None)

collection_name (str)

distance_strategy (DistanceStrategy)

ids (List[str] | None)

pre_delete_collection (bool)

kwargs (Any)

Return type
:
PGVector

classmethod from_existing_index(
embedding: Embeddings,
collection_name: str = 'langchain',
distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
pre_delete_collection: bool = False,
\*\*kwargs: Any,
) → PGVector[source]
Get instance of an existing PGVector store.This method will return the instance of the store without inserting any new embeddings

Parameters
:
embedding (Embeddings)

collection_name (str)

distance_strategy (DistanceStrategy)

pre_delete_collection (bool)

kwargs (Any)

Return type
:
PGVector

classmethod from_texts(
texts: List[str],
embedding: Embeddings,
metadatas: List[dict] | None = None,
collection_name: str = 'langchain',
distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
ids: List[str] | None = None,
pre_delete_collection: bool = False,
\*,
use_jsonb: bool = False,
\*\*kwargs: Any,
) → PGVector[source]
Return VectorStore initialized from texts and embeddings. Postgres connection string is required “Either pass it as a parameter or set the PGVECTOR_CONNECTION_STRING environment variable.

Parameters
:
texts (List[str])

embedding (Embeddings)

metadatas (List[dict] | None)

collection_name (str)

distance_strategy (DistanceStrategy)

ids (List[str] | None)

pre_delete_collection (bool)

use_jsonb (bool)

kwargs (Any)

Return type
:
PGVector

get_by_ids(ids: Sequence[str], /) → list[Document]
Get documents by their IDs.

The returned documents are expected to have the ID field set to the ID of the document in the vector store.

Fewer documents may be returned than requested if some IDs are not found or if there are duplicated IDs.

Users should not assume that the order of the returned documents matches the order of the input IDs. Instead, users should rely on the ID field of the returned documents.

This method should NOT raise exceptions if no documents are found for some IDs.

Parameters
:
ids (Sequence[str]) – List of ids to retrieve.

Returns
:
List of Documents.

Return type
:
list[Document]

Added in version 0.2.11.

get_collection(
session: Session,
) → Any[source]
Parameters
:
session (Session)

Return type
:
Any

classmethod get_connection_string(
kwargs: Dict[str, Any],
) → str[source]
Parameters
:
kwargs (Dict[str, Any])

Return type
:
str

max_marginal_relevance_search(
query: str,
k: int = 4,
fetch_k: int = 20,
lambda_mult: float = 0.5,
filter: Dict[str, str] | None = None,
\*\*kwargs: Any,
) → List[Document][source]
Return docs selected using the maximal marginal relevance.

Maximal marginal relevance optimizes for similarity to query AND diversity
among selected documents.

Parameters
:
query (str) – Text to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

fetch_k (int) – Number of Documents to fetch to pass to MMR algorithm. Defaults to 20.

lambda_mult (float) – Number between 0 and 1 that determines the degree of diversity among the results with 0 corresponding to maximum diversity and 1 to minimum diversity. Defaults to 0.5.

filter (Optional[Dict[str, str]]) – Filter by metadata. Defaults to None.

kwargs (Any)

Returns
:
List of Documents selected by maximal marginal relevance.

Return type
:
List[Document]

max_marginal_relevance_search_by_vector(
embedding: List[float],
k: int = 4,
fetch_k: int = 20,
lambda_mult: float = 0.5,
filter: Dict[str, str] | None = None,
\*\*kwargs: Any,
) → List[Document][source]
Return docs selected using the maximal marginal relevance
to embedding vector.

Maximal marginal relevance optimizes for similarity to query AND diversity
among selected documents.

Parameters
:
embedding (str) – Text to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

fetch_k (int) – Number of Documents to fetch to pass to MMR algorithm. Defaults to 20.

lambda_mult (float) – Number between 0 and 1 that determines the degree of diversity among the results with 0 corresponding to maximum diversity and 1 to minimum diversity. Defaults to 0.5.

filter (Optional[Dict[str, str]]) – Filter by metadata. Defaults to None.

kwargs (Any)

Returns
:
List of Documents selected by maximal marginal relevance.

Return type
:
List[Document]

max_marginal_relevance_search_with_score(
query: str,
k: int = 4,
fetch_k: int = 20,
lambda_mult: float = 0.5,
filter: dict | None = None,
\*\*kwargs: Any,
) → List[Tuple[Document, float]][source]
Return docs selected using the maximal marginal relevance with score.

Maximal marginal relevance optimizes for similarity to query AND diversity
among selected documents.

Parameters
:
query (str) – Text to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

fetch_k (int) – Number of Documents to fetch to pass to MMR algorithm. Defaults to 20.

lambda_mult (float) – Number between 0 and 1 that determines the degree of diversity among the results with 0 corresponding to maximum diversity and 1 to minimum diversity. Defaults to 0.5.

filter (Optional[Dict[str, str]]) – Filter by metadata. Defaults to None.

kwargs (Any)

Returns
:
List of Documents selected by maximal marginal
relevance to the query and score for each.

Return type
:
List[Tuple[Document, float]]

max_marginal_relevance_search_with_score_by_vector(
embedding: List[float],
k: int = 4,
fetch_k: int = 20,
lambda_mult: float = 0.5,
filter: Dict[str, str] | None = None,
\*\*kwargs: Any,
) → List[Tuple[Document, float]][source]
Return docs selected using the maximal marginal relevance with score
to embedding vector.

Maximal marginal relevance optimizes for similarity to query AND diversity
among selected documents.

Parameters
:
embedding (List[float]) – Embedding to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

fetch_k (int) – Number of Documents to fetch to pass to MMR algorithm. Defaults to 20.

lambda_mult (float) – Number between 0 and 1 that determines the degree of diversity among the results with 0 corresponding to maximum diversity and 1 to minimum diversity. Defaults to 0.5.

filter (Optional[Dict[str, str]]) – Filter by metadata. Defaults to None.

kwargs (Any)

Returns
:
List of Documents selected by maximal marginal
relevance to the query and score for each.

Return type
:
List[Tuple[Document, float]]

search(
query: str,
search_type: str,
\*\*kwargs: Any,
) → list[Document]
Return docs most similar to query using a specified search type.

Parameters
:
query (str) – Input text

search_type (str) – Type of search to perform. Can be “similarity”, “mmr”, or “similarity_score_threshold”.

\*\*kwargs (Any) – Arguments to pass to the search method.

Returns
:
List of Documents most similar to the query.

Raises
:
ValueError – If search_type is not one of “similarity”, “mmr”, or “similarity_score_threshold”.

Return type
:
list[Document]

similarity_search(
query: str,
k: int = 4,
filter: dict | None = None,
\*\*kwargs: Any,
) → List[Document][source]
Run similarity search with PGVector with distance.

Parameters
:
query (str) – Query text to search for.

k (int) – Number of results to return. Defaults to 4.

filter (Optional[Dict[str, str]]) – Filter by metadata. Defaults to None.

kwargs (Any)

Returns
:
List of Documents most similar to the query.

Return type
:
List[Document]

similarity_search_by_vector(
embedding: List[float],
k: int = 4,
filter: dict | None = None,
\*\*kwargs: Any,
) → List[Document][source]
Return docs most similar to embedding vector.

Parameters
:
embedding (List[float]) – Embedding to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

filter (Optional[Dict[str, str]]) – Filter by metadata. Defaults to None.

kwargs (Any)

Returns
:
List of Documents most similar to the query vector.

Return type
:
List[Document]

similarity_search_with_relevance_scores(
query: str,
k: int = 4,
\*\*kwargs: Any,
) → list[tuple[Document, float]]
Return docs and relevance scores in the range [0, 1].

0 is dissimilar, 1 is most similar.

Parameters
:
query (str) – Input text.

k (int) – Number of Documents to return. Defaults to 4.

\*\*kwargs (Any) –

kwargs to be passed to similarity search. Should include: score_threshold: Optional, a floating point value between 0 to 1 to

filter the resulting set of retrieved docs.

Returns
:
List of Tuples of (doc, similarity_score).

Return type
:
list[tuple[Document, float]]

similarity_search_with_score(
query: str,
k: int = 4,
filter: dict | None = None,
) → List[Tuple[Document, float]][source]
Return docs most similar to query.

Parameters
:
query (str) – Text to look up documents similar to.

k (int) – Number of Documents to return. Defaults to 4.

filter (Optional[Dict[str, str]]) – Filter by metadata. Defaults to None.

Returns
:
List of Documents most similar to the query and score for each.

Return type
:
List[Tuple[Document, float]]

similarity_search_with_score_by_vector(
embedding: List[float],
k: int = 4,
filter: dict | None = None,
) → List[Tuple[Document, float]][source]
Parameters
:
embedding (List[float])

k (int)

filter (dict | None)

Return type
:
List[Tuple[Document, float]]

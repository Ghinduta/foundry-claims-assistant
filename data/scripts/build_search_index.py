"""Upload the policy documents and build the AI Search pipeline over them (integrated vectorization).

Blob container -> data source -> indexer (markdown parsing: one search document per heading section)
-> skillset (embed each section) -> index.
The search service connects to Storage and to the embedding model with its own managed identity;
this script connects to everything with your az login. No keys anywhere.
"""

import time
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    AzureOpenAIEmbeddingSkill,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    DataSourceCredentials,
    FieldMapping,
    HnswAlgorithmConfiguration,
    IndexingParameters,
    IndexingParametersConfiguration,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchIndexer,
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection,
    SearchIndexerDataSourceType,
    SearchIndexerSkillset,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import QueryType, VectorizableTextQuery
from azure.storage.blob import BlobServiceClient

import azure_env

DATA = Path(__file__).resolve().parent.parent
NAME = "policy-docs"  # container, data source, index, skillset and indexer all share it
EMBEDDING = "text-embedding-3-small"
DIMENSIONS = 1536


def upload_documents(env: azure_env.AzureEnv, credential) -> None:
    container = BlobServiceClient(env.storage_blob_endpoint, credential).get_container_client(NAME)
    for path in sorted((DATA / "policy-docs").glob("*.md")):
        container.upload_blob(path.name, path.read_bytes(), overwrite=True)
    print(f"Uploaded {len(list((DATA / 'policy-docs').glob('*.md')))} documents to container '{NAME}'")


def build_index(env: azure_env.AzureEnv) -> SearchIndex:
    # One search document per heading section. The indexer generates chunk_id from the file and section position.
    fields = [
        SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True),
        SearchField(name="file_name", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="title", type=SearchFieldDataType.String, searchable=True),  # the document's # heading
        SearchField(name="section", type=SearchFieldDataType.String, searchable=True),  # the ## heading, "" if none
        SearchField(name="chunk", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True, vector_search_dimensions=DIMENSIONS, vector_search_profile_name="default"),
    ]
    # The vectorizer embeds the query text at search time, with the same model that embedded the chunks.
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        vectorizers=[AzureOpenAIVectorizer(
            vectorizer_name="aoai",
            parameters=AzureOpenAIVectorizerParameters(
                resource_url=env.openai_endpoint, deployment_name=EMBEDDING, model_name=EMBEDDING),
        )],
        profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw", vectorizer_name="aoai")],
    )
    semantic = SemanticSearch(configurations=[SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="section"),
            content_fields=[SemanticField(field_name="chunk")],
            keywords_fields=[SemanticField(field_name="title")]),
    )])
    return SearchIndex(name=NAME, fields=fields, vector_search=vector_search, semantic_search=semantic)


def build_skillset(env: azure_env.AzureEnv) -> SearchIndexerSkillset:
    # Markdown parsing already made one enrichment document per section, so there is nothing to split.
    embed = AzureOpenAIEmbeddingSkill(
        context="/document",
        resource_url=env.openai_endpoint,
        deployment_name=EMBEDDING,
        model_name=EMBEDDING,
        dimensions=DIMENSIONS,
        inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
        outputs=[OutputFieldMappingEntry(name="embedding", target_name="text_vector")],
    )
    return SearchIndexerSkillset(name=NAME, skills=[embed])


def build_indexer() -> SearchIndexer:
    return SearchIndexer(
        name=NAME, data_source_name=NAME, skillset_name=NAME, target_index_name=NAME,
        # Split each file at its headings (# and ##): one search document per section.
        parameters=IndexingParameters(configuration=IndexingParametersConfiguration(
            parsing_mode="markdown", markdown_parsing_submode="oneToMany", markdown_header_depth="h2")),
        field_mappings=[
            FieldMapping(source_field_name="/content", target_field_name="chunk"),
            FieldMapping(source_field_name="/sections/h1", target_field_name="title"),
            FieldMapping(source_field_name="/sections/h2", target_field_name="section"),
            FieldMapping(source_field_name="metadata_storage_name", target_field_name="file_name"),
        ],
        output_field_mappings=[FieldMapping(source_field_name="/document/text_vector", target_field_name="text_vector")],
    )


def wait_for_indexer(indexers: SearchIndexerClient):
    while True:
        status = indexers.get_indexer_status(NAME).last_result
        if status and status.status not in ("inProgress", "reset"):
            return status
        time.sleep(5)


def run_indexer(indexers: SearchIndexerClient) -> None:
    wait_for_indexer(indexers)  # a newly created indexer starts a run by itself; only one run at a time
    indexers.reset_indexer(NAME)  # re-read every blob, not only changed ones
    indexers.run_indexer(NAME)
    time.sleep(5)
    status = wait_for_indexer(indexers)
    print(f"Indexer: {status.status}, {status.item_count} documents, {status.failed_item_count} failed")
    for error in status.errors[:5]:
        print("  error:", error.key, error.error_message)
    for warning in status.warnings[:5]:
        print("  warning:", warning.key, warning.message)


def try_query(env: azure_env.AzureEnv, credential) -> None:
    question = "Which documents do I need if my car was stolen?"
    results = SearchClient(env.search_endpoint, NAME, credential).search(
        search_text=question,  # keyword part of the hybrid query
        vector_queries=[VectorizableTextQuery(text=question, k_nearest_neighbors=5, fields="text_vector")],
        query_type=QueryType.SEMANTIC,
        semantic_configuration_name="default",
        select=["file_name", "section"],
        top=3,
    )
    print(f"\nHybrid + semantic query: {question}")
    for r in results:
        print(f"  {r['@search.reranker_score']:.2f}  {r['file_name']}  ## {r['section']}")


def main() -> None:
    env = azure_env.load()
    credential = DefaultAzureCredential()
    upload_documents(env, credential)

    # Rebuild from scratch: oneToMany never deletes sections that were removed from a file.
    indexes = SearchIndexClient(env.search_endpoint, credential)
    indexers = SearchIndexerClient(env.search_endpoint, credential)
    indexers.delete_indexer(NAME)
    indexes.delete_index(NAME)
    indexes.create_index(build_index(env))
    indexers.create_or_update_data_source_connection(SearchIndexerDataSourceConnection(
        name=NAME,
        type=SearchIndexerDataSourceType.AZURE_BLOB,
        # A resource id instead of a connection string: the search service signs in with its managed identity.
        credentials=DataSourceCredentials(connection_string=f"ResourceId={env.storage_resource_id};"),
        container=SearchIndexerDataContainer(name=NAME),
    ))
    indexers.create_or_update_skillset(build_skillset(env))
    indexers.create_or_update_indexer(build_indexer())
    run_indexer(indexers)
    try_query(env, credential)


if __name__ == "__main__":
    main()

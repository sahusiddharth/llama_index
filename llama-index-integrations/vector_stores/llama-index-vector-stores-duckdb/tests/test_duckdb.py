import pytest
from typing import List
import importlib.util

from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery, FilterOperator
from llama_index.vector_stores.duckdb import DuckDBVectorStore
from llama_index.vector_stores.duckdb import DuckDBVectorStore
from llama_index.core.vector_stores.types import (
    MetadataFilter,
    MetadataFilters,
    FilterCondition,
)


def test_duckdb_installed():
    assert importlib.util.find_spec("duckdb") is not None


@pytest.fixture(scope="module")
def text_node_list() -> List[TextNode]:
    return [
        TextNode(
            text="lorem ipsum",
            id_="c330d77f-90bd-4c51-9ed2-57d8d693b3b0",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-0")},
            metadata={
                "author": "Stephen King",
                "theme": "Friendship",
            },
            embedding=[1.0, 0.0, 0.0],
        ),
        TextNode(
            text="lorem ipsum",
            id_="c3d1e1dd-8fb4-4b8f-b7ea-7fa96038d39d",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-1")},
            metadata={
                "director": "Francis Ford Coppola",
                "theme": "Mafia",
            },
            embedding=[0.0, 1.0, 0.0],
        ),
        TextNode(
            text="lorem ipsum",
            id_="c3ew11cd-8fb4-4b8f-b7ea-7fa96038d39d",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-2")},
            metadata={
                "director": "Christopher Nolan",
            },
            embedding=[0.0, 0.0, 1.0],
        ),
        TextNode(
            text="I was taught that the way of progress was neither swift nor easy.",
            id_="0b31ae71-b797-4e88-8495-031371a7752e",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-3")},
            metadata={
                "author": "Marie Curie",
            },
            embedding=[0.0, 0.0, 0.9],
        ),
        TextNode(
            text=(
                "The important thing is not to stop questioning."
                + " Curiosity has its own reason for existing."
            ),
            id_="bd2e080b-159a-4030-acc3-d98afd2ba49b",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-4")},
            metadata={
                "author": "Albert Einstein",
            },
            embedding=[0.0, 0.0, 0.5],
        ),
        TextNode(
            text=(
                "I am no bird; and no net ensnares me;"
                + " I am a free human being with an independent will."
            ),
            id_="f658de3b-8cef-4d1c-8bed-9a263c907251",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-5")},
            metadata={
                "author": "Charlotte Bronte",
            },
            embedding=[0.0, 0.0, 0.3],
        ),
        TextNode(
            text=("中文用户来了。"),
            id_="943ef4e5-b5bc-4b85-b0d7-bc4fb25417db",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-6")},
            metadata={
                "author": "Ava Wilson",
            },
            embedding=[0.3, 0.3, 0.3],
        ),
        TextNode(
            text=(
                "Vector stores contain embedding vectors of ingested document chunks (and sometimes the document chunks as well)."
            ),
            id_="e8f0c6cb-8d35-4240-a60a-b57070b3960f",
            relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="test-7")},
            metadata={
                "author": "Emma Johnson",
            },
            embedding=[0.9, 0.3, 0.3],
            excluded_embed_metadata_keys=["excluded_embed"],
            excluded_llm_metadata_keys=["excluded_llm", "metadata", "keys"],
        ),
    ]


@pytest.fixture(scope="module")
def vector_store() -> DuckDBVectorStore:
    return DuckDBVectorStore(embed_dim=3)


def test_instance_creation_from_memory(
    vector_store: DuckDBVectorStore,
) -> None:
    assert isinstance(vector_store, DuckDBVectorStore)
    assert vector_store.database_name == ":memory:"


def test_duckdb_add_and_query(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
) -> None:
    vector_store.add(text_node_list)

    nodes = vector_store.get_nodes(node_ids=["c330d77f-90bd-4c51-9ed2-57d8d693b3b0"])
    assert len(nodes) == 1

    res = vector_store.query(
        VectorStoreQuery(query_embedding=[1.1, 0.0, 0.0], similarity_top_k=1)
    )
    assert res.nodes
    assert res.nodes[0].node_id == "c330d77f-90bd-4c51-9ed2-57d8d693b3b0"
    assert res.nodes[0].get_content() == "lorem ipsum"
    assert res.nodes[0].metadata.get("author") == "Stephen King"
    assert res.nodes[0].metadata.get("theme") == "Friendship"

    assert res.nodes[0].excluded_embed_metadata_keys == []
    assert res.nodes[0].excluded_llm_metadata_keys == []
    assert res.nodes[0].source_node is not None
    assert res.nodes[0].source_node.node_id == "test-0"

    res = vector_store.query(
        VectorStoreQuery(query_embedding=[0.9, 0.3, 0.3], similarity_top_k=1)
    )
    assert res.nodes
    assert res.nodes[0].node_id == "e8f0c6cb-8d35-4240-a60a-b57070b3960f"
    assert (
        res.nodes[0].get_content()
        == "Vector stores contain embedding vectors of ingested document chunks (and sometimes the document chunks as well)."
    )
    assert res.nodes[0].metadata.get("author") == "Emma Johnson"
    assert res.nodes[0].excluded_embed_metadata_keys == ["excluded_embed"]
    assert res.nodes[0].excluded_llm_metadata_keys == [
        "excluded_llm",
        "metadata",
        "keys",
    ]
    assert res.nodes[0].source_node is not None
    assert res.nodes[0].source_node.node_id == "test-7"


def test_duckdb_from_local_and_params():
    store1 = DuckDBVectorStore.from_local(database_path=":memory:", embed_dim=3)
    assert isinstance(store1, DuckDBVectorStore)
    store2 = DuckDBVectorStore.from_params(embed_dim=3)
    assert isinstance(store2, DuckDBVectorStore)


def test_delete_nodes(vector_store: DuckDBVectorStore, text_node_list: List[TextNode]):
    vector_store.clear()
    vector_store.add(text_node_list[:2])
    node_ids = [n.node_id for n in text_node_list[:2]]
    assert len(vector_store.get_nodes(node_ids=node_ids)) == 2
    vector_store.delete_nodes(node_ids=[node_ids[0]])
    nodes = vector_store.get_nodes(node_ids=node_ids)
    assert len(nodes) == 1
    assert nodes[0].node_id == node_ids[1]


def test_clear(vector_store: DuckDBVectorStore, text_node_list: List[TextNode]):
    vector_store.add(text_node_list[:2])
    assert len(vector_store.get_nodes()) >= 2
    vector_store.clear()
    assert len(vector_store.get_nodes()) == 0


def test_delete_by_ref_doc_id(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    test_node = text_node_list[0]
    test_node_id = test_node.node_id
    assert test_node.source_node is not None

    test_node_source_document = test_node.source_node
    test_node_source_document_id = test_node_source_document.node_id

    vector_store.add([test_node])
    nodes = vector_store.get_nodes()
    assert vector_store.get_nodes(node_ids=[test_node_id])
    vector_store.delete(ref_doc_id=test_node_source_document_id)
    assert not vector_store.get_nodes(node_ids=[test_node_id])


def test_get_nodes_with_metadata_filters(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list[:2])

    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value="Stephen King", operator=FilterOperator.EQ
            ),
        ],
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 1
    assert nodes[0].metadata.get("author") == "Stephen King"


def test_lazy_table_initialization():
    store = DuckDBVectorStore(embed_dim=3)

    nodes = store.get_nodes(node_ids=["any"])
    assert len(nodes) == 0


def test_filter_operator_ne(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value="Stephen King", operator=FilterOperator.NE
            )
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 5
    # Only the second node has a different author
    assert all(n.metadata.get("author") != "Stephen King" for n in nodes)


def test_filter_operator_in(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)

    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author",
                value=["Marie Curie", "Stephen King"],
                operator=FilterOperator.IN,
            )
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 2
    assert any(n.metadata.get("author") == "Stephen King" for n in nodes)
    assert any(n.metadata.get("author") == "Marie Curie" for n in nodes)


def test_filter_operator_nin(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value=["Stephen King"], operator=FilterOperator.NIN
            )
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 5
    assert all(n.metadata.get("author") != "Stephen King" for n in nodes)


def test_filter_text_match(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="theme", value="Friend", operator=FilterOperator.TEXT_MATCH
            )
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 1
    assert any("Friend" in n.metadata.get("theme", "") for n in nodes)


def test_filter_text_match_insensitive(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="theme",
                value="friendship",
                operator=FilterOperator.TEXT_MATCH_INSENSITIVE,
            )
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 1
    assert any(n.metadata.get("theme", "").lower() == "friendship" for n in nodes)


def test_filter_is_empty_on_none(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    # Add a node with an empty field
    node = TextNode(
        text="empty test",
        id_="empty-node",
        relationships={},
        metadata={"empty_field": None},
        embedding=[0.1, 0.2, 0.3],
    )
    vector_store.add([node])
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="empty_field", value=None, operator=FilterOperator.IS_EMPTY
            )
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 1
    assert any(n.node_id == "empty-node" for n in nodes)


def test_filter_is_empty_on_missing_key(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    # Add a node with an empty field
    node = TextNode(
        text="empty test",
        id_="empty-node",
        relationships={},
        metadata={},
        embedding=[0.1, 0.2, 0.3],
    )
    vector_store.add([node])
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="empty_field", value=None, operator=FilterOperator.IS_EMPTY
            )
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 1
    assert any(n.node_id == "empty-node" for n in nodes)


def test_filter_and_condition(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value="Stephen King", operator=FilterOperator.EQ
            ),
            MetadataFilter(key="theme", value="Friendship", operator=FilterOperator.EQ),
        ],
        condition=FilterCondition.AND,
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 1
    assert nodes[0].metadata.get("author") == "Stephen King"
    assert nodes[0].metadata.get("theme") == "Friendship"


def test_filter_or_condition(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value="Stephen King", operator=FilterOperator.EQ
            ),
            MetadataFilter(key="theme", value="Mafia", operator=FilterOperator.EQ),
        ],
        condition=FilterCondition.OR,
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 2
    # Should match either author or theme
    assert any(n.metadata.get("author") == "Stephen King" for n in nodes)
    assert any(n.metadata.get("theme") == "Mafia" for n in nodes)


def test_filter_not_condition_excludes_null(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    # Based on our list, this doesn't exclude any values except where author is null
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value="Stephen King", operator=FilterOperator.EQ
            ),
            MetadataFilter(key="theme", value="Mafia", operator=FilterOperator.EQ),
        ],
        condition=FilterCondition.NOT,
    )
    nodes = vector_store.get_nodes(filters=filters)

    assert len(nodes) == 6

    assert any(n.metadata.get("author") == "Stephen King" for n in nodes)
    assert all(n.metadata.get("director") is None for n in nodes)


def test_filter_not_condition(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value="Stephen King", operator=FilterOperator.EQ
            ),
            MetadataFilter(key="theme", value="Friendship", operator=FilterOperator.EQ),
        ],
        condition=FilterCondition.NOT,
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 6

    assert all(n.metadata.get("theme") != "Friendship" for n in nodes)


def test_filter_nested_and_or_condition(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(
                key="author", value="Stephen King", operator=FilterOperator.EQ
            ),
            MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="theme", value="Mafia", operator=FilterOperator.EQ
                    ),
                    MetadataFilter(
                        key="theme", value="Friendship", operator=FilterOperator.EQ
                    ),
                ],
                condition=FilterCondition.OR,
            ),
        ],
        condition=FilterCondition.AND,
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 1
    # Should match either author or theme
    assert any(n.metadata.get("author") == "Stephen King" for n in nodes)
    assert any(n.metadata.get("theme") == "Friendship" for n in nodes)


def test_filter_missing_key(
    vector_store: DuckDBVectorStore, text_node_list: List[TextNode]
):
    vector_store.clear()
    vector_store.add(text_node_list)
    filters = MetadataFilters(
        filters=[
            MetadataFilter(key="not_a_key", value="foo", operator=FilterOperator.EQ)
        ]
    )
    nodes = vector_store.get_nodes(filters=filters)
    assert len(nodes) == 0

import os
import httpx
import base64
from pathlib import Path
from unittest.mock import patch

from mistralai import ToolCall, ImageURLChunk, TextChunk
import pytest

from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.llms import ChatMessage, ImageBlock, TextBlock
from llama_index.core.tools import FunctionTool
from llama_index.llms.mistralai import MistralAI
from llama_index.llms.mistralai.base import to_mistral_chunks


def test_llm_class():
    names_of_base_classes = [b.__name__ for b in MistralAI.__mro__]
    assert BaseLLM.__name__ in names_of_base_classes


def search(query: str) -> str:
    """Search for information about a query."""
    return f"Results for {query}"


search_tool = FunctionTool.from_defaults(
    fn=search, name="search_tool", description="A tool for searching information"
)


@pytest.mark.skipif(
    os.environ.get("MISTRAL_API_KEY") is None, reason="MISTRAL_API_KEY not set"
)
def test_tool_required():
    llm = MistralAI()
    result = llm.chat_with_tools(
        tools=[search_tool],
        user_msg="What is the capital of France?",
        tool_required=True,
    )
    additional_kwargs = result.message.additional_kwargs
    assert "tool_calls" in additional_kwargs
    tool_calls = additional_kwargs["tool_calls"]
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert isinstance(tool_call, ToolCall)
    assert tool_call.function.name == "search_tool"
    assert "query" in tool_call.function.arguments


@patch("mistralai.Mistral")
def test_prepare_chat_with_tools_tool_required(mock_mistral_client):
    """Test that tool_required is correctly passed to the API request when True."""
    # Mock the API key and client
    with patch("llama_index.llms.mistralai.base.get_from_param_or_env") as mock_get_env:
        mock_get_env.return_value = "fake-api-key"

        llm = MistralAI()

        # Test with tool_required=True
        result = llm._prepare_chat_with_tools(tools=[search_tool], tool_required=True)

        assert result["tool_choice"] == "required"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["type"] == "function"
        assert result["tools"][0]["function"]["name"] == "search_tool"


@patch("mistralai.Mistral")
def test_prepare_chat_with_tools_tool_not_required(mock_mistral_client):
    """Test that tool_required is correctly passed to the API request when False."""
    # Mock the API key and client
    with patch("llama_index.llms.mistralai.base.get_from_param_or_env") as mock_get_env:
        mock_get_env.return_value = "fake-api-key"

        llm = MistralAI()

        # Test with tool_required=False (default)
        result = llm._prepare_chat_with_tools(
            tools=[search_tool],
        )

        assert result["tool_choice"] == "auto"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["type"] == "function"
        assert result["tools"][0]["function"]["name"] == "search_tool"


@pytest.mark.skipif(
    os.environ.get("MISTRAL_API_KEY") is None, reason="MISTRAL_API_KEY not set"
)
def test_thinking():
    llm = MistralAI(model="magistral-small-latest", show_thinking=True)

    # It will sometimes not think, so we need to guard
    result = llm.complete("What is the capital of France?")
    if "thinking" in result.additional_kwargs:
        assert result.additional_kwargs["thinking"] is not None
        assert result.additional_kwargs["thinking"] != ""
        assert "<think>" in result.text

    result = llm.chat(
        [ChatMessage(role="user", content="What is the capital of France?")]
    )
    if "thinking" in result.message.additional_kwargs:
        assert result.message.additional_kwargs["thinking"] is not None
        assert result.message.additional_kwargs["thinking"] != ""
        assert "<think>" in result.message.content

    result = llm.stream_complete("What is the capital of France?")
    resp = None
    for resp in result:
        pass

    assert resp is not None
    if "thinking" in resp.additional_kwargs:
        assert resp.additional_kwargs["thinking"] is not None
        assert resp.additional_kwargs["thinking"] != ""
        assert "<think>" in resp.text

    result = llm.stream_chat(
        [ChatMessage(role="user", content="What is the capital of France?")]
    )
    resp = None
    for resp in result:
        pass

    assert resp is not None
    if "thinking" in resp.message.additional_kwargs:
        assert resp.message.additional_kwargs["thinking"] is not None
        assert resp.message.additional_kwargs["thinking"] != ""
        assert "<think>" in resp.message.content


@pytest.mark.skipif(
    os.environ.get("MISTRAL_API_KEY") is None, reason="MISTRAL_API_KEY not set"
)
def test_thinking_not_shown():
    llm = MistralAI(model="magistral-small-latest", show_thinking=False)

    result = llm.complete("What is the capital of France?")

    if "thinking" in result.additional_kwargs:
        assert result.additional_kwargs["thinking"] is None
        assert result.additional_kwargs["thinking"] is None
        assert "<think>" not in result.text

    response_gen = llm.stream_complete("What is the capital of France?")
    resp = None
    for resp in response_gen:
        assert "<think>" not in resp.text

    if "thinking" in resp.additional_kwargs:
        assert resp.additional_kwargs["thinking"] is None
        assert "<think>" not in resp.text


@pytest.fixture()
def image_url() -> str:
    return "https://astrabert.github.io/hophop-science/images/whale_doing_science.png"


def test_to_mistral_chunks(tmp_path: Path, image_url: str) -> None:
    blocks_with_url = [
        TextBlock(text="Provide an alternative text for this image"),
        ImageBlock(url=image_url),
    ]
    content = httpx.get(image_url).content
    expected_b64 = base64.b64encode(content).decode("utf-8")
    image_path = tmp_path / "test_image.png"
    image_path.write_bytes(content)
    blocks_with_path = [
        TextBlock(text="Provide an alternative text for this image"),
        ImageBlock(path=image_path, image_mimetype="image/png"),
    ]
    chunks_with_url = to_mistral_chunks(blocks_with_url)
    assert isinstance(chunks_with_url[0], TextChunk)
    assert chunks_with_url[0].text == blocks_with_url[0].text
    assert isinstance(chunks_with_url[1], ImageURLChunk)
    assert isinstance(chunks_with_url[1].image_url, str)
    assert chunks_with_url[1].image_url == str(blocks_with_url[1].url._url)
    chunks_with_path = to_mistral_chunks(blocks_with_path)
    assert isinstance(chunks_with_path[0], TextChunk)
    assert chunks_with_path[0].text == blocks_with_path[0].text
    assert isinstance(chunks_with_path[1], ImageURLChunk)
    assert isinstance(chunks_with_path[1].image_url, str)
    assert chunks_with_path[1].image_url == f"data:image/png;base64,{expected_b64}"

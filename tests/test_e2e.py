import pytest
from unittest.mock import MagicMock
from src.graph.graph import build_graph
from src.graph.state import AgentState
from src.graph.schemas import RouterDecision

@pytest.fixture(autouse=True)
def mock_embedding_e2e(mocker):
    # Mock embedding generator so we don't call Gemini API for indexing/querying
    mock_func = mocker.patch("src.rag.core.get_embedding")
    mock_func.side_effect = lambda text: [0.1] * 768  # ChromaDB default/custom dimension (Gemini = 768)
    return mock_func


def test_e2e_scraping_and_answering(mocker):
    # 1. Mock Router LLM to route to scraper_node
    mock_router_llm = MagicMock()
    mock_router_llm.invoke.return_value = RouterDecision(
        reasoning="User provided a direct URL",
        next_node="scraper_node",
        confidence=1.0
    )
    mock_chat_router = mocker.patch("src.graph.router.ChatGoogleGenerativeAI")
    mock_chat_router.return_value.with_structured_output.return_value = mock_router_llm
    
    # 2. Mock Generator LLM to return answer
    mock_generator_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Dựa trên bài viết, Python 3.12 cải thiện hiệu năng 5-10%."
    mock_generator_llm.invoke.return_value = mock_response
    mock_chat_generator = mocker.patch("src.graph.generator.ChatGoogleGenerativeAI")
    mock_chat_generator.return_value = mock_generator_llm
    
    # 3. Mock scraper network fetch to return mock XenForo thread HTML
    mock_html = """
    <div class="p-title"><h1 class="p-title-value">Python 3.12 Performance</h1></div>
    <article class="message message--post" data-content="post-111">
        <span class="username">Admin</span>
        <div class="bbWrapper">Hiệu năng cải thiện khoảng 5-10% nhờ tối ưu hóa trình thông dịch.</div>
        <time class="u-dt" datetime="2023-11-14">Nov 14</time>
    </article>
    """
    mock_fetch = mocker.patch("src.graph.nodes.scraper_node.fetch_voz_thread", return_value=mock_html)
    
    # 4. Compile the graph
    app = build_graph()
    
    # 5. Run the graph end-to-end
    initial_state = AgentState(
        question="Python 3.12 có gì mới?",
        loop_count=0,
        url="https://voz.vn/t/python-3-12.111/",
        retrieved_context=None,
        answer=None,
        route_decision=None
    )
    
    final_state = app.invoke(initial_state)
    
    # 6. Assertions
    # Router was not called because direct URL bypasses it
    mock_chat_router.assert_not_called()

    
    # Scraper was called with URL
    mock_fetch.assert_called_once_with("https://voz.vn/t/python-3-12.111/")
    
    # Generator was called
    mock_chat_generator.assert_called_once()
    
    # Final answer is populated correctly
    assert final_state["route_decision"] == "scraper_node"
    assert "Thread Title: Python 3.12 Performance" in final_state["retrieved_context"]
    assert "Hiệu năng cải thiện khoảng" in final_state["retrieved_context"]
    assert final_state["answer"] == "Dựa trên bài viết, Python 3.12 cải thiện hiệu năng 5-10%."

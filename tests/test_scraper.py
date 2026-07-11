import pytest
from unittest.mock import MagicMock
from src.scraper.core import parse_forum_html, fetch_forum_page, fetch_voz_thread
from src.scraper.exceptions import ForumBlockedException

def test_parse_forum_html_filters_noise():
    html_mock = """
    <div class="post">
        <div class="op">This is the original post with valuable technical content about Python.</div>
        <div class="comment">Chấm</div>
        <div class="comment">This is a valid long comment discussing the technical aspects in detail.</div>
        <div class="comment">Upp</div>
        <div class="comment">Hóng</div>
        <div class="signature">My signature here - don't read this</div>
    </div>
    """
    result = parse_forum_html(html_mock)
    assert "original post" in result
    assert "valid long comment" in result
    
    # Đảm bảo rác đã bị lọc
    assert "Chấm" not in result
    assert "Upp" not in result
    assert "Hóng" not in result
    assert "signature" not in result

def test_fetch_forum_page_detects_block(mocker):
    # Mock _do_fetch trả về trang bị block
    mocker.patch('src.scraper.core._do_fetch', return_value="<title>Just a moment...</title> Cloudflare ray ID")
    
    with pytest.raises(ForumBlockedException):
        fetch_forum_page("https://voz.vn/t/some-thread")

def test_parse_forum_html_adaptive_structure():
    # Cấu trúc HTML bị thay đổi nhưng vẫn phải tìm được nội dung
    html_mock_changed = """
    <article class="post-container">
        <div class="message-body">This is the valid content.</div>
    </article>
    """
    result = parse_forum_html(html_mock_changed)
    assert "valid content" in result


def test_fetch_voz_thread_success(mocker):
    mock_fetcher = mocker.patch("src.scraper.core.StealthyFetcher")
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = "<html>Voz Thread</html>"
    mock_fetcher.return_value.fetch.return_value = mock_response

    html = fetch_voz_thread("https://voz.vn/t/some-thread.123/")
    assert html == "<html>Voz Thread</html>"
    mock_fetcher.return_value.fetch.assert_called_once_with(
        "https://voz.vn/t/some-thread.123/", timeout=15000, solve_cloudflare=True
    )


def test_fetch_voz_thread_blocks(mocker):
    mock_fetcher = mocker.patch("src.scraper.core.StealthyFetcher")
    mock_response = MagicMock()
    mock_response.status = 403
    mock_response.text = "Cloudflare security check"
    mock_fetcher.return_value.fetch.return_value = mock_response

    # Patch wait to return 0 to make test run fast
    mocker.patch("src.scraper.core.fetch_voz_thread.retry.wait", return_value=0)

    with pytest.raises(ForumBlockedException):
        fetch_voz_thread("https://voz.vn/t/some-thread.123/")


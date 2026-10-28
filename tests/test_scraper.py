import pytest
from src.scraper import core
from src.scraper.core import parse_forum_html, fetch_voz_thread, load_saved_thread
from src.scraper.exceptions import ForumBlockedException


@pytest.fixture(autouse=True)
def fresh_fetch_state(mocker):
    core._robots.clear()
    core._last_request_at.clear()
    mocker.patch("src.scraper.core.fetch_voz_thread.retry.wait", return_value=0)

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

def test_parse_forum_html_adaptive_structure():
    # Cấu trúc HTML bị thay đổi nhưng vẫn phải tìm được nội dung
    html_mock_changed = """
    <article class="post-container">
        <div class="message-body">This is the valid content.</div>
    </article>
    """
    result = parse_forum_html(html_mock_changed)
    assert "valid content" in result


def fake_site(mocker, robots=(200, ""), page=(200, "<html>Voz Thread</html>")):
    """Patch the HTTP layer: robots.txt and the thread page return the given (status, body)."""
    return mocker.patch(
        "src.scraper.core._http_get",
        side_effect=lambda url, timeout=15: robots if url.endswith("/robots.txt") else page,
    )


def test_fetch_voz_thread_success(mocker):
    http = fake_site(mocker)

    html = fetch_voz_thread("https://voz.vn/t/some-thread.123/")
    assert html == "<html>Voz Thread</html>"
    assert [c.args[0] for c in http.call_args_list] == [
        "https://voz.vn/robots.txt",
        "https://voz.vn/t/some-thread.123/",
    ]


def test_fetch_voz_thread_does_not_retry_a_challenge(mocker):
    http = fake_site(mocker, page=(403, "<title>Just a moment...</title>"))

    with pytest.raises(ForumBlockedException, match="ingest"):
        fetch_voz_thread("https://voz.vn/t/some-thread.123/")
    assert http.call_count == 2  # robots.txt and one page request, no retries


def test_normal_page_with_cloudflare_script_is_not_a_challenge(mocker):
    page = '<script src="/cdn-cgi/challenge-platform/scripts/jsd/main.js"></script><div class="bbWrapper">Access Denied error on deploy</div>'
    fake_site(mocker, page=(200, page))

    assert fetch_voz_thread("https://voz.vn/t/some-thread.123/") == page


def test_fetch_voz_thread_respects_robots(mocker):
    http = fake_site(mocker, robots=(200, "User-agent: *\nDisallow: /t/"))

    with pytest.raises(ForumBlockedException, match="robots.txt"):
        fetch_voz_thread("https://voz.vn/t/some-thread.123/")
    assert http.call_count == 1  # the page itself is never requested


def test_fetch_voz_thread_retries_server_errors(mocker):
    responses = iter([(200, ""), (503, "busy"), (200, "<html>ok</html>")])
    mocker.patch("src.scraper.core._http_get", side_effect=lambda url, timeout=15: next(responses))

    assert fetch_voz_thread("https://voz.vn/t/some-thread.123/") == "<html>ok</html>"


def test_requests_to_the_same_host_are_rate_limited(mocker):
    clock = iter([100.0, 100.0, 100.5, 102.0])
    mocker.patch("src.scraper.core.time.monotonic", side_effect=lambda: next(clock))
    sleep = mocker.patch("src.scraper.core.time.sleep")

    core._throttle("voz.vn")
    core._throttle("voz.vn")
    sleep.assert_called_once_with(pytest.approx(core.MIN_REQUEST_INTERVAL - 0.5))


def test_load_saved_thread_reads_canonical_url(tmp_path):
    page = tmp_path / "thread.html"
    page.write_text(
        '<html><head><link rel="canonical" href="https://voz.vn/t/abc.42/"></head><body></body></html>',
        encoding="utf-8",
    )

    html, url = load_saved_thread(str(page))
    assert "canonical" in html
    assert url == "https://voz.vn/t/abc.42/"


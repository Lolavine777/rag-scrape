import pytest
from unittest.mock import MagicMock
from src.scraper.voz_search import parse_search_results, search_voz_threads

MOCK_SEARCH_RESULTS_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="block-container">
        <!-- Result 1 -->
        <div class="contentRow">
            <div class="contentRow-main">
                <h3 class="contentRow-title">
                    <a href="https://voz.vn/threads/tin-tuc-python-3-12.876543/">Tin tức Python 3.12 mới nhất</a>
                </h3>
                <div class="contentRow-minor">
                    <ul class="listInline listInline--bullet">
                        <li>Thành viên: Admin</li>
                        <li>Ngày đăng: Nov 14, 2023</li>
                        <li>Diễn đàn: Chuyện trò linh tinh</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Result 2 -->
        <div class="contentRow">
            <div class="contentRow-main">
                <h3 class="contentRow-title">
                    <a href="https://voz.vn/threads/hoc-python-o-dau-tot.123456/">Học Python ở đâu tốt?</a>
                </h3>
                <div class="contentRow-minor">
                    <ul class="listInline listInline--bullet">
                        <li>Thành viên: dev_pro</li>
                        <li>Diễn đàn: Lập trình & CNTT</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Google redirect url wrapper mock -->
        <div class="contentRow">
            <div class="contentRow-main">
                <h3 class="contentRow-title">
                    <a href="/url?q=https://voz.vn/threads/tu-hoc-python-101.999/&sa=U">Tự học Python 101</a>
                </h3>
            </div>
        </div>

        <!-- Noise/Spam row without thread link -->
        <div class="contentRow">
            <div class="contentRow-main">
                <h3 class="contentRow-title">Không có link thớt ở đây</h3>
            </div>
        </div>
    </div>
</body>
</html>
"""

def test_parse_search_results():
    results = parse_search_results(MOCK_SEARCH_RESULTS_HTML)
    assert len(results) == 3
    
    assert results[0]["title"] == "Tin tức Python 3.12 mới nhất"
    assert results[0]["url"] == "https://voz.vn/threads/tin-tuc-python-3-12.876543/"
    
    assert results[1]["title"] == "Học Python ở đâu tốt?"
    assert results[1]["url"] == "https://voz.vn/threads/hoc-python-o-dau-tot.123456/"

    assert results[2]["title"] == "Tự học Python 101"
    assert results[2]["url"] == "https://voz.vn/threads/tu-hoc-python-101.999/"

def test_search_voz_threads_success(mocker):
    # Mock StealthyFetcher
    mock_fetcher = mocker.patch("src.scraper.voz_search.StealthyFetcher")
    
    # Mock response
    mock_response = MagicMock()
    mock_response.text = MOCK_SEARCH_RESULTS_HTML
    mock_response.html_content = MOCK_SEARCH_RESULTS_HTML
    mock_response.status = 200
    
    mock_fetcher_instance = mock_fetcher.return_value
    mock_fetcher_instance.fetch.return_value = mock_response
    
    threads = search_voz_threads("python")
    
    assert len(threads) == 3
    assert threads[0]["title"] == "Tin tức Python 3.12 mới nhất"
    mock_fetcher_instance.fetch.assert_called_once()
    assert "q=site%3Avoz.vn+python" in mock_fetcher_instance.fetch.call_args[0][0]

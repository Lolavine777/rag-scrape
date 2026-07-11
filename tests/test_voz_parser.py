import pytest
from src.scraper.voz_parser import parse_voz_thread_title, parse_voz_posts, format_voz_thread

MOCK_VOZ_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Thảo luận về Python 3.12 trên Voz</title>
</head>
<body>
    <div class="p-title">
        <h1 class="p-title-value">Thảo luận về Python 3.12</h1>
    </div>
    
    <div class="block-container">
        <!-- Post 1 -->
        <article class="message message--post" data-content="post-123456">
            <div class="message-inner">
                <div class="message-cell message-cell--user">
                    <h4 class="message-name">
                        <a href="/members/user-admin.1/" class="username" data-user-id="1">AdminUser</a>
                    </h4>
                </div>
                <div class="message-cell message-cell--main">
                    <header class="message-attribution">
                        <a href="/threads/123/post-123456">
                            <time class="u-dt" data-time="1700000000" datetime="2023-11-14T21:46:40+0700">Nov 14, 2023</time>
                        </a>
                    </header>
                    <div class="message-content">
                        <div class="bbWrapper">
                            Python 3.12 ra mắt với nhiều cải tiến hiệu năng đáng giá.
                            Các bạn thấy thế nào?
                        </div>
                    </div>
                </div>
            </div>
        </article>

        <!-- Post 2 (short/spam to be filtered or kept based on rules) -->
        <article class="message message--post" data-content="post-123457">
            <div class="message-inner">
                <div class="message-cell message-cell--user">
                    <h4 class="message-name">
                        <span class="username">SpamUser</span>
                    </h4>
                </div>
                <div class="message-cell message-cell--main">
                    <header class="message-attribution">
                        <a href="/threads/123/post-123457">
                            <time class="u-dt" data-time="1700000060" datetime="2023-11-14T21:47:40+0700">Nov 14, 2023</time>
                        </a>
                    </header>
                    <div class="message-content">
                        <div class="bbWrapper">
                            Chấm
                        </div>
                    </div>
                </div>
            </div>
        </article>

        <!-- Post 3 -->
        <article class="message message--post" data-content="post-123458">
            <div class="message-inner">
                <div class="message-cell message-cell--user">
                    <h4 class="message-name">
                        <a href="/members/dev-pro.2/" class="username">dev_pro</a>
                    </h4>
                </div>
                <div class="message-cell message-cell--main">
                    <header class="message-attribution">
                        <a href="/threads/123/post-123458">
                            <time class="u-dt" data-time="1700000120" datetime="2023-11-14T21:48:40+0700">Nov 14, 2023</time>
                        </a>
                    </header>
                    <div class="message-content">
                        <div class="bbWrapper">
                            Hiệu năng cải thiện khoảng 5-10% nhờ tối ưu hóa trình thông dịch.
                            Rất đáng nâng cấp!
                        </div>
                    </div>
                </div>
            </div>
        </article>
    </div>
</body>
</html>
"""

def test_parse_voz_thread_title():
    title = parse_voz_thread_title(MOCK_VOZ_HTML)
    assert title == "Thảo luận về Python 3.12"

def test_parse_voz_posts():
    posts = parse_voz_posts(MOCK_VOZ_HTML)
    assert len(posts) == 2  # The short "Chấm" post (length < 10) should be filtered out
    
    assert posts[0]["id"] == "post-123456"
    assert posts[0]["author"] == "AdminUser"
    assert posts[0]["timestamp"] == "2023-11-14T21:46:40+0700"
    assert "cải tiến hiệu năng" in posts[0]["content"]

    assert posts[1]["id"] == "post-123458"
    assert posts[1]["author"] == "dev_pro"
    assert posts[1]["timestamp"] == "2023-11-14T21:48:40+0700"
    assert "tối ưu hóa trình thông dịch" in posts[1]["content"]

def test_format_voz_thread():
    formatted_text = format_voz_thread(MOCK_VOZ_HTML)
    assert "Thread Title: Thảo luận về Python 3.12" in formatted_text
    assert "[Post #post-123456 by AdminUser at 2023-11-14T21:46:40+0700]" in formatted_text
    assert "cải tiến hiệu năng" in formatted_text
    assert "dev_pro" in formatted_text
    assert "Chấm" not in formatted_text  # Filtered

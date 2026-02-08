"""
测试 scraper.py 模块
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
from src.scraper import ArticleScraper


class TestArticleScraper:
    """测试 ArticleScraper 类"""

    @pytest.fixture
    def scraper(self, mock_config):
        """创建scraper实例"""
        return ArticleScraper(mock_config)

    @pytest.fixture
    def sample_html(self):
        """示例HTML内容"""
        return """
        <html>
        <head>
            <title>Test Article</title>
            <meta name="author" content="John Doe">
            <meta property="article:published_time" content="2026-01-20">
            <meta name="description" content="This is a test article">
        </head>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>This is the article content.</p>
                <img src="/images/test.jpg" alt="Test Image">
                <img src="https://example.com/logo.png" alt="Logo">
            </article>
        </body>
        </html>
        """

    @pytest.mark.unit
    @patch('src.scraper.requests.get')
    def test_fetch_url_success(self, mock_get, scraper):
        """测试成功获取URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response

        result = scraper.fetch_url("https://example.com")

        assert result == "<html><body>Test</body></html>"
        mock_get.assert_called_once()

    @pytest.mark.unit
    @patch('src.scraper.requests.get')
    def test_fetch_url_failure(self, mock_get, scraper):
        """测试URL获取失败"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            scraper.fetch_url("https://example.com")

    @pytest.mark.unit
    def test_extract_article(self, scraper, sample_html):
        """测试文章提取"""
        result = scraper.extract_article(sample_html, "https://example.com")

        assert 'title' in result
        assert 'content_html' in result
        assert 'author' in result
        assert 'publish_date' in result
        assert result['author'] == "John Doe"
        assert result['publish_date'] == "2026-01-20"

    @pytest.mark.unit
    def test_convert_to_markdown(self, scraper):
        """测试HTML转Markdown"""
        html = "<h1>Title</h1><p>Content</p>"
        result = scraper.convert_to_markdown(html)

        assert "Title" in result
        assert "Content" in result
        assert "#" in result  # Markdown标题标记

    @pytest.mark.unit
    def test_extract_images(self, scraper, sample_html):
        """测试图片提取"""
        result = scraper.extract_images(sample_html, "https://example.com")

        assert isinstance(result, list)
        # 应该提取到图片,但过滤掉logo
        assert len(result) >= 1
        # 相对URL应该被转换为绝对URL
        assert any("https://example.com" in url for url in result)

    @pytest.mark.unit
    def test_extract_author(self, scraper):
        """测试作者提取"""
        html = '<html><head><meta name="author" content="Test Author"></head></html>'
        soup = BeautifulSoup(html, 'lxml')
        result = scraper._extract_author(soup)

        assert result == "Test Author"

    @pytest.mark.unit
    def test_extract_author_not_found(self, scraper):
        """测试作者未找到"""
        html = '<html><head></head></html>'
        soup = BeautifulSoup(html, 'lxml')
        result = scraper._extract_author(soup)

        assert result is None

    @pytest.mark.unit
    def test_extract_date(self, scraper):
        """测试日期提取"""
        html = '<html><head><meta property="article:published_time" content="2026-01-20"></head></html>'
        soup = BeautifulSoup(html, 'lxml')
        result = scraper._extract_date(soup)

        assert result == "2026-01-20"

    @pytest.mark.unit
    def test_extract_description(self, scraper):
        """测试描述提取"""
        html = '<html><head><meta name="description" content="Test description"></head></html>'
        soup = BeautifulSoup(html, 'lxml')
        result = scraper._extract_description(soup)

        assert result == "Test description"

    @pytest.mark.unit
    def test_is_valid_image_url_valid(self, scraper):
        """测试有效图片URL"""
        assert scraper._is_valid_image_url("https://example.com/image.jpg") is True
        assert scraper._is_valid_image_url("https://example.com/photo.png") is True

    @pytest.mark.unit
    def test_is_valid_image_url_invalid(self, scraper):
        """测试无效图片URL"""
        assert scraper._is_valid_image_url("https://example.com/logo.png") is False
        assert scraper._is_valid_image_url("https://example.com/icon.svg") is False
        assert scraper._is_valid_image_url("data:image/png;base64,xxx") is False

    @pytest.mark.unit
    @patch.object(ArticleScraper, 'fetch_url')
    @patch.object(ArticleScraper, 'extract_article')
    @patch.object(ArticleScraper, 'convert_to_markdown')
    @patch.object(ArticleScraper, 'extract_images')
    def test_fetch_and_extract(self, mock_images, mock_markdown, mock_extract, mock_fetch, scraper):
        """测试完整流程"""
        mock_fetch.return_value = "<html>test</html>"
        mock_extract.return_value = {
            'title': 'Test',
            'content_html': '<p>Content</p>',
            'author': 'Author',
            'publish_date': '2026-01-20',
            'description': 'Desc'
        }
        mock_markdown.return_value = "# Test\n\nContent"
        mock_images.return_value = ["https://example.com/img.jpg"]

        result = scraper.fetch_and_extract("https://example.com/article")

        assert 'title' in result
        assert 'content_markdown' in result
        assert 'image_urls' in result
        assert result['title'] == 'Test'
        assert len(result['image_urls']) == 1

    @pytest.mark.unit
    def test_should_use_dynamic_by_domain_enabled(self, mock_config):
        """测试域名匹配触发动态渲染"""
        mock_config['scraper']['dynamic_render'] = {
            'enabled': True,
            'domains': ['huggingface.co', 'gradio.app'],
            'min_content_length': 500
        }
        scraper = ArticleScraper(mock_config)

        # 模拟 Playwright 可用
        import src.scraper as scraper_module
        original_available = scraper_module.PLAYWRIGHT_AVAILABLE
        scraper_module.PLAYWRIGHT_AVAILABLE = True

        try:
            assert scraper._should_use_dynamic_by_domain("https://huggingface.co/spaces/test") is True
            assert scraper._should_use_dynamic_by_domain("https://www.gradio.app/demo") is True
            assert scraper._should_use_dynamic_by_domain("https://example.com/article") is False
        finally:
            scraper_module.PLAYWRIGHT_AVAILABLE = original_available

    @pytest.mark.unit
    def test_should_use_dynamic_by_domain_disabled(self, mock_config):
        """测试动态渲染禁用时不触发"""
        mock_config['scraper']['dynamic_render'] = {
            'enabled': False,
            'domains': ['huggingface.co'],
            'min_content_length': 500
        }
        scraper = ArticleScraper(mock_config)

        assert scraper._should_use_dynamic_by_domain("https://huggingface.co/spaces/test") is False

    @pytest.mark.unit
    def test_needs_dynamic_fallback_short_content(self, mock_config):
        """测试内容过短时触发动态回退"""
        mock_config['scraper']['dynamic_render'] = {
            'enabled': True,
            'domains': [],
            'min_content_length': 500
        }
        scraper = ArticleScraper(mock_config)

        # 模拟 Playwright 可用
        import src.scraper as scraper_module
        original_available = scraper_module.PLAYWRIGHT_AVAILABLE
        scraper_module.PLAYWRIGHT_AVAILABLE = True

        try:
            # 短内容应该触发回退
            short_html = "<html><body><p>Short</p></body></html>"
            assert scraper._needs_dynamic_fallback(short_html) is True

            # 长内容不应该触发回退
            long_content = "x" * 1000
            long_html = f"<html><body><article><p>{long_content}</p></article></body></html>"
            assert scraper._needs_dynamic_fallback(long_html) is False
        finally:
            scraper_module.PLAYWRIGHT_AVAILABLE = original_available

    @pytest.mark.unit
    def test_get_content_length(self, scraper):
        """测试内容长度计算"""
        html = "<html><body><article><p>Hello World</p></article></body></html>"
        length = scraper._get_content_length(html)
        assert length > 0

    @pytest.mark.unit
    def test_get_content_length_empty(self, scraper):
        """测试空内容长度计算"""
        html = "<html><body></body></html>"
        length = scraper._get_content_length(html)
        assert length == 0

    @pytest.mark.unit
    @patch('src.scraper.requests.get')
    def test_fetch_static_success(self, mock_get, scraper):
        """测试静态抓取成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test Content</body></html>"
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response

        result = scraper._fetch_static("https://example.com")

        assert result == "<html><body>Test Content</body></html>"
        mock_get.assert_called_once()

    @pytest.mark.unit
    def test_fetch_dynamic_not_available(self, mock_config):
        """测试 Playwright 未安装时抛出错误"""
        mock_config['scraper']['dynamic_render'] = {
            'enabled': True,
            'domains': [],
            'min_content_length': 500
        }
        scraper = ArticleScraper(mock_config)

        # 模拟 Playwright 不可用
        import src.scraper as scraper_module
        original_available = scraper_module.PLAYWRIGHT_AVAILABLE
        scraper_module.PLAYWRIGHT_AVAILABLE = False

        try:
            with pytest.raises(RuntimeError, match="Playwright is not installed"):
                scraper._fetch_dynamic("https://example.com")
        finally:
            scraper_module.PLAYWRIGHT_AVAILABLE = original_available

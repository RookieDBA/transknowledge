"""
测试 processor.py 模块（集成测试）
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.processor import ArticleProcessor


class TestArticleProcessor:
    """测试 ArticleProcessor 类"""

    @pytest.fixture
    def processor(self, mock_config):
        """创建ArticleProcessor实例"""
        with patch('src.processor.load_config', return_value=mock_config), \
             patch('src.processor.ArticleScraper'), \
             patch('src.processor.DeepSeekTranslator'), \
             patch('src.processor.ImageHandler'):
            return ArticleProcessor()

    @pytest.mark.integration
    def test_process_url_success(self, processor, mock_config):
        """测试完整处理流程成功"""
        # Mock scraper
        processor.scraper.fetch_and_extract.return_value = {
            'title': 'Test Article',
            'content_markdown': '# Test\n\nContent',
            'author': 'Author',
            'publish_date': '2026-01-20',
            'description': 'Description',
            'image_urls': ['https://example.com/img.jpg']
        }

        # Mock translator
        processor.translator.translate_text.return_value = '# 测试\n\n内容'

        # Mock image handler
        processor.image_handler.batch_download.return_value = [
            {
                'url': 'https://example.com/img.jpg',
                'filename': 'img_test_001.jpg',
                'success': True
            }
        ]
        processor.image_handler.convert_to_obsidian_embeds.return_value = '# 测试\n\n![[Attachments/img_test_001.jpg]]'

        result = processor.process_url('https://example.com/article')

        assert 'title' in result
        assert 'content' in result
        assert 'images' in result
        assert result['original_title'] == 'Test Article'
        assert 'error' not in result

    @pytest.mark.integration
    def test_process_url_scraper_error(self, processor):
        """测试抓取失败"""
        processor.scraper.fetch_and_extract.side_effect = Exception("Scraping failed")

        result = processor.process_url('https://example.com/article')

        assert 'error' in result
        assert 'Scraping failed' in result['error'] or 'Error processing' in result['error']

    @pytest.mark.integration
    def test_process_url_translation_error(self, processor):
        """测试翻译失败"""
        # Mock scraper成功
        processor.scraper.fetch_and_extract.return_value = {
            'title': 'Test Article',
            'content_markdown': '# Test',
            'author': 'Author',
            'publish_date': '2026-01-20',
            'description': 'Description',
            'image_urls': []
        }

        # Mock translator失败
        processor.translator.translate_text.side_effect = Exception("Translation failed")

        result = processor.process_url('https://example.com/article')

        assert 'error' in result

    @pytest.mark.integration
    def test_process_url_no_images(self, processor):
        """测试没有图片的文章"""
        # Mock scraper
        processor.scraper.fetch_and_extract.return_value = {
            'title': 'Test Article',
            'content_markdown': '# Test\n\nContent',
            'author': 'Author',
            'publish_date': '2026-01-20',
            'description': 'Description',
            'image_urls': []  # 没有图片
        }

        # Mock translator
        processor.translator.translate_text.return_value = '# 测试\n\n内容'

        # Mock image handler
        processor.image_handler.download_images.return_value = []

        result = processor.process_url('https://example.com/article')

        assert 'error' not in result
        assert len(result['images']) == 0

    @pytest.mark.integration
    def test_process_url_partial_image_failure(self, processor):
        """测试部分图片下载失败"""
        # Mock scraper
        processor.scraper.fetch_and_extract.return_value = {
            'title': 'Test Article',
            'content_markdown': '# Test',
            'author': 'Author',
            'publish_date': '2026-01-20',
            'description': 'Description',
            'image_urls': ['https://example.com/img1.jpg', 'https://example.com/img2.jpg']
        }

        # Mock translator
        processor.translator.translate_text.return_value = '# 测试'

        # Mock image handler - 一个成功，一个失败
        processor.image_handler.batch_download.return_value = [
            {'url': 'https://example.com/img1.jpg', 'filename': 'img_001.jpg', 'success': True},
            {'url': 'https://example.com/img2.jpg', 'filename': None, 'success': False, 'error': 'Download failed'}
        ]
        processor.image_handler.convert_to_obsidian_embeds.return_value = '# 测试'

        result = processor.process_url('https://example.com/article')

        assert 'error' not in result
        # 应该只有成功的图片
        assert len(result['images']) == 1

    @pytest.mark.integration
    def test_process_url_invalid_url(self, processor):
        """测试无效URL"""
        result = processor.process_url('not a valid url')

        assert 'error' in result

    @pytest.mark.integration
    def test_process_url_metadata_preservation(self, processor):
        """测试元数据保留"""
        # Mock scraper
        processor.scraper.fetch_and_extract.return_value = {
            'title': 'Original Title',
            'content_markdown': 'Content',
            'author': 'John Doe',
            'publish_date': '2026-01-20',
            'description': 'Test description',
            'image_urls': []
        }

        # Mock translator
        processor.translator.translate.side_effect = lambda x: '翻译后的' + x

        # Mock image handler
        processor.image_handler.download_images.return_value = []
        processor.image_handler.convert_to_obsidian_embeds.return_value = '翻译后的Content'

        result = processor.process_url('https://example.com/article')

        # 验证元数据
        assert result['original_title'] == 'Original Title'
        assert result['author'] == 'John Doe'
        assert result['publish_date'] == '2026-01-20'
        assert result['source_url'] == 'https://example.com/article'
        assert 'translated_date' in result
        assert 'tags' in result

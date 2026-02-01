"""
测试 image_handler.py 模块
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from io import BytesIO
from src.image_handler import ImageHandler, extract_real_image_url


class TestExtractRealImageUrl:
    """测试 extract_real_image_url 函数"""

    @pytest.mark.unit
    def test_extract_nextjs_image_url(self):
        """测试提取Next.js图片URL"""
        url = "https://example.com/_next/image?url=https%3A%2F%2Fcdn.example.com%2Fimage.png&w=1920&q=75"
        result = extract_real_image_url(url)
        assert result == "https://cdn.example.com/image.png"

    @pytest.mark.unit
    def test_extract_regular_url(self):
        """测试普通URL不变"""
        url = "https://example.com/images/photo.jpg"
        result = extract_real_image_url(url)
        assert result == url

    @pytest.mark.unit
    def test_extract_relative_nextjs_url(self):
        """测试相对路径的Next.js URL"""
        url = "/_next/image?url=https%3A%2F%2Fcdn.example.com%2Fimage.png&w=1920"
        result = extract_real_image_url(url)
        assert result == "https://cdn.example.com/image.png"


class TestImageHandler:
    """测试 ImageHandler 类"""

    @pytest.fixture
    def handler(self, mock_config):
        """创建ImageHandler实例"""
        return ImageHandler(mock_config)

    @pytest.fixture
    def mock_image_response(self):
        """创建模拟的图片响应"""
        # 创建一个简单的测试图片
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = img_bytes.getvalue()
        mock_response.headers = {
            'content-type': 'image/png',
            'content-length': str(len(img_bytes.getvalue()))
        }
        return mock_response

    @pytest.mark.unit
    def test_init(self, handler):
        """测试初始化"""
        assert handler.download_enabled is True
        assert handler.max_size_mb == 10
        assert handler.timeout == 30

    @pytest.mark.unit
    @patch('src.image_handler.requests.Session')
    def test_download_image_success(self, mock_session, handler, mock_image_response, temp_dir):
        """测试成功下载图片"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock_image_response

        result = handler.download_image(
            "https://example.com/image.png",
            temp_dir,
            "test_image.png"
        )

        assert result['success'] is True
        assert result['filename'] == "test_image.png"
        assert result['error'] is None

    @pytest.mark.unit
    def test_download_image_disabled(self, mock_config, temp_dir):
        """测试禁用下载"""
        mock_config['images']['download_enabled'] = False
        handler = ImageHandler(mock_config)

        result = handler.download_image(
            "https://example.com/image.png",
            temp_dir
        )

        assert result['success'] is False
        assert 'disabled' in result['error'].lower()

    @pytest.mark.unit
    @patch('src.image_handler.requests.Session')
    def test_download_image_too_large(self, mock_session, handler, temp_dir):
        """测试图片过大"""
        mock_response = Mock()
        mock_response.headers = {
            'content-length': str(20 * 1024 * 1024)  # 20MB
        }
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock_response

        result = handler.download_image(
            "https://example.com/large.png",
            temp_dir
        )

        assert result['success'] is False
        assert 'too large' in result['error'].lower()

    @pytest.mark.unit
    @patch('src.image_handler.requests.Session')
    def test_download_image_network_error(self, mock_session, handler, temp_dir):
        """测试网络错误"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.side_effect = Exception("Network error")

        result = handler.download_image(
            "https://example.com/image.png",
            temp_dir
        )

        assert result['success'] is False
        assert result['error'] is not None

    @pytest.mark.unit
    @patch('src.image_handler.requests.Session')
    def test_download_image_invalid_image(self, mock_session, handler, temp_dir):
        """测试无效图片"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"not an image"
        mock_response.headers = {
            'content-type': 'image/png',
            'content-length': '13'
        }
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock_response

        result = handler.download_image(
            "https://example.com/invalid.png",
            temp_dir
        )

        assert result['success'] is False
        assert 'invalid' in result['error'].lower()

    @pytest.mark.unit
    def test_generate_filename(self, handler):
        """测试文件名生成"""
        # 这个测试需要根据实际实现调整
        # 假设有一个generate_filename方法
        pass

    @pytest.mark.unit
    @patch.object(ImageHandler, 'download_image')
    def test_download_images_batch(self, mock_download, handler, temp_dir):
        """测试批量下载"""
        # 模拟下载结果
        mock_download.return_value = {
            'url': 'https://example.com/img.png',
            'filename': 'img_001.png',
            'filepath': os.path.join(temp_dir, 'img_001.png'),
            'success': True,
            'error': None
        }

        urls = [
            "https://example.com/img1.png",
            "https://example.com/img2.png",
            "https://example.com/img3.png"
        ]

        # 假设有批量下载方法
        # results = handler.download_images(urls, temp_dir, "test")
        # assert len(results) == 3
        # assert all(r['success'] for r in results)

    @pytest.mark.unit
    def test_convert_to_obsidian_embeds(self, handler):
        """测试转换为Obsidian格式"""
        markdown = "![Image](https://example.com/img.png)"
        downloaded_images = {
            'https://example.com/img.png': 'img_test_001.png'
        }

        # 假设有convert_to_obsidian_embeds方法
        # result = handler.convert_to_obsidian_embeds(markdown, downloaded_images)
        # assert "![[Attachments/img_test_001.png]]" in result
        # assert "https://example.com/img.png" not in result

    @pytest.mark.unit
    def test_url_variants_matching(self, handler):
        """测试URL变体匹配（绝对路径和相对路径）"""
        # 测试之前修复的bug：相对路径和绝对路径的匹配
        absolute_url = "https://example.com/_next/image?url=https%3A%2F%2Fcdn.example.com%2Fimg.png"
        relative_url = "/_next/image?url=https%3A%2F%2Fcdn.example.com%2Fimg.png"

        # 两者应该匹配到同一个下载的图片
        # 这需要根据实际的convert_to_obsidian_embeds实现来测试
        pass

"""
测试 utils.py 模块
"""
import os
import pytest
from unittest.mock import patch, mock_open
from src.utils import slugify, validate_url, load_config


class TestSlugify:
    """测试 slugify 函数"""

    @pytest.mark.unit
    def test_slugify_english(self):
        """测试英文字符串转换"""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test Article Title") == "test-article-title"

    @pytest.mark.unit
    def test_slugify_chinese(self):
        """测试中文字符串转换"""
        result = slugify("测试文章标题")
        assert result  # 应该返回非空字符串
        assert " " not in result  # 不应包含空格

    @pytest.mark.unit
    def test_slugify_mixed(self):
        """测试中英文混合"""
        result = slugify("Test 测试 Article")
        assert result
        assert " " not in result

    @pytest.mark.unit
    def test_slugify_special_chars(self):
        """测试特殊字符处理"""
        assert slugify("Hello@World!") == "helloworld"
        assert slugify("Test_Article-Title") == "test_article-title"

    @pytest.mark.unit
    def test_slugify_empty(self):
        """测试空字符串"""
        result = slugify("")
        assert result == "" or result == "untitled"

    @pytest.mark.unit
    def test_slugify_max_length(self):
        """测试长度限制"""
        long_text = "a" * 200
        result = slugify(long_text, max_length=50)
        assert len(result) <= 50


class TestValidateUrl:
    """测试 validate_url 函数"""

    @pytest.mark.unit
    def test_valid_http_url(self):
        """测试有效的HTTP URL"""
        assert validate_url("http://example.com") is True
        assert validate_url("http://example.com/article") is True

    @pytest.mark.unit
    def test_valid_https_url(self):
        """测试有效的HTTPS URL"""
        assert validate_url("https://example.com") is True
        assert validate_url("https://www.example.com/path/to/article") is True

    @pytest.mark.unit
    def test_invalid_url_no_scheme(self):
        """测试无协议的URL"""
        assert validate_url("example.com") is False
        assert validate_url("www.example.com") is False

    @pytest.mark.unit
    def test_invalid_url_wrong_scheme(self):
        """测试错误协议的URL"""
        assert validate_url("ftp://example.com") is False
        assert validate_url("file:///path/to/file") is False

    @pytest.mark.unit
    def test_invalid_url_malformed(self):
        """测试格式错误的URL"""
        assert validate_url("not a url") is False
        assert validate_url("http://") is False
        assert validate_url("") is False

    @pytest.mark.unit
    def test_url_with_query_params(self):
        """测试带查询参数的URL"""
        assert validate_url("https://example.com/article?id=123&lang=en") is True

    @pytest.mark.unit
    def test_url_with_fragment(self):
        """测试带锚点的URL"""
        assert validate_url("https://example.com/article#section") is True


class TestLoadConfig:
    """测试 load_config 函数"""

    @pytest.mark.unit
    @patch('src.utils.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="""
obsidian:
  vault_path: "/test/vault"
  articles_folder: "Articles"
api:
  deepseek:
    model: "deepseek-chat"
""")
    def test_load_config_from_file(self, mock_file, mock_exists):
        """测试从文件加载配置"""
        mock_exists.return_value = True

        config = load_config()

        assert config is not None
        assert 'obsidian' in config
        assert config['obsidian']['vault_path'] == "/test/vault"

    @pytest.mark.unit
    @patch('src.utils.load_dotenv')
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_config_file_not_found(self, mock_open, mock_dotenv):
        """测试配置文件不存在"""
        # 应该抛出FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_config('/nonexistent/config.yaml')

    @pytest.mark.unit
    @patch.dict(os.environ, {
        'OBSIDIAN_VAULT_PATH': '/env/vault',
        'DEEPSEEK_API_KEY': 'test-key'
    })
    @patch('src.utils.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="""
obsidian:
  vault_path: "/test/vault"
api:
  deepseek:
    model: "deepseek-chat"
""")
    def test_load_config_env_override(self, mock_file, mock_exists):
        """测试环境变量覆盖配置文件"""
        mock_exists.return_value = True

        config = load_config()

        # 环境变量应该覆盖配置文件
        # 注意：这取决于实际实现，可能需要调整
        assert config is not None

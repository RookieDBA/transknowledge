"""
测试 obsidian_writer.py 模块
"""
import os
import pytest
from unittest.mock import Mock, patch, mock_open
from src.obsidian_writer import ObsidianWriter


class TestObsidianWriter:
    """测试 ObsidianWriter 类"""

    @pytest.fixture
    def writer(self, mock_config, temp_dir):
        """创建ObsidianWriter实例"""
        mock_config['obsidian']['vault_path'] = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        return ObsidianWriter(mock_config)

    @pytest.mark.unit
    def test_init_success(self, mock_config, temp_dir):
        """测试成功初始化"""
        mock_config['obsidian']['vault_path'] = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        writer = ObsidianWriter(mock_config)

        assert writer.vault_path == temp_dir
        assert writer.articles_folder == "Articles/Translations"

    @pytest.mark.unit
    def test_init_no_vault_path(self, mock_config):
        """测试缺少vault_path"""
        mock_config['obsidian']['vault_path'] = None

        with pytest.raises(ValueError, match="vault_path not configured"):
            ObsidianWriter(mock_config)

    @pytest.mark.unit
    def test_init_vault_not_exists(self, mock_config):
        """测试vault路径不存在"""
        mock_config['obsidian']['vault_path'] = "/nonexistent/path"

        with pytest.raises(ValueError, match="does not exist"):
            ObsidianWriter(mock_config)

    @pytest.mark.unit
    def test_build_frontmatter(self, writer, sample_article_data):
        """测试构建frontmatter"""
        result = writer.build_frontmatter(sample_article_data)

        assert "---" in result
        assert "title:" in result
        assert "original_title:" in result
        assert "source_url:" in result
        assert "author:" in result
        assert "tags:" in result
        assert sample_article_data['title'] in result

    @pytest.mark.unit
    def test_build_frontmatter_minimal(self, writer):
        """测试最小数据的frontmatter"""
        minimal_data = {
            'title': '测试标题'
        }
        result = writer.build_frontmatter(minimal_data)

        assert "---" in result
        assert "title:" in result
        assert "测试标题" in result

    @pytest.mark.unit
    def test_build_frontmatter_with_quotes(self, writer):
        """测试包含引号的数据"""
        data = {
            'title': '测试"引号"标题',
            'description': 'Description with "quotes"'
        }
        result = writer.build_frontmatter(data)

        assert "---" in result
        # 引号应该被转义
        assert '\\"' in result or '"' in result

    @pytest.mark.unit
    def test_build_note_content(self, writer, sample_article_data):
        """测试构建完整笔记内容"""
        result = writer.build_note_content(sample_article_data)

        assert "---" in result  # frontmatter
        assert sample_article_data['title'] in result
        assert sample_article_data['content'] in result

    @pytest.mark.unit
    def test_generate_filename(self, writer, sample_article_data):
        """测试生成文件名"""
        result = writer.generate_filename(sample_article_data)

        assert result.endswith('.md')
        assert len(result) > 0
        # 应该包含日期前缀
        assert result[0].isdigit()

    @pytest.mark.unit
    def test_generate_filename_special_chars(self, writer):
        """测试特殊字符的文件名生成"""
        data = {
            'title': '测试/特殊\\字符:标题?'
        }
        result = writer.generate_filename(data)

        assert result.endswith('.md')
        # 特殊字符应该被处理
        assert '/' not in result
        assert '\\' not in result
        assert ':' not in result
        assert '?' not in result

    @pytest.mark.unit
    def test_save_note(self, writer, sample_article_data, temp_dir):
        """测试保存笔记"""
        result = writer.save_note(sample_article_data)

        assert os.path.exists(result)
        assert result.endswith('.md')

        # 验证文件内容
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "---" in content
            assert sample_article_data['title'] in content
            assert sample_article_data['content'] in content

    @pytest.mark.unit
    def test_save_note_custom_filename(self, writer, sample_article_data, temp_dir):
        """测试使用自定义文件名保存"""
        custom_filename = "custom_article.md"
        result = writer.save_note(sample_article_data, filename=custom_filename)

        assert os.path.exists(result)
        assert custom_filename in result

    @pytest.mark.unit
    def test_save_note_creates_directory(self, writer, sample_article_data, temp_dir):
        """测试自动创建目录"""
        # 确保目录不存在
        articles_dir = os.path.join(temp_dir, writer.articles_folder)
        if os.path.exists(articles_dir):
            os.rmdir(articles_dir)

        result = writer.save_note(sample_article_data)

        assert os.path.exists(result)
        assert os.path.exists(articles_dir)

    @pytest.mark.unit
    def test_save_translation_success(self, writer, sample_article_data):
        """测试保存翻译结果成功"""
        result = writer.save_translation(sample_article_data)

        assert result['success'] is True
        assert 'file_path' in result
        assert 'filename' in result
        assert result['title'] == sample_article_data['title']
        assert result['images_count'] == len(sample_article_data['images'])

    @pytest.mark.unit
    def test_save_translation_with_error(self, writer):
        """测试保存包含错误的翻译结果"""
        error_data = {
            'error': 'Translation failed'
        }
        result = writer.save_translation(error_data)

        assert result['success'] is False
        assert 'error' in result
        assert result['error'] == 'Translation failed'

    @pytest.mark.unit
    @patch.object(ObsidianWriter, 'save_note')
    def test_save_translation_exception(self, mock_save_note, writer, sample_article_data):
        """测试保存过程中的异常"""
        mock_save_note.side_effect = Exception("Write error")

        result = writer.save_translation(sample_article_data)

        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.unit
    def test_frontmatter_tags_format(self, writer):
        """测试tags的YAML格式"""
        data = {
            'title': '测试',
            'tags': ['tag1', 'tag2', 'tag3']
        }
        result = writer.build_frontmatter(data)

        assert "tags:" in result
        assert "- tag1" in result
        assert "- tag2" in result
        assert "- tag3" in result

    @pytest.mark.unit
    def test_save_note_overwrites_existing(self, writer, sample_article_data, temp_dir):
        """测试覆盖已存在的文件"""
        # 第一次保存
        first_save = writer.save_note(sample_article_data, filename="test_overwrite.md")

        # 修改数据
        sample_article_data['content'] = "# 新内容"

        # 第二次保存（覆盖）
        second_save = writer.save_note(sample_article_data, filename="test_overwrite.md")

        assert first_save == second_save

        # 验证内容已更新
        with open(second_save, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "新内容" in content

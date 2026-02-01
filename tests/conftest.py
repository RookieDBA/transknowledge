"""
pytest 配置和共享fixtures
"""
import os
import tempfile
import pytest
from pathlib import Path


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_config():
    """模拟配置字典"""
    return {
        'obsidian': {
            'vault_path': '/tmp/test_vault',
            'articles_folder': 'Articles/Translations',
            'attachments_folder': 'Attachments'
        },
        'api': {
            'deepseek': {
                'api_key': 'test-api-key-for-testing',  # 添加测试用的API密钥
                'model': 'deepseek-chat',
                'max_tokens': 4096,
                'temperature': 0.3,
                'base_url': 'https://api.deepseek.com'
            }
        },
        'translation': {
            'source_language': 'English',
            'target_language': 'Chinese',
            'preserve_code_blocks': True,
            'chunk_size': 3000
        },
        'images': {
            'download_enabled': True,
            'max_size_mb': 10,
            'timeout': 30,
            'use_obsidian_embeds': True
        }
    }


@pytest.fixture
def sample_article_data():
    """示例文章数据"""
    return {
        'title': '测试文章标题',
        'original_title': 'Test Article Title',
        'content': '# 测试文章\n\n这是测试内容。\n\n![[Attachments/img_test_001.png]]',
        'source_url': 'https://example.com/article',
        'author': 'Test Author',
        'publish_date': '2026-01-20',
        'translated_date': '2026-02-01T10:00:00',
        'description': '这是一篇测试文章',
        'images': ['img_test_001.png'],
        'tags': ['translation', 'test']
    }

"""
Obsidian 写入模块
直接将翻译结果保存为 Obsidian Markdown 文件
"""
import os
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from .utils import slugify


class ObsidianWriter:
    """Obsidian 文件写入器"""

    def __init__(self, config: Dict):
        """
        初始化写入器

        Args:
            config: 配置字典
        """
        self.config = config
        self.obsidian_config = config.get('obsidian', {})
        self.vault_path = self.obsidian_config.get('vault_path')
        self.articles_folder = self.obsidian_config.get('articles_folder', 'Articles/Translations')

        if not self.vault_path:
            raise ValueError("Obsidian vault_path not configured")

        if not os.path.exists(self.vault_path):
            raise ValueError(f"Obsidian vault path does not exist: {self.vault_path}")

    def build_frontmatter(self, data: Dict) -> str:
        """
        构建 Obsidian frontmatter (YAML 格式的 properties)

        Args:
            data: 文章数据字典

        Returns:
            frontmatter 字符串
        """
        frontmatter_lines = ["---"]

        # 标题
        if data.get('title'):
            frontmatter_lines.append(f"title: \"{data['title']}\"")

        # 原标题
        if data.get('original_title'):
            frontmatter_lines.append(f"original_title: \"{data['original_title']}\"")

        # 来源 URL
        if data.get('source_url'):
            frontmatter_lines.append(f"source_url: {data['source_url']}")

        # 作者
        if data.get('author'):
            frontmatter_lines.append(f"author: {data['author']}")

        # 发布日期
        if data.get('publish_date'):
            frontmatter_lines.append(f"publish_date: {data['publish_date']}")

        # 翻译日期
        if data.get('translated_date'):
            frontmatter_lines.append(f"translated_date: {data['translated_date']}")

        # 描述
        if data.get('description'):
            # 转义描述中的引号
            description = data['description'].replace('"', '\\"')
            frontmatter_lines.append(f"description: \"{description}\"")

        # 标签
        if data.get('tags'):
            frontmatter_lines.append("tags:")
            for tag in data['tags']:
                frontmatter_lines.append(f"  - {tag}")

        frontmatter_lines.append("---")

        return "\n".join(frontmatter_lines)

    def build_note_content(self, data: Dict) -> str:
        """
        构建完整的笔记内容

        Args:
            data: 文章数据字典

        Returns:
            完整的笔记内容
        """
        parts = []

        # 添加 frontmatter
        parts.append(self.build_frontmatter(data))
        parts.append("")  # 空行

        # 添加文章内容
        if data.get('content'):
            parts.append(data['content'])

        return "\n".join(parts)

    def generate_filename(self, data: Dict) -> str:
        """
        生成文件名

        Args:
            data: 文章数据字典

        Returns:
            文件名（不含路径）
        """
        # 使用翻译后的标题
        title = data.get('title', 'untitled')

        # 生成 slug
        title_slug = slugify(title)

        # 添加日期前缀
        date_str = datetime.now().strftime('%Y%m%d')

        # 组合文件名
        filename = f"{date_str}_{title_slug}.md"

        return filename

    def save_note(self, data: Dict, filename: Optional[str] = None) -> str:
        """
        保存笔记到 Obsidian vault

        Args:
            data: 文章数据字典
            filename: 可选的文件名，如果不提供则自动生成

        Returns:
            保存的文件完整路径
        """
        try:
            # 生成文件名
            if not filename:
                filename = self.generate_filename(data)

            # 确保文件名以 .md 结尾
            if not filename.endswith('.md'):
                filename += '.md'

            # 构建完整路径
            articles_dir = os.path.join(self.vault_path, self.articles_folder)

            # 确保目录存在
            os.makedirs(articles_dir, exist_ok=True)

            file_path = os.path.join(articles_dir, filename)

            # 构建笔记内容
            content = self.build_note_content(data)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Successfully saved note to: {file_path}")

            return file_path

        except Exception as e:
            error_msg = f"Failed to save note: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise

    def save_translation(self, translation_result: Dict) -> Dict:
        """
        保存翻译结果到 Obsidian

        Args:
            translation_result: processor.py 返回的翻译结果字典

        Returns:
            包含保存信息的字典
        """
        try:
            # 检查是否有错误
            if 'error' in translation_result:
                return {
                    'success': False,
                    'error': translation_result['error']
                }

            # 保存笔记
            file_path = self.save_note(translation_result)

            return {
                'success': True,
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'title': translation_result.get('title'),
                'images_count': len(translation_result.get('images', []))
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

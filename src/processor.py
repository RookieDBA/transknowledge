"""
主处理模块
整合抓取、翻译、图片处理等功能,提供完整的文章处理流程
"""
import os
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from .utils import load_config, setup_logger, validate_url, slugify
from .scraper import ArticleScraper
from .translator import DeepSeekTranslator
from .image_handler import ImageHandler


class ArticleProcessor:
    """文章处理器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化处理器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = load_config(config_path)

        # 设置日志
        setup_logger(self.config)

        # 初始化各个模块
        self.scraper = ArticleScraper(self.config)
        self.translator = DeepSeekTranslator(self.config)
        self.image_handler = ImageHandler(self.config)

        # 获取Obsidian配置
        self.obsidian_config = self.config.get('obsidian', {})
        self.vault_path = self.obsidian_config.get('vault_path')
        self.attachments_folder = self.obsidian_config.get('attachments_folder', 'Attachments')

        if not self.vault_path:
            logger.warning("Obsidian vault path not configured")

    def process_url(self, url: str) -> Dict:
        """
        处理文章URL,完成抓取、翻译、图片下载等全流程

        Args:
            url: 文章URL

        Returns:
            处理结果字典,包含标题、内容、图片等信息
        """
        try:
            logger.info(f"Processing article from URL: {url}")

            # 1. 验证URL
            if not validate_url(url):
                error_msg = f"Invalid URL: {url}"
                logger.error(error_msg)
                return {'error': error_msg}

            # 2. 抓取文章
            logger.info("Step 1/5: Scraping article")
            article = self.scraper.fetch_and_extract(url)

            # 3. 翻译标题和内容
            logger.info("Step 2/5: Translating content")
            translated_title = self.translator.translate_text(article['title'], preserve_format=False)
            translated_content = self.translator.translate_text(article['content_markdown'], preserve_format=True)

            # 4. 下载图片
            logger.info("Step 3/5: Downloading images")
            downloaded_images = []

            if self.vault_path and article['image_urls']:
                # 生成article slug用于文件名
                article_slug = slugify(translated_title)

                # 下载图片到Obsidian附件目录
                attachment_dir = os.path.join(self.vault_path, self.attachments_folder)
                downloaded_images = self.image_handler.batch_download(
                    article['image_urls'],
                    attachment_dir,
                    article_slug
                )
            else:
                if not self.vault_path:
                    logger.warning("Obsidian vault path not configured, skipping image download")
                elif not article['image_urls']:
                    logger.info("No images found in article")

            # 5. 替换图片引用为Obsidian格式
            logger.info("Step 4/5: Converting image references")
            if downloaded_images:
                translated_content = self.image_handler.convert_to_obsidian_embeds(
                    translated_content,
                    downloaded_images,
                    self.attachments_folder
                )

            # 6. 构建返回结果
            logger.info("Step 5/5: Building result")
            result = {
                'title': translated_title,
                'original_title': article['title'],
                'content': translated_content,
                'source_url': url,
                'author': article.get('author', 'Unknown'),
                'publish_date': article.get('publish_date'),
                'translated_date': datetime.now().isoformat(),
                'images': [img['filename'] for img in downloaded_images if img['success']],
                'tags': ['translation', 'article']
            }

            # 添加描述(如果有)
            if article.get('description'):
                result['description'] = article['description']

            logger.info(f"Successfully processed article: {translated_title}")
            logger.info(f"  - Images downloaded: {len(result['images'])}/{len(article['image_urls'])}")

            return result

        except Exception as e:
            error_msg = f"Error processing article: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}

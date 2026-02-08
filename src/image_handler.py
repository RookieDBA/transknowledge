"""
图片处理模块
负责下载图片并转换为Obsidian格式的引用
"""
import os
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from .utils import get_file_extension, format_size, ensure_dir


def extract_real_image_url(url: str) -> str:
    """
    提取真实的图片URL（处理Next.js等图片优化服务）

    Args:
        url: 可能是优化服务包装的URL

    Returns:
        真实的图片URL
    """
    parsed = urlparse(url)

    # 处理 Next.js 图片优化: /_next/image?url=...
    if '/_next/image' in parsed.path:
        query_params = parse_qs(parsed.query)
        if 'url' in query_params:
            real_url = unquote(query_params['url'][0])
            logger.info(f"Extracted real image URL from Next.js wrapper: {real_url}")
            return real_url

    # 处理其他常见的图片代理服务
    # Cloudinary, imgix 等通常直接在URL中包含原始URL

    return url


class ImageHandler:
    """图片处理器"""

    def __init__(self, config: Dict):
        """
        初始化图片处理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.image_config = config.get('images', {})

        self.download_enabled = self.image_config.get('download_enabled', True)
        self.max_size_mb = self.image_config.get('max_size_mb', 10)
        self.timeout = self.image_config.get('timeout', 30)
        self.filename_prefix = self.image_config.get('filename_prefix', 'img')
        self.allowed_formats = self.image_config.get(
            'allowed_formats',
            ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
        )

    def download_image(self, url: str, save_dir: str, filename: Optional[str] = None) -> Dict:
        """
        下载单张图片

        Args:
            url: 图片URL
            save_dir: 保存目录
            filename: 文件名(可选)

        Returns:
            包含下载信息的字典 {url, filename, filepath, success, error}
        """
        # 提取真实的图片URL（处理Next.js等图片优化服务）
        original_url = url
        url = extract_real_image_url(url)

        result = {
            'url': original_url,  # 保留原始URL用于替换
            'real_url': url,      # 实际下载的URL
            'filename': None,
            'filepath': None,
            'success': False,
            'error': None
        }

        if not self.download_enabled:
            result['error'] = 'Image download is disabled'
            logger.warning(f"Image download disabled, skipping: {url}")
            return result

        try:
            logger.info(f"Downloading image: {url}")

            # 创建带重试机制的 session
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # 完整的浏览器请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }

            # 添加 Referer（使用图片URL的域名）
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            headers['Referer'] = referer
            response = session.get(url, headers=headers, timeout=self.timeout, stream=True, verify=True)
            response.raise_for_status()

            # 检查文件大小
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > self.max_size_mb:
                    result['error'] = f'Image too large: {size_mb:.2f}MB > {self.max_size_mb}MB'
                    logger.warning(result['error'])
                    return result

            # 读取图片数据
            image_data = response.content

            # 验证图片
            try:
                img = Image.open(BytesIO(image_data))
                img.verify()  # 验证图片完整性
            except Exception as e:
                result['error'] = f'Invalid image: {str(e)}'
                logger.warning(f"Failed to verify image {url}: {e}")
                return result

            # 确定文件扩展名
            content_type = response.headers.get('content-type', '')
            ext = get_file_extension(url, content_type)

            # 检查格式是否允许
            if ext not in self.allowed_formats:
                result['error'] = f'Image format not allowed: {ext}'
                logger.warning(result['error'])
                return result

            # 生成文件名
            if not filename:
                filename = f"{self.filename_prefix}_{hash(url) % 100000:05d}.{ext}"
            elif not filename.endswith(f'.{ext}'):
                filename = f"{filename}.{ext}"

            # 确保保存目录存在
            ensure_dir(save_dir)

            # 保存文件
            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)

            result['filename'] = filename
            result['filepath'] = filepath
            result['success'] = True

            logger.info(f"Successfully downloaded: {filename} ({format_size(len(image_data))})")

        except requests.RequestException as e:
            result['error'] = f'Download failed: {str(e)}'
            logger.error(f"Failed to download {url}: {e}")

        except Exception as e:
            result['error'] = f'Unexpected error: {str(e)}'
            logger.error(f"Unexpected error downloading {url}: {e}")

        return result

    def batch_download(self, urls: List[str], save_dir: str, article_slug: Optional[str] = None, max_workers: int = 5) -> List[Dict]:
        """
        批量下载图片

        Args:
            urls: 图片URL列表
            save_dir: 保存目录
            article_slug: 文章slug,用于生成文件名
            max_workers: 最大并发数

        Returns:
            下载结果列表
        """
        if not urls:
            logger.info("No images to download")
            return []

        logger.info(f"Batch downloading {len(urls)} images with {max_workers} workers")

        results = []

        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有下载任务
            future_to_url = {}
            for idx, url in enumerate(urls, 1):
                # 生成文件名
                if article_slug:
                    filename = f"{self.filename_prefix}_{article_slug}_{idx:03d}"
                else:
                    filename = f"{self.filename_prefix}_{idx:03d}"

                future = executor.submit(self.download_image, url, save_dir, filename)
                future_to_url[future] = url

            # 收集结果
            for future in as_completed(future_to_url):
                result = future.result()
                results.append(result)

        # 统计
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful

        logger.info(f"Batch download completed: {successful} succeeded, {failed} failed")

        return results

    def convert_to_obsidian_embeds(self, markdown: str, image_results: List[Dict], attachments_folder: str = "Attachments") -> str:
        """
        将Markdown中的图片引用转换为Obsidian格式

        Args:
            markdown: Markdown内容
            image_results: 图片下载结果列表
            attachments_folder: Obsidian附件文件夹名称

        Returns:
            转换后的Markdown内容
        """
        if not image_results:
            return markdown

        logger.info("Converting image references to Obsidian format")

        content = markdown

        # 创建URL到本地文件名的映射（使用原始URL和真实URL）
        url_to_filename = {}
        for result in image_results:
            if result['success'] and result['filename']:
                # 使用原始URL（可能是Next.js包装的URL）
                original_url = result['url']
                url_to_filename[original_url] = result['filename']

                # 如果有真实URL且与原始URL不同，也添加映射
                if result.get('real_url') and result['real_url'] != original_url:
                    url_to_filename[result['real_url']] = result['filename']

                logger.debug(f"Mapping URL for replacement: {original_url[:100]}... -> {result['filename']}")

        # 替换图片引用
        for url, filename in url_to_filename.items():
            obsidian_ref = f"![[{attachments_folder}/{filename}]]"

            # 生成多种可能的 URL 变体
            url_variants = [url]

            # 如果是绝对 URL，也尝试相对路径版本
            # 例如：https://example.com/path -> /path
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                # 生成相对路径（路径 + 查询参数）
                relative_url = parsed.path
                if parsed.query:
                    relative_url += '?' + parsed.query
                if relative_url and relative_url != url:
                    url_variants.append(relative_url)

            # 如果 URL 包含编码字符，也尝试解码版本
            if '%' in url:
                try:
                    from urllib.parse import unquote
                    url_variants.append(unquote(url))
                except:
                    pass

            for url_variant in url_variants:
                # 转义特殊字符用于正则表达式
                escaped_url = re.escape(url_variant)

                # 替换各种可能的图片引用格式
                patterns = [
                    # Markdown格式: ![alt](url) - 最常见
                    rf'!\[([^\]]*)\]\({escaped_url}\)',
                    # HTML格式: <img src="url" ...>
                    rf'<img[^>]*src=["\']?{escaped_url}["\']?[^>]*>',
                ]

                for pattern in patterns:
                    old_content = content
                    content = re.sub(pattern, obsidian_ref, content)
                    if content != old_content:
                        logger.debug(f"Replaced image reference with pattern: {pattern[:50]}...")

        logger.info("Image reference conversion completed")

        return content

    def generate_filename(self, url: str, index: int, article_slug: Optional[str] = None) -> str:
        """
        生成图片文件名

        Args:
            url: 图片URL
            index: 索引号
            article_slug: 文章slug

        Returns:
            文件名(不含扩展名)
        """
        if article_slug:
            return f"{self.filename_prefix}_{article_slug}_{index:03d}"
        else:
            return f"{self.filename_prefix}_{index:03d}"

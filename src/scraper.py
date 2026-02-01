"""
网页抓取模块
负责从URL抓取文章内容,提取正文、元数据和图片
"""
import re
import requests
import html2text
from bs4 import BeautifulSoup
from readability import Document
from typing import Dict, List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib.parse import urljoin, urlparse


class ArticleScraper:
    """文章抓取器"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化抓取器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.scraper_config = self.config.get('scraper', {})
        self.user_agent = self.scraper_config.get(
            'user_agent',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        self.timeout = self.scraper_config.get('timeout', 30)
        self.verify_ssl = self.scraper_config.get('verify_ssl', True)

        # 配置html2text
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # 不自动换行
        self.h2t.single_line_break = False
        self.h2t.bypass_tables = False  # 启用表格转换为Markdown格式

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_url(self, url: str) -> str:
        """
        获取URL内容

        Args:
            url: 目标URL

        Returns:
            HTML内容

        Raises:
            requests.RequestException: 请求失败
        """
        logger.info(f"Fetching URL: {url}")

        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                allow_redirects=True
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            logger.info(f"Successfully fetched URL: {url} (status: {response.status_code})")
            return response.text

        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise

    def extract_article(self, html: str, base_url: Optional[str] = None) -> Dict:
        """
        从HTML中提取文章主体内容

        Args:
            html: HTML内容
            base_url: 基础URL,用于解析相对链接

        Returns:
            包含标题、内容、作者等信息的字典
        """
        logger.info("Extracting article content using readability")

        # 使用readability提取主体内容
        doc = Document(html)

        # 提取标题
        title = doc.title()

        # 提取正文HTML
        content_html = doc.summary()

        # 解析HTML获取更多元数据
        soup = BeautifulSoup(html, 'lxml')

        # 提取作者
        author = self._extract_author(soup)

        # 提取发布日期
        publish_date = self._extract_date(soup)

        # 提取描述
        description = self._extract_description(soup)

        logger.info(f"Extracted article: {title}")
        logger.debug(f"Author: {author}, Date: {publish_date}")

        return {
            'title': title,
            'content_html': content_html,
            'author': author,
            'publish_date': publish_date,
            'description': description,
        }

    def convert_to_markdown(self, html: str) -> str:
        """
        将HTML转换为Markdown

        Args:
            html: HTML内容

        Returns:
            Markdown内容
        """
        logger.info("Converting HTML to Markdown")

        # 预处理HTML：为代码块添加语言标识
        html = self._preprocess_code_blocks(html)

        markdown = self.h2t.handle(html)

        # 后处理：修复代码块和表格格式
        markdown = self._postprocess_markdown(markdown)

        # 清理多余的空行
        markdown = '\n'.join(line for line in markdown.split('\n') if line.strip() or line == '')

        return markdown

    def _preprocess_code_blocks(self, html: str) -> str:
        """
        预处理HTML中的代码块，确保正确转换

        Args:
            html: HTML内容

        Returns:
            处理后的HTML
        """
        soup = BeautifulSoup(html, 'lxml')

        # 处理 <pre> 标签中的代码
        for pre in soup.find_all('pre'):
            # 检查是否有 <code> 子标签
            code = pre.find('code')
            if code:
                # 尝试从 class 属性获取语言
                lang = ''
                code_class = code.get('class', [])
                if code_class:
                    for cls in code_class:
                        if cls.startswith('language-'):
                            lang = cls.replace('language-', '')
                            break
                        elif cls.startswith('lang-'):
                            lang = cls.replace('lang-', '')
                            break

                # 获取代码内容
                code_text = code.get_text()

                # 创建新的结构，使用特殊标记
                pre.clear()
                pre['data-lang'] = lang
                pre.string = code_text
            else:
                # 没有 code 子标签，直接处理 pre
                pre_class = pre.get('class', [])
                lang = ''
                if pre_class:
                    for cls in pre_class:
                        if cls.startswith('language-'):
                            lang = cls.replace('language-', '')
                            break
                pre['data-lang'] = lang

        return str(soup)

    def _postprocess_markdown(self, markdown: str) -> str:
        """
        后处理Markdown，修复代码块和表格格式

        Args:
            markdown: 原始Markdown

        Returns:
            修复后的Markdown
        """
        # 修复缩进的代码块（4空格缩进）转换为围栏代码块
        # 匹配连续的缩进行（4空格或1个tab开头）
        lines = markdown.split('\n')
        result_lines = []
        in_code_block = False
        code_block_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检测缩进代码块（4空格开头，且不是列表项的续行）
            is_indented_code = (line.startswith('    ') and
                               not line.strip().startswith('-') and
                               not line.strip().startswith('*') and
                               not line.strip().startswith('+') and
                               not (i > 0 and result_lines and
                                    (result_lines[-1].strip().startswith('-') or
                                     result_lines[-1].strip().startswith('*') or
                                     result_lines[-1].strip().startswith('1.'))))

            if is_indented_code:
                if not in_code_block:
                    in_code_block = True
                    code_block_lines = []
                # 移除4空格缩进
                code_block_lines.append(line[4:] if line.startswith('    ') else line)
            else:
                if in_code_block:
                    # 结束代码块
                    in_code_block = False
                    # 检测代码语言
                    lang = self._detect_code_language('\n'.join(code_block_lines))
                    result_lines.append(f'```{lang}')
                    result_lines.extend(code_block_lines)
                    result_lines.append('```')
                    result_lines.append('')

                result_lines.append(line)

            i += 1

        # 处理文件末尾的代码块
        if in_code_block:
            lang = self._detect_code_language('\n'.join(code_block_lines))
            result_lines.append(f'```{lang}')
            result_lines.extend(code_block_lines)
            result_lines.append('```')

        markdown = '\n'.join(result_lines)

        # 修复表格格式：确保表格行之间没有多余空格
        markdown = self._fix_table_format(markdown)

        return markdown

    def _detect_code_language(self, code: str) -> str:
        """
        根据代码内容检测编程语言

        Args:
            code: 代码内容

        Returns:
            语言标识符
        """
        code_stripped = code.strip()

        # JSON 检测
        if code_stripped.startswith('{') and code_stripped.endswith('}'):
            try:
                import json
                json.loads(code_stripped)
                return 'json'
            except:
                pass

        # Python 检测
        if re.search(r'\bdef\s+\w+\s*\(', code) or re.search(r'\bimport\s+\w+', code):
            return 'python'

        # JavaScript 检测
        if re.search(r'\bfunction\s+\w+\s*\(', code) or re.search(r'\bconst\s+\w+\s*=', code):
            return 'javascript'

        # Bash/Shell 检测
        if code_stripped.startswith('#!') or re.search(r'\b(echo|cd|ls|pwd|git)\s+', code):
            return 'bash'

        # HTML 检测
        if re.search(r'<\w+[^>]*>', code) and re.search(r'</\w+>', code):
            return 'html'

        return ''

    def _fix_table_format(self, markdown: str) -> str:
        """
        修复Markdown表格格式

        Args:
            markdown: Markdown内容

        Returns:
            修复后的Markdown
        """
        lines = markdown.split('\n')
        result_lines = []

        for i, line in enumerate(lines):
            # 检测表格行（以 | 开头或包含 | 分隔符）
            if '|' in line and line.strip().startswith('|'):
                # 移除行尾多余空格
                line = line.rstrip()
                # 确保表格行格式正确
                if not line.endswith('|'):
                    line = line + '|'

            result_lines.append(line)

        return '\n'.join(result_lines)

    def extract_images(self, html: str, base_url: str) -> List[str]:
        """
        从HTML中提取所有图片URL

        Args:
            html: HTML内容
            base_url: 基础URL,用于解析相对链接

        Returns:
            图片URL列表
        """
        logger.info("Extracting image URLs")

        soup = BeautifulSoup(html, 'lxml')
        image_urls = []

        # 查找所有img标签
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src and isinstance(src, str):
                # 转换为绝对URL
                absolute_url = urljoin(base_url, src)
                # 过滤掉一些常见的无用图片
                if not self._is_valid_image_url(absolute_url):
                    continue
                image_urls.append(absolute_url)

        # 去重并保持顺序
        image_urls = list(dict.fromkeys(image_urls))

        logger.info(f"Found {len(image_urls)} images")
        return image_urls

    def fetch_and_extract(self, url: str) -> Dict:
        """
        完整流程:抓取并提取文章

        Args:
            url: 文章URL

        Returns:
            文章数据字典
        """
        # 1. 抓取HTML
        html = self.fetch_url(url)

        # 2. 提取文章内容
        article = self.extract_article(html, base_url=url)

        # 3. 转换为Markdown
        content_markdown = self.convert_to_markdown(article['content_html'])
        article['content_markdown'] = content_markdown

        # 4. 提取图片
        image_urls = self.extract_images(article['content_html'], base_url=url)
        article['image_urls'] = image_urls

        return article

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """提取作者信息"""
        # 尝试多种方式提取作者
        patterns = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('meta', {'name': 'article:author'}),
            ('span', {'class': 'author'}),
            ('a', {'rel': 'author'}),
        ]

        for tag_name, attrs in patterns:
            tag = soup.find(tag_name, attrs=attrs)  # type: ignore
            if tag:
                content = tag.get('content') or tag.get_text()
                if content:
                    return content.strip()

        return None

    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """提取发布日期"""
        patterns = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publishdate'}),
            ('meta', {'name': 'date'}),
            ('time', {'class': 'published'}),
            ('time', {}),
        ]

        for tag_name, attrs in patterns:
            tag = soup.find(tag_name, attrs=attrs)  # type: ignore
            if tag:
                content = tag.get('content') or tag.get('datetime') or tag.get_text()
                if content:
                    return content.strip()

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """提取描述信息"""
        patterns = [
            ('meta', {'name': 'description'}),
            ('meta', {'property': 'og:description'}),
            ('meta', {'name': 'twitter:description'}),
        ]

        for tag_name, attrs in patterns:
            tag = soup.find(tag_name, attrs=attrs)  # type: ignore
            if tag:
                content = tag.get('content')
                if content:
                    return content.strip()

        return None

    def _is_valid_image_url(self, url: str) -> bool:
        """判断是否是有效的图片URL"""
        # 过滤掉一些常见的无用图片
        invalid_patterns = [
            'logo',  # 网站logo
            'icon',  # 图标
            'avatar',  # 头像(可选)
            'gravatar',  # Gravatar头像
            'tracking',  # 跟踪像素
            'ad.',  # 广告
            'advertisement',
            '.gif?',  # 跟踪GIF(通常很小)
        ]

        url_lower = url.lower()

        # 检查是否包含无效模式
        for pattern in invalid_patterns:
            if pattern in url_lower:
                # logo和icon可能是文章中的重要图片,需要更严格的判断
                if pattern in ['logo', 'icon']:
                    # 如果URL中有这些关键词,但也有其他内容,可能是正常图片
                    parsed = urlparse(url_lower)
                    path = parsed.path
                    if any(keyword in path for keyword in ['/content/', '/article/', '/post/', '/image/']):
                        continue
                return False

        # 检查是否是data URL(跳过)
        if url.startswith('data:'):
            return False

        # 检查文件扩展名
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        if any(url_lower.endswith(ext) for ext in valid_extensions):
            return True

        # 如果没有扩展名,也可能是有效图片(通过CDN等)
        return True

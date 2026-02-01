"""
翻译模块
使用DeepSeek API进行文本翻译,保持Markdown格式
"""
import re
import time
from typing import Dict, List
from openai import OpenAI, RateLimitError, APIError
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class DeepSeekTranslator:
    """DeepSeek API翻译器"""

    def __init__(self, config: Dict):
        """
        初始化翻译器

        Args:
            config: 配置字典
        """
        self.config = config
        self.api_config = config.get('api', {}).get('deepseek', {})
        self.translation_config = config.get('translation', {})

        # 初始化DeepSeek客户端
        api_key = self.api_config.get('api_key')
        if not api_key:
            raise ValueError("未找到DeepSeek API密钥,请在配置文件或环境变量中设置DEEPSEEK_API_KEY")

        base_url = self.api_config.get('base_url', 'https://api.deepseek.com')
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        self.model = self.api_config.get('model', 'deepseek-chat')
        self.max_tokens = self.api_config.get('max_tokens', 4096)
        self.temperature = self.api_config.get('temperature', 0.3)
        self.chunk_size = self.translation_config.get('chunk_size', 3000)

    def translate_text(self, text: str, preserve_format: bool = True) -> str:
        """
        翻译文本

        Args:
            text: 待翻译文本
            preserve_format: 是否保留Markdown格式

        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return text

        logger.info(f"Translating text (length: {len(text)} chars)")

        # 如果需要保护格式,先提取特殊元素
        if preserve_format:
            text, placeholders = self._preserve_markdown_elements(text)

        # 如果文本太长,分段翻译
        if len(text) > self.chunk_size:
            logger.info(f"Text is too long, splitting into chunks (chunk_size: {self.chunk_size})")
            translated = self._translate_long_text(text)
        else:
            translated = self._translate_with_retry(text)

        # 恢复保护的元素
        if preserve_format and placeholders:
            translated = self._restore_markdown_elements(translated, placeholders)

        logger.info("Translation completed")
        return translated

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, APIError))
    )
    def _translate_with_retry(self, text: str) -> str:
        """
        带重试机制的翻译

        Args:
            text: 待翻译文本

        Returns:
            翻译后的文本
        """
        try:
            prompt = f"""请将以下{self.translation_config.get('source_language', 'English')}文本翻译成{self.translation_config.get('target_language', 'Chinese')}。

要求:
1. 保持原文的Markdown格式,包括标题、列表、代码块、链接等
2. 代码块内的代码不要翻译,保持原样
3. URL和链接不要翻译
4. 专业术语保持原文或加上中文注释
5. 翻译要准确、流畅、符合中文表达习惯
6. 只返回翻译后的内容,不要添加任何解释

原文:
{text}

翻译:"""

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            translated_text = response.choices[0].message.content
            if translated_text is None:
                logger.warning("API returned None content, returning original text")
                return text

            return translated_text.strip()

        except RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}. Waiting before retry...")
            time.sleep(60)  # 等待60秒
            raise

        except APIError as e:
            logger.error(f"API error: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error during translation: {e}")
            # 如果翻译失败,返回原文
            return text

    def _translate_long_text(self, text: str) -> str:
        """
        分段翻译长文本

        Args:
            text: 长文本

        Returns:
            翻译后的文本
        """
        # 按标题分段(优先)或按段落分段
        chunks = self._split_text_by_headers(text)

        if not chunks or len(chunks) == 1:
            # 如果无法按标题分段,按长度分段
            chunks = self._split_text_by_length(text)

        logger.info(f"Split text into {len(chunks)} chunks")

        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Translating chunk {i}/{len(chunks)}")
            translated = self._translate_with_retry(chunk)
            translated_chunks.append(translated)

            # 避免API限流,稍作延迟
            if i < len(chunks):
                time.sleep(1)

        # 重新组合
        return '\n\n'.join(translated_chunks)

    def _split_text_by_headers(self, text: str) -> List[str]:
        """
        按Markdown标题分段

        Args:
            text: 文本

        Returns:
            分段列表
        """
        # 匹配Markdown标题
        header_pattern = r'^#{1,6}\s+.+$'
        lines = text.split('\n')

        chunks = []
        current_chunk = []

        for line in lines:
            if re.match(header_pattern, line) and len('\n'.join(current_chunk)) > self.chunk_size:
                # 遇到新标题且当前chunk已经足够长,保存当前chunk
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
            else:
                current_chunk.append(line)

        # 添加最后一个chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _split_text_by_length(self, text: str, overlap: int = 100) -> List[str]:
        """
        按长度分段,尽量在段落边界分割

        Args:
            text: 文本
            overlap: 重叠字符数,保持上下文连贯性

        Returns:
            分段列表
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_len = len(para)

            if current_length + para_len > self.chunk_size and current_chunk:
                # 保存当前chunk
                chunks.append('\n\n'.join(current_chunk))

                # 开始新chunk,包含一些重叠以保持上下文
                current_chunk = [para]
                current_length = para_len
            else:
                current_chunk.append(para)
                current_length += para_len + 2  # +2 for '\n\n'

        # 添加最后一个chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _preserve_markdown_elements(self, text: str) -> tuple:
        """
        保护Markdown元素不被翻译

        Args:
            text: 原始文本

        Returns:
            (处理后的文本, 占位符映射)
        """
        placeholders = {}
        counter = [0]

        def create_placeholder(match):
            counter[0] += 1
            placeholder = f"__PLACEHOLDER_{counter[0]}__"
            placeholders[placeholder] = match.group(0)
            return placeholder

        # 保护代码块 ```...```
        text = re.sub(r'```[\s\S]*?```', create_placeholder, text)

        # 保护行内代码 `...`
        text = re.sub(r'`[^`]+`', create_placeholder, text)

        # 保护URL
        text = re.sub(r'https?://[^\s\)]+', create_placeholder, text)

        # 保护图片引用 ![...](...) 和 ![[...]]
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', create_placeholder, text)
        text = re.sub(r'!\[\[([^\]]+)\]\]', create_placeholder, text)

        return text, placeholders

    def _restore_markdown_elements(self, text: str, placeholders: Dict[str, str]) -> str:
        """
        恢复保护的Markdown元素

        Args:
            text: 处理后的文本
            placeholders: 占位符映射

        Returns:
            恢复后的文本
        """
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)

        return text

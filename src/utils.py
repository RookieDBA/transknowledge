"""
工具函数模块
提供配置加载、日志设置、URL验证、文件名清理等通用功能
"""
import os
import re
import yaml
import validators
from pathlib import Path
from typing import Dict, Any, Optional, Union
from loguru import logger
from dotenv import load_dotenv


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，默认为 config/config.yaml

    Returns:
        配置字典
    """
    config_file: Union[str, Path]
    if config_path is None:
        # 获取项目根目录
        root_dir = Path(__file__).parent.parent
        config_file = root_dir / "config" / "config.yaml"
    else:
        config_file = config_path

    # 加载环境变量
    load_dotenv()

    # 读取YAML配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 从环境变量覆盖配置
    if os.getenv('DEEPSEEK_API_KEY'):
        config.setdefault('api', {}).setdefault('deepseek', {})['api_key'] = os.getenv('DEEPSEEK_API_KEY')

    if os.getenv('OBSIDIAN_VAULT_PATH'):
        config.setdefault('obsidian', {})['vault_path'] = os.getenv('OBSIDIAN_VAULT_PATH')

    if os.getenv('LOG_LEVEL'):
        config.setdefault('logging', {})['level'] = os.getenv('LOG_LEVEL')

    return config


def setup_logger(config: Optional[Dict[str, Any]] = None):
    """
    配置日志系统

    Args:
        config: 配置字典
    """
    if config is None:
        config = load_config()

    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_file = log_config.get('log_file', 'logs/app.log')

    # 确保日志目录存在
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除默认的logger
    logger.remove()

    # 添加控制台输出
    logger.add(
        lambda msg: print(msg, end=''),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        colorize=True
    )

    # 添加文件输出
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=log_config.get('max_file_size', '10 MB'),
        retention=f"{log_config.get('backup_count', 5)} days",
        compression="zip"
    )

    logger.info(f"Logger initialized with level: {log_level}")


def validate_url(url: str) -> bool:
    """
    验证URL格式是否正确（仅接受http和https协议）

    Args:
        url: 待验证的URL

    Returns:
        是否有效
    """
    if not validators.url(url):
        return False

    # 只接受http和https协议
    return url.startswith('http://') or url.startswith('https://')


def clean_filename(filename: str, max_length: int = 100) -> str:
    """
    清理文件名，移除特殊字符

    Args:
        filename: 原始文件名
        max_length: 最大长度

    Returns:
        清理后的文件名
    """
    # 移除或替换不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # 移除多余空白
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename.strip()

    # 限制长度
    if len(filename) > max_length:
        filename = filename[:max_length]

    return filename


def slugify(text: str, max_length: int = 50) -> str:
    """
    将文本转换为URL友好的slug

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        slug字符串
    """
    # 转小写
    slug = text.lower()

    # 移除特殊字符，保留字母数字和空格
    slug = re.sub(r'[^\w\s-]', '', slug)

    # 将空格和下划线替换为连字符
    slug = re.sub(r'[-\s]+', '-', slug)

    # 移除首尾的连字符
    slug = slug.strip('-')

    # 限制长度
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')

    return slug


def ensure_dir(path: str) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_extension(url: str, content_type: Optional[str] = None) -> str:
    """
    从URL或Content-Type获取文件扩展名

    Args:
        url: 文件URL
        content_type: HTTP Content-Type头

    Returns:
        文件扩展名（不含点号）
    """
    # 先尝试从URL获取
    if url:
        ext = Path(url.split('?')[0]).suffix.lstrip('.')
        if ext:
            return ext.lower()

    # 从Content-Type获取
    if content_type:
        content_type_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/svg+xml': 'svg',
        }
        return content_type_map.get(content_type.split(';')[0].strip().lower(), 'jpg')

    # 默认
    return 'jpg'


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小字符串
    """
    size: float = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

"""
使 src 包可以作为模块运行
用法: python -m src <url> [options]
"""
from .cli import main

if __name__ == '__main__':
    main()

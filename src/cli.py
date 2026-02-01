"""
命令行接口入口
"""
import sys
import json
import argparse
from loguru import logger

from .processor import ArticleProcessor
from .obsidian_writer import ObsidianWriter


def main():
    """
    命令行入口
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='翻译文章并可选保存到 Obsidian',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 仅翻译并输出 JSON
  python -m src.cli https://example.com/article

  # 翻译并保存到 Obsidian
  python -m src.cli https://example.com/article --save

  # 使用自定义配置文件
  python -m src.cli https://example.com/article --config config/custom.yaml

  # 翻译、保存并指定文件名
  python -m src.cli https://example.com/article --save --filename my-article.md
        """
    )

    parser.add_argument('url', help='要翻译的文章 URL')
    parser.add_argument('--config', help='配置文件路径', default=None)
    parser.add_argument('--save', '-s', action='store_true',
                        help='保存翻译结果到 Obsidian vault')
    parser.add_argument('--filename', '-f', help='保存时使用的文件名（可选）', default=None)
    parser.add_argument('--json-only', action='store_true',
                        help='仅输出 JSON，不输出日志信息到 stderr')

    args = parser.parse_args()

    try:
        # 创建处理器
        processor = ArticleProcessor(args.config)

        # 处理文章
        result = processor.process_url(args.url)

        # 如果需要保存到 Obsidian
        if args.save and 'error' not in result:
            try:
                writer = ObsidianWriter(processor.config)
                save_result = writer.save_translation(result)

                # 将保存结果添加到输出
                result['obsidian_save'] = save_result

                if save_result['success']:
                    logger.info(f"Saved to Obsidian: {save_result['file_path']}")
                else:
                    logger.error(f"Failed to save to Obsidian: {save_result.get('error')}")

            except Exception as e:
                error_msg = f"Error saving to Obsidian: {str(e)}"
                logger.error(error_msg, exc_info=True)
                result['obsidian_save'] = {
                    'success': False,
                    'error': error_msg
                }

        # 输出JSON结果
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 如果有错误,返回非0退出码
        if 'error' in result:
            sys.exit(1)

    except Exception as e:
        error_result = {
            'error': f'Unexpected error: {str(e)}'
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()

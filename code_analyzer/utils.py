"""
utils.py — 公共工具函数
功能: 编码回退读取、通用工具
"""

from pathlib import Path


def read_file_with_encoding(file_path: str | Path) -> str:
    """
    读取文件内容（支持多种编码回退）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容字符串
        
    Raises:
        ValueError: 无法读取文件（所有编码都失败）
    """
    path = Path(file_path)
    for encoding in ('utf-8', 'gbk', 'latin-1'):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"无法读取文件: {path}")

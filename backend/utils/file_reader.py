"""
文件读取服务
支持格式：PDF, DOCX, TXT, MD
"""

import os
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 支持的文件格式
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']


def read_file(file_path: str) -> Dict[str, any]:
    """
    读取单个文件

    Args:
        file_path: 文件路径

    Returns:
        包含 title, text, source 的字典
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}")

    # 获取文件名作为标题
    title = os.path.splitext(os.path.basename(file_path))[0]

    # 根据格式读取内容
    if ext == '.pdf':
        text = read_pdf(file_path)
    elif ext == '.docx':
        text = read_docx(file_path)
    elif ext in ['.txt', '.md']:
        text = read_text_file(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return {
        'title': title,
        'text': text,
        'source': file_path
    }


def read_pdf(file_path: str) -> str:
    """
    读取 PDF 文件

    使用 pdfplumber 提取文本，支持表格和布局

    Args:
        file_path: PDF 文件路径

    Returns:
        提取的文本内容
    """
    try:
        import pdfplumber

        text_parts = []

        with pdfplumber.open(file_path) as pdf:
            logger.info(f"Reading PDF: {file_path}, pages: {len(pdf.pages)}")

            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本
                page_text = page.extract_text()

                if page_text:
                    # 清理文本
                    page_text = clean_extracted_text(page_text)
                    text_parts.append(page_text)

                # 可选：提取表格
                # tables = page.extract_tables()
                # for table in tables:
                #     if table:
                #         table_text = '\n'.join([' | '.join(row) for row in table if row])
                #         text_parts.append(table_text)

        result = '\n\n'.join(text_parts)
        logger.info(f"Extracted {len(result)} characters from PDF")

        return result

    except ImportError:
        logger.error("pdfplumber not installed. Run: pip install pdfplumber")
        raise ImportError("Please install pdfplumber: pip install pdfplumber")
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        raise


def read_docx(file_path: str) -> str:
    """
    读取 DOCX 文件

    使用 python-docx 提取段落文本

    Args:
        file_path: DOCX 文件路径

    Returns:
        提取的文本内容
    """
    try:
        from docx import Document

        doc = Document(file_path)
        text_parts = []

        logger.info(f"Reading DOCX: {file_path}")

        # 提取段落
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())

        # 提取表格内容
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    text_parts.append(row_text)

        result = '\n\n'.join(text_parts)
        logger.info(f"Extracted {len(result)} characters from DOCX")

        return result

    except ImportError:
        logger.error("python-docx not installed. Run: pip install python-docx")
        raise ImportError("Please install python-docx: pip install python-docx")
    except Exception as e:
        logger.error(f"Error reading DOCX {file_path}: {e}")
        raise


def read_text_file(file_path: str) -> str:
    """
    读取文本文件 (TXT/MD)

    尝试多种编码

    Args:
        file_path: 文件路径

    Returns:
        文件内容
    """
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                logger.info(f"Read {len(content)} characters from {file_path}")
                return content
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Unable to read file with any encoding: {file_path}")


def clean_extracted_text(text: str) -> str:
    """
    清理提取的文本

    - 去除多余空白
    - 规范化换行
    - 去除页码等噪声

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    if not text:
        return ""

    # 规范化换行
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 去除连续空白
    import re
    text = re.sub(r'[ \t]+', ' ', text)  # 多个空格变一个
    text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行变两个

    # 去除可能的页码 (如 "Page 1 of 10" 或 "第1页")
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'第\s*\d+\s*页', '', text)

    return text.strip()


def read_files_from_folder(folder_path: str) -> List[Dict[str, any]]:
    """
    从文件夹读取所有支持的文件

    Args:
        folder_path: 文件夹路径

    Returns:
        文档列表，每项包含 title, text, source
    """
    documents = []

    if not os.path.exists(folder_path):
        raise ValueError(f"Folder not found: {folder_path}")

    if not os.path.isdir(folder_path):
        raise ValueError(f"Not a directory: {folder_path}")

    logger.info(f"Scanning folder: {folder_path}")

    # 递归遍历文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)

            try:
                doc = read_file(file_path)
                documents.append(doc)
                logger.info(f"Loaded: {file_path}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

    logger.info(f"Total documents loaded: {len(documents)}")

    return documents


def get_supported_formats() -> List[str]:
    """获取支持的文件格式列表"""
    return SUPPORTED_EXTENSIONS.copy()

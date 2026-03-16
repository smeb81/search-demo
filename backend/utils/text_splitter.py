"""
段落分割服务
功能：
- 按语义进行段落级分割
- 段落长度合理、不割裂语义
- 支持自定义段落长度
"""

import re
import sys
import os
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAX_PARAGRAPH_LENGTH, MIN_PARAGRAPH_LENGTH


class TextSplitter:
    """文本段落分割器"""

    def __init__(self,
                 max_length: int = MAX_PARAGRAPH_LENGTH,
                 min_length: int = MIN_PARAGRAPH_LENGTH,
                 overlap: int = 50):
        """
        初始化分割器

        Args:
            max_length: 单个段落最大字符数
            min_length: 单个段落最小字符数
            overlap: 相邻段落重叠字符数（保持语义连贯）
        """
        self.max_length = max_length
        self.min_length = min_length
        self.overlap = overlap

        # 句子结束标记（中文+英文）
        self.sentence_endings = r'[。！？\.!?\n]+'

    def split(self, text: str) -> List[str]:
        """
        分割文本为段落

        Args:
            text: 原始文本

        Returns:
            段落列表
        """
        if not text:
            return []

        # 预处理：清理空白
        text = self._preprocess(text)

        # 按段落分割
        paragraphs = self._split_by_paragraphs(text)

        # 合并过短的段落
        paragraphs = self._merge_short_paragraphs(paragraphs)

        # 分割过长的段落
        paragraphs = self._split_long_paragraphs(paragraphs)

        # 清理空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _preprocess(self, text: str) -> str:
        """预处理文本"""
        # 规范化换行
        text = re.sub(r'\r\n|\r', '\n', text)
        # 去除多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割"""
        # 先按换行符分割
        raw_paragraphs = text.split('\n')

        paragraphs = []
        for para in raw_paragraphs:
            para = para.strip()
            if para:
                paragraphs.append(para)

        return paragraphs

    def _merge_short_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """合并过短的段落"""
        if not paragraphs:
            return []

        merged = []
        current = paragraphs[0] if paragraphs else ""

        for i in range(1, len(paragraphs)):
            next_para = paragraphs[i]

            # 如果当前段落太短，尝试与下一段合并
            if len(current) < self.min_length:
                current = current + ' ' + next_para
            else:
                # 检查合并后是否超过最大长度
                if len(current) + len(next_para) + 1 <= self.max_length:
                    current = current + ' ' + next_para
                else:
                    merged.append(current)
                    current = next_para

        # 添加最后一段
        if current:
            merged.append(current)

        return merged

    def _split_long_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """分割过长的段落"""
        result = []

        for para in paragraphs:
            if len(para) <= self.max_length:
                result.append(para)
            else:
                # 需要分割的长段落
                chunks = self._split_long_paragraph(para)
                result.extend(chunks)

        return result

    def _split_long_paragraph(self, text: str) -> List[str]:
        """分割长段落为小块"""
        if len(text) <= self.max_length:
            return [text]

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # 确定当前块的结束位置
            end = min(start + self.max_length, text_length)

            # 尝试在句子边界处切割
            if end < text_length:
                # 查找最近的句子结束标记
                boundary = self._find_sentence_boundary(text, start, end)
                if boundary > start:
                    end = boundary

            # 提取块
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # 移动起始位置（考虑重叠）
            start = end - self.overlap if end < text_length else end

        return chunks

    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """在给定范围内查找句子边界"""
        # 查找最后一个句子结束标记
        search_text = text[start:end]

        # 匹配句子结束标记
        matches = list(re.finditer(self.sentence_endings, search_text))

        if matches:
            # 返回最后一个匹配后的位置
            last_match = matches[-1]
            return start + last_match.end()

        # 没有找到句子边界，返回结束位置
        return end

    def split_with_metadata(self, text: str, source: str = "") -> List[dict]:
        """
        分割文本并返回带元数据的段落

        Args:
            text: 原始文本
            source: 来源标识

        Returns:
            段落列表，每项包含 text, index, source
        """
        paragraphs = self.split(text)

        return [
            {
                'text': para,
                'index': idx,
                'source': source,
                'length': len(para)
            }
            for idx, para in enumerate(paragraphs)
        ]


# 全局分割器实例
_text_splitter = None


def get_text_splitter() -> TextSplitter:
    """获取文本分割器实例"""
    global _text_splitter
    if _text_splitter is None:
        _text_splitter = TextSplitter()
    return _text_splitter


def split_text(text: str) -> List[str]:
    """便捷函数：分割文本为段落"""
    return get_text_splitter().split(text)


def split_text_with_metadata(text: str, source: str = "") -> List[dict]:
    """便捷函数：分割文本并返回元数据"""
    return get_text_splitter().split_with_metadata(text, source)

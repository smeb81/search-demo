"""
文本预处理服务
功能：
- 繁简转换
- 去重、去噪
- 特殊字符清理
- 空白规范化
"""

import re
import unicodedata
from typing import Optional


class TextPreprocessor:
    """文本预处理服务"""

    def __init__(self, convert_to_simplified: bool = True):
        """
        初始化预处理器

        Args:
            convert_to_simplified: 是否转换为简体中文
        """
        self.convert_to_simplified = convert_to_simplified
        self._init_converter()

    def _init_converter(self):
        """初始化繁简转换器"""
        self.converter = None
        try:
            import opencc
            self.converter = opencc.OpenCC('t2s.json')  # 繁体转简体
        except ImportError:
            print("Warning: opencc not installed, skipping traditional to simplified conversion")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenCC: {e}")

    def preprocess(self, text: str) -> str:
        """
        预处理文本

        Args:
            text: 原始文本

        Returns:
            处理后的文本
        """
        if not text:
            return ""

        # 1. 繁简转换
        if self.convert_to_simplified and self.converter:
            text = self.converter.convert(text)

        # 2. Unicode 规范化
        text = unicodedata.normalize('NFKC', text)

        # 3. 去除控制字符
        text = self._remove_control_characters(text)

        # 4. 规范化空白字符
        text = self._normalize_whitespace(text)

        # 5. 去除特殊字符
        text = self._remove_special_characters(text)

        # 6. 去除重复空白
        text = self._remove_duplicate_whitespace(text)

        # 7. 去除重复行
        text = self._remove_duplicate_lines(text)

        return text.strip()

    def _remove_control_characters(self, text: str) -> str:
        """去除控制字符"""
        # 保留换行、制表
        return ''.join(char for char in text
                       if unicodedata.category(char) != 'Cc' or char in '\n\t\r')

    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
        # 将全角空格转换为半角
        text = text.replace('\u3000', ' ')
        # 将制表符转换为空格
        text = text.replace('\t', ' ')
        return text

    def _remove_special_characters(self, text: str) -> str:
        """去除特殊字符（保留中文、英文、数字、常用标点）"""
        # 保留：中文、英文、数字、常用标点、空格、换行
        pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:，。！？；：""''（）【】《》""''、…—–\-]'
        text = re.sub(pattern, '', text)
        return text

    def _remove_duplicate_whitespace(self, text: str) -> str:
        """去除重复空白字符"""
        return re.sub(r' +', ' ', text)

    def _remove_duplicate_lines(self, text: str) -> str:
        """去除重复行"""
        lines = text.split('\n')
        seen = set()
        result = []
        for line in lines:
            # 跳过空行和只含空白的行
            stripped = line.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                result.append(line)
            elif not stripped:
                result.append(line)  # 保留空行
        return '\n'.join(result)

    def batch_preprocess(self, texts: list) -> list:
        """
        批量预处理文本

        Args:
            texts: 文本列表

        Returns:
            处理后的文本列表
        """
        return [self.preprocess(text) for text in texts]


# 全局预处理器实例
_text_preprocessor = None


def get_text_preprocessor() -> TextPreprocessor:
    """获取文本预处理器实例"""
    global _text_preprocessor
    if _text_preprocessor is None:
        _text_preprocessor = TextPreprocessor()
    return _text_preprocessor


def preprocess_text(text: str) -> str:
    """便捷函数：预处理单段文本"""
    return get_text_preprocessor().preprocess(text)


def batch_preprocess_texts(texts: list) -> list:
    """便捷函数：批量预处理文本"""
    return get_text_preprocessor().batch_preprocess(texts)

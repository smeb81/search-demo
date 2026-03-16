from sentence_transformers import SentenceTransformer
import sys
import os
import warnings
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EMBEDDING_MODEL, EMBEDDING_DIM, USE_QUANTIZATION
from services.quantization import quantization_service


class EmbeddingService:
    """语义向量嵌入服务 - 支持中文和量化压缩"""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """加载中文语义向量模型"""
        print(f"Loading Chinese BERT model: {EMBEDDING_MODEL}")
        print("-" * 50)

        start_time = time.time()

        try:
            # 加载 SentenceTransformer 模型
            self._model = SentenceTransformer(EMBEDDING_MODEL)

            # 如果启用量化，则应用量化
            if USE_QUANTIZATION:
                print("Applying dynamic quantization...")
                self._model = quantization_service.quantize_model(self._model)

            load_time = time.time() - start_time
            dim = self._model.get_sentence_embedding_dimension()

            print(f"Model loaded successfully in {load_time:.2f}s")
            print(f"Embedding dimension: {dim}")
            print(f"Quantization: {'Enabled' if USE_QUANTIZATION else 'Disabled'}")

            # 打印模型大小信息
            original_size = quantization_service.get_model_size_mb()
            quantized_size = quantization_service.get_quantized_size_mb()
            print(f"Model size: {original_size} MB", end="")
            if USE_QUANTIZATION:
                print(f" -> {quantized_size} MB (compressed {100*(1-quantized_size/original_size):.0f}%)")
            else:
                print()

        except Exception as e:
            print(f"Error loading model: {e}")
            print("Please check your network connection or model cache")
            warnings.warn("Using fallback embedding - model may not work correctly")

    def encode(self, texts, batch_size=32, show_progress_bar=False):
        """
        将文本转换为向量

        Args:
            texts: 单个文本或文本列表
            batch_size: 批处理大小
            show_progress_bar: 是否显示进度条

        Returns:
            numpy array: 文本向量
        """
        if self._model is None:
            raise RuntimeError("BERT model not loaded. Please check your network connection.")

        if isinstance(texts, str):
            texts = [texts]

        # 编码文本
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
            normalize_embeddings=True  # 归一化，用于余弦相似度
        )

        return embeddings

    def get_embedding_dim(self):
        """获取向量维度"""
        if self._model is None:
            return EMBEDDING_DIM
        return self._model.get_sentence_embedding_dimension()

    def get_model_info(self):
        """获取模型信息"""
        return {
            'model_name': EMBEDDING_MODEL,
            'embedding_dim': self.get_embedding_dim(),
            'quantization_enabled': USE_QUANTIZATION,
            'original_size_mb': quantization_service.get_model_size_mb(),
            'quantized_size_mb': quantization_service.get_quantized_size_mb() if USE_QUANTIZATION else None
        }


# 全局实例 - 延迟加载
embedding_service = None


def get_embedding_service():
    """获取嵌入服务实例（单例）"""
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service

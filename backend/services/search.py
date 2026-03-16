"""
FAISS 向量搜索服务
支持：
- 段落向量批量写入
- 语义相似度检索
- 索引持久化
"""

import faiss
import pickle
import numpy as np
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FAISS_INDEX_PATH, DOC_IDS_PATH, DEFAULT_TOP_K
from services.embedding import get_embedding_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchService:
    """FAISS 向量搜索服务"""

    _instance = None
    index = None
    doc_ids = []
    _embedding_service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SearchService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self.index is None:
            self._embedding_service = get_embedding_service()
            self._load_index()

    def _load_index(self):
        """加载或创建 FAISS 索引"""
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(DOC_IDS_PATH):
            logger.info("Loading existing FAISS index...")
            try:
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                with open(DOC_IDS_PATH, 'rb') as f:
                    self.doc_ids = pickle.load(f)
                logger.info(f"Loaded index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Error loading index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """创建新索引"""
        logger.info("Creating new FAISS index...")
        dim = self._embedding_service.get_embedding_dim()
        # 使用内积索引（归一化后等同于余弦相似度）
        self.index = faiss.IndexFlatIP(dim)
        self.doc_ids = []
        logger.info(f"Created new index with dimension {dim}")

    def save_index(self):
        """保存 FAISS 索引到磁盘"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)

            faiss.write_index(self.index, FAISS_INDEX_PATH)
            with open(DOC_IDS_PATH, 'wb') as f:
                pickle.dump(self.doc_ids, f)
            logger.info(f"Index saved with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def add_document(self, doc_id: int, text: str, batch_mode: bool = False):
        """
        添加文档到索引

        Args:
            doc_id: 文档ID
            text: 文档文本（或段落列表）
            batch_mode: 是否批量添加段落
        """
        if batch_mode and isinstance(text, list):
            # 批量添加段落
            self._add_paragraphs(doc_id, text)
        else:
            # 添加单个文档/段落
            self._add_single_embedding(doc_id, text)

    def _add_single_embedding(self, doc_id: int, text: str):
        """添加单个向量"""
        try:
            embedding = self._embedding_service.encode(text)
            # 归一化向量（用于余弦相似度）
            embedding = embedding / np.linalg.norm(embedding)

            self.index.add(embedding)
            self.doc_ids.append(doc_id)
            self.save_index()
            logger.info(f"Added document {doc_id} to index")
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")

    def _add_paragraphs(self, doc_id: int, paragraphs: list):
        """批量添加段落向量"""
        if not paragraphs:
            return

        try:
            # 批量编码
            embeddings = self._embedding_service.encode(paragraphs)

            # 归一化
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # 避免除零
            embeddings = embeddings / norms

            # 添加到索引
            self.index.add(embeddings)

            # 添加对应的文档ID
            for i in range(len(paragraphs)):
                self.doc_ids.append((doc_id, i))  # (doc_id, paragraph_index)

            self.save_index()
            logger.info(f"Added {len(paragraphs)} paragraphs for document {doc_id}")

        except Exception as e:
            logger.error(f"Error adding paragraphs for document {doc_id}: {e}")

    def add_documents_batch(self, documents: list):
        """
        批量添加多个文档

        Args:
            documents: 文档列表，每项包含 id, text
        """
        if not documents:
            return

        texts = [doc['text'] for doc in documents]
        doc_ids = [doc['id'] for doc in documents]

        try:
            # 批量编码
            embeddings = self._embedding_service.encode(texts)

            # 归一化
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            embeddings = embeddings / norms

            # 添加到索引
            self.index.add(embeddings)
            self.doc_ids.extend(doc_ids)

            self.save_index()
            logger.info(f"Batch added {len(documents)} documents to index")

        except Exception as e:
            logger.error(f"Error in batch add: {e}")

    def delete_document(self, doc_id: int):
        """
        删除文档（通过重建索引）

        Args:
            doc_id: 文档ID
        """
        # 检查文档是否在索引中
        if doc_id not in [x if isinstance(x, int) else x[0] for x in self.doc_ids]:
            logger.warning(f"Document {doc_id} not in index")
            return

        # 重新构建索引
        from models.document import get_session, Document

        session = get_session()
        try:
            # 获取所有其他文档
            all_docs = session.query(Document).filter(Document.id != doc_id).all()

            # 重建索引
            dim = self._embedding_service.get_embedding_dim()
            self.index = faiss.IndexFlatIP(dim)
            self.doc_ids = []

            for doc in all_docs:
                text = doc.chunk_text or doc.text
                self._add_single_embedding(doc.id, text)

            logger.info(f"Deleted document {doc_id} from index")
        finally:
            session.close()

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            搜索结果列表，每项包含 doc_id, paragraph_index, similarity
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []

        try:
            # 将查询转换为向量
            query_embedding = self._embedding_service.encode(query)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)

            # 搜索
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_embedding, k)

            # 构建结果
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.doc_ids):
                    doc_id_or_tuple = self.doc_ids[idx]

                    # 处理单个ID或(文档ID, 段落索引)元组
                    if isinstance(doc_id_or_tuple, tuple):
                        doc_id, para_idx = doc_id_or_tuple
                    else:
                        doc_id = doc_id_or_tuple
                        para_idx = None

                    results.append({
                        'doc_id': doc_id,
                        'paragraph_index': para_idx,
                        'similarity': float(dist)
                    })

            logger.info(f"Search completed, found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def get_index_stats(self) -> dict:
        """获取索引统计信息"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self._embedding_service.get_embedding_dim() if self._embedding_service else 0,
            'index_type': 'FlatIP'  # 内积索引
        }

    def rebuild_index(self):
        """重建整个索引"""
        logger.info("Rebuilding index...")

        from models.document import get_session, Document

        session = get_session()
        try:
            # 获取所有文档
            all_docs = session.query(Document).all()

            # 重建索引
            dim = self._embedding_service.get_embedding_dim()
            self.index = faiss.IndexFlatIP(dim)
            self.doc_ids = []

            for doc in all_docs:
                text = doc.chunk_text or doc.text
                self._add_single_embedding(doc.id, text)

            logger.info(f"Index rebuilt with {len(all_docs)} documents")
        finally:
            session.close()


# 全局实例
search_service = SearchService()


def get_search_service() -> SearchService:
    """获取搜索服务实例"""
    return search_service

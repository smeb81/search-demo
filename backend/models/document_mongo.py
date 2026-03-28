"""
MongoDB 文档管理模块
支持：
- 文档CRUD
- 段落级操作
"""

from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from datetime import datetime
from bson import ObjectId
import sys
import os
import logging
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB 客户端（单例）
_client = None
_db = None
_collection = None


def get_mongo_client():
    """获取 MongoDB 客户端（单例）"""
    global _client, _db, _collection
    if _client is None:
        try:
            _client = MongoClient(MONGODB_URI)
            # 验证连接
            _client.admin.command('ping')
            _db = _client[MONGODB_DATABASE]
            _collection = _db[MONGODB_COLLECTION]
            # 创建索引
            _collection.create_index('source_file')
            _collection.create_index('paragraph_index')
            _collection.create_index('created_at')
            _collection.create_index('file_hash')
            logger.info(f"Connected to MongoDB: {MONGODB_DATABASE}.{MONGODB_COLLECTION}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    return _collection


class MongoDocument:
    """
    MongoDB 文档模型
    """

    @staticmethod
    def to_dict(doc) -> dict:
        """将 MongoDB 文档转换为字典"""
        if doc is None:
            return None

        result = {
            'id': str(doc.get('_id')),
            'title': doc.get('title'),
            'text': doc.get('text'),
            'source_file': doc.get('source_file'),
            'file_type': doc.get('file_type'),
            'paragraph_index': doc.get('paragraph_index', 0),
            'chunk_text': doc.get('chunk_text'),
            'has_vector': doc.get('has_vector', False),
            'file_hash': doc.get('file_hash'),
            'created_at': doc.get('created_at').isoformat() if doc.get('created_at') else None,
            'updated_at': doc.get('updated_at').isoformat() if doc.get('updated_at') else None
        }
        return result

    @staticmethod
    def to_search_result(doc, similarity: float = None) -> dict:
        """转换为搜索结果格式"""
        result = {
            'id': str(doc.get('_id')) if doc.get('_id') else None,
            'title': doc.get('title'),
            'text': doc.get('chunk_text') or doc.get('text'),
            'source': doc.get('source_file') or 'Manual Input',
            'file_type': doc.get('file_type')
        }
        if similarity is not None:
            result['similarity'] = float(similarity)
        return result


def create_document(title: str, text: str, source_file: str = None,
                   file_type: str = None, paragraph_index: int = 0,
                   chunk_text: str = None, file_hash: str = None) -> dict:
    """
    创建文档记录

    Args:
        title: 文档标题
        text: 完整文本
        source_file: 源文件路径
        file_type: 文件类型
        paragraph_index: 段落索引
        chunk_text: 段落文本
        file_hash: 文件内容hash（用于幂等性）

    Returns:
        创建的文档字典
    """
    collection = get_mongo_client()

    doc = {
        'title': title,
        'text': text,
        'source_file': source_file,
        'file_type': file_type,
        'paragraph_index': paragraph_index,
        'chunk_text': chunk_text or text,
        'has_vector': False,
        'file_hash': file_hash,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    result = collection.insert_one(doc)
    doc['_id'] = result.inserted_id
    logger.info(f"Created document: {result.inserted_id}")
    return MongoDocument.to_dict(doc)


def get_documents(limit: int = None) -> list:
    """获取所有文档"""
    collection = get_mongo_client()
    query = collection.find().sort('created_at', DESCENDING)
    if limit:
        query = query.limit(limit)
    return [MongoDocument.to_dict(doc) for doc in query]


def get_all_mongo_docs(limit: int = None) -> list:
    """获取所有 MongoDB 文档对象（用于索引重建）"""
    collection = get_mongo_client()
    query = collection.find()
    if limit:
        query = query.limit(limit)
    return list(query)


def get_document_by_id(doc_id: str) -> dict:
    """根据ID获取文档"""
    collection = get_mongo_client()
    try:
        doc = collection.find_one({'_id': ObjectId(doc_id)})
        return MongoDocument.to_dict(doc)
    except Exception as e:
        logger.error(f"Error finding document {doc_id}: {e}")
        return None


def get_document_by_mongo_id(mongo_id: ObjectId) -> dict:
    """根据 MongoDB ObjectId 获取文档"""
    collection = get_mongo_client()
    doc = collection.find_one({'_id': mongo_id})
    return MongoDocument.to_dict(doc)


def delete_document_by_id(doc_id: str) -> bool:
    """删除文档"""
    collection = get_mongo_client()
    try:
        result = collection.delete_one({'_id': ObjectId(doc_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        return False


def delete_paragraphs_by_source(source_file: str) -> int:
    """删除指定源文件的所有段落"""
    collection = get_mongo_client()
    try:
        result = collection.delete_many({'source_file': source_file})
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error deleting paragraphs for {source_file}: {e}")
        return 0


def get_paragraphs_by_source(source_file: str) -> list:
    """根据源文件获取所有段落"""
    collection = get_mongo_client()
    docs = collection.find({'source_file': source_file}).sort('paragraph_index', 1)
    return [MongoDocument.to_dict(doc) for doc in docs]


def update_document_vector_status(doc_id: str, has_vector: bool = True) -> bool:
    """更新文档向量状态"""
    collection = get_mongo_client()
    try:
        result = collection.update_one(
            {'_id': ObjectId(doc_id)},
            {'$set': {'has_vector': has_vector, 'updated_at': datetime.utcnow()}}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating vector status for {doc_id}: {e}")
        return False


def get_documents_without_vector() -> list:
    """获取未生成向量的文档"""
    collection = get_mongo_client()
    docs = collection.find({'has_vector': False})
    return [MongoDocument.to_dict(doc) for doc in docs]


def get_document_count() -> int:
    """获取文档总数"""
    collection = get_mongo_client()
    return collection.count_documents({})


def find_by_hash(file_hash: str) -> dict:
    """根据文件内容hash查找文档（取paragraph_index=0的根文档）"""
    collection = get_mongo_client()
    doc = collection.find_one({
        'file_hash': file_hash,
        'paragraph_index': 0
    })
    return MongoDocument.to_dict(doc) if doc else None


def find_by_source(source_file: str) -> dict:
    """根据源文件路径查找文档（取paragraph_index=0的根文档，用于无hash的旧数据兜底）"""
    collection = get_mongo_client()
    doc = collection.find_one({
        'source_file': source_file,
        'paragraph_index': 0
    })
    return MongoDocument.to_dict(doc) if doc else None


def find_existing(file_hash: str = None, source_file: str = None) -> tuple:
    """
    统一的重复检查：优先按 hash，其次按 source_file

    Returns:
        (existing_doc, reason)  # reason: 'hash' | 'source' | None
    """
    if file_hash:
        doc = find_by_hash(file_hash)
        if doc:
            return doc, 'hash'
    if source_file:
        doc = find_by_source(source_file)
        if doc:
            return doc, 'source'
    return None, None


def find_by_source(source_file: str) -> dict:
    """根据源文件路径查找文档（取paragraph_index=0的根文档）"""
    collection = get_mongo_client()
    doc = collection.find_one({
        'source_file': source_file,
        'paragraph_index': 0
    })
    return MongoDocument.to_dict(doc) if doc else None


def compute_file_hash(file_path: str) -> str:
    """计算文件的SHA256哈希值，用于幂等性校验"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_text_hash(text: str) -> str:
    """计算文本内容的SHA256哈希值"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def get_paragraphs_by_hash(file_hash: str) -> list:
    """根据文件hash获取该文件的所有段落"""
    collection = get_mongo_client()
    docs = collection.find({'file_hash': file_hash}).sort('paragraph_index', 1)
    return [MongoDocument.to_dict(doc) for doc in docs]

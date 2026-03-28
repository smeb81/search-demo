"""
文档管理路由 (MongoDB版本)
支持：
- 文档CRUD
- 段落级操作
"""

from flask import Blueprint, request, jsonify
from models.document_mongo import (
    create_document, get_documents, get_document_by_id,
    delete_document_by_id, get_paragraphs_by_source, delete_paragraphs_by_source
)
from services.search import search_service
from utils.text_preprocessor import preprocess_text
from utils.text_splitter import split_text_with_metadata
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

document_bp = Blueprint('document', __name__)


@document_bp.route('/documents', methods=['GET'])
def get_all_documents():
    """
    获取所有文档（去重，每个源文件只返回一条）

    Query参数:
        - limit: 限制数量
        - source: 按源文件筛选

    返回:
        [ {...}, {...} ]
    """
    try:
        limit = request.args.get('limit', type=int)
        source = request.args.get('source', type=str)

        # 获取所有文档
        all_docs = get_documents(limit=limit)

        # 只获取 paragraph_index=0 的记录，即每个源文件的根文档
        docs = [doc for doc in all_docs if doc.get('paragraph_index', 0) == 0]

        # 按源文件筛选
        if source:
            docs = [doc for doc in docs if doc.get('source_file') == source]

        # 按创建时间降序
        docs.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return jsonify(docs)

    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return jsonify({'error': str(e)}), 500


@document_bp.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """获取单个文档"""
    try:
        doc = get_document_by_id(doc_id)
        if doc is None:
            return jsonify({'error': 'Document not found'}), 404
        return jsonify(doc)
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        return jsonify({'error': str(e)}), 500


@document_bp.route('/documents', methods=['POST'])
def add_document():
    """
    添加文档

    请求体:
        {
            "title": "标题",
            "text": "文本内容",
            "split_paragraphs": true  // 可选，是否分割段落
        }
    """
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is empty'}), 400

    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Text is required'}), 400

    # 检查文本长度
    if len(text) > 100000:  # 100KB
        return jsonify({'error': 'Text too long (max 100KB)'}), 400

    split_paragraphs = data.get('split_paragraphs', False)

    try:
        # 预处理
        text = preprocess_text(text)

        if split_paragraphs:
            # 分割段落
            paragraphs = split_text_with_metadata(text, 'Manual Input')

            first_doc = None
            for para in paragraphs:
                doc = create_document(
                    title=data.get('title', ''),
                    text=text,
                    source_file='Manual Input',
                    file_type='txt',
                    paragraph_index=para['index'],
                    chunk_text=para['text']
                )
                if first_doc is None:
                    first_doc = doc

            # 添加到搜索索引（添加第一条）
            search_service.add_document(first_doc['id'], paragraphs[0]['text'])

            return jsonify({
                'message': f'Document added with {len(paragraphs)} paragraphs',
                'document': first_doc
            }), 201
        else:
            # 不分割
            doc = create_document(
                title=data.get('title', ''),
                text=text,
                source_file='Manual Input',
                file_type='txt'
            )

            # 添加到搜索索引
            search_service.add_document(doc['id'], text)

            return jsonify(doc), 201

    except Exception as e:
        logger.error(f"Error adding document: {e}")
        return jsonify({'error': str(e)}), 500


@document_bp.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """删除文档"""
    try:
        doc = get_document_by_id(doc_id)
        if doc is None:
            return jsonify({'error': 'Document not found'}), 404

        # 删除源文件的所有段落
        if doc.get('source_file'):
            delete_paragraphs_by_source(doc['source_file'])

        # 从搜索索引中删除
        search_service.delete_document(doc_id)

        return jsonify({'message': 'Document deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        return jsonify({'error': str(e)}), 500


@document_bp.route('/documents/source/<path:source>', methods=['GET'])
def get_documents_by_source(source):
    """根据源文件获取所有段落"""
    try:
        paragraphs = get_paragraphs_by_source(source)
        return jsonify(paragraphs)
    except Exception as e:
        logger.error(f"Error getting paragraphs for {source}: {e}")
        return jsonify({'error': str(e)}), 500

from flask import Blueprint, request, jsonify
from services.search import search_service
from models.document_mongo import get_document_by_id
from config import SIMILARITY_THRESHOLD
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['POST'])
def search():
    """
    语义搜索接口

    请求体:
        {
            "query": "查询文本",
            "top_k": 5  // 可选，返回结果数量
        }

    返回:
        [
            {
                "id": "ObjectId字符串",
                "title": "文档标题",
                "text": "段落文本",
                "source": "源文件路径",
                "file_type": "pdf/docx/txt",
                "similarity": 0.95
            }
        ]
    """
    # 参数验证
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is empty'}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query is required'}), 400

    # 检查查询长度
    if len(query) > 1000:
        return jsonify({'error': 'Query too long (max 1000 characters)'}), 400

    top_k = data.get('top_k', 5)
    if not isinstance(top_k, int) or top_k < 1 or top_k > 100:
        return jsonify({'error': 'top_k must be an integer between 1 and 100'}), 400

    # 获取相似度阈值（可选参数）
    threshold = data.get('threshold', SIMILARITY_THRESHOLD)
    if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
        return jsonify({'error': 'threshold must be a number between 0 and 1'}), 400

    try:
        # 执行搜索（传入阈值参数）
        results = search_service.search(query, top_k, threshold)

        if not results:
            return jsonify({
                'message': 'No results found',
                'results': []
            })

        # 获取完整的文档信息
        response = []
        for result in results:
            doc_id = result['doc_id']
            doc = get_document_by_id(doc_id)

            if doc:
                response.append({
                    'id': doc.get('id'),
                    'title': doc.get('title') or 'Untitled',
                    'text': doc.get('chunk_text') or doc.get('text'),
                    'source': doc.get('source_file') or 'Manual Input',
                    'file_type': doc.get('file_type'),
                    'paragraph_index': doc.get('paragraph_index', 0),
                    'similarity': round(result['similarity'], 4)
                })

        logger.info(f"Search query: '{query}', found {len(response)} results")

        return jsonify({
            'query': query,
            'count': len(response),
            'results': response
        })

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


@search_bp.route('/search/stats', methods=['GET'])
def get_stats():
    """获取搜索服务状态"""
    try:
        stats = search_service.get_index_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


@search_bp.route('/search/rebuild', methods=['POST'])
def rebuild_index():
    """重建索引"""
    try:
        search_service.rebuild_index()
        return jsonify({'message': 'Index rebuilt successfully'})
    except Exception as e:
        logger.error(f"Rebuild error: {e}")
        return jsonify({'error': str(e)}), 500

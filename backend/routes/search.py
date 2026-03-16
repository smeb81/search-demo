from flask import Blueprint, request, jsonify
from services.search import search_service
from models.document import get_session, Document
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
                "id": 1,
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

    try:
        # 执行搜索
        results = search_service.search(query, top_k)

        if not results:
            return jsonify({
                'message': 'No results found',
                'results': []
            })

        # 获取完整的文档信息
        session = get_session()
        try:
            response = []
            for result in results:
                doc_id = result['doc_id']
                doc = session.query(Document).filter(Document.id == doc_id).first()

                if doc:
                    response.append({
                        'id': doc.id,
                        'title': doc.title or 'Untitled',
                        'text': doc.chunk_text or doc.text,
                        'source': doc.source_file or 'Manual Input',
                        'file_type': doc.file_type,
                        'paragraph_index': doc.paragraph_index,
                        'similarity': round(result['similarity'], 4)
                    })

            logger.info(f"Search query: '{query}', found {len(response)} results")

            return jsonify({
                'query': query,
                'count': len(response),
                'results': response
            })

        finally:
            session.close()

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

"""
文档导入路由 (MongoDB版本)
支持：
- 文件夹批量导入
- PDF/DOCX/TXT 多格式解析
- 文本预处理
- 段落级分割
- 文件上传
- 幂等性：基于文件内容 hash，重复时拒绝操作
"""

from flask import Blueprint, request, jsonify
from models.document_mongo import (
    create_document, delete_paragraphs_by_source,
    find_existing, find_by_source, get_paragraphs_by_hash,
    get_paragraphs_by_source,
    compute_file_hash, compute_text_hash,
    get_mongo_client
)
from services.search import search_service
from utils.file_reader import read_files_from_folder, read_file, get_supported_formats, read_file_content
from utils.text_preprocessor import preprocess_text
from utils.text_splitter import split_text_with_metadata
import logging
import os
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import_bp = Blueprint('import', __name__)


@import_bp.route('/documents/clear', methods=['DELETE'])
def clear_all_documents():
    """
    清空数据库中的所有文档及向量索引

    返回:
        {
            "message": "...",
            "deleted_count": 100
        }
    """
    try:
        collection = get_mongo_client()

        # 1. 清空 MongoDB
        deleted_count = collection.delete_many({}).deleted_count

        # 2. 清空 FAISS 索引
        from config import EMBEDDING_DIM
        import faiss
        dim = 384  # 索引维度
        search_service.index = faiss.IndexFlatIP(dim)
        search_service.doc_ids = []
        search_service.save_index()

        logger.info(f"Cleared {deleted_count} documents from database and vector index")
        return jsonify({
            'message': f'All documents cleared',
            'deleted_count': deleted_count
        }), 200

    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        return jsonify({'error': str(e)}), 500


def _process_and_save_document(doc_data: dict, text: str, file_type: str,
                                file_hash: str, split_paragraphs: bool,
                                source: str) -> dict:
    """
    通用文档处理和保存逻辑

    幂等性：优先按 file_hash 去重（新版），
            兜底按 source_file 去重（旧版/无hash文档）
    """
    # 1. 检查是否已存在（统一查重入口）
    existing, dup_reason = find_existing(file_hash=file_hash, source_file=source)

    if existing:
        # 获取段落数
        if file_hash:
            paragraphs = get_paragraphs_by_hash(file_hash)
        else:
            paragraphs = get_paragraphs_by_source(source)
        reason = f'({dup_reason})' if dup_reason else ''
        logger.warning(f"Duplicate rejected {reason}: {source}")
        return {
            'is_duplicate': True,
            'document': existing,
            'paragraph_count': len(paragraphs)
        }

    # 2. 不存在，创建新文档
    paragraphs_data = []
    if split_paragraphs:
        paragraphs_data = split_text_with_metadata(text, source)

    # 3. 创建段落文档
    created_docs = []
    for para in (paragraphs_data or [{'index': 0, 'text': text}]):
        doc = create_document(
            title=doc_data.get('title', ''),
            text=text,
            source_file=source,
            file_type=file_type,
            paragraph_index=para['index'],
            chunk_text=para['text'],
            file_hash=file_hash
        )
        created_docs.append(doc)

    # 4. 添加向量索引
    for doc in created_docs:
        if doc.get('chunk_text'):
            search_service.add_document(doc['id'], doc['chunk_text'])

    return {
        'is_duplicate': False,
        'document': created_docs[0] if created_docs else None,
        'paragraph_count': len(created_docs)
    }


@import_bp.route('/documents/import', methods=['POST'])
def import_documents():
    """
    从文件夹批量导入文档

    请求体:
        {
            "folder_path": "/path/to/folder",
            "split_paragraphs": true,
            "preprocess": true
        }

    返回:
        {
            "message": "...",
            "count": 10,
            "paragraphs": 50,
            "duplicates": 2   // 重复被拒绝的数量
        }
    """
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is empty'}), 400

    folder_path = data.get('folder_path', '').strip()
    if not folder_path:
        return jsonify({'error': 'Folder path is required'}), 400

    split_paragraphs = data.get('split_paragraphs', True)
    preprocess = data.get('preprocess', True)

    try:
        documents = read_files_from_folder(folder_path)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error reading folder: {e}")
        return jsonify({'error': f'Failed to read folder: {str(e)}'}), 500

    if not documents:
        return jsonify({'error': 'No valid documents found'}), 400

    imported_count = 0
    duplicate_count = 0
    paragraph_count = 0
    duplicate_names = []

    for doc_data in documents:
        try:
            file_path = doc_data['source']
            if not file_path or not os.path.exists(file_path):
                continue

            # 计算文件hash
            try:
                file_hash = compute_file_hash(file_path)
            except Exception as e:
                logger.warning(f"Cannot compute hash for {file_path}: {e}")
                file_hash = compute_text_hash(doc_data['text'])

            # 文本预处理
            if preprocess:
                text = preprocess_text(doc_data['text'])
            else:
                text = doc_data['text']

            if not text.strip():
                continue

            ext = os.path.splitext(file_path)[1].lower()
            file_type = ext[1:] if ext else None

            result = _process_and_save_document(
                doc_data, text, file_type, file_hash, split_paragraphs, file_path
            )

            if result['is_duplicate']:
                duplicate_count += 1
                duplicate_names.append(doc_data.get('title', file_path))
                logger.info(f"Duplicate rejected: {doc_data.get('title', file_path)}")
            else:
                imported_count += 1
                paragraph_count += result['paragraph_count']
                logger.info(f"Imported: {doc_data['title']}")

        except Exception as e:
            logger.error(f"Error importing {doc_data.get('title', 'unknown')}: {e}")
            continue

    response = {
        'message': f'Imported {imported_count}, rejected {duplicate_count} duplicates',
        'count': imported_count,
        'duplicates': duplicate_count,
        'paragraphs': paragraph_count,
        'duplicate_names': duplicate_names
    }
    return jsonify(response), 201


@import_bp.route('/documents/import/file', methods=['POST'])
def import_single_file():
    """
    导入单个文件（服务器路径）

    请求体:
        {
            "file_path": "/path/to/file.pdf"
        }

    返回:
        - 成功: HTTP 201
        - 重复: HTTP 409
    """
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is empty'}), 400

    file_path = data.get('file_path', '').strip()
    if not file_path:
        return jsonify({'error': 'File path is required'}), 400

    split_paragraphs = data.get('split_paragraphs', True)
    preprocess = data.get('preprocess', True)

    try:
        doc_data = read_file(file_path)

        try:
            file_hash = compute_file_hash(file_path)
        except Exception:
            file_hash = compute_text_hash(doc_data['text'])

        if preprocess:
            text = preprocess_text(doc_data['text'])
        else:
            text = doc_data['text']

        ext = os.path.splitext(file_path)[1].lower()
        file_type = ext[1:] if ext else None

        result = _process_and_save_document(
            doc_data, text, file_type, file_hash, split_paragraphs, file_path
        )

        if result['is_duplicate']:
            return jsonify({
                'error': 'Document already exists, operation rejected',
                'existing_document_id': result['document']['id'],
                'title': result['document']['title'],
                'source_file': result['document']['source_file']
            }), 409

        return jsonify({
            'message': 'File imported successfully',
            'document': result['document'],
            'paragraph_count': result['paragraph_count']
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error importing file: {e}")
        return jsonify({'error': f'Failed to import file: {str(e)}'}), 500


@import_bp.route('/documents/formats', methods=['GET'])
def get_formats():
    """获取支持的文件格式"""
    return jsonify({
        'formats': get_supported_formats()
    })


@import_bp.route('/documents/upload', methods=['POST'])
def upload_file():
    """
    上传单个文件（multipart/form-data）

    返回:
        - 成功: HTTP 201
        - 重复: HTTP 409
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    allowed_extensions = {'.txt', '.md', '.pdf', '.docx'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        return jsonify({'error': f'Unsupported file type. Allowed: {allowed_extensions}'}), 400

    split_paragraphs = request.form.get('split_paragraphs', 'true').lower() == 'true'
    preprocess = request.form.get('preprocess', 'true').lower() == 'true'

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            doc_data = read_file_content(tmp_path, file.filename)
            file_hash = compute_file_hash(tmp_path)

            if preprocess:
                text = preprocess_text(doc_data['text'])
            else:
                text = doc_data['text']

            if not text.strip():
                return jsonify({'error': 'File content is empty'}), 400

            source = file.filename

            result = _process_and_save_document(
                doc_data, text, ext[1:], file_hash, split_paragraphs, source
            )

            if result['is_duplicate']:
                return jsonify({
                    'error': 'Document already exists, operation rejected',
                    'existing_document_id': result['document']['id'],
                    'title': result['document']['title'],
                    'source_file': result['document']['source_file']
                }), 409

            return jsonify({
                'message': 'File uploaded successfully',
                'document': result['document'],
                'paragraph_count': result['paragraph_count']
            }), 201

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

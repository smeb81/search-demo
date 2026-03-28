"""
文档导入路由 (MongoDB版本)
支持：
- 文件夹批量导入
- PDF/DOCX/TXT 多格式解析
- 文本预处理
- 段落级分割
- 文件上传
"""

from flask import Blueprint, request, jsonify
from models.document_mongo import create_document, delete_paragraphs_by_source
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


@import_bp.route('/documents/import', methods=['POST'])
def import_documents():
    """
    从文件夹批量导入文档

    请求体:
        {
            "folder_path": "/path/to/folder",
            "split_paragraphs": true,  // 是否分割段落
            "preprocess": true          // 是否预处理文本
        }

    返回:
        {
            "message": "...",
            "count": 10,
            "paragraphs": 50
        }
    """
    # 参数验证
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

    # 读取文件
    try:
        documents = read_files_from_folder(folder_path)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error reading folder: {e}")
        return jsonify({'error': f'Failed to read folder: {str(e)}'}), 500

    if not documents:
        return jsonify({'error': 'No valid documents found'}), 400

    # 导入文档
    imported_count = 0
    paragraph_count = 0

    for doc_data in documents:
        try:
            # 文本预处理
            if preprocess:
                text = preprocess_text(doc_data['text'])
            else:
                text = doc_data['text']

            if not text.strip():
                continue

            # 获取文件类型
            file_type = None
            if doc_data['source']:
                ext = os.path.splitext(doc_data['source'])[1].lower()
                if ext:
                    file_type = ext[1:]  # 去掉点号

            if split_paragraphs:
                # 分割为段落
                paragraphs = split_text_with_metadata(text, doc_data['source'])

                # 先创建所有段落文档，获取ID
                created_docs = []
                for para in paragraphs:
                    # 创建段落文档
                    doc = create_document(
                        title=doc_data['title'],
                        text=text,  # 完整文本
                        source_file=doc_data['source'],
                        file_type=file_type,
                        paragraph_index=para['index'],
                        chunk_text=para['text']
                    )
                    created_docs.append(doc)
                    paragraph_count += 1

                # 为每个段落添加向量索引
                for doc in created_docs:
                    if doc.get('chunk_text'):
                        search_service.add_document(doc['id'], doc['chunk_text'])

            else:
                # 不分割，整个文档作为一条记录
                doc = create_document(
                    title=doc_data['title'],
                    text=text,
                    source_file=doc_data['source'],
                    file_type=file_type
                )

                # 添加到搜索索引
                search_service.add_document(doc['id'], text)

            imported_count += 1
            logger.info(f"Imported: {doc_data['title']}")

        except Exception as e:
            logger.error(f"Error importing {doc_data.get('title', 'unknown')}: {e}")
            continue

    return jsonify({
        'message': f'Successfully imported {imported_count} documents',
        'count': imported_count,
        'paragraphs': paragraph_count,
        'formats': get_supported_formats()
    }), 201


@import_bp.route('/documents/import/file', methods=['POST'])
def import_single_file():
    """
    导入单个文件

    请求体:
        {
            "file_path": "/path/to/file.pdf"
        }

    返回:
        {
            "message": "...",
            "document": {...}
        }
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
        # 读取文件
        doc_data = read_file(file_path)

        # 文本预处理
        if preprocess:
            text = preprocess_text(doc_data['text'])
        else:
            text = doc_data['text']

        # 获取文件类型
        ext = os.path.splitext(file_path)[1].lower()
        file_type = ext[1:] if ext else None

        # 检查是否已存在该文件的段落
        existing_count = 0
        if doc_data['source']:
            existing_count = delete_paragraphs_by_source(doc_data['source'])

        if existing_count > 0:
            logger.info(f"Replacing {existing_count} existing paragraphs")

        paragraph_count = 0
        doc = None

        if split_paragraphs:
            # 分割为段落
            paragraphs = split_text_with_metadata(text, doc_data['source'])

            for para in paragraphs:
                doc = create_document(
                    title=doc_data['title'],
                    text=text,
                    source_file=doc_data['source'],
                    file_type=file_type,
                    paragraph_index=para['index'],
                    chunk_text=para['text']
                )
                paragraph_count += 1
        else:
            # 不分割
            doc = create_document(
                title=doc_data['title'],
                text=text,
                source_file=doc_data['source'],
                file_type=file_type
            )

        # 添加到搜索索引
        if doc:
            search_service.add_document(doc['id'], text)

        return jsonify({
            'message': 'File imported successfully',
            'document': doc,
            'paragraphs': paragraph_count
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
    上传单个文件

    请求: multipart/form-data
        - file: 文件

    返回:
        {
            "message": "...",
            "document": {...}
        }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # 检查文件类型
    allowed_extensions = {'.txt', '.md', '.pdf', '.docx'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        return jsonify({'error': f'Unsupported file type. Allowed: {allowed_extensions}'}), 400

    split_paragraphs = request.form.get('split_paragraphs', 'true').lower() == 'true'
    preprocess = request.form.get('preprocess', 'true').lower() == 'true'

    # 保存上传的文件到临时目录
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            # 读取文件内容
            doc_data = read_file_content(tmp_path, file.filename)

            # 文本预处理
            if preprocess:
                text = preprocess_text(doc_data['text'])
            else:
                text = doc_data['text']

            if not text.strip():
                return jsonify({'error': 'File content is empty'}), 400

            # 获取文件类型
            file_type = ext[1:] if ext else None

            # 检查是否已存在该文件的段落
            existing_count = 0
            if doc_data['source']:
                existing_count = delete_paragraphs_by_source(doc_data['source'])

            if existing_count > 0:
                logger.info(f"Replacing {existing_count} existing paragraphs")

            paragraph_count = 0
            doc = None

            if split_paragraphs:
                # 分割为段落
                paragraphs = split_text_with_metadata(text, doc_data['source'])

                # 先创建所有段落文档，获取ID
                created_docs = []
                for para in paragraphs:
                    doc = create_document(
                        title=doc_data['title'],
                        text=text,
                        source_file=doc_data['source'],
                        file_type=file_type,
                        paragraph_index=para['index'],
                        chunk_text=para['text']
                    )
                    created_docs.append(doc)
                    paragraph_count += 1

                # 为每个段落添加向量索引
                for created_doc in created_docs:
                    if created_doc.get('chunk_text'):
                        search_service.add_document(created_doc['id'], created_doc['chunk_text'])

                # 返回第一个文档
                doc = created_docs[0] if created_docs else None
            else:
                # 不分割
                doc = create_document(
                    title=doc_data['title'],
                    text=text,
                    source_file=doc_data['source'],
                    file_type=file_type
                )

                # 添加到搜索索引
                if doc:
                    search_service.add_document(doc['id'], text)

            return jsonify({
                'message': 'File uploaded successfully',
                'document': doc,
                'paragraphs': paragraph_count,
                'existing_paragraphs_replaced': existing_count
            }), 201

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

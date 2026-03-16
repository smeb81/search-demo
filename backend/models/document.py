from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH, REBUILD_DATABASE

Base = declarative_base()


class Document(Base):
    """
    文档模型
    支持段落级分割存储
    """
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=True)
    text = Column(Text, nullable=False)  # 完整文本

    # 元数据字段
    source_file = Column(String(1000), nullable=True)  # 原始文件路径
    file_type = Column(String(20), nullable=True)  # 文件类型: pdf, docx, txt, md

    # 段落级字段
    paragraph_index = Column(Integer, default=0)  # 段落索引
    chunk_text = Column(Text, nullable=True)  # 分割后的段落文本

    # 向量字段
    has_vector = Column(Integer, default=0)  # 是否已生成向量

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'text': self.text,
            'source_file': self.source_file,
            'file_type': self.file_type,
            'paragraph_index': self.paragraph_index,
            'chunk_text': self.chunk_text,
            'has_vector': bool(self.has_vector),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_search_result(self, similarity: float = None):
        """转换为搜索结果格式"""
        result = {
            'id': self.id,
            'title': self.title,
            'text': self.chunk_text or self.text,
            'source': self.source_file or 'Manual Input',
            'file_type': self.file_type
        }
        if similarity is not None:
            result['similarity'] = float(similarity)
        return result


# 创建数据库引擎
engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)

# 如果需要重建数据库，先删除旧表
if REBUILD_DATABASE and os.path.exists(DATABASE_PATH):
    try:
        Base.metadata.drop_all(engine)
        print("Old database dropped")
    except:
        pass

# 创建表
Base.metadata.create_all(engine)

# 创建会话
Session = sessionmaker(bind=engine)


def get_session():
    return Session()


def create_document(title: str, text: str, source_file: str = None,
                    file_type: str = None, paragraph_index: int = 0,
                    chunk_text: str = None) -> Document:
    """
    创建文档记录

    Args:
        title: 文档标题
        text: 完整文本
        source_file: 源文件路径
        file_type: 文件类型
        paragraph_index: 段落索引
        chunk_text: 段落文本

    Returns:
        Document对象
    """
    session = get_session()
    try:
        doc = Document(
            title=title,
            text=text,
            source_file=source_file,
            file_type=file_type,
            paragraph_index=paragraph_index,
            chunk_text=chunk_text or text
        )
        session.add(doc)
        session.commit()

        # 刷新获取ID
        session.refresh(doc)
        return doc
    finally:
        session.close()


def get_documents(limit: int = None) -> list:
    """获取所有文档"""
    session = get_session()
    try:
        query = session.query(Document).order_by(Document.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    finally:
        session.close()


def get_document_by_id(doc_id: int) -> Document:
    """根据ID获取文档"""
    session = get_session()
    try:
        return session.query(Document).filter(Document.id == doc_id).first()
    finally:
        session.close()


def delete_document_by_id(doc_id: int) -> bool:
    """删除文档"""
    session = get_session()
    try:
        doc = session.query(Document).filter(Document.id == doc_id).first()
        if doc:
            session.delete(doc)
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_paragraphs_by_source(source_file: str) -> list:
    """根据源文件获取所有段落"""
    session = get_session()
    try:
        return session.query(Document).filter(
            Document.source_file == source_file
        ).order_by(Document.paragraph_index).all()
    finally:
        session.close()


def delete_paragraphs_by_source(source_file: str) -> int:
    """删除指定源文件的所有段落"""
    session = get_session()
    try:
        count = session.query(Document).filter(
            Document.source_file == source_file
        ).delete()
        session.commit()
        return count
    finally:
        session.close()

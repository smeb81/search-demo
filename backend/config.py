import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库配置
DATABASE_PATH = os.path.join(BASE_DIR, 'documents.db')
REBUILD_DATABASE = True  # 设为 True 自动重建数据库（首次运行后改为 False）

# FAISS索引文件路径
FAISS_INDEX_PATH = os.path.join(BASE_DIR, 'faiss_index.bin')
DOC_IDS_PATH = os.path.join(BASE_DIR, 'doc_ids.pkl')

# BERT模型配置 - 使用中文多语言模型
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'  # 支持中文的多语言模型
EMBEDDING_DIM = 384  # 向量维度

# 模型量化配置
USE_QUANTIZATION = True  # 启用动态量化
QUANTIZATION_TYPE = 'dynamic'  # 动态量化

# 文本分割配置
MAX_PARAGRAPH_LENGTH = 500  # 最大段落长度
MIN_PARAGRAPH_LENGTH = 50  # 最小段落长度

# Flask配置
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000

# 搜索配置
DEFAULT_TOP_K = 5

from flask import Flask
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FLASK_HOST, FLASK_PORT
from routes.document import document_bp
from routes.search import search_bp
from routes.import_documents import import_bp

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 注册路由
app.register_blueprint(document_bp, url_prefix='/api')
app.register_blueprint(search_bp, url_prefix='/api')
app.register_blueprint(import_bp, url_prefix='/api')


@app.route('/')
def index():
    return {'message': 'Semantic Document Search API', 'status': 'running'}


@app.route('/health')
def health():
    return {'status': 'healthy'}


if __name__ == '__main__':
    print(f"Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)

import subprocess
import sys

# 先确保pip安装
subprocess.run([sys.executable, "-m", "ensurepip", "--default-pip"], capture_output=True)

# 然后安装依赖
requirements = [
    "Flask==3.0.0",
    "flask-cors==4.0.0",
    "sentence-transformers==2.2.2",
    "faiss-cpu==1.7.4",
    "SQLAlchemy==2.0.23"
]

result = subprocess.run([sys.executable, "-m", "pip", "install"] + requirements + ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

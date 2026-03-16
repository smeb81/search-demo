# Algorithmic Art MCP Server

MCP 服务器，提供生成算法艺术 SVG 代码的工具，支持多种风格。

## 功能

- **generate_algorithmic_art**: 使用 MiniMax API 生成算法艺术 SVG 代码

## 支持的风格

| 风格 | 参数值 | 描述 |
|------|--------|------|
| 科技风 | `科技风` | 深色背景 + 蓝色渐变网格 + 发光效果 |
| 分形 | `分形` | 金色螺旋结构 + 分形图案 |
| 粒子 | `粒子` | 紫色粒子效果 + 柔和光晕 |

## 安装

```bash
pip install -r requirements.txt
```

## 配置

设置环境变量：

```bash
export MINIMAX_API_KEY="your_api_key_here"
```

## 使用方法

### 作为 MCP 服务器运行

```bash
# stdio 模式（默认，用于本地工具）
python server.py

# HTTP 模式（远程访问）
python server.py --port 8000
```

### 在 Claude Code 中使用

1. 在 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "algorithmic-art": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

2. 设置环境变量：
```bash
export MINIMAX_API_KEY="your_api_key"
```

### 调用示例

```python
# 参数说明：
# - style: 艺术风格 ('科技风', '分形', '粒子')
# - width: 画布宽度 (100-2000)
# - height: 画布高度 (100-2000)
# - output_dir: 输出目录 (可选)
# - filename: 文件名 (可选)

{
  "style": "科技风",
  "width": 500,
  "height": 500
}
```

## 返回格式

成功时返回：
```json
{
  "success": true,
  "svg_code": "<svg>...</svg>",
  "filepath": "./output/tech_20240315_143022.svg",
  "style": "科技风",
  "dimensions": {
    "width": 500,
    "height": 500
  }
}
```

失败时返回：
```json
{
  "success": false,
  "error": "Error message here"
}
```

## 文件输出

生成的 SVG 文件默认保存在 `./output` 目录，文件名格式为：
- `{style}_{timestamp}.svg`

例如：`tech_20240315_143022.svg`
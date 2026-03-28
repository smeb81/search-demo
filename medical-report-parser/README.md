# 体检报告 AI 解析系统

基于 Spring Boot + Spring AI (Claude Sonnet 4.6) 的体检报告智能解析系统，支持 PDF、图片、DOCX 等格式的医学报告解析，自动提取健康指标并判断异常。

---

## 功能特性

- **多格式支持**：PDF（文本/扫描件）、图片（jpg/png/webp）、DOCX
- **AI 智能解析**：调用 Claude Sonnet 4.6 精确提取医学指标
- **自动异常判断**：内置 60+ 医学指标正常范围，自动判断偏高/偏低
- **结构化输出**：标准 JSON 返回，便于前端展示和数据处理
- **本地持久化**：JSON 文件存储，无需额外数据库

---

## 快速开始

### 1. 环境要求

- JDK 17+
- Maven 3.9+ 或 Gradle 8+

### 2. 配置 API Key

复制环境变量模板并填入你的 Anthropic API Key：

```bash
# Windows
copy .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# Linux/Mac
cp .env.example .env
```

或直接设置环境变量：

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-xxxxx"

# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
```

### 3. 编译运行

**使用 Maven：**
```bash
mvn clean package -DskipTests
java -jar target/medical-report-parser-1.0.0.jar
```

**使用 Gradle：**
```bash
gradle bootRun
```

**或直接运行启动脚本（Windows）：**
```bash
start.bat
```

服务启动后访问：**http://localhost:8081**

---

## API 接口

### 上传并解析报告
```
POST /api/medical/upload
Content-Type: multipart/form-data

参数: file (上传文件)

响应示例:
{
  "success": true,
  "message": "报告解析成功",
  "data": {
    "id": "a1b2c3d4e5f6",
    "fileName": "体检报告.pdf",
    "reportType": "体检报告",
    "title": "2024年度健康体检报告",
    "patientName": "张三",
    "examDate": "2024-03-15",
    "hospital": "某某医院",
    "totalCount": 28,
    "abnormalCount": 3,
    "summary": "本次体检共检测 28 项指标，其中 3 项异常：空腹血糖(偏高)、尿酸(偏高)、尿蛋白(异常)。建议关注并咨询医生。",
    "indicators": [
      {
        "name": "空腹血糖",
        "originalName": "GLU 空腹血糖",
        "value": "6.8",
        "numericValue": 6.8,
        "unit": "mmol/L",
        "referenceRange": "3.9-6.1 mmol/L",
        "isAbnormal": true,
        "abnormalType": "偏高",
        "category": "血糖"
      },
      ...
    ]
  }
}
```

### 查询报告列表
```
GET /api/medical/reports

响应: { "success": true, "total": 5, "data": [...] }
```

### 查询报告详情
```
GET /api/medical/reports/{id}
```

### 删除报告
```
DELETE /api/medical/reports/{id}
```

### 健康检查
```
GET /api/medical/health
```

---

## 指标覆盖范围

| 类别 | 指标数 | 示例 |
|------|--------|------|
| 血糖 | 4 | 空腹血糖、餐后2h血糖、糖化血红蛋白 |
| 血压 | 3 | 收缩压、舒张压、脉搏 |
| 血脂 | 7 | 总胆固醇、甘油三酯、HDL、LDL |
| 肝功能 | 9 | ALT、AST、GGT、胆红素系列 |
| 肾功能 | 4 | 肌酐、尿素氮、尿酸、eGFR |
| 血常规 | 11 | 白细胞、红细胞、血红蛋白、血小板 |
| 尿常规 | 8 | 尿蛋白、尿糖、尿潜血、pH值 |
| 内分泌 | 7 | 胰岛素、C肽、TSH、甲状腺激素 |
| 其他 | 10+ | 同型半胱氨酸、C反应蛋白等 |

---

## 项目结构

```
medical-report-parser/
├── pom.xml                          # Maven 依赖配置
├── build.gradle                     # Gradle 构建配置
├── src/main/java/com/medical/report/
│   ├── MedicalReportApplication.java
│   ├── config/
│   │   └── SpringAIConfig.java      # Spring AI 配置
│   ├── controller/
│   │   └── MedicalReportController.java
│   ├── service/
│   │   ├── MedicalReportService.java  # 核心解析逻辑
│   │   ├── FileExtractService.java     # 文件解析（PDF/图片）
│   │   └── NormalRangeService.java    # 正常范围 + 异常判断
│   ├── model/
│   │   ├── MedicalReport.java
│   │   ├── MedicalIndicator.java
│   │   └── ReportResult.java
│   ├── dto/
│   │   ├── MedicalReportResponse.java
│   │   └── IndicatorDto.java
│   ├── repository/
│   │   └── MedicalReportRepository.java
│   └── util/
│       └── JsonFileStorage.java
└── src/main/resources/
    ├── application.yml
    └── normal_ranges.json            # 医学指标参考范围
```

---

## 验收标准保障

### 准确性保障
- AI 提示词明确要求"严格从原文提取，不得猜测"，数值精度与报告完全一致
- Claude Sonnet 4.6 作为业界领先模型，理解医学报告格式能力强
- 支持重试机制：指标数量过少（<5项）时自动重试，最多重试2次

### 完整性保障
- 提示词要求"逐条列出所有指标，不得遗漏"
- 内置 60+ 医学指标标准名称和别名，覆盖常见体检报告各项
- 返回结果包含 `totalCount` 和 `abnormalCount`，便于核对完整性

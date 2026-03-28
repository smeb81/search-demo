package com.medical.report.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.medical.report.model.MedicalIndicator;
import com.medical.report.model.MedicalReport;
import com.medical.report.model.ReportResult;
import com.medical.report.repository.MedicalReportRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 体检报告 AI 解析核心服务
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class MedicalReportService {

    private final ChatClient chatClient;
    private final FileExtractService fileExtractService;
    private final NormalRangeService normalRangeService;
    private final MedicalReportRepository repository;
    private final ObjectMapper objectMapper;

    /** 最大重试次数（当指标数量过少时） */
    private static final int MAX_RETRIES = 2;
    /** 最小期望指标数量 */
    private static final int MIN_EXPECTED_INDICATORS = 5;

    /**
     * 上传并解析体检报告
     */
    public MedicalReport parseReport(MultipartFile file) throws IOException {
        log.info("开始解析报告: {}", file.getOriginalFilename());

        // 1. 提取文件内容
        FileExtractService.ExtractResult extractResult = fileExtractService.extract(file);
        String rawText = extractResult.getText();
        String imageBase64 = extractResult.getImageBase64();

        log.info("文件提取完成: 文本长度={}, 含图片={}", rawText.length(), !imageBase64.isEmpty());

        // 2. 调用 AI 解析（最多重试2次）
        String aiResponse = null;
        List<MedicalIndicator> indicators = new ArrayList<>();

        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                aiResponse = callClaudeParse(rawText, imageBase64, attempt);
                indicators = parseIndicatorsFromResponse(aiResponse);

                if (indicators.size() >= MIN_EXPECTED_INDICATORS) {
                    log.info("AI 解析成功（第{}次）: {} 个指标", attempt, indicators.size());
                    break;
                } else if (attempt < MAX_RETRIES) {
                    log.warn("指标数量过少（{}），重试 ({}/{})", indicators.size(), attempt, MAX_RETRIES);
                }
            } catch (Exception e) {
                log.error("AI 解析失败（第{}次）", attempt, e);
                if (attempt == MAX_RETRIES) {
                    throw new RuntimeException("AI 解析失败，已达最大重试次数: " + e.getMessage(), e);
                }
            }
        }

        log.info("AI 解析完成: 共提取 {} 个指标", indicators.size());

        // 3. 评估异常
        indicators = normalRangeService.evaluateIndicators(indicators);
        long abnormalCount = indicators.stream().filter(MedicalIndicator::isAbnormal).count();

        // 4. 构建报告结果
        ReportResult result = ReportResult.builder()
                .reportType(detectReportType(rawText))
                .title(extractTitle(rawText))
                .patientName(extractPatientName(rawText))
                .examDate(extractExamDate(rawText))
                .hospital(extractHospital(rawText))
                .indicators(indicators)
                .summary(generateSummary(indicators, abnormalCount))
                .abnormalCount((int) abnormalCount)
                .totalCount(indicators.size())
                .rawText(rawText.length() > 5000 ? rawText.substring(0, 5000) + "[截断]" : rawText)
                .rawResponse(aiResponse != null && aiResponse.length() > 2000
                        ? aiResponse.substring(0, 2000) : aiResponse)
                .build();

        // 5. 构建报告实体
        MedicalReport report = MedicalReport.builder()
                .id(UUID.randomUUID().toString().replace("-", ""))
                .fileName(file.getOriginalFilename())
                .fileType(getExtension(file.getOriginalFilename()))
                .fileSize(file.getSize())
                .result(result)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        // 6. 保存原始文件
        saveOriginalFile(file, report.getId());

        // 7. 持久化
        repository.save(report);

        log.info("报告解析完成: id={}, 指标数={}, 异常={}",
                report.getId(), indicators.size(), abnormalCount);
        return report;
    }

    /**
     * 调用 Claude 解析报告
     *
     * @param text      文档文本（OCR 提取）
     * @param imageB64  图片 base64（扫描件时使用）
     * @param attempt   当前尝试次数（用于调整提示词）
     */
    private String callClaudeParse(String text, String imageB64, int attempt) {
        String systemPrompt = buildSystemPrompt();
        String userPrompt = buildUserPrompt(text, imageB64, attempt);

        try {
            String response = chatClient.prompt()
                    .messages(
                            new SystemMessage(systemPrompt),
                            new UserMessage(userPrompt)
                    )
                    .call()
                    .content();

            return response != null ? response.trim() : "";

        } catch (Exception e) {
            throw new RuntimeException("Claude API 调用失败: " + e.getMessage(), e);
        }
    }

    /**
     * 构建系统提示词
     */
    private String buildSystemPrompt() {
        return """
                你是一位专业的医学检验医生，擅长从各种体检报告、检查单、化验单中精确提取健康指标数据。

                请严格按照以下 JSON Schema 输出（不输出任何解释，只输出 JSON）：

                {
                  "indicators": [
                    {
                      "name": "标准化指标中文名称",
                      "original_name": "报告中原始的指标名称",
                      "value": "报告中的原始数值",
                      "unit": "单位",
                      "reference_range": "报告中印刷的参考范围",
                      "note": "备注（可选）"
                    }
                  ],
                  "report_type": "报告类型",
                  "title": "报告标题",
                  "patient_name": "被检查者姓名",
                  "exam_date": "检查日期",
                  "hospital": "医院名称"
                }

                重要规则：
                1. 【准确性】严格从报告原文提取数值，不得猜测！如报告写"5.2"，输出"5.2"，不得擅自更改。
                2. 【完整性】逐条列出报告中的每一个指标，不得遗漏！包括正常指标（如尿蛋白阴性）也要列出。
                3. 【标准化】指标名称使用标准中文医学术语。
                4. 【参考范围】以报告中印刷的为准；未印刷则填"参考范围以报告为准"。
                5. 【单位】与报告一致（mmol/L、mmHg、g/L、U/L 等）。
                6. 【输出格式】只输出 JSON，以 { 开始、 } 结束，不包裹代码块，不输出解释。
                7. 【阴性指标】如尿蛋白阴性，value 填"阴性"。
                """;
    }

    /**
     * 构建用户提示词
     */
    private String buildUserPrompt(String text, String imageB64, int attempt) {
        StringBuilder sb = new StringBuilder();

        if (text != null && !text.isBlank() && text.length() > 20) {
            sb.append("【文本内容】以下是从报告中提取的文字：\n\n")
              .append(text)
              .append("\n\n");
        }

        if (imageB64 != null && !imageB64.isEmpty()) {
            sb.append("【图片内容】上述文本为空或过少，请识别图片中的所有数据。以下是报告图片（base64）：\n\n")
              .append("data:image/png;base64,")
              .append(imageB64)
              .append("\n\n")
              .append("请仔细阅读图片中的所有文字、数字和表格，提取全部健康指标。\n\n");
        }

        if (attempt > 1) {
            sb.append("【注意】上次提取的指标数量过少，请仔细检查报告中的每一个项目，确保不遗漏任何指标。\n\n");
        }

        sb.append("请严格按照 JSON Schema 输出所有指标，只输出 JSON。");

        return sb.toString();
    }

    /**
     * 解析 AI 响应中的 JSON
     */
    private List<MedicalIndicator> parseIndicatorsFromResponse(String response) {
        List<MedicalIndicator> indicators = new ArrayList<>();
        if (response == null || response.isBlank()) return indicators;

        String json = extractJson(response);
        if (json.isEmpty()) {
            log.warn("AI 响应中未找到有效 JSON: {}", response.substring(0, Math.min(200, response.length())));
            return indicators;
        }

        try {
            JsonNode root = objectMapper.readTree(json);
            JsonNode indicatorsNode = root.get("indicators");
            if (indicatorsNode != null && indicatorsNode.isArray()) {
                for (JsonNode node : indicatorsNode) {
                    try {
                        MedicalIndicator ind = MedicalIndicator.builder()
                                .name(getTextOrNull(node, "name"))
                                .originalName(getTextOrNull(node, "original_name"))
                                .value(getTextOrNull(node, "value"))
                                .unit(getTextOrNull(node, "unit"))
                                .referenceRange(getTextOrNull(node, "reference_range"))
                                .note(getTextOrNull(node, "note"))
                                .build();
                        ind.setNumericValue(normalRangeService.parseNumericValue(ind.getValue()));
                        indicators.add(ind);
                    } catch (Exception e) {
                        log.warn("解析指标节点失败: {}", node, e);
                    }
                }
            }
        } catch (JsonProcessingException e) {
            log.error("JSON 解析失败，原始响应前300字符: {}", json.substring(0, Math.min(300, json.length())), e);
        }

        return indicators;
    }

    private String getTextOrNull(JsonNode node, String field) {
        JsonNode n = node.get(field);
        return (n != null && !n.isNull()) ? n.asText() : null;
    }

    /**
     * 从 AI 响应中提取 JSON
     * 处理 markdown 代码块包裹的情况
     */
    private String extractJson(String response) {
        String trimmed = response.trim();

        // 尝试提取 ```json ... ``` 或 ``` ... ```
        Pattern pattern = Pattern.compile("```(?:json)?\\s*([\\s\\S]*?)```", Pattern.MULTILINE);
        Matcher matcher = pattern.matcher(trimmed);
        if (matcher.find()) {
            return matcher.group(1).trim();
        }

        // 直接找 { ... }
        int start = trimmed.indexOf('{');
        int end = trimmed.lastIndexOf('}');
        if (start >= 0 && end > start) {
            return trimmed.substring(start, end + 1);
        }

        return "";
    }

    // ---- 信息提取辅助方法 ----

    private String detectReportType(String text) {
        if (text == null) return "未知";
        if (text.contains("体检") || text.contains("健康体检")) return "体检报告";
        if (text.contains("化验") || text.contains("检验")) return "化验单";
        if (text.contains("影像") || text.contains("CT") || text.contains("B超")
                || text.contains("超声") || text.contains("X光")) return "检查单";
        if (text.contains("病例") || text.contains("病历")) return "病例";
        return "其他";
    }

    private String extractTitle(String text) {
        if (text == null || text.isBlank()) return null;
        String[] lines = text.split("\n");
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.length() > 2 && trimmed.length() < 60
                    && !trimmed.matches(".*\\d{4}-\\d{2}-\\d{2}.*")
                    && !trimmed.matches(".*男.*|.*女.*|.*年龄.*")) {
                return trimmed;
            }
        }
        return null;
    }

    private String extractPatientName(String text) {
        if (text == null) return null;
        Pattern pattern = Pattern.compile("姓名[：:][\\s]*([\\u4e00-\\u9fa5a-zA-Z]{2,10})");
        Matcher m = pattern.matcher(text);
        if (m.find()) return m.group(1);
        return null;
    }

    private String extractExamDate(String text) {
        if (text == null) return null;
        Pattern pattern = Pattern.compile("\\d{4}[-/年]\\d{1,2}[-/月]\\d{1,2}[日]?");
        Matcher m = pattern.matcher(text);
        if (m.find()) return m.group();
        return null;
    }

    private String extractHospital(String text) {
        if (text == null) return null;
        Pattern pattern = Pattern.compile("[\\u4e00-\\u9fa5]{2,20}(?:医院|卫生院|诊所|中心|体检|门诊)");
        Matcher m = pattern.matcher(text);
        if (m.find()) return m.group();
        return null;
    }

    private String generateSummary(List<MedicalIndicator> indicators, long abnormalCount) {
        if (indicators == null || indicators.isEmpty()) {
            return "未能提取到有效指标数据，请检查报告内容。";
        }
        int total = indicators.size();
        if (abnormalCount == 0) {
            return String.format("本次体检共检测 %d 项指标，所有指标均在正常范围内。", total);
        }
        List<String> abnormalNames = indicators.stream()
                .filter(MedicalIndicator::isAbnormal)
                .map(ind -> ind.getName() + "(" + ind.getAbnormalType() + ")")
                .toList();
        String names = String.join("、", abnormalNames);
        return String.format("本次体检共检测 %d 项指标，其中 %d 项异常：%s。建议关注并咨询医生。",
                total, abnormalCount, names);
    }

    private void saveOriginalFile(MultipartFile file, String reportId) throws IOException {
        Path dir = Paths.get("./data/uploads");
        Files.createDirectories(dir);
        String ext = getExtension(file.getOriginalFilename());
        Path dest = dir.resolve(reportId + "." + ext);
        Files.copy(file.getInputStream(), dest);
        log.info("原始文件已保存: {}", dest);
    }

    private String getExtension(String filename) {
        if (filename == null) return "";
        int lastDot = filename.lastIndexOf('.');
        return lastDot > 0 ? filename.substring(lastDot + 1).toLowerCase() : "";
    }
}

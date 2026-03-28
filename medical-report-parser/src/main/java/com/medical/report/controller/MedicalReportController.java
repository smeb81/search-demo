package com.medical.report.controller;

import com.medical.report.dto.MedicalReportResponse;
import com.medical.report.model.MedicalReport;
import com.medical.report.repository.MedicalReportRepository;
import com.medical.report.service.MedicalReportService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 体检报告 AI 解析 REST 接口
 */
@RestController
@RequestMapping("/api/medical")
@RequiredArgsConstructor
@Slf4j
@CrossOrigin(origins = "*")
public class MedicalReportController {

    private final MedicalReportService medicalReportService;
    private final MedicalReportRepository repository;

    // ---- 允许的文件类型 ----
    private static final List<String> ALLOWED_TYPES = List.of(
            "pdf", "jpg", "jpeg", "png", "webp", "gif", "bmp", "docx", "txt", "md"
    );

    // ---- 文件大小限制 ----
    private static final long MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB

    /**
     * 上传体检报告文件，AI 解析
     *
     * @param file 上传的文件（支持 PDF、图片、DOCX）
     * @return 解析结果
     */
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Map<String, Object>> uploadAndParse(
            @RequestParam("file") MultipartFile file) {

        // 1. 参数校验
        if (file == null || file.isEmpty()) {
            return badRequest("请上传文件");
        }
        if (file.getSize() > MAX_FILE_SIZE) {
            return badRequest("文件大小超过 20MB 限制");
        }
        String filename = file.getOriginalFilename();
        if (filename == null) {
            return badRequest("文件名无效");
        }
        String ext = getExtension(filename).toLowerCase();
        if (!ALLOWED_TYPES.contains(ext)) {
            return badRequest("不支持的文件格式，仅支持: " + ALLOWED_TYPES);
        }

        // 2. 解析报告
        try {
            MedicalReport report = medicalReportService.parseReport(file);
            MedicalReportResponse response = MedicalReportResponse.from(report);

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "报告解析成功");
            result.put("data", response);

            return ResponseEntity.ok(result);

        } catch (Exception e) {
            log.error("报告解析失败", e);
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("message", "解析失败: " + e.getMessage());
            error.put("error", e.getClass().getSimpleName());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
        }
    }

    /**
     * 获取所有历史报告列表（摘要）
     */
    @GetMapping("/reports")
    public ResponseEntity<Map<String, Object>> listReports() {
        try {
            List<MedicalReportRepository.MedicalReportIndex> reports = repository.findAll();

            List<Map<String, Object>> items = reports.stream()
                    .map(r -> {
                        Map<String, Object> item = new HashMap<>();
                        item.put("id", r.getId());
                        item.put("fileName", r.getFileName());
                        item.put("fileType", r.getFileType());
                        item.put("reportType", r.getReportType());
                        item.put("title", r.getTitle());
                        item.put("abnormalCount", r.getAbnormalCount());
                        item.put("totalCount", r.getTotalCount());
                        item.put("createdAt", r.getCreatedAt());
                        return item;
                    })
                    .collect(Collectors.toList());

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("total", items.size());
            result.put("data", items);
            return ResponseEntity.ok(result);

        } catch (Exception e) {
            log.error("获取报告列表失败", e);
            return serverError("获取报告列表失败: " + e.getMessage());
        }
    }

    /**
     * 获取指定报告详情
     */
    @GetMapping("/reports/{id}")
    public ResponseEntity<Map<String, Object>> getReport(@PathVariable String id) {
        try {
            var reportOpt = repository.findById(id);
            if (reportOpt.isEmpty()) {
                return notFound("报告不存在: " + id);
            }

            MedicalReportResponse response = MedicalReportResponse.from(reportOpt.get());

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("data", response);
            return ResponseEntity.ok(result);

        } catch (Exception e) {
            log.error("获取报告失败: id={}", id, e);
            return serverError("获取报告详情失败: " + e.getMessage());
        }
    }

    /**
     * 删除指定报告
     */
    @DeleteMapping("/reports/{id}")
    public ResponseEntity<Map<String, Object>> deleteReport(@PathVariable String id) {
        try {
            boolean deleted = repository.deleteById(id);
            if (!deleted) {
                return notFound("报告不存在: " + id);
            }

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "报告已删除: " + id);
            return ResponseEntity.ok(result);

        } catch (Exception e) {
            log.error("删除报告失败: id={}", id, e);
            return serverError("删除报告失败: " + e.getMessage());
        }
    }

    /**
     * 获取支持的指标类别
     */
    @GetMapping("/indicators/categories")
    public ResponseEntity<Map<String, Object>> getCategories(
            @org.springframework.beans.factory.annotation.Autowired
            com.medical.report.service.NormalRangeService normalRangeService) {
        List<String> categories = normalRangeService.getCategories();
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("data", categories);
        return ResponseEntity.ok(result);
    }

    /**
     * 健康检查
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> result = new HashMap<>();
        result.put("status", "running");
        result.put("service", "medical-report-parser");
        result.put("timestamp", java.time.Instant.now().toString());
        return ResponseEntity.ok(result);
    }

    // ---- 私有辅助方法 ----

    private ResponseEntity<Map<String, Object>> badRequest(String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("success", false);
        body.put("message", message);
        return ResponseEntity.badRequest().body(body);
    }

    private ResponseEntity<Map<String, Object>> notFound(String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("success", false);
        body.put("message", message);
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }

    private ResponseEntity<Map<String, Object>> serverError(String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("success", false);
        body.put("message", message);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(body);
    }

    private String getExtension(String filename) {
        if (filename == null) return "";
        int lastDot = filename.lastIndexOf('.');
        return lastDot > 0 ? filename.substring(lastDot + 1).toLowerCase() : "";
    }
}

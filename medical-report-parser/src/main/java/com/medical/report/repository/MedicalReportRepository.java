package com.medical.report.repository;

import com.medical.report.model.MedicalReport;
import com.medical.report.util.JsonFileStorage;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * 体检报告仓储层（本地 JSON 文件持久化）
 */
@Repository
@RequiredArgsConstructor
@Slf4j
public class MedicalReportRepository {

    private final JsonFileStorage jsonFileStorage;

    @Value("${storage.data-dir:./data}")
    private String dataDir;

    private Path reportsDir;
    private Path indexFile;

    // 内存索引：id -> MedicalReport（仅保存元数据，不含 result）
    private final Map<String, MedicalReportIndex> index = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        this.reportsDir = Paths.get(dataDir, "reports").toAbsolutePath();
        this.indexFile = reportsDir.resolve("index.json");
        try {
            Files.createDirectories(reportsDir);
            loadIndex();
        } catch (IOException e) {
            throw new RuntimeException("初始化报告存储失败", e);
        }
    }

    private void loadIndex() throws IOException {
        if (jsonFileStorage.exists(indexFile)) {
            IndexWrapper wrapper = jsonFileStorage.load(indexFile, IndexWrapper.class);
            if (wrapper != null && wrapper.records != null) {
                for (MedicalReportIndex rec : wrapper.records) {
                    index.put(rec.id, rec);
                }
            }
        }
    }

    private void saveIndex() throws IOException {
        List<MedicalReportIndex> records = new ArrayList<>(index.values());
        jsonFileStorage.save(indexFile, new IndexWrapper(records));
    }

    /**
     * 保存完整报告（含解析结果）
     */
    public MedicalReport save(MedicalReport report) throws IOException {
        if (report.getId() == null) {
            report.setId(UUID.randomUUID().toString().replace("-", ""));
        }
        report.setCreatedAt(LocalDateTime.now());
        report.setUpdatedAt(LocalDateTime.now());

        // 保存完整报告到独立文件
        Path reportFile = reportsDir.resolve(report.getId() + ".json");
        jsonFileStorage.save(reportFile, report);

        // 更新索引
        MedicalReportIndex idx = MedicalReportIndex.builder()
                .id(report.getId())
                .fileName(report.getFileName())
                .fileType(report.getFileType())
                .reportType(report.getResult() != null ? report.getResult().getReportType() : null)
                .title(report.getResult() != null ? report.getResult().getTitle() : null)
                .abnormalCount(report.getResult() != null ? report.getResult().getAbnormalCount() : 0)
                .totalCount(report.getResult() != null ? report.getResult().getTotalCount() : 0)
                .createdAt(report.getCreatedAt())
                .build();
        index.put(report.getId(), idx);
        saveIndex();

        log.info("报告已保存: id={}, 文件={}", report.getId(), report.getFileName());
        return report;
    }

    /**
     * 查询完整报告
     */
    public Optional<MedicalReport> findById(String id) throws IOException {
        Path reportFile = reportsDir.resolve(id + ".json");
        if (!jsonFileStorage.exists(reportFile)) {
            return Optional.empty();
        }
        return Optional.of(jsonFileStorage.load(reportFile, MedicalReport.class));
    }

    /**
     * 查询所有报告摘要
     */
    public List<MedicalReportIndex> findAll() {
        return new ArrayList<>(index.values()).stream()
                .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .collect(Collectors.toList());
    }

    /**
     * 删除报告
     */
    public boolean deleteById(String id) throws IOException {
        Path reportFile = reportsDir.resolve(id + ".json");
        if (!jsonFileStorage.exists(reportFile)) {
            return false;
        }
        jsonFileStorage.delete(reportFile);
        index.remove(id);
        saveIndex();
        log.info("报告已删除: id={}", id);
        return true;
    }

    /**
     * 索引记录（不含完整解析结果，用于列表展示）
     */
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class MedicalReportIndex {
        private String id;
        private String fileName;
        private String fileType;
        private String reportType;
        private String title;
        private int abnormalCount;
        private int totalCount;
        private LocalDateTime createdAt;
    }

    @lombok.Data
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    private static class IndexWrapper {
        private List<MedicalReportIndex> records;
    }
}

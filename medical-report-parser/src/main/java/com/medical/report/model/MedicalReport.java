package com.medical.report.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 体检报告实体（持久化用）
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MedicalReport {

    /**
     * 报告唯一ID
     */
    private String id;

    /**
     * 原始文件名
     */
    private String fileName;

    /**
     * 文件类型（pdf、jpg、png等）
     */
    private String fileType;

    /**
     * 文件大小（字节）
     */
    private long fileSize;

    /**
     * 原始文件存储路径
     */
    private String originalFilePath;

    /**
     * 报告类型
     */
    private String reportType;

    /**
     * 报告标题
     */
    private String title;

    /**
     * 报告解析结果
     */
    private ReportResult result;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}

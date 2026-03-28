package com.medical.report.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * AI 解析结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReportResult {

    /**
     * 报告类型（体检报告、检查单、病例等）
     */
    private String reportType;

    /**
     * 报告标题
     */
    private String title;

    /**
     * 被检查者姓名
     */
    private String patientName;

    /**
     * 检查日期
     */
    private String examDate;

    /**
     * 医院/机构名称
     */
    private String hospital;

    /**
     * 提取的所有医学指标列表
     */
    private List<MedicalIndicator> indicators;

    /**
     * 总体评价
     */
    private String summary;

    /**
     * 异常指标数量
     */
    private int abnormalCount;

    /**
     * 指标总数
     */
    private int totalCount;

    /**
     * AI 解析时使用的原始文本
     */
    private String rawText;

    /**
     * AI 原始响应（调试用）
     */
    private String rawResponse;
}

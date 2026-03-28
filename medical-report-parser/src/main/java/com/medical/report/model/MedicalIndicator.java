package com.medical.report.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 医学指标实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MedicalIndicator {

    /**
     * 指标标准化名称
     */
    private String name;

    /**
     * 指标原始名称（报告中显示的名称）
     */
    private String originalName;

    /**
     * 数值（字符串，保留原始精度）
     */
    private String value;

    /**
     * 数值（数值型，用于比较）
     */
    private Double numericValue;

    /**
     * 单位
     */
    private String unit;

    /**
     * 参考范围（报告中印刷的范围）
     */
    private String referenceRange;

    /**
     * 是否异常
     */
    @JsonProperty("isAbnormal")
    private boolean abnormal;

    /**
     * 异常类型：偏高、偏低、正常
     */
    private String abnormalType;

    /**
     * 指标类别：血糖、血压、血脂、肝功能等
     */
    private String category;

    /**
     * 备注（如有）
     */
    private String note;
}

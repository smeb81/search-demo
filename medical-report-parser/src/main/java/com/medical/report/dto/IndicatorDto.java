package com.medical.report.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 指标 DTO（接口返回用）
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IndicatorDto {

    private String name;

    private String originalName;

    private String value;

    private Double numericValue;

    private String unit;

    private String referenceRange;

    @JsonProperty("isAbnormal")
    private boolean abnormal;

    private String abnormalType;

    private String category;

    private String note;
}

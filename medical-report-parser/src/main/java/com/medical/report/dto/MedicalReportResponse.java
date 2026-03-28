package com.medical.report.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 报告返回 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MedicalReportResponse {

    private String id;

    private String fileName;

    private String fileType;

    private String reportType;

    private String title;

    private String patientName;

    private String examDate;

    private String hospital;

    private String summary;

    private List<IndicatorDto> indicators;

    @JsonProperty("abnormalCount")
    private int abnormalCount;

    private int totalCount;

    private LocalDateTime createdAt;

    private String rawText;

    public static MedicalReportResponse from(
            com.medical.report.model.MedicalReport report) {
        if (report == null || report.getResult() == null) {
            return MedicalReportResponse.builder()
                    .id(report != null ? report.getId() : null)
                    .fileName(report != null ? report.getFileName() : null)
                    .fileType(report != null ? report.getFileType() : null)
                    .reportType(report != null ? report.getReportType() : null)
                    .title(report != null ? report.getTitle() : null)
                    .createdAt(report != null ? report.getCreatedAt() : null)
                    .build();
        }

        var result = report.getResult();
        List<IndicatorDto> dtos = result.getIndicators() == null
                ? List.of()
                : result.getIndicators().stream()
                    .map(ind -> IndicatorDto.builder()
                            .name(ind.getName())
                            .originalName(ind.getOriginalName())
                            .value(ind.getValue())
                            .numericValue(ind.getNumericValue())
                            .unit(ind.getUnit())
                            .referenceRange(ind.getReferenceRange())
                            .abnormal(ind.isAbnormal())
                            .abnormalType(ind.getAbnormalType())
                            .category(ind.getCategory())
                            .note(ind.getNote())
                            .build())
                    .toList();

        return MedicalReportResponse.builder()
                .id(report.getId())
                .fileName(report.getFileName())
                .fileType(report.getFileType())
                .reportType(result.getReportType())
                .title(result.getTitle())
                .patientName(result.getPatientName())
                .examDate(result.getExamDate())
                .hospital(result.getHospital())
                .summary(result.getSummary())
                .indicators(dtos)
                .abnormalCount(result.getAbnormalCount())
                .totalCount(result.getTotalCount())
                .createdAt(report.getCreatedAt())
                .rawText(result.getRawText())
                .build();
    }
}

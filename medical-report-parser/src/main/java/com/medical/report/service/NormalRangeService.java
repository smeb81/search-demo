package com.medical.report.service;

import com.medical.report.model.MedicalIndicator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 医学指标正常范围服务
 * 负责：
 * 1. 加载本地指标参考范围配置
 * 2. 将 AI 返回的指标与参考范围对比，判断是否异常
 * 3. 对异常指标进行偏高/偏低分类
 */
@Service
@Slf4j
public class NormalRangeService {

    private final ObjectMapper objectMapper = new ObjectMapper();

    /** 标准指标配置列表 */
    private List<IndicatorConfig> configs = new ArrayList<>();

    /** 名称别名 -> 配置 的快速映射 */
    private final Map<String, IndicatorConfig> configByAlias = new HashMap<>();

    /** 标准化名称 -> 配置 */
    private final Map<String, IndicatorConfig> configByName = new HashMap<>();

    @PostConstruct
    public void init() {
        try {
            ClassPathResource resource = new ClassPathResource("normal_ranges.json");
            JsonNode root = objectMapper.readTree(resource.getInputStream());
            JsonNode indicators = root.get("indicators");
            if (indicators != null && indicators.isArray()) {
                for (JsonNode node : indicators) {
                    IndicatorConfig cfg = objectMapper.treeToValue(node, IndicatorConfig.class);
                    configs.add(cfg);
                    configByName.put(cfg.getName(), cfg);
                    if (cfg.getAliases() != null) {
                        for (String alias : cfg.getAliases()) {
                            configByAlias.put(normalize(alias), cfg);
                        }
                    }
                }
            }
            log.info("已加载 {} 条医学指标参考范围", configs.size());
        } catch (IOException e) {
            log.error("加载 normal_ranges.json 失败", e);
        }
    }

    /**
     * 判断指标是否异常
     */
    public MedicalIndicator evaluateAbnormality(MedicalIndicator indicator) {
        if (indicator.getNumericValue() == null) {
            indicator.setAbnormal(false);
            indicator.setAbnormalType("无法判断");
            return indicator;
        }

        // 先尝试用原始名称别名匹配
        IndicatorConfig cfg = findConfig(indicator.getOriginalName());
        if (cfg == null) {
            cfg = findConfig(indicator.getName());
        }

        if (cfg == null) {
            // 无法匹配配置，标记为无法判断
            indicator.setAbnormal(false);
            indicator.setAbnormalType("参考范围未知");
            return indicator;
        }

        // 阴性指标（如尿蛋白阴性）
        if (cfg.isNegativeNormal()) {
            String val = normalizeValue(indicator.getValue());
            boolean isNegative = val.contains("阴") || val.contains("-")
                    || val.equals("neg") || val.equals("normal");
            indicator.setAbnormal(!isNegative);
            indicator.setAbnormalType(isNegative ? "正常" : "异常");
            indicator.setReferenceRange(cfg.getMin() + "-" + cfg.getMax() + cfg.getUnit());
            indicator.setCategory(cfg.getCategory());
            return indicator;
        }

        double val = indicator.getNumericValue();
        double min = cfg.getMin();
        double max = cfg.getMax();

        boolean isAbnormal;
        String abnormalType;

        if (val < min) {
            isAbnormal = true;
            abnormalType = "偏低";
        } else if (val > max) {
            isAbnormal = true;
            abnormalType = "偏高";
        } else {
            isAbnormal = false;
            abnormalType = "正常";
        }

        indicator.setAbnormal(isAbnormal);
        indicator.setAbnormalType(abnormalType);
        indicator.setReferenceRange(min + "-" + max + " " + cfg.getUnit());
        indicator.setCategory(cfg.getCategory());

        return indicator;
    }

    /**
     * 批量评估指标列表的异常情况
     */
    public List<MedicalIndicator> evaluateIndicators(List<MedicalIndicator> indicators) {
        if (indicators == null) return List.of();
        return indicators.stream()
                .map(this::evaluateAbnormality)
                .toList();
    }

    /**
     * 根据名称查找配置
     */
    private IndicatorConfig findConfig(String name) {
        if (name == null) return null;
        // 精确匹配
        IndicatorConfig cfg = configByName.get(name);
        if (cfg != null) return cfg;
        // 别名匹配（标准化后）
        return configByAlias.get(normalize(name));
    }

    /**
     * 标准化指标名称（去除空格、括号、特殊字符，转小写）
     */
    private String normalize(String s) {
        return s.toLowerCase()
                .replaceAll("[\\s　]+", "")
                .replaceAll("[()（）]", "")
                .replaceAll("[/／]", "")
                .trim();
    }

    /**
     * 标准化指标值（去除空格、阴阳符号等）
     */
    private String normalizeValue(String value) {
        if (value == null) return "";
        return value.toLowerCase()
                .replaceAll("[\\s　]+", "")
                .trim();
    }

    /**
     * 尝试从字符串中提取数值
     */
    public Double parseNumericValue(String valueStr) {
        if (valueStr == null || valueStr.isBlank()) return null;
        // 移除逗号和空格
        String cleaned = valueStr.replace(",", "").replace(" ", "");
        // 匹配整数或小数（处理 Unicode 乘方符号）
        Pattern pattern = Pattern.compile("[-+]?\\d+(?:\\.\\d+)?");
        Matcher matcher = pattern.matcher(cleaned);
        if (matcher.find()) {
            try {
                return Double.parseDouble(matcher.group());
            } catch (NumberFormatException e) {
                return null;
            }
        }
        return null;
    }

    /**
     * 获取所有已配置的指标类别
     */
    public List<String> getCategories() {
        return configs.stream()
                .map(IndicatorConfig::getCategory)
                .distinct()
                .toList();
    }

    // --- 内部配置类 ---

    @lombok.Data
    public static class IndicatorConfig {
        private String name;
        private List<String> aliases;
        private double min;
        private double max;
        private String unit;
        private String category;
        private boolean negativeNormal;
    }
}

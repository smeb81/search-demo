package com.medical.report.service;

import lombok.extern.slf4j.Slf4j;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.rendering.PDFRenderer;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * 文件内容提取服务
 * 支持 PDF、图片（jpg/png/webp）、DOCX 格式
 * 图片直接转 base64 供 AI 视觉识别
 */
@Service
@Slf4j
public class FileExtractService {

    private static final int MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

    /**
     * 提取文件内容
     *
     * @param file 上传的文件
     * @return 提取结果
     */
    public ExtractResult extract(MultipartFile file) throws IOException {
        String filename = file.getOriginalFilename();
        if (filename == null) filename = "unknown";
        String ext = getExtension(filename).toLowerCase();

        return switch (ext) {
            case "pdf" -> extractPdf(file);
            case "jpg", "jpeg", "png", "webp", "gif", "bmp" -> extractImage(file);
            case "docx" -> extractDocx(file);
            case "txt", "md" -> extractText(file);
            default -> throw new IOException("不支持的文件格式: " + ext);
        };
    }

    /**
     * 提取 PDF 文本，如果文本为空（扫描件），转为图片 base64
     */
    public ExtractResult extractPdf(MultipartFile file) throws IOException {
        byte[] bytes = file.getBytes();
        StringBuilder textBuilder = new StringBuilder();
        StringBuilder imageBase64 = new StringBuilder();

        try (PDDocument document = Loader.loadPDF(bytes)) {
            PDFTextStripper stripper = new PDFTextStripper();
            int pageCount = document.getNumberOfPages();

            for (int i = 1; i <= pageCount; i++) {
                stripper.setStartPage(i);
                stripper.setEndPage(i);
                String pageText = stripper.getText(document);
                textBuilder.append(pageText).append("\n");
            }

            String text = textBuilder.toString().trim();
            log.info("PDF 文本提取: {} 页, 文本长度: {} 字符", pageCount, text.length());

            // 如果文本为空或极短（扫描件），转为图片
            if (text.length() < 50) {
                log.info("PDF 文本过少（{} 字符），转为图片供视觉识别", text.length());
                PDFRenderer renderer = new PDFRenderer(document);
                for (int i = 0; i < pageCount; i++) {
                    PDPage page = document.getPage(i);
                    float width = page.getMediaBox().getWidth();
                    float height = page.getMediaBox().getHeight();
                    float scale = Math.min(2048f / width, 2048f / height, 2.0f);

                    BufferedImage image = renderer.renderImageWithDPI(i, 150 * scale);
                    if (image != null) {
                        String b64 = encodeImageToBase64(image, "png");
                        imageBase64.append(b64).append("\n");
                    }
                }
            }
        }

        return ExtractResult.builder()
                .text(textBuilder.toString().trim())
                .imageBase64(imageBase64.toString().trim())
                .pageCount(textBuilder.toString().split("\n").length)
                .build();
    }

    /**
     * 提取图片并转为 base64
     */
    public ExtractResult extractImage(MultipartFile file) throws IOException {
        byte[] bytes = file.getBytes();
        if (bytes.length > MAX_IMAGE_SIZE) {
            log.warn("图片文件过大 ({} bytes)，将压缩处理", bytes.length);
        }

        // 尝试压缩大图
        ByteArrayInputStream bais = new ByteArrayInputStream(bytes);
        BufferedImage original = ImageIO.read(bais);

        if (original == null) {
            // 无法解码，直接 base64
            String b64 = Base64.getEncoder().encodeToString(bytes);
            return ExtractResult.builder()
                    .text("")
                    .imageBase64(b64)
                    .pageCount(1)
                    .build();
        }

        // 限制最大尺寸为 2048px 宽高
        BufferedImage scaled = scaleImage(original, 2048, 2048);
        String b64 = encodeImageToBase64(scaled, getExtension(file.getOriginalFilename()));
        log.info("图片已编码: {}x{} -> base64长度: {}", original.getWidth(), original.getHeight(), b64.length());

        return ExtractResult.builder()
                .text("")
                .imageBase64(b64)
                .pageCount(1)
                .build();
    }

    /**
     * 提取 DOCX 文本
     */
    public ExtractResult extractDocx(MultipartFile file) throws IOException {
        try (XWPFDocument document = new XWPFDocument(file.getInputStream())) {
            StringBuilder sb = new StringBuilder();
            for (XWPFParagraph para : document.getParagraphs()) {
                String text = para.getText();
                if (text != null && !text.isBlank()) {
                    sb.append(text).append("\n");
                }
            }
            String text = sb.toString().trim();
            log.info("DOCX 文本提取: {} 字符", text.length());
            return ExtractResult.builder()
                    .text(text)
                    .imageBase64("")
                    .pageCount(1)
                    .build();
        }
    }

    /**
     * 提取纯文本
     */
    public ExtractResult extractText(MultipartFile file) throws IOException {
        String text = new String(file.getBytes(), StandardCharsets.UTF_8).trim();
        log.info("TXT 文本提取: {} 字符", text.length());
        return ExtractResult.builder()
                .text(text)
                .imageBase64("")
                .pageCount(1)
                .build();
    }

    // ---- 私有辅助方法 ----

    private String getExtension(String filename) {
        if (filename == null) return "";
        int lastDot = filename.lastIndexOf('.');
        return lastDot > 0 ? filename.substring(lastDot + 1) : "";
    }

    private BufferedImage scaleImage(BufferedImage original, int maxW, int maxH) {
        int w = original.getWidth();
        int h = original.getHeight();
        if (w <= maxW && h <= maxH) return original;

        double scale = Math.min((double) maxW / w, (double) maxH / h);
        int newW = (int) (w * scale);
        int newH = (int) (h * scale);
        BufferedImage scaled = new BufferedImage(newW, newH, BufferedImage.TYPE_INT_RGB);
        scaled.getGraphics().drawImage(
                original.getScaledInstance(newW, newH, java.awt.Image.SCALE_SMOOTH),
                0, 0, null);
        return scaled;
    }

    private String encodeImageToBase64(BufferedImage image, String format) throws IOException {
        java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
        ImageIO.write(image, format != null && format.equalsIgnoreCase("jpg") ? "png" : format, baos);
        return Base64.getEncoder().encodeToString(baos.toByteArray());
    }

    // ---- 提取结果封装 ----

    @lombok.Data
    @lombok.Builder
    @lombok.AllArgsConstructor
    @lombok.NoArgsConstructor
    public static class ExtractResult {
        /** 提取的文本内容 */
        private String text;
        /** 图片 base64 编码（扫描件或纯图片格式） */
        private String imageBase64;
        /** 页数/数量 */
        private int pageCount;
    }
}

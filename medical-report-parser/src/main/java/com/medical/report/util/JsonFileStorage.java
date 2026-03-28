package com.medical.report.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;

/**
 * JSON 文件存储工具类
 */
@Component
public class JsonFileStorage {

    private final ObjectMapper objectMapper;

    public JsonFileStorage() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }

    public <T> void save(Path filePath, T obj) throws IOException {
        Files.createDirectories(filePath.getParent());
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(filePath.toFile(), obj);
    }

    public <T> T load(Path filePath, Class<T> clazz) throws IOException {
        return objectMapper.readValue(filePath.toFile(), clazz);
    }

    public boolean exists(Path filePath) {
        return Files.exists(filePath);
    }

    public void delete(Path filePath) throws IOException {
        Files.deleteIfExists(filePath);
    }

    public List<Path> listJsonFiles(Path dir) throws IOException {
        if (!Files.exists(dir)) {
            return List.of();
        }
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.json")) {
            return stream.collect(Collectors.toList());
        }
    }

    public ObjectMapper getObjectMapper() {
        return objectMapper;
    }
}

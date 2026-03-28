package com.medical.report.config;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SpringAIConfig {

    @Bean
    public ChatClient chatClient(org.springframework.ai.anthropic.AnthropicChatModel chatModel) {
        return ChatClient.builder(chatModel).build();
    }
}

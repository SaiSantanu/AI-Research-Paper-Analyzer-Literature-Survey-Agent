package com.research.research_chat.model;

import java.util.List;

public class AskRequest {
    private String topic;
    private String question;
    private List<ChatMessage> history;

    public AskRequest() {}

    public String getTopic()    { return topic; }
    public void setTopic(String t) { this.topic = t; }

    public String getQuestion()    { return question; }
    public void setQuestion(String q) { this.question = q; }

    public List<ChatMessage> getHistory() { return history; }
    public void setHistory(List<ChatMessage> h) { this.history = h; }

    // Inner class for chat history messages
    public static class ChatMessage {
        private String role;
        private String content;

        public ChatMessage() {}
        public String getRole()    { return role; }
        public void setRole(String r) { this.role = r; }
        public String getContent() { return content; }
        public void setContent(String c) { this.content = c; }
    }
}
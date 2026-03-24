package com.research.research_chat.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.research.research_chat.model.AskRequest;
import com.research.research_chat.model.AskResponse;
import com.research.research_chat.model.ResearchResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class PipelineService {

    @Value("${pipeline.url:http://localhost:8502}")
    private String pipelineUrl;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper mapper = new ObjectMapper();

    public ResearchResponse runResearch(String topic) {
        ResearchResponse response = new ResearchResponse();
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, String> body = new HashMap<>();
            body.put("topic", topic);
            HttpEntity<Map<String, String>> request = new HttpEntity<>(body, headers);
            ResponseEntity<String> raw = restTemplate.postForEntity(
                pipelineUrl + "/api/research", request, String.class);
            if (raw.getStatusCode().is2xxSuccessful()) {
                JsonNode json = mapper.readTree(raw.getBody());
                response.setStatus("done");
                response.setReport(json.path("final_report").asText(""));
                response.setPaperCount(json.path("paper_count").asInt(0));
                response.setReviewScore(json.path("review_score").asInt(0));
                response.setRevisionCount(json.path("revision_count").asInt(0));
            } else {
                response.setStatus("error");
                response.setError("Pipeline returned: " + raw.getStatusCode());
            }
        } catch (ResourceAccessException e) {
            response.setStatus("error");
            response.setError("Cannot reach the Python pipeline at " + pipelineUrl + ". Make sure bridge.py is running.");
        } catch (Exception e) {
            response.setStatus("error");
            response.setError("Unexpected error: " + e.getMessage());
        }
        return response;
    }

    public AskResponse askQuestion(AskRequest askRequest) {
        AskResponse response = new AskResponse();
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = new HashMap<>();
            body.put("topic", askRequest.getTopic());
            body.put("question", askRequest.getQuestion());
            body.put("history", askRequest.getHistory() != null ? askRequest.getHistory() : new ArrayList<>());
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<String> raw = restTemplate.postForEntity(
                pipelineUrl + "/api/ask", request, String.class);
            if (raw.getStatusCode().is2xxSuccessful()) {
                JsonNode json = mapper.readTree(raw.getBody());
                response.setStatus("done");
                response.setAnswer(json.path("answer").asText(""));
                response.setTopic(json.path("topic").asText(""));
                List<String> papersUsed = new ArrayList<>();
                json.path("papers_used").forEach(n -> papersUsed.add(n.asText()));
                response.setPapersUsed(papersUsed);
                List<String> paperTitles = new ArrayList<>();
                json.path("paper_titles").forEach(n -> paperTitles.add(n.asText()));
                response.setPaperTitles(paperTitles);
            } else {
                response.setStatus("error");
                response.setError("Pipeline returned: " + raw.getStatusCode());
            }
        } catch (ResourceAccessException e) {
            response.setStatus("error");
            response.setError("Cannot reach the Python pipeline. Make sure bridge.py is running.");
        } catch (Exception e) {
            response.setStatus("error");
            response.setError("Unexpected error: " + e.getMessage());
        }
        return response;
    }

    public byte[] exportPdf(String topic) {
        try { return restTemplate.getForObject(pipelineUrl + "/api/export/pdf?topic=" + topic, byte[].class); }
        catch (Exception e) { return null; }
    }

    public byte[] exportMarkdown(String topic) {
        try { return restTemplate.getForObject(pipelineUrl + "/api/export/md?topic=" + topic, byte[].class); }
        catch (Exception e) { return null; }
    }
}
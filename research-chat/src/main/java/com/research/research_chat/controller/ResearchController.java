package com.research.research_chat.controller;

import com.research.research_chat.model.AskRequest;
import com.research.research_chat.model.AskResponse;
import com.research.research_chat.model.ResearchRequest;
import com.research.research_chat.model.ResearchResponse;
import com.research.research_chat.service.PipelineService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:5173")
public class ResearchController {

    @Autowired
    private PipelineService pipelineService;

    /** POST /api/research */
    @PostMapping("/research")
    public ResponseEntity<ResearchResponse> research(@RequestBody ResearchRequest req) {
        if (req.getTopic() == null || req.getTopic().isBlank()) {
            ResearchResponse err = new ResearchResponse();
            err.setStatus("error");
            err.setError("Topic cannot be empty");
            return ResponseEntity.badRequest().body(err);
        }
        ResearchResponse result = pipelineService.runResearch(req.getTopic().trim());
        HttpStatus status = "error".equals(result.getStatus()) ? HttpStatus.BAD_GATEWAY : HttpStatus.OK;
        return ResponseEntity.status(status).body(result);
    }

    /** POST /api/ask */
    @PostMapping("/ask")
    public ResponseEntity<AskResponse> ask(@RequestBody AskRequest req) {
        if (req.getTopic() == null || req.getTopic().isBlank() ||
            req.getQuestion() == null || req.getQuestion().isBlank()) {
            AskResponse err = new AskResponse();
            err.setStatus("error");
            err.setError("Topic and question are required");
            return ResponseEntity.badRequest().body(err);
        }
        AskResponse result = pipelineService.askQuestion(req);
        HttpStatus status = "error".equals(result.getStatus()) ? HttpStatus.BAD_GATEWAY : HttpStatus.OK;
        return ResponseEntity.status(status).body(result);
    }

    /** GET /api/export/pdf?topic=... */
    @GetMapping("/export/pdf")
    public ResponseEntity<byte[]> exportPdf(@RequestParam String topic) {
        byte[] pdf = pipelineService.exportPdf(topic);
        if (pdf == null || pdf.length == 0) return ResponseEntity.status(HttpStatus.BAD_GATEWAY).build();
        String filename = "literature_review_" + topic.replace(" ", "_") + ".pdf";
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + "\"")
            .contentType(MediaType.APPLICATION_PDF)
            .body(pdf);
    }

    /** GET /api/export/md?topic=... */
    @GetMapping("/export/md")
    public ResponseEntity<byte[]> exportMd(@RequestParam String topic) {
        byte[] md = pipelineService.exportMarkdown(topic);
        if (md == null || md.length == 0) return ResponseEntity.status(HttpStatus.BAD_GATEWAY).build();
        String filename = "literature_review_" + topic.replace(" ", "_") + ".md";
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + "\"")
            .contentType(MediaType.parseMediaType("text/markdown"))
            .body(md);
    }

    /** GET /api/health */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("{\"status\":\"ok\",\"service\":\"ScholarAI\"}");
    }
}
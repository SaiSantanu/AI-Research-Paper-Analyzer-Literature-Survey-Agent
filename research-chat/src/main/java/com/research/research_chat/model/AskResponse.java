package com.research.research_chat.model;

import java.util.List;

public class AskResponse {
    private String status;
    private String answer;
    private String topic;
    private List<String> papersUsed;
    private List<String> paperTitles;
    private String error;

    public AskResponse() {}

    public String getStatus()           { return status; }
    public void   setStatus(String s)   { this.status = s; }

    public String getAnswer()           { return answer; }
    public void   setAnswer(String a)   { this.answer = a; }

    public String getTopic()            { return topic; }
    public void   setTopic(String t)    { this.topic = t; }

    public List<String> getPapersUsed()              { return papersUsed; }
    public void         setPapersUsed(List<String> p){ this.papersUsed = p; }

    public List<String> getPaperTitles()              { return paperTitles; }
    public void         setPaperTitles(List<String> p){ this.paperTitles = p; }

    public String getError()            { return error; }
    public void   setError(String e)    { this.error = e; }
}
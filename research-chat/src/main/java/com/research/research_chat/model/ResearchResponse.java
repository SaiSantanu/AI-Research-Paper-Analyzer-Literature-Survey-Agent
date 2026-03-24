package com.research.research_chat.model;

public class ResearchResponse {
    private String status;
    private String report;
    private int    paperCount;
    private int    reviewScore;
    private int    revisionCount;
    private String error;

    public ResearchResponse() {}

    public String getStatus()            { return status; }
    public void   setStatus(String s)    { this.status = s; }

    public String getReport()            { return report; }
    public void   setReport(String r)    { this.report = r; }

    public int  getPaperCount()          { return paperCount; }
    public void setPaperCount(int n)     { this.paperCount = n; }

    public int  getReviewScore()         { return reviewScore; }
    public void setReviewScore(int s)    { this.reviewScore = s; }

    public int  getRevisionCount()       { return revisionCount; }
    public void setRevisionCount(int n)  { this.revisionCount = n; }

    public String getError()             { return error; }
    public void   setError(String e)     { this.error = e; }
}
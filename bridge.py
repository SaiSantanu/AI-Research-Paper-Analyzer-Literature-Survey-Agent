"""
bridge.py - FastAPI REST bridge between Spring Boot and the Python pipeline.

Run with:
    uvicorn bridge:app --port 8502 --reload

Endpoints:
    POST /api/research        { "topic": "..." }
    POST /api/ask             { "topic": "...", "question": "...", "history": [...] }
    GET  /api/export/pdf?topic=...
    GET  /api/export/md?topic=...
    GET  /api/health
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from pipeline import (
    create_state, planner_agent, searcher_agent,
    reader_agent, build_vectorstore, reader_agent_rag,
    synthesizer_agent, reviewer_agent, reviser_agent,
    query_vectorstore, answer_question_with_llm,
    answer_question_rag_only, ollama_available,
    MAX_REVIEW_LOOPS
)
from pdf_generator import generate_ieee_pdf

app = FastAPI(title="ScholarAI Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache: topic -> final state
_cache: dict = {}


# -- Request models ------------------------------------------------------------

class ResearchRequest(BaseModel):
    topic: str


class ChatMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    topic: str
    question: str
    history: Optional[List[ChatMessage]] = []


# -- Routes --------------------------------------------------------------------

@app.post("/api/research")
async def run_research(req: ResearchRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    try:
        state = create_state(topic)
        state = planner_agent(state)      # also checks Ollama availability
        state = searcher_agent(state)

        if not state["papers"]:
            return {
                "status":         "done",
                "final_report":   "",
                "paper_count":    0,
                "review_score":   0,
                "revision_count": 0,
                "ollama_used":    False,
            }

        state = reader_agent(state)
        state = build_vectorstore(state)
        state = reader_agent_rag(state)   # uses Ollama if available
        state = synthesizer_agent(state)  # uses Ollama for summary if available

        for _ in range(MAX_REVIEW_LOOPS + 1):
            state = reviewer_agent(state)
            if not state["needs_revision"]:
                break
            state = reviser_agent(state)

        _cache[topic] = state

        return {
            "status":         "done",
            "final_report":   state["final_report"],
            "paper_count":    len(state["papers"]),
            "review_score":   state["review_score"],
            "revision_count": state["revision_count"],
            "ollama_used":    state.get("ollama_active", False),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
async def ask_question(req: AskRequest):
    topic    = req.topic.strip()
    question = req.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    state = _cache.get(topic)
    if not state or state.get("chroma_collection") is None:
        raise HTTPException(
            status_code=404,
            detail="No research data found for this topic. Run /api/research first."
        )

    try:
        # Retrieve relevant chunks from vector store
        hits = query_vectorstore(state, question, top_k=6)

        # Build history list for context
        history = [{"role": m.role, "content": m.content} for m in (req.history or [])]

        # Use Ollama if available, else fall back to RAG-only
        if state.get("ollama_active") and ollama_available():
            answer = answer_question_with_llm(question, hits, topic, history)
            if not answer or len(answer) < 20:
                answer = answer_question_rag_only(question, hits)
            method = "llm"
        else:
            answer = answer_question_rag_only(question, hits)
            method = "rag"

        paper_titles = [p["title"] for p in state.get("papers", [])]
        papers_used  = list({h["meta"].get("title", "")[:60] for h in hits})

        return {
            "status":       "done",
            "answer":       answer,
            "topic":        topic,
            "papers_used":  papers_used,
            "paper_titles": paper_titles,
            "method":       method,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/pdf")
async def export_pdf(topic: str):
    state = _cache.get(topic)
    if not state or not state.get("final_report"):
        raise HTTPException(status_code=404, detail="Run /api/research first.")
    pdf      = generate_ieee_pdf(state, topic)
    filename = "literature_review_" + topic.replace(" ", "_") + ".pdf"
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="' + filename + '"'}
    )


@app.get("/api/export/md")
async def export_md(topic: str):
    state = _cache.get(topic)
    if not state or not state.get("final_report"):
        raise HTTPException(status_code=404, detail="Run /api/research first.")
    content  = "# Literature Review: " + topic + "\n\n" + state["final_report"]
    filename = "literature_review_" + topic.replace(" ", "_") + ".md"
    return Response(
        content=content.encode("utf-8"), media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="' + filename + '"'}
    )


@app.get("/api/health")
async def health():
    olm = ollama_available()
    return {
        "status":  "ok",
        "service": "ScholarAI Bridge",
        "ollama":  "running" if olm else "offline",
        "model":   "llama3" if olm else "N/A",
    }


if __name__ == "__main__":
    uvicorn.run("bridge:app", host="0.0.0.0", port=8502, reload=True)
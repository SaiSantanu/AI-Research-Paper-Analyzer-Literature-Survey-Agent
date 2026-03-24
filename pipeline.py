"""
pipeline.py - All agent functions for the Research Paper Analyzer.
Imported by bridge.py (FastAPI) and app.py (Streamlit).

Ollama is used in:
  1. reader_agent_rag() - summarizes methodology, results, limitations per paper
  2. synthesizer_agent() - writes the final report introduction and conclusion
  3. query_vectorstore_with_llm() - answers follow-up questions properly
"""

import requests
import feedparser
import urllib.parse
import urllib.request
import fitz  # PyMuPDF
import os
import re
import uuid
from typing import TypedDict, List, Dict, Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer

# -- Constants -----------------------------------------------------------------
REVIEW_THRESHOLD = 7
MAX_REVIEW_LOOPS = 3
OLLAMA_URL       = "http://localhost:11434/api/generate"

# Your installed models (from: ollama list):
#   mistral:latest       7.2B  - best for academic writing  (RECOMMENDED)
#   qwen2.5:latest       7.6B  - highest quality, slightly slower
#   llama3:latest        8.0B  - best for conversational Q&A
#   gemma:2b             3B    - fastest option
#   deepseek-coder:1.3b  1B    - code only, not suitable here
OLLAMA_MODEL = "gemma:2b"   # change this to switch models

print("Loading embedding model...")
EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model ready")


# -- Ollama helper -------------------------------------------------------------

def ask_ollama(prompt, max_tokens=300, temperature=0.3):
    """
    Call local Ollama LLM. Returns clean text response.
    Falls back gracefully if Ollama is not running.
    """
    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model":   OLLAMA_MODEL,
                "prompt":  prompt,
                "stream":  False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            },
            timeout=120
        )
        res.raise_for_status()
        text = res.json().get("response", "").strip()
        return text if text else None
    except requests.exceptions.ConnectionError:
        print("  [Ollama] Not running - falling back to RAG extraction")
        return None
    except requests.exceptions.Timeout:
        print("  [Ollama] Timeout - falling back to RAG extraction")
        return None
    except requests.exceptions.HTTPError as e:
        # Print the actual error body from Ollama for debugging
        body = ""
        try: body = e.response.text[:200]
        except: pass
        print("  [Ollama] HTTP " + str(e.response.status_code) + ": " + body)
        return None
    except Exception as e:
        print("  [Ollama] Error: " + str(e))
        return None


def ollama_available():
    """Quick check if Ollama is running."""
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=3)
        return res.status_code == 200
    except Exception:
        return False


# -- State ---------------------------------------------------------------------

class ResearchState(TypedDict):
    topic             : str
    plan              : List[str]
    papers            : List[Dict[str, Any]]
    raw_text          : List[str]
    summaries         : List[str]
    extractions       : List[Dict[str, Any]]
    chroma_client     : Optional[Any]
    chroma_collection : Optional[Any]
    review_feedback   : str
    review_score      : int
    revision_count    : int
    needs_revision    : bool
    final_report      : str
    ollama_active     : bool   # tracks if Ollama is being used this run


def create_state(topic: str) -> ResearchState:
    return ResearchState(
        topic=topic, plan=[], papers=[], raw_text=[],
        summaries=[], extractions=[],
        chroma_client=None, chroma_collection=None,
        review_feedback="", review_score=0,
        revision_count=0, needs_revision=False,
        final_report="", ollama_active=False
    )


# -- Planner -------------------------------------------------------------------

def planner_agent(state):
    topic = state["topic"]
    tasks = [
        "Search papers about " + topic,
        "Extract methodology",
        "Extract results",
        "Summarize findings"
    ]
    state["plan"] = tasks
    print("Planner Output: " + str(state["plan"]))

    # Check Ollama once at pipeline start
    active = ollama_available()
    state["ollama_active"] = active
    if active:
        print("Ollama is running - LLM summaries enabled")
    else:
        print("Ollama not detected - using RAG extraction only")

    return state


# -- arXiv search --------------------------------------------------------------

def search_arxiv(query, max_results=10):
    encoded_query = urllib.parse.quote(query)
    url = (
        "http://export.arxiv.org/api/query"
        "?search_query=all:" + encoded_query +
        "&start=0&max_results=" + str(max_results)
    )
    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries:
        pdf_link = ""
        for link in entry.links:
            if link.get("type") == "application/pdf":
                pdf_link = link.href
        if not pdf_link and hasattr(entry, "id"):
            arxiv_id = entry.id.split("/abs/")[-1]
            pdf_link = "https://arxiv.org/pdf/" + arxiv_id + ".pdf"
        papers.append({
            "title":   entry.title,
            "summary": entry.summary,
            "pdf":     pdf_link
        })
    return papers


def is_relevant(paper, topic):
    text = (paper["title"] + " " + paper["summary"]).lower()
    stopwords = {
        "in", "on", "of", "and", "the", "for", "with",
        "a", "an", "to", "at", "by", "is", "are", "was",
        "ai", "using", "based", "towards", "via"
    }
    topic_words = [w for w in topic.lower().split() if w not in stopwords]
    if not topic_words:
        return True
    matched = sum(1 for word in topic_words if word in text)
    return matched == len(topic_words)


def searcher_agent(state):
    topic = state["topic"]
    papers = search_arxiv(topic, max_results=50)
    filtered = [p for p in papers if is_relevant(p, topic)]
    if not filtered:
        print("No relevant papers found. Using all fetched papers.")
        filtered = papers
    state["papers"] = filtered[:10]
    print("Filtered Papers:")
    for p in state["papers"]:
        print("  - " + p["title"])
    return state


# -- Reader --------------------------------------------------------------------

def download_pdf(url, filename):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (research-tool)"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            with open(filename, "wb") as f:
                f.write(resp.read())
        return filename
    except Exception as e:
        print("Failed to download " + url + ": " + str(e))
        return None


def extract_text(pdf_path, char_limit=5000):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
            if len(text) >= char_limit:
                break
        doc.close()
        return text[:char_limit]
    except Exception as e:
        print("Text extraction failed: " + str(e))
        return ""


def reader_agent(state):
    papers = state["papers"]
    raw_text, summaries = [], []
    os.makedirs("papers", exist_ok=True)

    for i, paper in enumerate(papers):
        print("Processing: " + paper["title"])
        if not paper.get("pdf"):
            raw_text.append("")
            summaries.append("No PDF link")
            continue
        pdf_path = "papers/paper_" + str(i) + ".pdf"
        file = download_pdf(paper["pdf"], pdf_path)
        if file:
            text = extract_text(file)
            raw_text.append(text)
            summaries.append("Extracted: " + paper["title"])
        else:
            raw_text.append("")
            summaries.append("Download failed")

    state["raw_text"]  = raw_text
    state["summaries"] = summaries
    return state


# -- Vector Store --------------------------------------------------------------

def chunk_text(text, chunk_size=500, overlap=100):
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def build_vectorstore(state):
    papers    = state["papers"]
    raw_texts = state["raw_text"]
    client    = chromadb.Client()

    collection_name = re.sub(r'[^a-z0-9-]', '-', state["topic"].lower())[:40]
    collection = client.get_or_create_collection(collection_name)

    total = 0
    for idx, (paper, text) in enumerate(zip(papers, raw_texts)):
        if not text:
            continue
        chunks     = chunk_text(text)
        embeddings = EMBED_MODEL.encode(chunks, show_progress_bar=False).tolist()
        collection.upsert(
            ids        = [str(uuid.uuid4()) for _ in chunks],
            documents  = chunks,
            embeddings = embeddings,
            metadatas  = [{"paper_idx": idx, "title": paper.get("title", "")} for _ in chunks]
        )
        total += len(chunks)
        print("  Paper " + str(idx) + ": " + str(len(chunks)) + " chunks indexed")

    state["chroma_client"]     = client
    state["chroma_collection"] = collection
    print("Vector store built - " + str(total) + " total chunks")
    return state


def query_vectorstore(state, query, paper_idx=None, top_k=5):
    collection      = state["chroma_collection"]
    query_embedding = EMBED_MODEL.encode([query], show_progress_bar=False).tolist()
    where_filter    = {"paper_idx": paper_idx} if paper_idx is not None else None

    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = top_k,
        where            = where_filter,
        include          = ["documents", "metadatas", "distances"]
    )
    return [
        {"text": c, "score": round(1 - d, 3), "meta": m}
        for c, d, m in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0]
        )
    ]


# -- RAG Reader (with Ollama) --------------------------------------------------

RAG_QUERIES = {
    "methodology": "research method approach model architecture dataset training procedure",
    "results":     "accuracy performance evaluation metrics benchmark results findings",
    "limitations": "limitations future work failure cases drawbacks challenges",
}

# Prompts for Ollama - kept short to avoid context window overflow
EXTRACTION_PROMPTS = {
    "methodology": (
        "Paper: {title}\n"
        "Text: {context}\n\n"
        "Respond with ONLY 2 sentences describing the research methodology. "
        "No introduction, no bullet points, no 'Sure'. Start directly with the content:"
    ),
    "results": (
        "Paper: {title}\n"
        "Text: {context}\n\n"
        "Respond with ONLY 2 sentences summarizing the key results. "
        "Include specific numbers if present. No introduction, no 'Sure'. Start directly:"
    ),
    "limitations": (
        "Paper: {title}\n"
        "Text: {context}\n\n"
        "Respond with ONLY 1-2 sentences about the main limitations. "
        "No introduction, no bullet points, no 'Sure'. Start directly with the content:"
    ),
}


def clean_llm_output(text):
    """Strip common LLM filler phrases and format bullet lists as prose."""
    if not text:
        return text
    import re

    # Apply to every line (handles multi-line LLM responses)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        if not l:
            continue
        # Remove "Sure, here's..." variants - with or without colon
        l = re.sub("^Sure,?.*?:", "", l, flags=re.IGNORECASE).strip()
        l = re.sub("^Sure,? *", "", l, flags=re.IGNORECASE).strip()
        # Remove "Of course / Certainly" openers
        l = re.sub("^(Of course|Certainly|Absolutely)[,!]?.*?:", "", l, flags=re.IGNORECASE).strip()
        # Remove "Here's the..." openers
        l = re.sub("^Here.s[^:]*:", "", l, flags=re.IGNORECASE).strip()
        # Remove bold section headers e.g. **Key Results:**
        l = re.sub("^[*][*][^*]+[*][*][: *]+", "", l, flags=re.IGNORECASE).strip()
        l = re.sub("^(Key Results|Methodology|Limitations|Accuracy)[: ]+", "", l, flags=re.IGNORECASE).strip()
        # Remove leading bullets
        l = re.sub("^[-*] +", "", l).strip()
        if l:
            cleaned_lines.append(l)

    # Join lines and convert inline bullet separators to spaces
    text = " ".join(cleaned_lines)
    text = re.sub(" [-*] ", " ", text)
    text = re.sub("  +", " ", text).strip()

    return text


def extract_field_with_ollama(title, context_chunks, field):
    """Use Ollama to generate a clean summary for a specific field."""
    # Trim each chunk to 300 chars and use only top 2 to avoid context overflow
    trimmed = [c[:300] for c in context_chunks[:2]]
    context = " ".join(trimmed)[:600]   # hard cap at 600 total chars
    prompt  = EXTRACTION_PROMPTS[field].format(
        title   = title[:80],
        context = context
    )
    result  = ask_ollama(prompt, max_tokens=150, temperature=0.2)
    if result:
        result = clean_llm_output(result)
    return result


def extract_field_from_chunks(chunks):
    """Fallback: extract best content from RAG chunks without LLM."""
    if not chunks:
        return "Not found in paper."

    seen, unique = set(), []
    for h in chunks:
        key = h["text"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(h["text"])

    # Clean the text
    text = " [...] ".join(unique)
    text = re.sub(r'\[\.{2,3}\]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    if text and text[0].islower():
        match = re.search(r'(?<=[.!?] )[A-Z]', text)
        if match:
            text = text[match.start() - 1:]
        else:
            text = text[0].upper() + text[1:]

    return text[:600] if text else "Not found in paper."


def reader_agent_rag(state):
    """
    RAG-based reader with optional Ollama LLM summarization.
    If Ollama is running: generates clean academic summaries.
    If Ollama is offline: falls back to best RAG chunk extraction.
    """
    papers         = state["papers"]
    extractions    = []
    use_llm        = state.get("ollama_active", False)

    if use_llm:
        print("Using Ollama LLM for extraction")
    else:
        print("Using RAG chunk extraction (Ollama offline)")

    for idx, paper in enumerate(papers):
        title = paper["title"]
        print("Extracting: " + title[:70])
        ext = {"title": title, "pdf": paper.get("pdf", "")}

        for field, query in RAG_QUERIES.items():
            hits = query_vectorstore(
                state,
                query     = title + " " + query,
                paper_idx = idx,
                top_k     = 5
            )

            if use_llm and hits:
                # Try LLM summarization
                context_chunks = [h["text"] for h in hits[:3]]
                llm_result     = extract_field_with_ollama(title, context_chunks, field)

                if llm_result and len(llm_result) > 30:
                    ext[field] = llm_result
                    print("  " + field + ": LLM summary generated")
                else:
                    # LLM gave empty result, fall back
                    ext[field] = extract_field_from_chunks(hits)
                    print("  " + field + ": LLM empty, used RAG fallback")
            else:
                ext[field] = extract_field_from_chunks(hits)
                if not hits:
                    print("  " + field + ": no chunks found")

        extractions.append(ext)

    state["extractions"] = extractions
    return state


# -- Synthesizer (with Ollama) -------------------------------------------------

def synthesizer_agent(state):
    extractions  = state.get("extractions", [])
    use_llm      = state.get("ollama_active", False)

    # Build the report header
    report  = "# Literature Review\n" + "=" * 60 + "\n\n"
    report += "**Topic:** " + state["topic"] + "\n"
    report += "**Papers analysed:** " + str(len(extractions)) + "\n\n"
    report += "=" * 60 + "\n\n"

    # Per-paper sections
    for i, ext in enumerate(extractions, 1):
        report += "## [" + str(i) + "] " + ext["title"] + "\n\n"
        report += "**Methodology:**\n"  + ext.get("methodology", "N/A")[:600] + "\n\n"
        report += "**Key Results:**\n"  + ext.get("results",     "N/A")[:600] + "\n\n"
        report += "**Limitations:**\n"  + ext.get("limitations", "N/A")[:400] + "\n\n"
        report += "-" * 50 + "\n\n"

    # Optional: LLM-generated overall summary paragraph
    if use_llm and len(extractions) > 0:
        print("Generating overall summary with Ollama...")
        titles = ", ".join([e["title"][:50] for e in extractions[:5]])
        summary_prompt = (
            "Write a 3-4 sentence academic summary paragraph for a literature review on the topic: "
            + state["topic"] + ".\n"
            "The review covers the following papers: " + titles + ".\n"
            "Mention key themes, common methodological approaches, and overall research trends. "
            "Write in formal academic style. Do not use bullet points."
        )
        summary = ask_ollama(summary_prompt, max_tokens=250, temperature=0.4)
        if summary:
            report += "\n## Overall Summary\n\n" + summary + "\n"

    state["final_report"] = report
    return state


# -- Ask (with Ollama) ---------------------------------------------------------

def answer_question_with_llm(question, hits, topic, chat_history=None):
    """
    Use Ollama to give a proper conversational answer based on
    retrieved paper chunks. Much better than raw chunk pasting.
    """
    if not hits:
        return (
            "I could not find relevant information about that in the papers. "
            "Try rephrasing or asking about methodology, results, or limitations."
        )

    # Build context from top hits
    context_parts = []
    seen_titles   = set()
    for h in hits[:5]:
        t = h["meta"].get("title", "")[:60]
        if t not in seen_titles:
            seen_titles.add(t)
            context_parts.append("[" + t + "]\n" + h["text"][:400])

    context = "\n\n".join(context_parts)

    # Build chat history context (last 3 exchanges)
    history_str = ""
    if chat_history:
        recent = chat_history[-6:]  # last 3 user+assistant pairs
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_str += role + ": " + msg.get("content", "")[:200] + "\n"

    prompt = (
        "You are a research assistant. Answer based only on these excerpts.\n\n"
        "Topic: " + topic + "\n"
        "Question: " + question + "\n\n"
        "Excerpts:\n" + context[:800] + "\n\n"
        "Answer in 2-3 sentences:"
    )

    result = ask_ollama(prompt, max_tokens=350, temperature=0.3)
    return result


def answer_question_rag_only(question, hits):
    """Fallback answer builder without LLM."""
    if not hits:
        return (
            "I could not find specific information about that in the papers. "
            "Try rephrasing your question or asking about methodology, results, or limitations."
        )

    by_paper = {}
    for h in hits:
        title = h["meta"].get("title", "Unknown Paper")[:70]
        if title not in by_paper:
            by_paper[title] = []
        by_paper[title].append(h["text"])

    answer = "Based on the papers in this review:\n\n"
    for title, chunks in by_paper.items():
        answer += "**" + title + "**\n"
        seen = set()
        for chunk in chunks[:2]:
            clean = chunk.strip()[:300]
            key   = clean[:60]
            if key not in seen:
                seen.add(key)
                answer += "- " + clean + "\n"
        answer += "\n"

    return answer.strip()


# -- Reviewer ------------------------------------------------------------------

def reviewer_agent(state):
    report   = state["final_report"]
    papers   = state["papers"]
    revision = state["revision_count"]

    print("Reviewer running (revision #" + str(revision) + ")...")
    feedback_parts, score = [], 10

    for section in ["Methodology", "Results", "Limitations"]:
        if section not in report:
            score -= 2
            feedback_parts.append("MISSING SECTIONS: " + section)

    uncited = [p["title"] for p in papers if p["title"][:40].lower() not in report.lower()]
    if uncited:
        score -= len(uncited)
        feedback_parts.append("UNCITED PAPERS: " + str(uncited))

    min_chars = 300 * max(len(papers), 1)
    if len(report) < min_chars:
        score -= 3
        feedback_parts.append("REPORT TOO SHORT: " + str(len(report)) + " chars")

    score          = max(0, score)
    needs_revision = (score < REVIEW_THRESHOLD) and (revision < MAX_REVIEW_LOOPS)
    feedback       = "\n".join(feedback_parts) if feedback_parts else "Report meets all quality criteria."

    print("  Score: " + str(score) + "/10 | Needs revision: " + str(needs_revision))

    return {
        **state,
        "review_score"   : score,
        "review_feedback": feedback,
        "needs_revision" : needs_revision
    }


# -- Reviser -------------------------------------------------------------------

def reviser_agent(state):
    feedback    = state["review_feedback"]
    report      = state["final_report"]
    extractions = state["extractions"]
    revision    = state["revision_count"]

    print("Reviser running (pass #" + str(revision + 1) + ")...")
    revised = report

    for section in ["Methodology", "Results", "Limitations"]:
        if section not in revised:
            additions = [
                "- **" + e["title"][:60] + "**: " + e.get(section.lower(), "N/A")[:300]
                for e in extractions
            ]
            revised += "\n\n## " + section + " Summary (Reviser)\n" + "\n".join(additions)

    if "UNCITED PAPERS" in feedback:
        for paper in state["papers"]:
            if paper["title"][:40].lower() not in revised.lower():
                ext = next((e for e in extractions if e.get("title") == paper["title"]), {})
                revised += (
                    "\n\n## [+] " + paper["title"] + "\n"
                    "**Methodology:** " + ext.get("methodology", "N/A")[:300] + "\n\n"
                    "**Results:** "     + ext.get("results",     "N/A")[:300] + "\n\n"
                    "**Limitations:** " + ext.get("limitations", "N/A")[:200] + "\n"
                    + "-" * 50
                )

    if "TOO SHORT" in feedback and state.get("chroma_collection") is not None:
        hits = query_vectorstore(
            state,
            query  = state["topic"] + " key contributions findings",
            top_k  = 3
        )
        if hits:
            revised += "\n\n## Additional Findings (Reviser)\n"
            for h in hits:
                revised += "- " + h["text"][:200] + "\n"

    print("  Report: " + str(len(report)) + " -> " + str(len(revised)) + " chars")

    return {
        **state,
        "final_report"  : revised,
        "revision_count": revision + 1,
        "needs_revision": False
    }
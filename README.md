# AI Research Paper Analyzer & Literature Survey Agent 🤖📚

An autonomous AI agent designed to streamline the academic research process. This tool automates the ingestion, analysis, and synthesis of research papers to generate comprehensive literature surveys and critical insights.

# 🚀 Key Features

    Automated Literature Search: Integration with APIs (e.g., ArXiv, Semantic Scholar) to find relevant papers based on keywords.

    Deep PDF Analysis: Extracts methodology, key findings, limitations, and future work from complex academic layouts.

    Literature Survey Generation: Automatically synthesizes multiple papers into a cohesive summary or comparative table.

    Citation Mapping: Identifies influential papers and traces the evolution of specific concepts.

    Interactive Q&A: Chat with your research corpus to find specific details without reading every page.

# 🛠️ Tech Stack

# 📋 Prerequisites

# ⚙️ Installation

    Clone the repository:

    Bash
    git clone https://github.com/SaiSantanu/AI-Research-Paper-Analyzer-Literature-Survey-Agent.git
    cd AI-Research-Paper-Analyzer-Literature-Survey-Agent

# 🤝 Contributing

Name:Abu Unaib
Date: 25/03
Today's contibution :
Backend Integration: Initiated the setup for the Python-based "Bridge" using Uvicorn and FastAPI.
Environment Troubleshooting: Diagnosed and documented fixes for Python PATH and pip alias conflicts on Windows.
API Research: Researched and selected high-authority Research APIs (OpenAlex and Semantic Scholar) to retrieve verified, high-rank papers for automated literature reviews.

Name:Dilshad Alam
Date: 25/03
Today's contibution :
Added Topic Clarifier Agent
Introduced a new clarifier_agent() that runs before the main pipeline. It detects when a user enters a broad or vague topic — such as "cancer", "machine learning", or "climate change" — and automatically asks a short series of targeted follow-up questions to narrow the focus.
For example, entering cancer triggers questions like: which cancer type, which research aspect (detection, treatment, genomics), and preferred methodology. The answers are combined into a refined query such as cancer lung early detection deep learning — which the pipeline then uses for a far more targeted arXiv search.

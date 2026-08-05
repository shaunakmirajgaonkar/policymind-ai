# 🏛️ PolicyMind AI

100% local, privacy-first Government Policy Analysis platform combining
RAG over policy documents, Monte Carlo impact simulation, and stakeholder
network analysis — zero cloud calls.

**⚠️ No internet access.** All economic/demographic figures, historical
outcomes, and stakeholder data must come from your own research. This
tool never fabricates statistics — the safe AST-based formula evaluator
and Monte Carlo engine are reused, security-tested patterns from
DecisionMind AI / ClimateVision AI.

**Stack:** FastAPI · SQLAlchemy/SQLite · ChromaDB + sentence-transformers
(RAG) · NetworkX · Ollama · Streamlit

## Setup
```bash
ollama pull phi3 && ollama serve
cd policymind-ai
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m app.main               # Terminal 1, port 8600
streamlit run dashboard/app.py   # Terminal 2, port 8501
```

## What it does
1. **Documents** — upload legislation/reports, RAG-searchable
2. **Scenarios** — define policy scenarios to evaluate
3. **Impact Simulation** — Monte Carlo on a user-defined formula and
   variable ranges, reporting a full outcome distribution (mean/P10/P90),
   never a false-precision single number
4. **Stakeholders** — track affected groups and build an interaction
   network with real graph centrality analysis
5. **Compare & Recommend** — rank scenarios by simulated outcome; local
   LLM synthesizes a recommendation, explicitly forbidden from inventing
   any statistic beyond what's provided

## Crash-safety
`KMP_DUPLICATE_LIB_OK=TRUE` set before ML imports (Apple Silicon OpenMP
crash fix). `pyarrow==17.0.0` pinned for Streamlit dataframe stability.

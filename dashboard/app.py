import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import math
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

API = "http://localhost:8600"
st.set_page_config(page_title="PolicyMind AI", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #FBF9FF 0%, #F3F6FF 40%, #FFF8FB 100%); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #F1ECFF 0%, #E8FBFA 100%); border-right: 1px solid rgba(124,92,255,0.15); }
h1, h2, h3 { color: #2D2A45 !important; font-weight: 800 !important; }
p, span, label, div { color: #3A3752; }
.pm-card { background: #FFFFFF; border: 1px solid rgba(124,92,255,0.15); box-shadow: 0 4px 14px rgba(124,92,255,0.08);
    border-radius: 16px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; color: #2D2A45; }
.pm-badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
.badge-online { background: #00C48C; color: white; } .badge-offline { background: #FF5C5C; color: white; }
.metric-gradient { background: linear-gradient(135deg, #7C5CFF 0%, #00B4B0 100%); border-radius: 16px;
    padding: 1rem 1.2rem; color: white; box-shadow: 0 6px 18px rgba(124,92,255,0.25); }
.metric-gradient h3, .metric-gradient div { color: white !important; }
.stButton>button { background: linear-gradient(135deg, #7C5CFF, #FF5FA2); color: white; border: none; border-radius: 10px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


def api_get(path, timeout=15, **params):
    try:
        r = requests.get(f"{API}{path}", params=params, timeout=timeout); r.raise_for_status(); return r.json()
    except Exception as e:
        st.error(f"Backend not reachable at {API}. Is `python -m app.main` running? ({e})"); return None


def api_post(path, json=None, params=None, timeout=60):
    try:
        r = requests.post(f"{API}{path}", json=json, params=params, timeout=timeout); r.raise_for_status(); return r.json()
    except Exception as e:
        st.error(f"Request failed: {e}"); return None


def render_graph(summary):
    nodes = [e["entity"] for e in summary.get("top_entities", [])]
    if not nodes:
        return None
    n = len(nodes)
    angle = 2 * math.pi / n
    pos = {node: (math.cos(i * angle), math.sin(i * angle)) for i, node in enumerate(nodes)}
    fig = go.Figure(data=[go.Scatter(
        x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes], mode="markers+text",
        text=nodes, textposition="top center",
        marker=dict(size=[20 + e["centrality"] * 30 for e in summary["top_entities"]], color="#7C5CFF", line=dict(width=1, color="white")),
    )])
    fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), height=450)
    return fig


with st.sidebar:
    st.markdown("## 🏛️ PolicyMind AI")
    st.caption("100% local • policy impact analysis")
    health = api_get("/health") or {}
    badge = '<span class="pm-badge badge-online">● LLM Online</span>' if health.get("llm_available") else '<span class="pm-badge badge-offline">● LLM Offline</span>'
    st.markdown(badge, unsafe_allow_html=True)
    st.metric("Policy chunks indexed", health.get("policy_chunks", 0))
    st.divider()
    page = st.radio("Navigate", ["📄 Documents", "📋 Scenarios", "🎲 Impact Simulation", "👥 Stakeholders", "⚖️ Compare & Recommend"], label_visibility="collapsed")
    st.divider()
    st.caption("Backend: FastAPI · RAG: ChromaDB · Simulation: Monte Carlo · Graph: NetworkX · LLM: Ollama")
    st.caption("⚠️ No internet access — economic/demographic figures must come from your own research. Never fabricated.")

if "scenario_id" not in st.session_state:
    st.session_state.scenario_id = None
    st.session_state.scenario_name = None

if page == "📄 Documents":
    st.title("📄 Policy Documents")
    st.caption("Upload legislation, reports, or economic data for RAG-based retrieval.")
    uploaded = st.file_uploader("Upload document", type=["pdf", "txt", "md"])
    c1, c2 = st.columns(2)
    title = c1.text_input("Title (optional)")
    doc_type = c2.selectbox("Type", ["legislation", "report", "economic_data", "other"])
    if uploaded and st.button("📥 Ingest document"):
        try:
            r = requests.post(f"{API}/documents/upload", params={"title": title, "doc_type": doc_type},
                               files={"file": (uploaded.name, uploaded.getvalue())}, timeout=60)
            r.raise_for_status()
            res = r.json()
            st.success(f"Ingested '{res['title']}' — {res['chunks_indexed']} chunks indexed")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    st.subheader("📋 Ingested documents")
    docs = api_get("/documents/") or []
    if docs:
        df = pd.DataFrame(docs)[["id", "title", "doc_type", "chunk_count", "ingested_at"]].astype(str)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("🔍 Search documents")
    q = st.text_input("Search")
    if q:
        for r in (api_get("/documents/search", q=q) or []):
            st.markdown(f'<div class="pm-card"><b>{r["title"]}</b> · relevance {r["score"]}<br>{r["text"][:400]}...</div>', unsafe_allow_html=True)

elif page == "📋 Scenarios":
    st.title("📋 Policy Scenarios")
    with st.form("scenario_form"):
        name = st.text_input("Scenario name")
        description = st.text_area("Description")
        if st.form_submit_button("💾 Save scenario"):
            res = api_post("/scenarios/", json={"name": name, "description": description})
            if res:
                st.session_state.scenario_id = res["id"]
                st.session_state.scenario_name = res["name"]
                st.success(f"Saved '{res['name']}' — now active.")

    st.subheader("📋 All scenarios")
    scenarios = api_get("/scenarios/") or []
    if scenarios:
        df = pd.DataFrame(scenarios)[["id", "name", "description", "created_at"]].astype(str)
        st.dataframe(df, use_container_width=True, hide_index=True)
        ids = {f"{s['name']} (id={s['id']})": s for s in scenarios}
        chosen = st.selectbox("Set active scenario", list(ids.keys()))
        if st.button("Set active"):
            s = ids[chosen]
            st.session_state.scenario_id = s["id"]
            st.session_state.scenario_name = s["name"]
            st.success(f"Active scenario: {s['name']}")

elif page == "🎲 Impact Simulation":
    st.title("🎲 Policy Impact Simulation")
    st.caption("Model economic/social/environmental impact as a formula with variable ranges — Monte Carlo shows the full outcome distribution.")
    if not st.session_state.scenario_id:
        st.info("Create or select a scenario first.")
    else:
        st.caption(f"Active scenario: **{st.session_state.scenario_name}**")
        impact_category = st.selectbox("Impact category", ["economic", "social", "environmental"])
        formula = st.text_input("Impact formula", placeholder="affected_workers * wage_increase * (1 - job_loss_rate) - implementation_cost")
        var_names_input = st.text_input("Variable names (comma-separated)", placeholder="affected_workers, wage_increase, job_loss_rate, implementation_cost")
        var_ranges = {}
        if var_names_input.strip():
            for name in [v.strip() for v in var_names_input.split(",") if v.strip()]:
                st.markdown(f"**{name}**")
                c1, c2, c3 = st.columns(3)
                low = c1.number_input(f"{name} low", key=f"{name}_low", value=0.0)
                base = c2.number_input(f"{name} base", key=f"{name}_base", value=0.0)
                high = c3.number_input(f"{name} high", key=f"{name}_high", value=0.0)
                var_ranges[name] = {"low": low, "base": base, "high": high}

        if st.button("🎲 Run simulation"):
            if formula and var_ranges:
                res = api_post("/scenarios/simulate", json={
                    "scenario_id": st.session_state.scenario_id, "impact_category": impact_category,
                    "formula": formula, "variable_ranges": var_ranges,
                }, timeout=60)
                if res:
                    c1, c2, c3, c4 = st.columns(4)
                    for col, label, val in zip([c1, c2, c3, c4], ["Mean impact", "P10", "P90", "Volatility"],
                                                 [res["mean"], res["p10"], res["p90"], res["volatility"]]):
                        with col:
                            st.markdown(f'<div class="metric-gradient"><h3>{val:,.0f}</h3>{label}</div>', unsafe_allow_html=True)
                    fig = px.histogram(x=res["sample_distribution"], nbins=40, title="Impact distribution (Monte Carlo)", color_discrete_sequence=["#7C5CFF"])
                    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#2D2A45")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Fill in formula and at least one variable.")

elif page == "👥 Stakeholders":
    st.title("👥 Stakeholder Analysis")
    if not st.session_state.scenario_id:
        st.info("Create or select a scenario first.")
    else:
        st.caption(f"Active scenario: **{st.session_state.scenario_name}**")
        with st.form("stakeholder_form"):
            name = st.text_input("Stakeholder name")
            stype = st.text_input("Type (e.g. beneficiary, employer, agency)")
            pop = st.number_input("Affected population (optional)", value=0.0)
            direction = st.selectbox("Impact direction", ["positive", "negative", "mixed", "unknown"])
            if st.form_submit_button("➕ Add stakeholder"):
                res = api_post("/scenarios/stakeholders", json={
                    "scenario_id": st.session_state.scenario_id, "name": name, "stakeholder_type": stype,
                    "affected_population": pop or None, "impact_direction": direction,
                })
                if res:
                    st.success(f"Added stakeholder '{res['name']}'")

        stakeholders = api_get(f"/scenarios/{st.session_state.scenario_id}/stakeholders") or []
        if stakeholders:
            st.dataframe(pd.DataFrame(stakeholders).astype(str), use_container_width=True, hide_index=True)

        st.subheader("🕸️ Stakeholder network")
        st.caption("Add edges connecting stakeholders to this scenario or each other.")
        edges_input = st.text_area("Edges (one per line: source -> target : relationship)",
                                    placeholder="Low-income workers -> Minimum Wage Increase : benefits from")
        if st.button("🔨 Build network"):
            edges = []
            for line in edges_input.strip().split("\n"):
                if "->" in line:
                    src, rest = line.split("->", 1)
                    if ":" in rest:
                        tgt, rel = rest.split(":", 1)
                    else:
                        tgt, rel = rest, ""
                    edges.append({"source": src.strip(), "target": tgt.strip(), "relationship": rel.strip()})
            if edges:
                summary = api_post("/analysis/stakeholder-graph", json={"edges": edges})
                if summary:
                    c1, c2 = st.columns(2)
                    c1.metric("Entities", summary["n_nodes"])
                    c2.metric("Connections", summary["n_edges"])
                    fig = render_graph(summary)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

elif page == "⚖️ Compare & Recommend":
    st.title("⚖️ Compare Scenarios & Get Recommendation")
    scenarios = api_get("/scenarios/") or []
    if len(scenarios) < 1:
        st.info("Create at least one scenario first.")
    else:
        options = {f"{s['name']} (id={s['id']})": s["id"] for s in scenarios}
        chosen = st.multiselect("Select scenarios to compare", list(options.keys()), default=list(options.keys())[:2])
        if st.button("⚖️ Compare") and len(chosen) >= 1:
            ids = [options[c] for c in chosen]
            res = api_post("/scenarios/compare", json=ids)
            if res and res["scenarios"]:
                df = pd.DataFrame(res["scenarios"]).T.reset_index().rename(columns={"index": "scenario"})
                fig = px.bar(df, x="scenario", y="mean", color="scenario", color_discrete_sequence=px.colors.qualitative.Bold, title="Scenario comparison — mean impact")
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#2D2A45")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(f'<div class="pm-card">🏆 Highest mean impact: <b>{res["ranked"][0]}</b></div>', unsafe_allow_html=True)
            else:
                st.info("No simulations found — run a simulation for these scenarios first.")

        if st.session_state.scenario_id and st.button("💡 Generate recommendation for active scenario"):
            with st.spinner("Synthesizing..."):
                res = api_post("/analysis/recommendation", json={"scenario_id": st.session_state.scenario_id}, timeout=120)
            if res:
                st.markdown(f'<div class="pm-card">{res["recommendation"]}</div>', unsafe_allow_html=True)

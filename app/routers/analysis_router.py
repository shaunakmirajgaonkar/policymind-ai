import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.policy_models import PolicyScenario, ImpactSimulation, Stakeholder, Recommendation
from app.graph.stakeholder_network import build_stakeholder_graph, graph_summary
from app.services import llm_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str = ""


class GraphBuildRequest(BaseModel):
    edges: list[GraphEdge]


@router.post("/stakeholder-graph")
def build_graph(req: GraphBuildRequest):
    if not req.edges:
        raise HTTPException(status_code=400, detail="No edges provided.")
    edge_dicts = [e.dict() for e in req.edges]
    G = build_stakeholder_graph(edge_dicts)
    return graph_summary(G)


class RecommendationRequest(BaseModel):
    scenario_id: int


@router.post("/recommendation")
def get_recommendation(req: RecommendationRequest, db: Session = Depends(get_db)):
    scenario = db.query(PolicyScenario).get(req.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    simulations = db.query(ImpactSimulation).filter(ImpactSimulation.scenario_id == req.scenario_id).all()
    impact_summary = "\n".join(f"- {s.impact_category}: mean={s.mean_impact}, P10={s.p10_impact}, P90={s.p90_impact}, volatility={s.volatility}" for s in simulations) or "No simulations run yet."

    stakeholders = db.query(Stakeholder).filter(Stakeholder.scenario_id == req.scenario_id).all()
    stakeholder_summary = "\n".join(f"- {s.name} ({s.stakeholder_type}): impact={s.impact_direction}, affected population={s.affected_population}" for s in stakeholders) or "No stakeholders recorded yet."

    text = llm_service.generate_policy_recommendation(scenario.name, scenario.description, impact_summary, stakeholder_summary)
    record = Recommendation(scenario_id=req.scenario_id, content=text)
    db.add(record)
    db.commit()
    return {"recommendation": text}

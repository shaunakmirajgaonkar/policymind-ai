from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.policy_models import PolicyScenario, ImpactSimulation, Stakeholder
from app.simulation.formula import compile_formula, extract_variable_names, FormulaError
from app.simulation.impact_engine import run_policy_simulation

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioCreate(BaseModel):
    name: str
    description: str = ""


@router.post("/")
def create_scenario(s: ScenarioCreate, db: Session = Depends(get_db)):
    record = PolicyScenario(**s.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/")
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(PolicyScenario).order_by(PolicyScenario.created_at.desc()).all()


class VariableRange(BaseModel):
    low: float
    base: float
    high: float


class SimulateRequest(BaseModel):
    scenario_id: int
    impact_category: str   # economic, social, environmental
    formula: str
    variable_ranges: dict[str, VariableRange]


@router.post("/simulate")
def simulate(req: SimulateRequest, db: Session = Depends(get_db)):
    try:
        impact_fn = compile_formula(req.formula)
        formula_vars = extract_variable_names(req.formula)
    except FormulaError as e:
        raise HTTPException(status_code=400, detail=str(e))

    missing = formula_vars - set(req.variable_ranges.keys())
    if missing:
        raise HTTPException(status_code=400, detail=f"Formula references undefined variables: {missing}")

    ranges = {name: (v.low, v.base, v.high) for name, v in req.variable_ranges.items()}
    result = run_policy_simulation(impact_fn, ranges)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    record = ImpactSimulation(
        scenario_id=req.scenario_id, impact_category=req.impact_category,
        mean_impact=result["mean"], p10_impact=result["p10"], p90_impact=result["p90"], volatility=result["volatility"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {"simulation_id": record.id, "mean": result["mean"], "p10": result["p10"], "p50": result["p50"],
            "p90": result["p90"], "volatility": result["volatility"], "sample_distribution": result["samples"][:500]}


@router.get("/{scenario_id}/simulations")
def get_simulations(scenario_id: int, db: Session = Depends(get_db)):
    return db.query(ImpactSimulation).filter(ImpactSimulation.scenario_id == scenario_id).order_by(ImpactSimulation.created_at.desc()).all()


class StakeholderCreate(BaseModel):
    scenario_id: int
    name: str
    stakeholder_type: str = ""
    affected_population: float = None
    impact_direction: str = "unknown"


@router.post("/stakeholders")
def add_stakeholder(s: StakeholderCreate, db: Session = Depends(get_db)):
    record = Stakeholder(**s.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{scenario_id}/stakeholders")
def get_stakeholders(scenario_id: int, db: Session = Depends(get_db)):
    return db.query(Stakeholder).filter(Stakeholder.scenario_id == scenario_id).all()


@router.post("/compare")
def compare_scenarios(scenario_ids: list[int], db: Session = Depends(get_db)):
    results = {}
    for sid in scenario_ids:
        scenario = db.query(PolicyScenario).get(sid)
        latest = db.query(ImpactSimulation).filter(ImpactSimulation.scenario_id == sid).order_by(ImpactSimulation.created_at.desc()).first()
        if scenario and latest:
            results[scenario.name] = {"mean": latest.mean_impact, "p10": latest.p10_impact, "p90": latest.p90_impact}
    ranked = sorted(results.items(), key=lambda kv: kv[1]["mean"], reverse=True)
    return {"scenarios": results, "ranked": [name for name, _ in ranked]}

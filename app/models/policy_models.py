from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float

from app.core.database import Base


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    doc_type = Column(String(50), default="")   # legislation, report, economic_data
    filename = Column(String(255))
    chunk_count = Column(Integer, default=0)
    ingested_at = Column(DateTime, default=datetime.utcnow)


class PolicyScenario(Base):
    __tablename__ = "policy_scenarios"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ImpactSimulation(Base):
    __tablename__ = "impact_simulations"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer)
    impact_category = Column(String(50))    # economic, social, environmental
    mean_impact = Column(Float)
    p10_impact = Column(Float)
    p90_impact = Column(Float)
    volatility = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Stakeholder(Base):
    __tablename__ = "stakeholders"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer)
    name = Column(String(255))
    stakeholder_type = Column(String(100), default="")
    affected_population = Column(Float, nullable=True)
    impact_direction = Column(String(20), default="unknown")   # positive, negative, mixed, unknown


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

"""
Strategies API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Strategy
from app.schemas.strategy import (
    StrategyResponse, 
    StrategyCreate, 
    StrategyUpdate,
    STRATEGY_TEMPLATES
)

router = APIRouter()


@router.get("/", response_model=List[StrategyResponse])
def list_strategies(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all strategies"""
    query = db.query(Strategy)
    
    if active_only:
        query = query.filter(Strategy.is_active == True)
    
    strategies = query.offset(skip).limit(limit).all()
    return strategies


@router.get("/templates")
def get_strategy_templates():
    """Get pre-configured strategy templates"""
    return STRATEGY_TEMPLATES


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get strategy by ID"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    return strategy


@router.post("/", response_model=StrategyResponse, status_code=201)
def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new trading strategy"""
    db_strategy = Strategy(**strategy.dict())
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    
    return db_strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing strategy"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    # Update fields
    update_data = strategy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)
    
    db.commit()
    db.refresh(strategy)
    
    return strategy


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Delete a strategy (soft delete - sets is_active to False)"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    strategy.is_active = False
    db.commit()
    
    return {"message": f"Strategy {strategy_id} deleted successfully"}


@router.post("/from-template/{template_name}", response_model=StrategyResponse)
def create_from_template(template_name: str, db: Session = Depends(get_db)):
    """Create a strategy from a template"""
    if template_name not in STRATEGY_TEMPLATES:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available: {list(STRATEGY_TEMPLATES.keys())}"
        )
    
    template = STRATEGY_TEMPLATES[template_name]
    
    strategy = Strategy(**template)
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return strategy

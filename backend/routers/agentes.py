from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/operacao", tags=["Gestão de Agentes"])

# --- CRUD AGENTES ---

@router.post("/agentes/", status_code=status.HTTP_201_CREATED)
def adicionar_agente_na_fila(payload: schemas.QueueMemberSchema, db: Session = Depends(get_db)):
    dados = payload.dict()
    dados['queue_name'] = dados['queue_name'].upper()
    # interface deve manter o formato original (ex: PJSIP/1202)
    
    db_agente = models.QueueMemberModel(**dados)
    db.merge(db_agente)
    db.commit()
    return {"message": "Agente adicionado à fila"}

@router.get("/agentes/{queue_name}")
def listar_agentes_da_fila(queue_name: str, db: Session = Depends(get_db)):
    return db.query(models.QueueMemberModel).filter(models.QueueMemberModel.queue_name == queue_name.upper()).all()

@router.delete("/agentes/{queue_name}/{interface:path}")
def remover_agente(queue_name: str, interface: str, db: Session = Depends(get_db)):
    # interface:path é usado para aceitar a barra do 'PJSIP/1202' na URL
    db.query(models.QueueMemberModel).filter(
        models.QueueMemberModel.queue_name == queue_name.upper(),
        models.QueueMemberModel.interface == interface
    ).delete()
    db.commit()
    return {"message": "Agente removido da fila"}

# --- MANIPULAÇÃO DE ESTADO (PAUSA) ---

@router.patch("/agentes/pausar")
def alternar_pausa_agente(queue_name: str, interface: str, pausar: bool, db: Session = Depends(get_db)):
    db_agente = db.query(models.QueueMemberModel).filter(
        models.QueueMemberModel.queue_name == queue_name.upper(),
        models.QueueMemberModel.interface == interface
    ).first()
    
    if not db_agente:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
        
    db_agente.paused = 1 if pausar else 0
    db.commit()
    return {"message": "Estado de pausa atualizado", "pausado": pausar}

@router.patch("/agentes/prioridade")
def alterar_prioridade_agente(queue_name: str, interface: str, peso: int, db: Session = Depends(get_db)):
    db_agente = db.query(models.QueueMemberModel).filter(
        models.QueueMemberModel.queue_name == queue_name.upper(),
        models.QueueMemberModel.interface == interface
    ).first()
    
    if not db_agente:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
        
    db_agente.penalty = peso
    db.commit()
    return {"message": f"Penalidade de {interface} alterada para {peso}"}
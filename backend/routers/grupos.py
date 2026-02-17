from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from typing import List

router = APIRouter(prefix="/grupos", tags=["Grupos (Busca/Captura)"])

# --- GRUPO DE CAPTURA (Pickup) ---

@router.patch("/captura/atribuir")
def configurar_captura(payload: schemas.PickupUpdate, db: Session = Depends(get_db)):
    """ Define o grupo de captura para um ramal """
    ramal = db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == payload.ramal).first()
    if not ramal:
        raise HTTPException(status_code=404, detail="Ramal não encontrado")
    
    ramal.named_call_group = payload.grupo
    ramal.named_pickup_group = payload.grupo
    db.commit()
    return {"message": f"Ramal {payload.ramal} atribuído ao grupo {payload.grupo}"}

@router.patch("/captura/remover/{ramal_id}")
def remover_captura(ramal_id: str, db: Session = Depends(get_db)):
    """ Remove o ramal de qualquer grupo de captura """
    ramal = db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == ramal_id).first()
    if not ramal:
        raise HTTPException(status_code=404, detail="Ramal não encontrado")
    
    ramal.named_call_group = None
    ramal.named_pickup_group = None
    db.commit()
    return {"message": f"Captura removida do ramal {ramal_id}"}

# --- GRUPO DE CHAMADA (Ring Group / Busca) ---

@router.post("/chamada/", status_code=status.HTTP_201_CREATED)
def criar_grupo_chamada(payload: schemas.RingGroupCreate, db: Session = Depends(get_db)):
    novo_grupo = models.RingGroup(**payload.dict())
    try:
        db.add(novo_grupo)
        db.commit()
        db.refresh(novo_grupo)
        return novo_grupo
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao criar grupo ou nome já existente.")

@router.get("/chamada/", response_model=List[schemas.RingGroupCreate])
def listar_grupos_chamada(db: Session = Depends(get_db)):
    return db.query(models.RingGroup).all()

@router.get("/chamada/{grupo_id}")
def buscar_grupo_chamada(grupo_id: int, db: Session = Depends(get_db)):
    grupo = db.query(models.RingGroup).filter(models.RingGroup.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo de chamada não encontrado")
    return grupo

@router.patch("/chamada/{grupo_id}")
def atualizar_grupo_chamada(grupo_id: int, payload: schemas.RingGroupUpdate, db: Session = Depends(get_db)):
    db_grupo = db.query(models.RingGroup).filter(models.RingGroup.id == grupo_id).first()
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    dados_atualizacao = payload.dict(exclude_unset=True)
    for chave, valor in dados_atualizacao.items():
        setattr(db_grupo, chave, valor)
    
    db.commit()
    db.refresh(db_grupo)
    return db_grupo

@router.delete("/chamada/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_grupo_chamada(grupo_id: int, db: Session = Depends(get_db)):
    grupo = db.query(models.RingGroup).filter(models.RingGroup.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    db.delete(grupo)
    db.commit()
    return None
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas

router = APIRouter(prefix="/configuracao/uras", tags=["Configuração de URAs"])

# --- CRUD DE URAS (PRINCIPAL) ---

@router.post("/", response_model=schemas.UraSchema, status_code=status.HTTP_201_CREATED)
def criar_ura(payload: schemas.UraSchema, db: Session = Depends(get_db)):
    db_ura = db.query(models.UraModel).filter(models.UraModel.nome == payload.nome).first()
    if db_ura:
        raise HTTPException(status_code=400, detail="URA com este nome já existe")
    
    nova_ura = models.UraModel(**payload.dict())
    db.add(nova_ura)
    db.commit()
    db.refresh(nova_ura)
    return nova_ura

@router.get("/", response_model=List[schemas.UraSchema])
def listar_uras(db: Session = Depends(get_db)):
    return db.query(models.UraModel).all()

@router.get("/{ura_id}", response_model=schemas.UraSchema)
def obter_ura(ura_id: int, db: Session = Depends(get_db)):
    db_ura = db.query(models.UraModel).filter(models.UraModel.id == ura_id).first()
    if not db_ura:
        raise HTTPException(status_code=404, detail="URA não encontrada")
    return db_ura

@router.put("/{ura_id}", response_model=schemas.UraSchema)
def atualizar_ura(ura_id: int, payload: schemas.UraSchema, db: Session = Depends(get_db)):
    db_ura = db.query(models.UraModel).filter(models.UraModel.id == ura_id).first()
    if not db_ura:
        raise HTTPException(status_code=404, detail="URA não encontrada")
    
    for key, value in payload.dict().items():
        setattr(db_ura, key, value)
    
    db.commit()
    db.refresh(db_ura)
    return db_ura

@router.delete("/{ura_id}")
def deletar_ura(ura_id: int, db: Session = Depends(get_db)):
    db_ura = db.query(models.UraModel).filter(models.UraModel.id == ura_id).first()
    if not db_ura:
        raise HTTPException(status_code=404, detail="URA não encontrada")
    
    # Ao deletar uma URA, as opções relacionadas devem ser limpas
    db.query(models.UraOpcaoModel).filter(models.UraOpcaoModel.ura_id == ura_id).delete()
    db.delete(db_ura)
    db.commit()
    return {"message": "URA e suas opções foram removidas com sucesso"}


# --- CRUD DE OPÇÕES DA URA (TECLAS) ---

@router.post("/{ura_id}/opcoes", response_model=schemas.UraOpcaoSchema)
def adicionar_opcao_ura(ura_id: int, payload: schemas.UraOpcaoSchema, db: Session = Depends(get_db)):
    # Verifica se a URA existe
    db_ura = db.query(models.UraModel).filter(models.UraModel.id == ura_id).first()
    if not db_ura:
        raise HTTPException(status_code=404, detail="URA pai não encontrada")
    
    # Verifica se a tecla já está em uso nesta URA
    db_opcao = db.query(models.UraOpcaoModel).filter(
        models.UraOpcaoModel.ura_id == ura_id, 
        models.UraOpcaoModel.tecla == payload.tecla
    ).first()
    
    if db_opcao:
        # Se já existe, atualiza o destino
        db_opcao.tipo_destino = payload.tipo_destino.upper()
        db_opcao.destino = payload.destino
    else:
        # Se não existe, cria nova
        db_opcao = models.UraOpcaoModel(ura_id=ura_id, **payload.dict())
        db_opcao.tipo_destino = db_opcao.tipo_destino.upper()
        db.add(db_opcao)
    
    db.commit()
    db.refresh(db_opcao)
    return db_opcao

@router.get("/{ura_id}/opcoes", response_model=List[schemas.UraOpcaoSchema])
def listar_opcoes_da_ura(ura_id: int, db: Session = Depends(get_db)):
    return db.query(models.UraOpcaoModel).filter(models.UraOpcaoModel.ura_id == ura_id).all()

@router.delete("/{ura_id}/opcoes/{tecla}")
def remover_opcao_ura(ura_id: int, tecla: str, db: Session = Depends(get_db)):
    db_opcao = db.query(models.UraOpcaoModel).filter(
        models.UraOpcaoModel.ura_id == ura_id, 
        models.UraOpcaoModel.tecla == tecla
    ).first()
    
    if not db_opcao:
        raise HTTPException(status_code=404, detail="Opção de tecla não encontrada para esta URA")
    
    db.delete(db_opcao)
    db.commit()
    return {"message": f"Tecla {tecla} removida"}
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas

router = APIRouter(prefix="/configuracao/abreviados", tags=["Números Abreviados (Speed Dial)"])

@router.post("/", response_model=schemas.NumeroAbreviadoSchema, status_code=status.HTTP_201_CREATED)
def criar_numero_abreviado(payload: schemas.NumeroAbreviadoSchema, db: Session = Depends(get_db)):
    # Verifica se o código já existe
    db_abrev = db.query(models.NumeroAbreviadoModel).filter(
        models.NumeroAbreviadoModel.codigo == payload.codigo
    ).first()
    
    if db_abrev:
        raise HTTPException(status_code=400, detail="Este código de discagem rápida já está em uso")
    
    novo_abrev = models.NumeroAbreviadoModel(**payload.dict())
    db.add(novo_abrev)
    db.commit()
    db.refresh(novo_abrev)
    return novo_abrev

@router.get("/", response_model=List[schemas.NumeroAbreviadoSchema])
def listar_numeros_abreviados(db: Session = Depends(get_db)):
    return db.query(models.NumeroAbreviadoModel).all()

@router.get("/{codigo}", response_model=schemas.NumeroAbreviadoSchema)
def obter_numero_abreviado(codigo: str, db: Session = Depends(get_db)):
    db_abrev = db.query(models.NumeroAbreviadoModel).filter(
        models.NumeroAbreviadoModel.codigo == codigo
    ).first()
    
    if not db_abrev:
        raise HTTPException(status_code=404, detail="Código não encontrado")
    return db_abrev

@router.put("/{codigo}", response_model=schemas.NumeroAbreviadoSchema)
def atualizar_numero_abreviado(codigo: str, payload: schemas.NumeroAbreviadoSchema, db: Session = Depends(get_db)):
    db_abrev = db.query(models.NumeroAbreviadoModel).filter(
        models.NumeroAbreviadoModel.codigo == codigo
    ).first()
    
    if not db_abrev:
        raise HTTPException(status_code=404, detail="Código não encontrado")
    
    for key, value in payload.dict().items():
        setattr(db_abrev, key, value)
    
    db.commit()
    db.refresh(db_abrev)
    return db_abrev

@router.delete("/{codigo}")
def deletar_numero_abreviado(codigo: str, db: Session = Depends(get_db)):
    db_abrev = db.query(models.NumeroAbreviadoModel).filter(
        models.NumeroAbreviadoModel.codigo == codigo
    ).first()
    
    if not db_abrev:
        raise HTTPException(status_code=404, detail="Código não encontrado")
    
    db.delete(db_abrev)
    db.commit()
    return {"message": f"Código {codigo} removido com sucesso"}
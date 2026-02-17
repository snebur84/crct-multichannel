from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List

router = APIRouter(prefix="/features", tags=["Feature Codes (Serviços)"])

@router.get("/", response_model=List[schemas.FeatureCodeSchema])
def listar_features(db: Session = Depends(get_db)):
    """ Retorna todos os códigos de facilidades (features) """
    return db.query(models.FeatureCode).all()

@router.patch("/{nome}")
def editar_feature(nome: str, payload: schemas.FeatureCodeUpdate, db: Session = Depends(get_db)):
    """ Altera o código de uma feature específica (ex: captura_grupo) """
    feature = db.query(models.FeatureCode).filter(models.FeatureCode.nome == nome).first()
    
    if not feature:
        raise HTTPException(status_code=404, detail="Feature não encontrada")
    
    feature.codigo = payload.codigo
    db.commit()
    return {"status": "atualizado", "feature": nome, "novo_codigo": payload.codigo}

@router.post("/inicializar/", status_code=201)
def inicializar_features(db: Session = Depends(get_db)):
    """ Cria os códigos padrão caso a tabela esteja vazia """
    defaults = [
        {"nome": "captura_grupo", "descricao": "Captura em Grupo", "codigo": "*8"},
        {"nome": "captura_direta", "descricao": "Captura Individual/Direta", "codigo": "**"},
        {"nome": "puxar_tronco", "descricao": "Acesso Direto ao Tronco", "codigo": "0"},
        {"nome": "desvio_sempre", "descricao": "Ativar Desvio Sempre", "codigo": "*21*"},
        {"nome": "cancelar_desvios", "descricao": "Cancelar Todos os Desvios", "codigo": "#21#"},
    ]
    
    for item in defaults:
        exists = db.query(models.FeatureCode).filter(models.FeatureCode.nome == item["nome"]).first()
        if not exists:
            db.add(models.FeatureCode(**item))
    
    db.commit()
    return {"message": "Features padrão inicializadas"}
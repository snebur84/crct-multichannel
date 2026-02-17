from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/configuracao", tags=["Rotas de Saída"])

@router.post("/rotas-saida/", status_code=status.HTTP_201_CREATED)
def criar_rota_saida(payload: schemas.RotaSaidaSchema, db: Session = Depends(get_db)):
    dados = payload.dict()
    p = dados['padrao']
    
    # Converte padrão Asterisk para Regex Postgres
    # Remove o '_' inicial se existir
    p = p.lstrip('_')
    # Substitui 'X' ou '.' por '.*' (ou '.' para um dígito apenas, mas '.*' é mais seguro aqui)
    p = p.replace('X', '[0-9]').replace('.', '.*')
    # Garante que comece com ^ e termine (opcionalmente) permitindo mais dígitos
    if not p.startswith('^'):
        p = '^' + p
    if not p.endswith('.*'):
        p = p + '.*'
        
    dados['padrao'] = p
    nova_rota = models.RotaSaida(**dados)
    db.add(nova_rota)
    db.commit()
    return {"message": "Rota criada com Regex: " + p}

@router.get("/rotas-saida/", response_model=List[schemas.RotaSaidaSchema])
def listar_rotas_saida(db: Session = Depends(get_db)):
    return db.query(models.RotaSaida).order_by(models.RotaSaida.prioridade.asc()).all()

@router.put("/rotas-saida/{rota_id}")
def atualizar_rota_saida(rota_id: int, payload: schemas.RotaSaidaSchema, db: Session = Depends(get_db)):
    db_rota = db.query(models.RotaSaida).filter(models.RotaSaida.id == rota_id).first()
    if not db_rota:
        raise HTTPException(status_code=404, detail="Rota de saída não encontrada")
    
    dados = payload.dict()
    # Normalização no Update
    if dados['padrao'].startswith('_'):
        dados['padrao'] = dados['padrao'].replace('_', '', 1).replace('X', '%').replace('.', '%')

    for key, value in dados.items():
        setattr(db_rota, key, value)
    
    db.commit()
    return {"message": "Rota de saída atualizada"}

@router.delete("/rotas-saida/{rota_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_rota_saida(rota_id: int, db: Session = Depends(get_db)):
    db_rota = db.query(models.RotaSaida).filter(models.RotaSaida.id == rota_id).first()
    if not db_rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    
    db.delete(db_rota)
    db.commit()
    return None
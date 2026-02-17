from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/configuracao", tags=["Calendario"])

# --- CRUD CALENDÁRIOS ---

@router.post("/calendarios/", status_code=status.HTTP_201_CREATED)
def adicionar_regra_calendario(payload: schemas.CalendarioRegraSchema, db: Session = Depends(get_db)):
    dados = payload.dict()
    # Converte o tipo de destino da regra de calendário também
    if 'tipo_destino' in dados:
        dados['tipo_destino'] = dados['tipo_destino'].upper()
        
    nova_regra = models.CalendarioRegra(**dados)
    db.add(nova_regra)
    db.commit()
    return {"message": "Regra de calendário adicionada"}

@router.put("/calendarios/regra/{regra_id}")
def atualizar_regra_calendario(regra_id: int, payload: schemas.CalendarioRegraSchema, db: Session = Depends(get_db)):
    db_regra = db.query(models.CalendarioRegra).filter(models.CalendarioRegra.id == regra_id).first()
    if not db_regra:
        raise HTTPException(status_code=404, detail="Regra não encontrada")

    for key, value in payload.dict().items():
        if key == 'tipo_destino' and value:
            value = value.upper()
        setattr(db_regra, key, value)
        
    db.commit()
    return {"message": "Regra de calendário atualizada"}

@router.get("/calendarios/{nome_calendario}")
def listar_regras_calendario(nome_calendario: str, db: Session = Depends(get_db)):
    return db.query(models.CalendarioRegra).filter(
        models.CalendarioRegra.nome_calendario == nome_calendario
    ).order_by(models.CalendarioRegra.prioridade).all()

@router.delete("/calendarios/regra/{regra_id}")
def deletar_regra_calendario(regra_id: int, db: Session = Depends(get_db)):
    db.query(models.CalendarioRegra).filter(models.CalendarioRegra.id == regra_id).delete()
    db.commit()
    return {"message": "Regra removida"}
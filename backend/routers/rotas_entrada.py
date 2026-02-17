from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/configuracao", tags=["Rotas de entrada"])

# --- CRUD ROTAS DE ENTRADA ---

@router.post("/rotas/", status_code=status.HTTP_201_CREATED)
def criar_rota(payload: schemas.RotaEntradaSchema, db: Session = Depends(get_db)):
    # Converte para UPPER antes de salvar
    dados = payload.dict()
    dados['did'] = dados['did'].upper()
    dados['tipo_destino'] = dados['tipo_destino'].upper()
    
    db_rota = models.RotaEntrada(**dados)
    db.merge(db_rota)
    db.commit()
    return {"message": "Rota configurada com sucesso"}

@router.put("/rotas/{did}")
def atualizar_rota(did: str, payload: schemas.RotaEntradaSchema, db: Session = Depends(get_db)):
    db_rota = db.query(models.RotaEntrada).filter(models.RotaEntrada.did == did).first()
    if not db_rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    
    for key, value in payload.dict().items():
        # Garante UPPERCASE nos campos de decisão
        if key in ['did', 'tipo_destino']:
            value = value.upper()
        setattr(db_rota, key, value)
    
    db.commit()
    return {"message": "Rota atualizada com sucesso"}

@router.get("/rotas/")
def listar_rotas(db: Session = Depends(get_db)):
    return db.query(models.RotaEntrada).all()

@router.delete("/rotas/{did}")
def deletar_rota(did: str, db: Session = Depends(get_db)):
    db.query(models.RotaEntrada).filter(models.RotaEntrada.did == did).delete()
    db.commit()
    return {"message": "Rota removida"}
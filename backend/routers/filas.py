from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/configuracao", tags=["Configuração de Filas"])

@router.post("/filas/", status_code=status.HTTP_201_CREATED)
def criar_fila(payload: schemas.QueueSchema, db: Session = Depends(get_db)):
    dados = payload.dict()
    # Asterisk é Case Sensitive para nomes de filas, mas UPPER facilita o Dialplan
    dados['name'] = dados['name'].upper()
    dados['strategy'] = dados['strategy'].lower() # Estratégias costumam ser lower (rrmemory, ringall)
    
    db_fila = models.QueueModel(**dados)
    db.merge(db_fila)
    db.commit()
    return {"message": f"Fila {dados['name']} configurada com sucesso"}

@router.get("/filas/")
def listar_filas(db: Session = Depends(get_db)):
    return db.query(models.QueueModel).all()

@router.delete("/filas/{name}")
def deletar_fila(name: str, db: Session = Depends(get_db)):
    db.query(models.QueueModel).filter(models.QueueModel.name == name.upper()).delete()
    db.commit()
    return {"message": "Fila removida"}

@router.put("/filas/{name}")
def atualizar_fila(name: str, payload: schemas.QueueSchema, db: Session = Depends(get_db)):
    # Busca a fila pelo nome (em UPPER para garantir a consistência)
    nome_fila = name.upper()
    db_fila = db.query(models.QueueModel).filter(models.QueueModel.name == nome_fila).first()
    
    if not db_fila:
        raise HTTPException(status_code=404, detail="Fila não encontrada")
    
    dados_novos = payload.dict()
    
    for key, value in dados_novos.items():
        # Tratamento de campos específicos
        if key == 'name':
            value = value.upper()
        if key == 'strategy':
            value = value.lower()
            
        setattr(db_fila, key, value)
    
    db.commit()
    return {"message": f"Fila {nome_fila} atualizada com sucesso"}
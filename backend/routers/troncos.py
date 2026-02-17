from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/troncos", tags=["Troncos (SIP/ATA)"])

# --- TRONCOS DE OPERADORA (REGISTER) ---

@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_tronco(payload: schemas.TroncoSchema, db: Session = Depends(get_db)):
    novo_auth = models.PjsipAuth(id=payload.nome, username=payload.usuario, password=payload.senha)
    novo_aor = models.PjsipAor(id=payload.nome, contact=f"sip:{payload.host}")
    novo_ep = models.PjsipEndpoint(
        id=payload.nome, transport='transport-udp', context=payload.contexto_entrada,
        disallow='all', allow='ulaw,alaw', auth=payload.nome, outbound_auth=payload.nome,
        aors=payload.nome, from_user=payload.usuario, direct_media='no'
    )
    novo_reg = models.PjsipRegistration(
        id=payload.nome, transport='transport-udp', outbound_auth=payload.nome,
        server_uri=f"sip:{payload.host}", client_uri=f"sip:{payload.usuario}@{payload.host}",
        endpoint=payload.nome
    )
    try:
        db.add_all([novo_auth, novo_aor, novo_ep, novo_reg])
        db.commit()
        return {"status": "sucesso", "tronco": payload.nome}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def listar_troncos(db: Session = Depends(get_db)):
    return db.query(models.PjsipRegistration).all()

@router.delete("/{nome}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tronco(nome: str, db: Session = Depends(get_db)):
    db.query(models.PjsipRegistration).filter(models.PjsipRegistration.id == nome).delete()
    db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == nome).delete()
    db.query(models.PjsipAuth).filter(models.PjsipAuth.id == nome).delete()
    db.query(models.PjsipAor).filter(models.PjsipAor.id == nome).delete()
    db.commit()
    return None

# --- TRONCOS ATA (IDENTIFY POR IP) ---

@router.post("/ata/", status_code=status.HTTP_201_CREATED)
def criar_tronco_ata(payload: schemas.TroncoATASchema, db: Session = Depends(get_db)):
    # Note que aqui usamos o nome do endpoint para amarrar tudo
    novo_auth = models.PjsipAuth(id=payload.username_ata, username=payload.username_ata, password=payload.password_ata)
    novo_aor = models.PjsipAor(id=payload.username_ata, max_contacts=1, remove_existing='yes')
    novo_ep = models.PjsipEndpoint(
        id=payload.nome, transport='transport-udp', context=payload.contexto,
        disallow='all', allow='alaw,g722,ulaw,g729', auth=payload.username_ata,
        aors=payload.username_ata, language='pt-br'
    )
    novo_id = models.PjsipIdentify(id=f"identify-{payload.nome}", endpoint=payload.nome, match=payload.ip_ata)
    
    try:
        db.add_all([novo_auth, novo_aor, novo_ep, novo_id])
        db.commit()
        return {"status": "tronco ata criado", "id": payload.nome}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ata/")
def listar_troncos_ata(db: Session = Depends(get_db)):
    return db.query(models.PjsipIdentify).all()

@router.patch("/ata/{nome}")
def atualizar_tronco_ata(nome: str, payload: schemas.TroncoATAUpdate, db: Session = Depends(get_db)):
    db_ep = db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == nome).first()
    db_id = db.query(models.PjsipIdentify).filter(models.PjsipIdentify.endpoint == nome).first()
    if not db_ep: raise HTTPException(status_code=404, detail="Não encontrado")
    
    if payload.contexto: db_ep.context = payload.contexto
    if payload.ip_ata: db_id.match = payload.ip_ata
    if payload.password_ata:
        db_auth = db.query(models.PjsipAuth).filter(models.PjsipAuth.id == db_ep.auth).first()
        if db_auth: db_auth.password = payload.password_ata
    db.commit()
    return {"status": "atualizado"}

@router.delete("/ata/{nome}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tronco_ata(nome: str, db: Session = Depends(get_db)):
    db_ep = db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == nome).first()
    if db_ep:
        auth_id = db_ep.auth
        db.query(models.PjsipIdentify).filter(models.PjsipIdentify.endpoint == nome).delete()
        db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == nome).delete()
        db.query(models.PjsipAuth).filter(models.PjsipAuth.id == auth_id).delete()
        db.query(models.PjsipAor).filter(models.PjsipAor.id == auth_id).delete()
        db.commit()
    return None
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/ramais", tags=["Ramais (SIP/WebRTC)"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_ramal(payload: schemas.RamalSchema, db: Session = Depends(get_db)):
    # Criar Auth e AOR
    novo_auth = models.PjsipAuth(id=payload.numero, username=payload.numero, password=payload.senha)
    novo_aor = models.PjsipAor(id=payload.numero, max_contacts=5, remove_existing='yes')
    nome_transporte = f"transport-{payload.transport if payload.transport else 'udp'}"
    
    # Configurações Base para ambos (WebRTC ou SIP comum)
    base_config = {
        "id": payload.numero,
        "auth": payload.numero,
        "aors": payload.numero,
        "callerid": f'"{payload.displayname}" <{payload.numero}>',
        "context": payload.contexto,
        "direct_media": 'no',
        "rewrite_contact": 'yes',
        "rtp_symmetric": 'yes',
        "force_rport": 'yes'
    }

    if payload.webrtc:
        novo_ep = models.PjsipEndpoint(
            **base_config,
            transport='transport-wss', 
            webrtc='yes',
            use_avpf='yes', 
            media_encryption='dtls', 
            dtls_verify='no',
            dtls_setup='actpass', 
            ice_support='yes', 
            rtcp_mux='yes',
            dtls_auto_generate_cert='yes', 
            allow='opus,ulaw,alaw'
        )
    else:
        novo_ep = models.PjsipEndpoint(
            **base_config,
            transport=nome_transporte, 
            allow='ulaw,alaw'
        )
    
    try:
        db.add_all([novo_auth, novo_aor, novo_ep])
        db.commit()
        return {"status": "sucesso", "ramal": payload.numero}
    except Exception as e:
        db.rollback()
        # Logar o erro real ajuda no debug
        print(f"Erro ao criar ramal: {e}")
        raise HTTPException(status_code=400, detail="Ramal já existe ou erro nos dados enviados.")

@router.get("/")
def listar_ramais(db: Session = Depends(get_db)):
    return db.query(models.PjsipEndpoint).all()

@router.get("/{numero}")
def buscar_ramal(numero: str, db: Session = Depends(get_db)):
    endpoint = db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == numero).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Ramal não encontrado")
    auth = db.query(models.PjsipAuth).filter(models.PjsipAuth.id == numero).first()
    return {"endpoint": endpoint, "senha": auth.password if auth else None}

@router.patch("/{numero}")
def atualizar_ramal(numero: str, payload: schemas.RamalUpdate, db: Session = Depends(get_db)):
    db_ep = db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == numero).first()
    db_auth = db.query(models.PjsipAuth).filter(models.PjsipAuth.id == numero).first()
    
    if not db_ep: 
        raise HTTPException(status_code=404, detail="Ramal não encontrado")
    
    # 1. Atualização de Senha
    if payload.senha: 
        db_auth.password = payload.senha
    
    # 2. Atualização de Contexto e Display Name
    if payload.contexto: 
        db_ep.context = payload.contexto
    if payload.displayname:
        db_ep.callerid = f'"{payload.displayname}" <{numero}>'

    # 3. Lógica de Transporte e Perfil (WebRTC vs SIP)
    target_transport = payload.transport if payload.transport else "udp"

    if payload.webrtc is not None:
        if payload.webrtc:
            db_ep.transport = 'transport-wss'
            db_ep.webrtc = 'yes'
            db_ep.use_avpf = 'yes'
            db_ep.media_encryption = 'dtls'
            db_ep.dtls_verify = 'no'
            db_ep.dtls_setup = 'actpass'
            db_ep.ice_support = 'yes'
            db_ep.rtcp_mux = 'yes'
            db_ep.dtls_auto_generate_cert = 'yes'
        else:
            db_ep.transport = f'transport-{target_transport}'
            db_ep.webrtc = 'no'
            db_ep.use_avpf = 'no'
            db_ep.media_encryption = 'no'
            db_ep.ice_support = 'no'
            db_ep.rtcp_mux = 'no'
            db_ep.rewrite_contact = 'yes'
            db_ep.force_rport = 'yes'
            db_ep.rtp_symmetric = 'yes'
    
    elif payload.transport:
        db_ep.transport = f'transport-{payload.transport}'

    try:
        db.commit()
        return {"status": "atualizado", "numero": numero, "transport": db_ep.transport}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {str(e)}")

@router.delete("/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_ramal(numero: str, db: Session = Depends(get_db)):
    db.query(models.PjsipEndpoint).filter(models.PjsipEndpoint.id == numero).delete()
    db.query(models.PjsipAuth).filter(models.PjsipAuth.id == numero).delete()
    db.query(models.PjsipAor).filter(models.PjsipAor.id == numero).delete()
    db.commit()
    return None
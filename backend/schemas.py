from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# --- Schemas de Ramais ---
class RamalSchema(BaseModel):
    numero: str
    senha: str
    displayname : str
    webrtc: bool = False
    transport: Optional[str] = "udp"
    contexto: Optional[str] = "crctx-interno"

class RamalUpdate(BaseModel):
    senha: Optional[str] = None
    displayname : Optional[str] = None
    contexto: Optional[str] = None
    webrtc: Optional[bool] = None
    transport: Optional[str]

# --- Schemas de Troncos SIP (Operadoras) ---
class TroncoSchema(BaseModel):
    nome: str
    usuario: str
    senha: str
    host: str
    contexto_entrada: str = "crctx-entrada"

class TroncoUpdate(BaseModel):
    usuario: Optional[str] = None
    senha: Optional[str] = None
    host: Optional[str] = None
    contexto_entrada: Optional[str] = None

# --- Schemas de Troncos ATA (Identificação por IP) ---
class TroncoATASchema(BaseModel):
    nome: str
    username_ata: str
    password_ata: str
    ip_ata: str
    contexto: str = "crctx-entrada"

class TroncoATAUpdate(BaseModel):
    password_ata: Optional[str] = None
    ip_ata: Optional[str] = None
    contexto: Optional[str] = None

# --- Schema Grupos
class RingGroupCreate(BaseModel):
    nome: str
    exten: str
    estrategia: str = "ringall"
    membros: str # Ex: "1000,1001"

class PickupUpdate(BaseModel):
    ramal: str
    grupo: str

class RingGroupUpdate(BaseModel):
    nome: Optional[str] = None
    exten: Optional[str] = None
    estrategia: Optional[str] = None
    membros: Optional[str] = None

# --- Schema Features
class FeatureCodeSchema(BaseModel):
    nome: str
    descricao: Optional[str] = None
    codigo: str

class FeatureCodeUpdate(BaseModel):
    codigo: str

# --- SCHEMAS DE ROTAS ---
class RotaEntradaSchema(BaseModel):
    did: str
    nome_rota: str
    tipo_destino: str
    destino: str
    calendario_id: Optional[str] = None

# --- SCHEMAS DE CALENDÁRIO ---
class CalendarioRegraSchema(BaseModel):
    nome_calendario: str
    prioridade: int
    tipo: str
    horario: str = "*"
    dias_semana: str = "*"
    dias_mes: str = "*"
    meses: str = "*"
    acao: str
    destino_acao: str

class CalendarioRegraUpdate(BaseModel):
    prioridade: Optional[int] = None
    horario: Optional[str] = None
    acao: Optional[str] = None
    destino_acao: Optional[str] = None

class RotaSaidaSchema(BaseModel):
    nome: str
    padrao: str  
    tronco: str  
    remover_prefixo: int = 0
    adicionar_prefixo: str = ""

# --- SCHEMAS PARA FILAS ---

class QueueSchema(BaseModel):
    name: str
    strategy: str = "rrmemory"
    timeout: int = 15
    musiconhold: str = "default"
    joinempty: str = "yes"
    leavewhenempty: str = "no"

    class Config:
        from_attributes = True

class QueueMemberSchema(BaseModel):
    queue_name: str
    interface: str  # Ex: PJSIP/1202
    membername: Optional[str] = None
    penalty: int = 0
    paused: int = 0

    class Config:
        from_attributes = True

class CDRResponseSchema(BaseModel):
    id: int
    uniqueid: Optional[str]
    src: Optional[str]
    dst: Optional[str]
    start: Optional[datetime]
    answer: Optional[datetime]
    termino: Optional[datetime]
    duration: int
    billsec: int
    disposition: Optional[str]
    accountcode: Optional[str]

    class Config:
        from_attributes = True

# Schema para envolver a lista e metadados
class CDRRelatorioSchema(BaseModel):
    total_registros: int
    filtros_aplicados: dict
    dados: List[CDRResponseSchema]

# --- SCHEMAS PARA OPÇÕES DA URA (TECLAS) ---
class UraOpcaoSchema(BaseModel):
    tecla: str  # 0-9, *, #
    tipo_destino: str  # FILA, RAMAL, URA, EXTERNO
    destino: str

    class Config:
        from_attributes = True

# --- SCHEMAS PARA URA PRINCIPAL ---
class UraSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    saudacao: str  # Nome do arquivo de áudio no Asterisk
    timeout: Optional[int] = 5
    tentativas: Optional[int] = 3

    class Config:
        from_attributes = True

class NumeroAbreviadoSchema(BaseModel):
    codigo: str  # Ex: 100
    numero_destino: str # Ex: 011988887777
    descricao: Optional[str] = None

    class Config:
        from_attributes = True
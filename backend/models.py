from sqlalchemy import Column, String, Integer, Text, ForeignKey, Table, PrimaryKeyConstraint, DateTime
from database import Base

class PjsipEndpoint(Base):
    __tablename__ = 'ps_endpoints'
    
    id = Column(String(40), primary_key=True)
    transport = Column(String(40))
    aors = Column(String(40))
    auth = Column(String(40))
    outbound_auth = Column(String(40))
    context = Column(String(40), default='crctx-interno')
    callerid = Column(String(80))
    disallow = Column(String(200), default='all')
    allow = Column(String(200), default='ulaw,alaw')
    
    # Colunas de WebRTC e Mídia
    webrtc = Column(String(3), default='no')
    use_avpf = Column(String(3), default='no')
    media_encryption = Column(String(10))
    dtls_verify = Column(String(10))
    dtls_setup = Column(String(10))
    ice_support = Column(String(3), default='no')
    rtcp_mux = Column(String(3), default='no')
    dtls_cert_file = Column(String(200))
    dtls_auto_generate_cert = Column(String(3), default='no')
    
    # Colunas de Rede e NAT
    rewrite_contact = Column(String(3), default='yes')
    rtp_symmetric = Column(String(3), default='yes')
    force_rport = Column(String(3), default='yes')
    direct_media = Column(String(3), default='no')
    from_domain = Column(String(80))
    outbound_proxy = Column(String(40)) # Adicionada para evitar erros de esquema
    
    # Colunas de Configuração Extra
    language = Column(String(40), default='pt-br')
    named_call_group = Column(String(80))
    named_pickup_group = Column(String(80))
    
    # --- COLUNAS OBRIGATÓRIAS PARA EVITAR ERRO DE REALTIME ---
    mailboxes = Column(String(80)) # Corrigindo o erro do log
    aggregate_mwi = Column(String(3), default='no')
    media_encryption_optimistic = Column(String(3), default='no')
    identify_by = Column(String(80), default='username,ip')

class PjsipAuth(Base):
    __tablename__ = 'ps_auths'
    id = Column(String(40), primary_key=True)
    auth_type = Column(String(40), default='userpass')
    password = Column(String(80))
    username = Column(String(80))

class PjsipAor(Base):
    __tablename__ = 'ps_aors'
    id = Column(String(40), primary_key=True)
    max_contacts = Column(Integer, default=5)
    remove_existing = Column(String(3), default='yes')
    contact = Column(String(255))

class PjsipContact(Base):
    __tablename__ = 'ps_contacts'
    id = Column(String(255), primary_key=True)
    uri = Column(String(255))
    expiration_time = Column(String(40))
    qualify_frequency = Column(String(40)) 
    outbound_proxy = Column(String(255))
    path = Column(Text)
    user_agent = Column(String(255))
    prune_on_boot = Column(String(3))
    via_addr = Column(String(40))
    via_port = Column(String(40))       
    call_id = Column(String(255))
    endpoint = Column(String(40))
    qualify_timeout = Column(String(40))   
    reg_server = Column(String(20))
    authenticate_qualify = Column(String(3))

class PjsipRegistration(Base):
    __tablename__ = 'ps_registrations'
    id = Column(String(40), primary_key=True)
    transport = Column(String(40))
    outbound_auth = Column(String(40))
    server_uri = Column(String(255))
    client_uri = Column(String(255))
    endpoint = Column(String(40))

class PjsipIdentify(Base):
    __tablename__ = 'ps_endpoint_id_ips'
    
    id = Column(String(40), primary_key=True)
    endpoint = Column(String(40))
    match = Column(String(80))
    srv_lookups = Column(String(3), default='yes')

class FeatureCode(Base):
    __tablename__ = 'feature_codes'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), unique=True)
    descricao = Column(String(100))
    codigo = Column(String(10))

class RingGroup(Base):
    __tablename__ = 'ring_groups'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(40), unique=True)
    exten = Column(String(20))
    estrategia = Column(String(20), default='ringall')
    membros = Column(Text)

class RotaEntrada(Base):
    __tablename__ = 'rotas_entrada'
    did = Column(String(20), primary_key=True, index=True)
    nome_rota = Column(String(50))
    tipo_destino = Column(String(20))
    destino = Column(String(50))
    calendario_id = Column(String(50))

class CalendarioRegra(Base):
    __tablename__ = 'calendarios_regras'
    id = Column(Integer, primary_key=True, index=True)
    nome_calendario = Column(String(50), index=True)
    prioridade = Column(Integer)
    tipo = Column(String(20))
    horario = Column(String(50), default='*')
    dias_semana = Column(String(50), default='*')
    dias_mes = Column(String(50), default='*')
    meses = Column(String(50), default='*')
    acao = Column(String(20))
    destino_acao = Column(String(100))

class RotaSaida(Base):
    __tablename__ = 'rotas_saida'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50))
    padrao = Column(String(50))      # Ex: _0ZZXXXXXXXX (padrão Asterisk)
    tronco = Column(String(50))      # Nome do tronco
    prioridade = Column(Integer, default=100)
    remover_prefixo = Column(Integer, default=0)
    adicionar_prefixo = Column(String(20), default="")

# --- Adicione estas classes ao final do seu models.py ---

class QueueModel(Base):
    __tablename__ = 'queues'
    
    name = Column(String(128), primary_key=True)
    musiconhold = Column(String(128), default="default")
    announce = Column(String(128))
    context = Column(String(128))
    timeout = Column(Integer, default=15)
    strategy = Column(String(128), default="rrmemory")
    joinempty = Column(String(128), default="yes")
    leavewhenempty = Column(String(128), default="no")
    maxlen = Column(Integer, default=0)
    wrapuptime = Column(Integer, default=5)

class QueueMemberModel(Base):
    __tablename__ = 'queue_members'
    
    queue_name = Column(String(128), primary_key=True)
    interface = Column(String(128), primary_key=True)
    membername = Column(String(128))
    state_interface = Column(String(128))
    penalty = Column(Integer, default=0)
    paused = Column(Integer, default=0)

    # Define a chave primária composta exigida pelo Asterisk
    __table_args__ = (
        PrimaryKeyConstraint('queue_name', 'interface'),
    )

class CDRModel(Base):
    __tablename__ = 'cdr'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uniqueid = Column(String(150))
    accountcode = Column(String(20))
    src = Column(String(80))
    dst = Column(String(80))
    dcontext = Column(String(80))
    clid = Column(String(80))
    channel = Column(String(80))
    dstchannel = Column(String(80))
    lastapp = Column(String(80))
    lastdata = Column(String(80))
    start = Column(DateTime)
    answer = Column(DateTime)
    termino = Column(DateTime) 
    duration = Column(Integer)
    billsec = Column(Integer)
    disposition = Column(String(45))
    amaflags = Column(Integer)
    userfield = Column(String(255))
    sequence = Column(Integer)

class UraModel(Base):
    __tablename__ = 'uras'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), unique=True)
    saudacao = Column(String(100))  # Caminho do arquivo de áudio
    timeout = Column(Integer, default=5)
    tentativas = Column(Integer, default=3)

class UraOpcaoModel(Base):
    __tablename__ = 'uras_opcoes'
    id = Column(Integer, primary_key=True, index=True)
    ura_id = Column(Integer, ForeignKey('uras.id'))
    tecla = Column(String(1), index=True) # 0-9, *, #
    tipo_destino = Column(String(20))     # FILA, RAMAL, URA, EXTERNO
    destino = Column(String(50))

class NumeroAbreviadoModel(Base):
    __tablename__ = 'numeros_abreviados'
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), unique=True, index=True) # Ex: 100
    numero_destino = Column(String(50)) # Ex: 011999999999
    descricao = Column(String(100))
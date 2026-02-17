#!/bin/sh

# --- 0. AGUARDAR API (Garantia de que as tabelas existem) ---
echo "Aguardando pbx-api (Porta 8000)..."
python3 -c "
import socket
import time
while True:
    try:
        with socket.create_connection(('127.0.0.1', 8000), timeout=2):
            print('API detectada!')
            break
    except:
        print('API ainda não responde, aguardando...')
        time.sleep(2)
"

# --- 1. IP E CERTIFICADOS (DINÂMICO) ---
# Detecta o IP real da interface do servidor para o áudio (RTP)
SERVER_IP=$(hostname -I | awk '{print $1}')
PABX_DOMAIN=${PABX_DOMAIN:-$SERVER_IP}

echo "Iniciando Asterisk..."
echo "IP Real do Servidor: $SERVER_IP"

mkdir -p /etc/asterisk/keys
if [ ! -f /etc/asterisk/keys/asterisk.pem ]; then
    echo "Gerando certificados para $PABX_DOMAIN..."
    openssl req -x509 -newkey rsa:4096 -keyout /etc/asterisk/keys/asterisk.key \
        -out /etc/asterisk/keys/asterisk.crt -days 365 -nodes \
        -subj "/CN=$PABX_DOMAIN"
    cat /etc/asterisk/keys/asterisk.crt /etc/asterisk/keys/asterisk.key > /etc/asterisk/keys/asterisk.pem
fi
chown -R asterisk:asterisk /etc/asterisk/keys

# --- 2. CONFIGURAÇÃO ODBC (SISTEMA) ---
cat <<EOF > /etc/odbcinst.ini
[PostgreSQL]
Description = PostgreSQL ODBC Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/psqlodbcw.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libodbcpsqlS.so
EOF

cat <<EOF > /etc/odbc.ini
[asterisk-connector]
Driver = PostgreSQL
Database = ${DB_NAME:-crctx_db}
Servername = 127.0.0.1
UserName = ${DB_USER:-crctx_user}
Password = ${DB_PASS:-crctx_pass}
Port = 5432
ReadOnly = No
EOF

# --- 3. CONFIGURAÇÕES DO ASTERISK ---
sed -i 's/;defaultlanguage = en/defaultlanguage = pt_BR/' /etc/asterisk/asterisk.conf

cat <<EOF > /etc/asterisk/res_odbc.conf
[asterisk]
enabled => yes
dsn => asterisk-connector
username => ${DB_USER:-crctx_user}
password => ${DB_PASS:-crctx_pass}
pre-connect => yes
max_connections => 20
EOF

cat <<EOF > /etc/asterisk/func_odbc.conf
[GET_ROTA]
dsn=asterisk
readsql=SELECT tipo_destino, destino, calendario_id FROM rotas_entrada WHERE did='\${ARG1}'

[GET_CALENDARIO]
dsn=asterisk
readsql=SELECT horario, dias_semana, dias_mes, meses, acao, destino_acao FROM calendarios_regras WHERE nome_calendario='\${ARG1}' ORDER BY prioridade

[GET_OUTBOUND_ROUTE]
dsn=asterisk
readsql=SELECT tronco, remover_prefixo, adicionar_prefixo FROM rotas_saida WHERE LEFT('\${ARG1}', LENGTH(padrao)) = padrao ORDER BY LENGTH(padrao) DESC LIMIT 1

[CHECK_PAUSE]
dsn=asterisk
readsql=SELECT paused FROM queue_members WHERE interface='\${ARG1}' LIMIT 1

[UPDATE_PAUSE]
dsn=asterisk
writesql=UPDATE queue_members SET paused='\${VAL1}' WHERE interface='\${ARG2}'

[GET_URA]
dsn=asterisk
readsql=SELECT saudacao, timeout FROM uras WHERE id='\${ARG1}'

[GET_URA_OPCAO]
dsn=asterisk
readsql=SELECT tipo_destino, destino FROM uras_opcoes WHERE ura_id='\${ARG1}' AND tecla='\${ARG2}'

[GET_ABREV]
dsn=asterisk
readsql=SELECT numero_destino FROM numeros_abreviados WHERE codigo='\${ARG1}'
EOF

cat <<EOF > /etc/asterisk/extconfig.conf
[settings]
ps_endpoints => odbc,asterisk
ps_auths => odbc,asterisk
ps_aors => odbc,asterisk
ps_contacts => odbc,asterisk
ps_registrations => odbc,asterisk
ps_endpoint_id_ips => odbc,asterisk
queues => odbc,asterisk
queue_members => odbc,asterisk
EOF

cat <<EOF > /etc/asterisk/sorcery.conf
[res_pjsip]
endpoint=realtime,ps_endpoints
auth=realtime,ps_auths
aor=realtime,ps_aors
contact=realtime,ps_contacts

[res_pjsip_endpoint_identifier_ip]
identify=realtime,ps_endpoint_id_ips

[res_pjsip_outbound_registration]
registration=realtime,ps_registrations
EOF

cat <<EOF > /etc/asterisk/rtp.conf
[general]
rtpstart=10000
rtpend=10100
EOF

cat <<EOF > /etc/asterisk/cdr_adaptive_odbc.conf
[first]
connection=asterisk
table=cdr
alias start => start
alias answer => answer
alias end => termino
EOF

cat <<EOF > /etc/asterisk/cdr.conf
[general]
enable=yes
unanswered=yes
congestion=yes
EOF

cat <<EOF > /etc/asterisk/modules.conf
[modules]
autoload=yes
preload => res_odbc.so
preload => res_config_odbc.so
load => res_pjsip.so
load => res_pjsip_outbound_registration.so
noload => cdr_odbc.so
load => cdr_adaptive_odbc.so
noload => res_config_pgsql.so
noload => app_jack.so
noload => chan_alsa.so
noload => chan_console.so
EOF

# PJSIP Core e Transports 
cat <<EOF > /etc/asterisk/pjsip.conf
[global]
type=global
default_language=pt_BR
endpoint_identifier_order=ip,username,anonymous

[transport-udp]
type=transport
protocol=udp
bind=0.0.0.0:5060
local_net=${LOCAL_NETWORK}

# Transporte específico para acesso via DDNS (Porta 8384)
[transport-external]
type=transport
protocol=udp
bind=0.0.0.0:8384
external_media_address=${PABX_DOMAIN}
external_signaling_address=${PABX_DOMAIN}
local_net=${LOCAL_NETWORK}
allow_reload=yes

[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089

[system]
type=system
EOF

cat <<EOF > /etc/asterisk/http.conf
[general]
enabled=yes
bindaddr=0.0.0.0
bindport=8088
tlsenable=yes
tlsbindaddr=0.0.0.0:8089
tlscertfile=/etc/asterisk/keys/asterisk.pem
EOF

# --- DIALPLAN (MANTIDO ORIGINAL) ---
cat <<EOF > /etc/asterisk/extensions.conf
[general]
static=yes
writeprotect=no

[ura-dinamica]
exten => s,1,NoOp(--- Entrando na URA: \${ID_URA} ---)
    same => n,Set(DADOS_URA=\${ODBC_GET_URA(\${ID_URA})})
    same => n,Set(AUDIO=\${CUT(DADOS_URA,\, ,1)})
    same => n,Set(T_OUT=\${CUT(DADOS_URA,\, ,2)})
    
    same => n(menu),Background(\${AUDIO})
    same => n,WaitExten(\${T_OUT})

; Captura qualquer dígito e busca o destino
exten => _[0-9*#],1,NoOp(Digitou a tecla \${EXTEN})
    same => n,Set(DADOS_OPCAO=\${ODBC_GET_URA_OPCAO(\${ID_URA},\${EXTEN})})
    same => n,GotoIf($["\${DADOS_OPCAO}" = ""]?i,1) ; Tecla inválida se vazio
    
    same => n,Set(TIPO=\${CUT(DADOS_OPCAO,\, ,1)})
    same => n,Set(DEST=\${CUT(DADOS_OPCAO,\, ,2)})
    
    ; Reutiliza a lógica de direcionamento que já temos nas rotas de entrada
    same => n,Set(TIPO_DESTINO=\${TIPO})
    same => n,Set(DESTINO=\${DEST})
    same => n,Goto(crctx-entrada,direcionar,1)

; Tratamento de erro
exten => i,1,Playback(option-is-invalid)
    same => n,Goto(s,menu)

exten => t,1,Playback(vm-goodbye)
    same => n,Hangup()

[crctx-facilidades]
exten => _*8,1,NoOp(Captura de Grupo)
    same => n,PickupChan()
    same => n,Hangup()

exten => _**XXXX,1,NoOp(Captura Direta do ramal \${EXTEN:2})
    same => n,Pickup(\${EXTEN:2}@crctx-interno)
    same => n,Hangup()

; Alternar Pausa na Fila (*99)
exten => *99,1,NoOp(--- Alternando Pausa para o Agente \${CALLERID(num)} ---)
    same => n,Set(AGENTE=PJSIP/\${CALLERID(num)})
    ; Consulta o estado atual no banco (0 ou 1)
    same => n,Set(ESTADO_ATUAL=\${ODBC_CHECK_PAUSE(\${AGENTE})})
    
    ; Inverte o estado
    same => n,Set(NOVO_ESTADO=\${IF($["\${ESTADO_ATUAL}"="1"]?0:1)})
    
    ; Atualiza no banco
    same => n,Set(ODBC_UPDATE_PAUSE(\${NOVO_ESTADO},\${AGENTE})=1)
    
    ; Feedback sonoro para o agente
    same => n,GotoIf($["\${NOVO_ESTADO}"="1"]?pausado:disponivel)
    
    same => n(pausado),Playback(dictation-paused)
    same => n,Hangup()
    
    same => n(disponivel),Playback(available)
    same => n,Hangup()

[crctx-interno]
include => crctx-facilidades
exten => _XXXX,1,NoOp(Chamada Interna para \${EXTEN})
    same => n,Dial(PJSIP/\${EXTEN},30,Tt)
    same => n,Hangup()

exten => _*1XX,1,NoOp(--- Busca Numero Abreviado ---)
    same => n,Set(DEST_REAL=\${ODBC_GET_ABREV(\${EXTEN:1})})
    same => n,GotoIf($["\${DEST_REAL}" = ""]?nao_encontrado)
    same => n,Log(NOTICE, Dialing abbreviated \${EXTEN} to \${DEST_REAL})
    same => n,Goto(saida-lcr,\${DEST_REAL},1)
    
    same => n(nao_encontrado),Playback(beeperr)
    same => n,Hangup()

exten => *81,1,NoOp(--- TESTE DE AUDIO PT-BR ---)
    same => n,Answer()
    same => n,Set(CHANNEL(language)=pt_BR)
    same => n,Playback(demo-thanks)        
    same => n,SayDigits(12345)             
    same => n,Hangup()

exten => *82,1,NoOp(--- DESCOBERTA DE RAMAL ---)
    same => n,Answer()
    same => n,Set(CHANNEL(language)=pt_BR)  
    same => n,SayDigits(\${CALLERID(num)})             
    same => n,Hangup()

[crctx-nacional]
include => crctx-interno
include => saida-lcr

; Rota para Celular/Fixo Local (8 ou 9 dígitos)
exten => _[2-9]XXXXXXXX.,1,Goto(saida-lcr,\${EXTEN},1)

; Rota para DDD (0 + DDD + 8 ou 9 dígitos)
; O '.' após o sétimo dígito garante que pegue fixo (10) ou móvel (11)
exten => _0[1-9][1-9][2-9]XXXXXX.,1,Goto(saida-lcr,\${EXTEN},1)

; Bloqueio de DDI (opcional, já que você tem o premium)
exten => _00X.,1,Playback(ss-noservice)
    same => n,Hangup()

[crctx-premium]
include => crctx-interno
include => crctx-nacional
exten => _00X.,1,Goto(saida-lcr,\${EXTEN},1)

[saida-lcr]
exten => _X.,1,NoOp(--- ROTA DE SAIDA DINAMICA ---)
    ; Busca: Tronco, Remover, Adicionar
    same => n,Set(DADOS_ROTA=\${ODBC_GET_OUTBOUND_ROUTE(\${EXTEN})})
    
    ; Se não encontrar rota no banco, encerra
    same => n,GotoIf(\$["\${DADOS_ROTA}" = ""]?falha-saida)
    
    ; Separa as variáveis (o ODBC retorna as colunas separadas por vírgula)
    same => n,Set(TRONCO_DESTINO=\${CUT(DADOS_ROTA,\, ,1)})
    same => n,Set(REMOVER=\${CUT(DADOS_ROTA,\, ,2)})
    same => n,Set(ADICIONAR=\${CUT(DADOS_ROTA,\, ,3)})
    
    ; Tratamento do número discado (Ex: remove 0, adiciona 55)
    same => n,Set(NUMERO_FINAL=\${ADICIONAR}\${EXTEN:\${REMOVER}})
    
    same => n,NoOp(Discando para \${NUMERO_FINAL} via \${TRONCO_DESTINO})
    same => n,Dial(PJSIP/\${NUMERO_FINAL}@\${TRONCO_DESTINO},60,rtT)
    same => n,Hangup()

    same => n(falha-saida),NoOp(Nenhuma rota encontrada para \${EXTEN})
    same => n,Playback(ss-noservice)
    same => n,Hangup()

[crctx-entrada]
exten => _X.,1,NoOp(--- Inicio DID: \${EXTEN} ---)
    same => n,Set(DADOS_ROTA=\${ODBC_GET_ROTA(\${EXTEN})})
    same => n,GotoIf($["\${DADOS_ROTA}" = ""]?contexto-fallback,s,1)
    
    same => n,Set(TIPO_DESTINO=\${CUT(DADOS_ROTA,\, ,1)})
    same => n,Set(DESTINO=\${CUT(DADOS_ROTA,\, ,2)})
    same => n,Set(ID_CALENDARIO=\${CUT(DADOS_ROTA,\, ,3)})

    same => n,GotoIf($["\${ID_CALENDARIO}" = ""]?direcionar)
    same => n,Set(REGRA_NUM=1)

    same => n(loop-agenda),Set(DADOS_AGENDA=\${ODBC_GET_CALENDARIO(\${ID_CALENDARIO},\${REGRA_NUM})})
    same => n,GotoIf($["\${DADOS_AGENDA}" = ""]?direcionar)

    same => n,Set(G_HORA=\${CUT(DADOS_AGENDA,\, ,1)})
    same => n,Set(G_DSEM=\${CUT(DADOS_AGENDA,\, ,2)})
    same => n,Set(G_DMES=\${CUT(DADOS_AGENDA,\, ,3)})
    same => n,Set(G_MES=\${CUT(DADOS_AGENDA,\, ,4)})
    same => n,Set(G_ACAO=\${CUT(DADOS_AGENDA,\, ,5)})
    same => n,Set(G_DEST=\${CUT(DADOS_AGENDA,\, ,6)})

    same => n,GotoIfTime(\${G_HORA},\${G_DSEM},\${G_DMES},\${G_MES}?executar-regra)

    same => n,Set(REGRA_NUM=$[ \${REGRA_NUM} + 1 ])
    same => n,Goto(loop-agenda)

    same => n(executar-regra),NoOp(Regra Coincidiu: Acao=\${G_ACAO})
    same => n,GotoIf($["\${G_ACAO}" = "FECHADO"]?falar-fechado)
    same => n,Set(DESTINO=\${G_DEST})
    ; Se a regra de calendário mudar o destino para uma URA, precisamos atualizar o tipo
    same => n,Set(TIPO_DESTINO=\${IF($["\${G_ACAO}"="URA"]?URA:\${TIPO_DESTINO})})
    same => n,Goto(direcionar)

    same => n(falar-fechado),Answer()
    same => n,Playback(\${G_DEST})
    same => n,Hangup()

    same => n(direcionar),NoOp(Direcionando: Tipo=\${TIPO_DESTINO} | Destino=\${DESTINO})
    same => n,GotoIf($["\${TIPO_DESTINO}" = "RAMAL"]?dial-ramal)
    same => n,GotoIf($["\${TIPO_DESTINO}" = "FILA"]?dial-fila)
    same => n,GotoIf($["\${TIPO_DESTINO}" = "URA"]?dial-ura)
    same => n,GotoIf($["\${TIPO_DESTINO}" = "EXTERNO"]?dial-externo)
    same => n,GotoIf($["\${TIPO_DESTINO}" = "INTERCEPTAR"]?dial-intercept)
    same => n,Hangup()

    same => n(dial-ramal),Dial(PJSIP/\${DESTINO},30,Tt)
    same => n,Hangup()

    same => n(dial-fila),Queue(\${DESTINO},rtT)
    same => n,Playback(vm-nobodyavail)
    same => n,Goto(contexto-fallback,s,1)

    ; --- ATUALIZAÇÃO PARA URA DINÂMICA ---
    same => n(dial-ura),Set(ID_URA=\${DESTINO})
    same => n,Goto(ura-dinamica,s,1)
    ; -------------------------------------

    same => n(dial-externo),Set(TR_EXTERN=\${ODBC_GET_TRONCO_SAIDA()})
    same => n,Dial(PJSIP/\${DESTINO}@\${TR_EXTERN},60,T)
    same => n,Hangup()

    same => n(dial-intercept),Answer()
    same => n,Playback(\${DESTINO})
    same => n,Hangup()

[contexto-fallback]
exten => s,1,Answer()
    same => n,Playback(ss-noservice)
    same => n,Hangup()
EOF

# --- 4. PERMISSÕES E INICIALIZAÇÃO ---
echo "Sincronizando permissões de arquivos..."
chown -R asterisk:asterisk /etc/asterisk /var/lib/asterisk /var/log/asterisk /var/spool/asterisk

echo "Iniciando Asterisk (Foreground)..."
exec asterisk -f -U asterisk -vvvg
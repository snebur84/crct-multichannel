FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    asterisk \
    unixodbc \
    odbc-postgresql \
    openssl \
    dos2unix \
    python3 \
    wget tar \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

# Preparação de diretórios
RUN mkdir -p /etc/asterisk /var/lib/asterisk /var/log/asterisk /var/spool/asterisk \
    && chown -R asterisk:asterisk /etc/asterisk /var/lib/asterisk /var/log/asterisk /var/spool/asterisk

# --- ÁUDIOS PT-BR ---
# No seu Dockerfile:

# 1. Limpa qualquer som que o apt-get possa ter instalado (evita confusão)
RUN rm -rf /var/lib/asterisk/sounds/en /var/lib/asterisk/sounds/en_US

# 2. Cria a pasta destino
RUN mkdir -p /var/lib/asterisk/sounds/pt_BR

# 3. Copia e extrai
COPY ./asterisk_assets/sounds_pt/pt-br.tar.gz /tmp/pt-br.tar.gz
RUN tar -zxvf /tmp/pt-br.tar.gz -C /var/lib/asterisk/sounds/pt_BR --strip-components=1 \
    && rm /tmp/pt-br.tar.gz

# 4. Link simbólico (O "Pulo do Gato")
# Muitos módulos do Asterisk buscam a pasta 'pt' ou 'pt_BR' de forma variada. 
# Criar um link garante que ele ache de qualquer jeito.
RUN ln -s /var/lib/asterisk/sounds/pt_BR /var/lib/asterisk/sounds/pt

# Garante as permissões
RUN chown -R asterisk:asterisk /var/lib/asterisk/sounds/pt_BR
RUN chown -R asterisk:asterisk /var/lib/asterisk/sounds/
RUN chmod -R 775 /var/lib/asterisk/sounds/

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
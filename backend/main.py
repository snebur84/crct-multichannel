from fastapi import FastAPI
from database import engine
import models
from routers import ramais, troncos, grupos, features, rotas_entrada, rotas_saida, calendar, filas, agentes, cdr, uras, arquivos, abreviados

# Cria as tabelas baseadas no models.py 
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRCTX Management API")

# Acopla os roteadores modularizados
app.include_router(ramais.router)
app.include_router(troncos.router)
app.include_router(grupos.router)
app.include_router(features.router)
app.include_router(rotas_entrada.router)
app.include_router(rotas_saida.router)
app.include_router(calendar.router)
app.include_router(filas.router)
app.include_router(agentes.router)
app.include_router(cdr.router)
app.include_router(uras.router)
app.include_router(arquivos.router)
app.include_router(abreviados.router)

@app.get("/")
def root():
    return {"message": "API CRCTX Ativa", "docs": "/docs"}
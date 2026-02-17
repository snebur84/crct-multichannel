from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from database import get_db
from datetime import datetime
import csv
import io
import models, schemas
from typing import List

router = APIRouter(prefix="/report", tags=["CDR (Call Detail Record)"])

@router.get("/cdr/")
def listar_historico(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.CDRModel).order_by(models.CDRModel.start.desc()).limit(limit).all()

@router.get("/cdr/extrair", response_model=schemas.CDRRelatorioSchema)
def extrair_relatorio_personalizado(
    data_inicio: datetime,
    data_fim: datetime,
    origem: str = Query(None),
    destino: str = Query(None),
    status: str = Query(None, description="Ex: ANSWERED, NO ANSWER, BUSY"),
    db: Session = Depends(get_db)
):
    # Base da query entre as datas obrigatórias
    query = db.query(models.CDRModel).filter(
        models.CDRModel.start.between(data_inicio, data_fim)
    )

    # Filtros opcionais dinâmicos
    if origem:
        query = query.filter(models.CDRModel.src.ilike(f"%{origem}%"))
    if destino:
        query = query.filter(models.CDRModel.dst.ilike(f"%{destino}%"))
    if status:
        query = query.filter(models.CDRModel.disposition == status.upper())

    # Ordenação por data mais recente
    resultados = query.order_by(models.CDRModel.start.desc()).all()

    return {
        "total_registros": len(resultados),
        "filtros_aplicados": {
            "inicio": data_inicio,
            "fim": data_fim,
            "status": status
        },
        "dados": resultados
    }

@router.get("/cdr/exportar-csv",responses={200: {"content": {"text/csv": {}},"description": "Retorna um arquivo CSV com os registros filtrados.",}})
def exportar_cdr_csv(
    data_inicio: datetime,
    data_fim: datetime,
    db: Session = Depends(get_db)
):
    # 1. Busca os dados no banco
    chamadas = db.query(models.CDRModel).filter(
        models.CDRModel.start.between(data_inicio, data_fim)
    ).order_by(models.CDRModel.start.asc()).all()

    # 2. Cria um fluxo de texto em memória
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';') # Excel prefere ';' em PT-BR

    # 3. Cabeçalho do CSV
    writer.writerow([
        "Data/Hora", "Origem", "Destino", "Duracao Total", 
        "Tempo Falado", "Status", "ID Unico"
    ])

    # 4. Linhas de dados
    for c in chamadas:
        writer.writerow([
            c.start.strftime("%d/%m/%Y %H:%M:%S"),
            c.src,
            c.dst,
            f"{c.duration}s",
            f"{c.billsec}s",
            c.disposition,
            c.uniqueid
        ])

    # 5. Prepara a resposta para download
    output.seek(0)
    filename = f"relatorio_cdr_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
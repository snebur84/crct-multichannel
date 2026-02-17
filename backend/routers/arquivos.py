from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os

router = APIRouter(prefix="/configuracao/audios", tags=["Gestão de Áudios"])

# O caminho deve ser exatamente onde o volume está montado
UPLOAD_DIR = "/var/lib/asterisk/sounds/custom"

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    # Asterisk lida melhor com .wav (16bit, 8khz mono é o ideal)
    if not file.filename.endswith(('.wav', '.gsm', '.sln')):
        raise HTTPException(status_code=400, detail="Formato inválido. Use .wav, .gsm ou .sln")

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
    
    # Retorna o nome sem extensão para facilitar o uso no Dialplan/URA
    nome_audio = os.path.splitext(file.filename)[0]
    return {
        "message": "Áudio enviado com sucesso", 
        "caminho_asterisk": f"custom/{nome_audio}"
    }

@router.get("/")
def listar_audios():
    if not os.path.exists(UPLOAD_DIR):
        return []
    # Lista arquivos e remove extensões para a visualização na URA
    arquivos = os.listdir(UPLOAD_DIR)
    return {"audios_disponiveis": arquivos}

@router.delete("/{nome_arquivo}")
def deletar_audio(nome_arquivo: str):
    file_path = os.path.join(UPLOAD_DIR, nome_arquivo)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": f"Arquivo {nome_arquivo} removido"}
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")
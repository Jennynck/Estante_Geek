from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base, Usuario
from models.base import TipoObra
from schemas.obra import ObraDetalhe, ObraResponse, ObraImportar
from schemas.usuario import TokenResponse, UsuarioCreate, UsuarioLogin, UsuarioResponse
from schemas.usuario_obra import (
    ResenhaCreate, ResenhaResponse, ResenhasObra, UsuarioObraCreate, UsuarioObraResponse,
    UsuarioObraUpdate,)
from schemas.usuario_volume import ChecklistObra, UsuarioVolumeResponse, UsuarioVolumeUpdate
from services.service_catalogo import CatalogoService
from services.service_estante import EstanteService
from services.service_usuario import UsuarioService

# Cria as tabelas no banco caso não existam
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Estante Geek")

# Libera o frontend (Svelte, porta 5173) para chamar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usuário logado, a partir do token enviado no cabeçalho Authorization
def usuarioLogado(credenciais=Depends(HTTPBearer()), db: Session = Depends(get_db)) -> Usuario:
    return UsuarioService.buscarPorToken(db, credenciais.credentials)


# ---------- Importação das APIs ----------
@app.post("/obras/importar", response_model=ObraDetalhe)
def importarObra(dados: ObraImportar, usuario: Usuario = Depends(usuarioLogado),
                 db: Session = Depends(get_db)):
    return CatalogoService.importarPorIdApi(db, dados.tipo_obra, dados.id_api)

# ---------- Autenticação e perfil ----------
@app.post("/auth/cadastro", response_model=UsuarioResponse, status_code=201)
def cadastrar(dados: UsuarioCreate, db: Session = Depends(get_db)):
    return UsuarioService.cadastrar(db, dados)

@app.post("/auth/login", response_model=TokenResponse)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    return UsuarioService.login(db, dados)

@app.get("/usuarios/me", response_model=UsuarioResponse)
def meuPerfil(usuario: Usuario = Depends(usuarioLogado)):
    return usuario


# ---------- Catálogo ----------
@app.get("/obras", response_model=list[ObraResponse])
def listarObras(busca: str | None = None, tipo_obra: TipoObra | None = None,
                 usuario: Usuario = Depends(usuarioLogado), db: Session = Depends(get_db)):
    return CatalogoService.listar(db, busca, tipo_obra)

@app.get("/obras/{obras_id}", response_model=ObraDetalhe)
def detalharObra(obras_id: int, usuario: Usuario = Depends(usuarioLogado),
                  db: Session = Depends(get_db)):
    return CatalogoService.detalhar(db, obras_id)

@app.get("/obras/{obras_id}/resenhas", response_model=ResenhasObra)
def listarResenhas(obras_id: int, usuario: Usuario = Depends(usuarioLogado),
                    db: Session = Depends(get_db)):
    return CatalogoService.resenhas(db, obras_id)


# ---------- Estante ----------
@app.get("/estante", response_model=list[UsuarioObraResponse])
def listarEstante(usuario: Usuario = Depends(usuarioLogado), db: Session = Depends(get_db)):
    return EstanteService.listar(db, usuario.id)

@app.post("/estante", response_model=UsuarioObraResponse, status_code=201)
def adicionarObra(dados: UsuarioObraCreate, usuario: Usuario = Depends(usuarioLogado),
                   db: Session = Depends(get_db)):
    return EstanteService.adicionar(db, usuario.id, dados.obras_id)

@app.patch("/estante/{obras_id}", response_model=UsuarioObraResponse)
def atualizarStatus(obras_id: int, dados: UsuarioObraUpdate,
                     usuario: Usuario = Depends(usuarioLogado), db: Session = Depends(get_db)):
    return EstanteService.atualizarStatus(db, usuario.id, obras_id, dados.status)

@app.delete("/estante/{obras_id}", status_code=204)
def removerObra(obras_id: int, usuario: Usuario = Depends(usuarioLogado),
                 db: Session = Depends(get_db)):
    EstanteService.remover(db, usuario.id, obras_id)


# ---------- Checklist de volumes ----------
@app.get("/estante/{obras_id}/checklist", response_model=ChecklistObra)
def verChecklist(obras_id: int, usuario: Usuario = Depends(usuarioLogado),
                  db: Session = Depends(get_db)):
    return EstanteService.checklist(db, usuario.id, obras_id)

@app.patch("/estante/{obras_id}/volumes/{volumes_id}", response_model=UsuarioVolumeResponse)
def atualizarVolume(obras_id: int, volumes_id: int, dados: UsuarioVolumeUpdate,
                     usuario: Usuario = Depends(usuarioLogado), db: Session = Depends(get_db)):
    return EstanteService.atualizarVolume(db, usuario.id, obras_id, volumes_id,
                                           dados.possui_volume, dados.lido)


# ---------- Resenha ----------
@app.put("/estante/{obras_id}/resenha", response_model=ResenhaResponse)
def salvarResenha(obras_id: int, dados: ResenhaCreate, usuario: Usuario = Depends(usuarioLogado),
                   db: Session = Depends(get_db)):
    return EstanteService.salvarResenha(db, usuario.id, obras_id, dados)

# Documentação: http://localhost:8000/docs
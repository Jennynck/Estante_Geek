from fastapi import BackgroundTasks, Depends, FastAPI, UploadFile, HTTPException, Response, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base, Usuario
from models.base import TipoObra
from schemas.obra import ObraDetalhe, ObraResponse, ObraImportar, ObraCatalogo
from schemas.usuario import (ConfirmarEmail, ExcluirConta, MensagemResponse, ReenviarConfirmacao,
                             TokenResponse, UsuarioCreate, UsuarioLogin, UsuarioResponse, UsuarioPublico, 
                             LeitorAfinidade,EsqueciSenha, RedefinirSenha)
from schemas.usuario_obra import (
    ResenhaCreate, ResenhaResponse, ResenhasObra, UsuarioObraCreate, UsuarioObraResponse,
    UsuarioObraUpdate)
from schemas.usuario_volume import ChecklistObra, UsuarioVolumeResponse, UsuarioVolumeUpdate
from services.service_catalogo import CatalogoService
from services.service_estante import EstanteService
from services.service_usuario import FOTO_MAX_BYTES, UsuarioService, UsuarioUpdate, tipoDaImagem
from services.service_afinidade import AfinidadeService

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
def cadastrar(dados: UsuarioCreate, tarefas: BackgroundTasks, db: Session = Depends(get_db)):
    usuario = UsuarioService.cadastrar(db, dados)
    tarefas.add_task(UsuarioService.enviarConfirmacao, usuario.id, usuario.email, usuario.nome_usuario)
    return usuario

@app.post("/auth/confirmar-email", response_model=MensagemResponse)
def confirmarEmail(dados: ConfirmarEmail, db: Session = Depends(get_db)):
    UsuarioService.confirmarEmail(db, dados.token)
    return MensagemResponse(mensagem="E-mail confirmado com sucesso! Agora você já pode fazer login")

@app.post("/auth/reenviar-confirmacao", response_model=MensagemResponse)
def reenviarConfirmacao(dados: ReenviarConfirmacao, tarefas: BackgroundTasks,
                        db: Session = Depends(get_db)):
    usuario = UsuarioService.pendenteDeConfirmacao(db, dados.email)
    if usuario:
        tarefas.add_task(UsuarioService.enviarConfirmacao, usuario.id, usuario.email, usuario.nome_usuario)
    return MensagemResponse(mensagem="Se o e-mail estiver cadastrado e pendente, enviamos um novo link")


# ---------- Login -----------
@app.post("/auth/login", response_model=TokenResponse)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    return UsuarioService.login(db, dados)


# --------- Redefição de senha ---------
@app.post("/auth/esqueci-senha", response_model=MensagemResponse)
def esqueciSenha(dados: EsqueciSenha, tarefas: BackgroundTasks, db: Session = Depends(get_db)):
    usuario = UsuarioService.buscarPorEmail(db, dados.email)
    if usuario:
        tarefas.add_task(UsuarioService.enviarRedefinicao, usuario.id, usuario.email,
                         usuario.nome_usuario, usuario.senha)
    # Resposta igual se existe ou não a conta para não revelar os e-mails cadastrados
    return MensagemResponse(mensagem="Se o e-mail estiver cadastrado, enviamos um link para redefinir a senha")

@app.post("/auth/redefinir-senha", response_model=MensagemResponse)
def redefinirSenha(dados: RedefinirSenha, db: Session = Depends(get_db)):
    UsuarioService.redefinirSenha(db, dados.token, dados.nova_senha)
    return MensagemResponse(mensagem="Senha redefinida com sucesso! Agora você já pode fazer login")


# --------- CRUD Usuario ----------
@app.get("/usuarios/me", response_model=UsuarioResponse)
def meuPerfil(usuario: Usuario = Depends(usuarioLogado)):
    return usuario

@app.patch("/usuarios/me", response_model=UsuarioResponse)
def atualizarMeuPerfil(dados: UsuarioUpdate, usuario: Usuario = Depends(usuarioLogado),
                       db: Session = Depends(get_db)):
    return UsuarioService.atualizarPerfil(db, usuario, dados)

@app.delete("/usuarios/me", status_code=204)
def excluirMinhaConta(dados: ExcluirConta, usuario: Usuario = Depends(usuarioLogado),
                      db: Session = Depends(get_db)):
    UsuarioService.excluirConta(db, usuario, dados.senha)


# --------- Fotos de perfil ----------
@app.put("/usuarios/me/foto", status_code=204)
def enviarMinhaFoto(arquivo: UploadFile = File(...), usuario: Usuario = Depends(usuarioLogado),
                    db: Session = Depends(get_db)):
# le no máximo 1 byte além do limite pra detectar arquivos grandes sem carregá-los inteiros
    conteudo = arquivo.file.read(FOTO_MAX_BYTES + 1)
    UsuarioService.salvarFoto(db, usuario, conteudo)

@app.get("/usuarios/me/foto")
def verMinhaFoto(usuario: Usuario = Depends(usuarioLogado)):
    if not usuario.foto:
        raise HTTPException(404, "Você ainda não tem foto de perfil")
    return Response(content=usuario.foto,
                    media_type=tipoDaImagem(usuario.foto) or "application/octet-stream")

@app.delete("/usuarios/me/foto", status_code=204)
def removerMinhaFoto(usuario: Usuario = Depends(usuarioLogado), db: Session = Depends(get_db)):
    UsuarioService.removerFoto(db, usuario)

@app.get("/usuarios/{usuarios_id}", response_model=UsuarioPublico)
def verPerfilDeUsuario(usuarios_id: int, usuario: Usuario = Depends(usuarioLogado),
                       db: Session = Depends(get_db)):
    return UsuarioService.verPerfil(db, usuarios_id, usuario.id)

@app.get("/usuarios/{usuarios_id}/foto")
def verFotoDeUsuario(usuarios_id: int, usuario: Usuario = Depends(usuarioLogado),
                     db: Session = Depends(get_db)):
    foto = UsuarioService.buscarFoto(db, usuarios_id)
    return Response(content=foto, media_type=tipoDaImagem(foto) or "application/octet-stream")

@app.get("/usuarios/{usuarios_id}/obras-em-comum", response_model=list[ObraCatalogo])
def obrasEmComum(usuarios_id: int, usuario: Usuario = Depends(usuarioLogado),
                 db: Session = Depends(get_db)):
    return AfinidadeService.obrasEmComum(db, usuario.id, usuarios_id)


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


# ---------- Leitores por Afinidade ---------
@app.get("/leitores", response_model=list[LeitorAfinidade])
def descobrirLeitores(pagina: int = 1, limite: int = 20,
                      usuario: Usuario = Depends(usuarioLogado), db: Session = Depends(get_db)):
    return AfinidadeService.leitores(db, usuario.id, pagina, limite)


# ---------- Checklist de volumes ----------
@app.get("/estante/{obras_id}/checklist", response_model=ChecklistObra)
def verChecklist(obras_id: int, usuario: Usuario = Depends(usuarioLogado),
                  db: Session = Depends(get_db)):
    return EstanteService.checklist(db, usuario.id, obras_id)

@app.patch("/estante/{obras_id}/volumes/{volumes_id}", response_model=UsuarioVolumeResponse)
def atualizarVolume(obras_id: int, volumes_id: int, dados: UsuarioVolumeUpdate,
                     usuario: Usuario = Depends(usuarioLogado), db: Session = Depends(get_db)):
    return EstanteService.atualizarVolume(db, usuario.id, obras_id, volumes_id, dados.lido)


# ---------- Resenha ----------
@app.put("/estante/{obras_id}/resenha", response_model=ResenhaResponse)
def salvarResenha(obras_id: int, dados: ResenhaCreate, usuario: Usuario = Depends(usuarioLogado),
                   db: Session = Depends(get_db)):
    return EstanteService.salvarResenha(db, usuario.id, obras_id, dados)

@app.delete("/estante/{obras_id}/resenha", status_code=204)
def removerMinhaResenha(obras_id: int, usuario: Usuario = Depends(usuarioLogado),
                        db: Session = Depends(get_db)):
    EstanteService.removerResenha(db, usuario.id, obras_id)


# Documentação: http://localhost:8000/docs
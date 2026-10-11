from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

def _vazio_vira_none(valor):
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor

class UsuarioCreate(BaseModel):
    nome_perfil: str = Field(min_length=1, max_length=50)
    nome_usuario: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=100)
    senha: str = Field(min_length=8, max_length=72)
    instagram: str | None = Field(default=None, max_length=50)
    discord: str | None = Field(default=None, max_length=50)
    x: str | None = Field(default=None, max_length=50)

    _contatos = field_validator("instagram", "discord", "x", mode="before")(_vazio_vira_none)

# Login
class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ConfirmarEmail(BaseModel):
    token: str

class EsqueciSenha(BaseModel):
    email: EmailStr

class RedefinirSenha(BaseModel):
    token: str
    nova_senha: str = Field(min_length=8, max_length=72)

class MensagemResponse(BaseModel):
    mensagem: str

# Edição do perfil e da visibilidade
# Tudo é opcional, só muda o que o usuário enviar (um contato enviado como null é removido)
class UsuarioUpdate(BaseModel):
    nome_perfil: str | None = Field(default=None, min_length=1, max_length=50)
    nome_usuario: str | None = Field(default=None, min_length=1, max_length=50)
    instagram: str | None = Field(default=None, max_length=50)
    discord: str | None = Field(default=None, max_length=50)
    x: str | None = Field(default=None, max_length=50)
    perfil_publico: bool | None = None

    _contatos = field_validator("instagram", "discord", "x", mode="before")(_vazio_vira_none)

# O que o próprio usuário vê da sua conta
class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome_perfil: str
    nome_usuario: str
    email: str
    email_confirmado: bool
    instagram: str | None = None
    discord: str | None = None
    x: str | None = None
    perfil_publico: bool
    is_admin: bool

# Perfil visto por outros usuários
class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome_perfil: str
    instagram: str | None = None
    discord: str | None = None
    x: str | None = None

# Leitor encontrado na descoberta, com as obras que tem em comum com quem consulta
class LeitorAfinidade(UsuarioPublico):
    total_em_comum: int = 0
    obras_em_comum: list[str] = []

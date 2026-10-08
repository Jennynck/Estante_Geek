from pydantic import BaseModel, ConfigDict, Field
# A senha chega aqui em texto normal e é criptografada antes de salvar
class UsuarioCreate(BaseModel):
    nome_perfil: str = Field(max_length=50)
    nome_usuario: str = Field(max_length=50)
    email: str = Field(max_length=100)
    senha: str = Field(max_length=72)
# Login (RF02)
class UsuarioLogin(BaseModel):
    email: str
    senha: str
# Edição do perfil e da visibilidade
# Tudo é opcional só muda o que o usuário enviar
class UsuarioUpdate(BaseModel):
    nome_perfil: str | None = Field(default=None, max_length=50)
    nome_usuario: str | None = Field(default=None, max_length=50)
    instagram: str | None = Field(default=None, max_length=50)
    discord: str | None = Field(default=None, max_length=50)
    x: str | None = Field(default=None, max_length=50)
    perfil_publico: bool | None = None
#
class UsuarioResponse(BaseModel):
    #  O que o próprio usuário vê da sua conta
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
# Se perfil_publico for false o endpoint não deve devolver os contatos
class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome_perfil: str
    instagram: str | None = None
    discord: str | None = None
    x: str | None = None
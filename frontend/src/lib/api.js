
/*
  ESTANTE GEEK — SERVIÇO DE API

  Centraliza as requisições ao backend e o
  tratamento de sessões expiradas.
*/

export const API_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CHAVE_TOKEN = 'estante_geek_token';

export function obterToken() {
  if (typeof localStorage === 'undefined') {
    return null;
  }

  return localStorage.getItem(CHAVE_TOKEN);
}

export function guardarToken(token) {
  if (typeof localStorage === 'undefined') return;

  localStorage.setItem(CHAVE_TOKEN, token);
}

export function apagarToken() {
  if (typeof localStorage === 'undefined') return;

  localStorage.removeItem(CHAVE_TOKEN);
}

/*
  Executada apenas quando uma requisição autenticada
  recebe HTTP 401.

  Verifica o token utilizado para não encerrar uma
  sessão nova por causa de uma requisição antiga.
*/
function tratarSessaoExpirada(tokenUtilizado) {
  if (!tokenUtilizado) return;

  if (obterToken() !== tokenUtilizado) {
    return;
  }

  apagarToken();

  if (typeof window === 'undefined') {
    return;
  }

  const caminho = window.location.pathname;

  // Evita redirecionamentos repetidos no login.
  if (caminho === '/login') {
    return;
  }

  window.location.replace('/login?sessao=expirada');
}

/*
  Converte os erros retornados pelo FastAPI
  em mensagens que podem aparecer nas telas.
*/
async function obterMensagemErro(resposta, alternativa) {
  const resultado = await resposta
    .json()
    .catch(() => ({}));

  if (typeof resultado.detail === 'string') {
    return resultado.detail;
  }

  if (Array.isArray(resultado.detail)) {
    return (
      resultado.detail
        .map((erro) => erro.msg)
        .filter(Boolean)
        .join('; ') || alternativa
    );
  }

  return alternativa;
}

/*
  Requisições comuns: GET, POST, PATCH, PUT e DELETE.

  autenticar: false é usado no login, cadastro,
  confirmação de e-mail e recuperação de senha.
*/
export async function requisicao(
  caminho,
  {
    metodo = 'GET',
    dados = null,
    autenticar = true
  } = {}
) {
  const cabecalhos = {
    Accept: 'application/json'
  };

  if (dados !== null) {
    cabecalhos['Content-Type'] = 'application/json';
  }

  const tokenUtilizado = autenticar
    ? obterToken()
    : null;

  if (tokenUtilizado) {
    cabecalhos.Authorization = `Bearer ${tokenUtilizado}`;
  }

  let resposta;

  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      method: metodo,
      headers: cabecalhos,
      body:
        dados !== null
          ? JSON.stringify(dados)
          : undefined
    });
  } catch {
    throw new Error(
      'Não foi possível conectar ao servidor. ' +
      'Verifique se o backend está funcionando.'
    );
  }

  if (resposta.status === 204) {
    return null;
  }

  if (!resposta.ok) {
    const mensagem = await obterMensagemErro(
      resposta,
      'Não foi possível concluir a operação.'
    );

    if (resposta.status === 401 && autenticar) {
      tratarSessaoExpirada(tokenUtilizado);

      throw new Error(
        tokenUtilizado
          ? 'Sua sessão expirou. Entre novamente para continuar.'
          : 'Faça login para continuar.'
      );
    }

    throw new Error(mensagem);
  }

  return resposta.json().catch(() => null);
}

/*
  Upload de arquivos, como a foto do perfil.

  Não configura Content-Type manualmente porque
  o navegador monta o multipart/form-data.
*/
export async function enviarArquivo(
  caminho,
  arquivo,
  {
    metodo = 'PUT',
    campo = 'arquivo'
  } = {}
) {
  const formulario = new FormData();
  formulario.append(campo, arquivo);

  const cabecalhos = {
    Accept: 'application/json'
  };

  const tokenUtilizado = obterToken();

  if (tokenUtilizado) {
    cabecalhos.Authorization = `Bearer ${tokenUtilizado}`;
  }

  let resposta;

  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      method: metodo,
      headers: cabecalhos,
      body: formulario
    });
  } catch {
    throw new Error(
      'Não foi possível conectar ao servidor. ' +
      'Verifique se o backend está funcionando.'
    );
  }

  if (resposta.ok) {
    return null;
  }

  const mensagem = await obterMensagemErro(
    resposta,
    'Não foi possível enviar o arquivo.'
  );

  if (resposta.status === 401) {
    tratarSessaoExpirada(tokenUtilizado);

    throw new Error(
      'Sua sessão expirou. Entre novamente para continuar.'
    );
  }

  throw new Error(mensagem);
}

/*
  Busca uma foto protegida por autenticação
  e devolve uma URL temporária.

  Quem utiliza essa URL deve chamar
  URL.revokeObjectURL ao terminar.
*/
export async function buscarFoto(caminho) {
  const tokenUtilizado = obterToken();

  if (!tokenUtilizado) {
    return null;
  }

  try {
    const resposta = await fetch(
      `${API_URL}${caminho}`,
      {
        headers: {
          Authorization: `Bearer ${tokenUtilizado}`
        }
      }
    );

    if (resposta.status === 401) {
      tratarSessaoExpirada(tokenUtilizado);
      return null;
    }

    if (!resposta.ok) {
      return null;
    }

    const imagem = await resposta.blob();

    return URL.createObjectURL(imagem);
  } catch {
    return null;
  }
}

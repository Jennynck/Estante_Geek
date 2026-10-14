// Todas as chamadas ao backend passam por este serviço.
// Altere VITE_API_URL no .env do frontend caso o backend use outro endereço.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CHAVE_TOKEN = 'estante_geek_token';

export function obterToken() {
  return typeof localStorage === 'undefined' ? null : localStorage.getItem(CHAVE_TOKEN);
}

export function guardarToken(token) {
  localStorage.setItem(CHAVE_TOKEN, token);
}

export function apagarToken() {
  localStorage.removeItem(CHAVE_TOKEN);
}

export async function requisicao(caminho, { metodo = 'GET', dados = null, autenticar = true } = {}) {
  const cabecalhos = { Accept: 'application/json' };
  if (dados !== null) cabecalhos['Content-Type'] = 'application/json';
  if (autenticar && obterToken()) cabecalhos.Authorization = `Bearer ${obterToken()}`;

  let resposta;
  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      method: metodo,
      headers: cabecalhos,
      body: dados !== null ? JSON.stringify(dados) : undefined
    });
  } catch {
    throw new Error('Não foi possível conectar ao servidor. Verifique se o backend está funcionando.');
  }

  if (resposta.status === 204) return null;
  const resultado = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    let mensagem = 'Não foi possível concluir a operação.';
    if (typeof resultado.detail === 'string') mensagem = resultado.detail;
    else if (Array.isArray(resultado.detail)) {
      mensagem = resultado.detail.map((erro) => erro.msg).filter(Boolean).join('; ') || mensagem;
    }
    if (resposta.status === 401 && autenticar) {
      mensagem = 'Sua sessão expirou ou você não está autenticado. Faça login novamente.';
    }
    throw new Error(mensagem);
  }
  return resultado;
}

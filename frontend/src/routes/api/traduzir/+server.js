import { json } from '@sveltejs/kit';

// Traduz sinopses usando o servidor do SvelteKit.
// Serviço público não oficial do Google Tradutor:
// pode apresentar bloqueios ou limites de uso.

const cache = new Map();

const TAMANHO_MAXIMO = 4500;

function separar(texto, tamanho = 1200) {
  const partes = [];

  let restante = texto;

  while (restante.length > tamanho) {
    let corte = restante.lastIndexOf(' ', tamanho);

    if (corte < tamanho / 2) {
      corte = tamanho;
    }

    partes.push(
      restante.slice(0, corte).trim()
    );

    restante = restante.slice(corte).trim();
  }

  if (restante) {
    partes.push(restante);
  }

  return partes;
}

async function traduzirParte(fetchApi, trecho) {
  const url = new URL(
    'https://translate.googleapis.com/translate_a/single'
  );

  url.searchParams.set('client', 'gtx');
  url.searchParams.set('sl', 'auto');
  url.searchParams.set('tl', 'pt');
  url.searchParams.set('dt', 't');
  url.searchParams.set('q', trecho);

  const resposta = await fetchApi(url.toString());

  if (!resposta.ok) {
    throw new Error(
      'Serviço de tradução indisponível.'
    );
  }

  const dados = await resposta.json();

  const traducao = (dados?.[0] || [])
    .map((item) => item?.[0] || '')
    .join('');

  if (!traducao) {
    throw new Error(
      'O serviço não retornou uma tradução.'
    );
  }

  return traducao;
}

export async function POST({ request, fetch }) {
  let entrada;

  try {
    entrada = await request.json();
  } catch {
    return json(
      { erro: 'Dados inválidos.' },
      { status: 400 }
    );
  }

  const texto =
    typeof entrada?.texto === 'string'
      ? entrada.texto.trim()
      : '';

  if (!texto || texto.length > TAMANHO_MAXIMO) {
    return json(
      {
        erro: 'Texto vazio ou muito longo para traduzir.'
      },
      { status: 400 }
    );
  }

  if (cache.has(texto)) {
    return json({
      traducao: cache.get(texto)
    });
  }

  try {
    const traducoes = [];

    for (const trecho of separar(texto)) {
      traducoes.push(
        await traduzirParte(fetch, trecho)
      );
    }

    const traducao = traducoes.join(' ');

    if (cache.size >= 80) {
      cache.delete(
        cache.keys().next().value
      );
    }

    cache.set(texto, traducao);

    return json({ traducao });
  } catch {
    return json(
      {
        erro: 'Tradução automática indisponível neste momento.'
      },
      { status: 502 }
    );
  }
}
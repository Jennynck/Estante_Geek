import { json } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

// ========================================
// CONFIGURAÇÕES DAS APIS
// ========================================

const TENRAI = (
  env.TENRAI_BASE_URL ||
  'https://api.tenrai.org/v1'
)
  .trim()
  .replace(/^['"]|['"]$/g, '')
  .replace(/\/$/, '');

const COMIC_VINE =
  'https://comicvine.gamespot.com/api/search/';

const POR_FONTE = 18;
const MAX_PAGINA = 100;


// ========================================
// NORMALIZAÇÃO DOS TÍTULOS
// ========================================

// Exemplo:
// "ONE PIECE", "One-Piece" e "One Piece"
// passam a ter o mesmo formato para comparação.

function normalizar(texto) {
  return String(texto || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim();
}


// ========================================
// GÊNEROS EM PORTUGUÊS
// ========================================

const generosPTBR = {
  Action: 'Ação',
  Adventure: 'Aventura',
  Comedy: 'Comédia',
  Drama: 'Drama',
  Fantasy: 'Fantasia',
  Horror: 'Terror',
  Mystery: 'Mistério',
  Romance: 'Romance',
  'Sci-Fi': 'Ficção científica',
  'Slice of Life': 'Cotidiano',
  Sports: 'Esportes',
  Supernatural: 'Sobrenatural',
  Suspense: 'Suspense',
  Historical: 'Histórico',
  Psychological: 'Psicológico',
  School: 'Escolar',
  'Award Winning': 'Premiado'
};


// ========================================
// TENRAI — BUSCAR MANGÁS
// ========================================

async function buscarMangas(fetchApi, busca, pagina) {
  const url = new URL(
    busca
      ? `${TENRAI}/manga`
      : `${TENRAI}/top/manga`
  );

  if (busca) {
    url.searchParams.set('q', busca);
    url.searchParams.set('sfw', 'true');
  }

  url.searchParams.set('page', String(pagina));
  url.searchParams.set('limit', String(POR_FONTE));

  const resposta = await fetchApi(url.toString(), {
    headers: {
      Accept: 'application/json'
    }
  });

  if (!resposta.ok) {
    throw new Error(
      `Tenrai indisponível (HTTP ${resposta.status}).`
    );
  }

  const dados = await resposta.json();

  const registros = Array.isArray(dados.data)
    ? dados.data
    : [];

  const obras = registros
    .filter((item) => item.mal_id && item.title)
    .map((item) => {
      // Guardamos os nomes alternativos para comparar
      // uma obra com registros de outras APIs.

      const titulos = [
        item.title,
        item.title_english,
        ...(item.title_synonyms || [])
      ]
        .filter(Boolean)
        .map(normalizar);

      return {
        id: `manga-${item.mal_id}`,

        titulo: item.title_english || item.title,

        tipo_obra: 'Manga',

        capa_url:
          item.images?.jpg?.large_image_url ||
          item.images?.jpg?.image_url ||
          null,

        editora:
          item.serializations?.[0]?.name || null,

        generos: (item.genres || []).map(
          (genero) =>
            generosPTBR[genero.name] || genero.name
        ),

        api_url:
          item.url ||
          `https://myanimelist.net/manga/${item.mal_id}`,

        origem: 'tenrai',

        // Usado apenas durante a filtragem.
        _titulosComparacao: [...new Set(titulos)]
      };
    });

  return {
    obras,
    proxima: Boolean(dados.pagination?.has_next_page)
  };
}


// ========================================
// COMIC VINE — BUSCAR SÉRIES DE HQS
// ========================================

async function buscarHQs(fetchApi, busca, pagina) {
  const chave = env.COMIC_VINE_API;

  if (!chave) {
    throw new Error(
      'Chave COMIC_VINE_API não configurada.'
    );
  }

  const url = new URL(COMIC_VINE);

  url.searchParams.set('api_key', chave);
  url.searchParams.set('format', 'json');

  url.searchParams.set(
    'query',
    busca || 'Batman'
  );

  // "Volume" na Comic Vine significa uma série.
  url.searchParams.set('resources', 'volume');

  url.searchParams.set(
    'limit',
    String(POR_FONTE)
  );

  url.searchParams.set(
    'offset',
    String((pagina - 1) * POR_FONTE)
  );

  // O ano ajuda a diferenciar séries com
  // o mesmo nome, mas publicadas em épocas diferentes.

  url.searchParams.set(
    'field_list',
    'id,name,image,publisher,site_detail_url,start_year'
  );

  const resposta = await fetchApi(url.toString(), {
    headers: {
      Accept: 'application/json',
      'User-Agent': 'EstanteGeek/1.0'
    }
  });

  if (!resposta.ok) {
    throw new Error(
      `Comic Vine indisponível (HTTP ${resposta.status}).`
    );
  }

  const dados = await resposta.json();

  if (dados.status_code !== 1) {
    throw new Error(
      `Comic Vine: ${dados.error || 'Erro na consulta.'}`
    );
  }

  const registros = Array.isArray(dados.results)
    ? dados.results
    : [];

  const obras = registros
    .filter((item) => item.id && item.name)
    .map((item) => ({
      id: `hq-${item.id}`,

      titulo: item.name,

      tipo_obra: 'HQ',

      capa_url:
        item.image?.medium_url ||
        item.image?.original_url ||
        null,

      editora: item.publisher?.name || null,

      generos: [],

      api_url:
        item.site_detail_url ||
        `https://comicvine.gamespot.com/volume/4050-${item.id}/`,

      origem: 'comicvine',

      ano_inicio: item.start_year || null
    }));

  const total = Number(
    dados.number_of_total_results
  );

  return {
    obras,

    proxima:
      Number.isFinite(total) && total >= 0
        ? pagina * POR_FONTE < total
        : registros.length === POR_FONTE
  };
}


// ========================================
// REMOVER REGISTROS IDÊNTICOS
// ========================================

// Mesmo ID da mesma API = mesmo registro.
//
// Títulos iguais com IDs diferentes não são
// apagados automaticamente nesta etapa.

function removerMesmoRegistro(lista) {
  const identificadores = new Set();

  return lista.filter((obra) => {
    if (identificadores.has(obra.id)) {
      return false;
    }

    identificadores.add(obra.id);
    return true;
  });
}


// ========================================
// IDENTIFICAR HQS REPETIDAS
// ========================================

// Compara título e ano de início.
//
// Batman (1940) e Batman (2011) são preservados
// como séries diferentes.
//
// Se o ano não estiver disponível, usamos também
// a editora, de forma mais conservadora.

function hqsParecidas(a, b) {
  if (a.id === b.id) {
    return true;
  }

  if (
    normalizar(a.titulo) !==
    normalizar(b.titulo)
  ) {
    return false;
  }

  const anoA = String(a.ano_inicio || '');
  const anoB = String(b.ano_inicio || '');

  // Mesmo título e mesmo ano conhecido.
  if (anoA && anoB) {
    return anoA === anoB;
  }

  // Ambos sem ano e com a mesma editora.
  if (!anoA && !anoB) {
    const editoraA = normalizar(a.editora);
    const editoraB = normalizar(b.editora);

    return Boolean(
      editoraA &&
      editoraB &&
      editoraA === editoraB
    );
  }

  // Informação insuficiente para afirmar
  // que são a mesma série.
  return false;
}

function removerHqsRepetidas(hqs) {
  const resultado = [];

  for (const hq of hqs) {
    const duplicada = resultado.some(
      (existente) => hqsParecidas(existente, hq)
    );

    if (!duplicada) {
      resultado.push(hq);
    }
  }

  return resultado;
}


// ========================================
// REMOVER DUPLICATAS ENTRE AS DUAS APIS
// ========================================

// Exemplo:
// Tenrai retorna "Naruto" como mangá.
// Comic Vine retorna "Naruto" como HQ.
//
// Como o título corresponde ao mangá da Tenrai,
// priorizamos a Tenrai.
//
// Não eliminamos títulos derivados:
// "Naruto Gaiden" é diferente de "Naruto".

function removerRepeticoesEntreApis(mangas, hqs) {
  const titulosDosMangas = new Set();

  for (const manga of mangas) {
    for (const titulo of manga._titulosComparacao || []) {
      if (titulo) {
        titulosDosMangas.add(titulo);
      }
    }

    titulosDosMangas.add(
      normalizar(manga.titulo)
    );
  }

  return hqs.filter((hq) => {
    const tituloHQ = normalizar(hq.titulo);

    // Se não corresponde a nenhum mangá,
    // mantemos a série da Comic Vine.
    return !titulosDosMangas.has(tituloHQ);
  });
}


// ========================================
// INTERCALAR MANGÁS E HQS
// ========================================

function intercalar(mangas, hqs) {
  const resultado = [];

  const quantidade = Math.max(
    mangas.length,
    hqs.length
  );

  for (let i = 0; i < quantidade; i++) {
    if (mangas[i]) {
      resultado.push(mangas[i]);
    }

    if (hqs[i]) {
      resultado.push(hqs[i]);
    }
  }

  return resultado;
}


// ========================================
// ORGANIZAR RESULTADOS DO CATÁLOGO
// ========================================

function organizarObras(mangas, hqs) {
  // Primeira etapa: remover IDs repetidos.

  const mangasUnicos = removerMesmoRegistro(mangas);
  const hqsUnicas = removerMesmoRegistro(hqs);

  // Segunda etapa: evitar HQs repetidas
  // da mesma série e mesmo ano.

  const hqsSemRepeticao = removerHqsRepetidas(
    hqsUnicas
  );

  // Terceira etapa: evitar que um mangá
  // apareça outra vez como HQ.

  const hqsFinais = removerRepeticoesEntreApis(
    mangasUnicos,
    hqsSemRepeticao
  );

  // Quarta etapa: misturar mangás e HQs.

  const resultado = intercalar(
    mangasUnicos,
    hqsFinais
  );

  // Retirar os campos internos utilizados
  // apenas para comparar as obras.

  return resultado.map((obra) => {
    const {
      _titulosComparacao,
      ...dadosPublicos
    } = obra;

    return dadosPublicos;
  });
}


// ========================================
// ROTA PÚBLICA DO CATÁLOGO
// ========================================

export async function GET({ url, fetch }) {
  const busca = (
    url.searchParams.get('busca') || ''
  )
    .trim()
    .slice(0, 100);

  const tipoSolicitado =
    url.searchParams.get('tipo') || '';

  const tipo = ['Manga', 'HQ'].includes(tipoSolicitado)
    ? tipoSolicitado
    : '';

  const paginaSolicitada = Number.parseInt(
    url.searchParams.get('pagina') || '1',
    10
  );

  const pagina = Math.min(
    MAX_PAGINA,
    Math.max(
      1,
      Number.isFinite(paginaSolicitada)
        ? paginaSolicitada
        : 1
    )
  );

  const consultas = [];

  if (tipo !== 'HQ') {
    consultas.push({
      fonte: 'mangas',
      promessa: buscarMangas(
        fetch,
        busca,
        pagina
      )
    });
  }

  if (tipo !== 'Manga') {
    consultas.push({
      fonte: 'hqs',
      promessa: buscarHQs(
        fetch,
        busca,
        pagina
      )
    });
  }

  const respostas = await Promise.allSettled(
    consultas.map((consulta) => consulta.promessa)
  );

  const listas = {
    mangas: [],
    hqs: []
  };

  const avisos = [];

  let temProxima = false;

  respostas.forEach((resposta, indice) => {
    if (resposta.status === 'fulfilled') {
      const fonte = consultas[indice].fonte;

      listas[fonte] = resposta.value.obras;

      if (resposta.value.proxima) {
        temProxima = true;
      }
    } else {
      avisos.push(
        resposta.reason?.message ||
        'Uma das APIs está indisponível.'
      );
    }
  });

  // Filtragem aplicada a qualquer pesquisa,
  // sem nomes de obras definidos no código.

  const obras = organizarObras(
    listas.mangas,
    listas.hqs
  );

  return json(
    {
      obras,
      avisos,
      pagina,
      temProxima:
        pagina < MAX_PAGINA && temProxima,
      porPagina: POR_FONTE
    },
    {
      headers: {
        'Cache-Control': 'no-store'
      }
    }
  );
}
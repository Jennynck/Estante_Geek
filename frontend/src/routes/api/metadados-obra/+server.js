import { json } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

// Consulta informações da obra completa nas APIs externas.
// Tenrai: quantidade de volumes do mangá.
// Comic Vine: quantidade de edições da série de HQs.
//
// Nenhum registro é alterado no banco de dados.

export async function GET({ url, fetch }) {
  const tipo = url.searchParams.get('tipo');
  const id = url.searchParams.get('id') || '';

  if (
    !['Manga', 'HQ'].includes(tipo) ||
    !/^\d{1,10}$/.test(id) ||
    Number(id) === 0
  ) {
    return json(
      { erro: 'Identificador da obra inválido.' },
      { status: 400 }
    );
  }

  try {
    // MANGÁS - TENRAI

    if (tipo === 'Manga') {
      const base = (
        env.TENRAI_BASE_URL ||
        'https://api.tenrai.org/v1'
      )
        .trim()
        .replace(/^['"]|['"]$/g, '')
        .replace(/\/$/, '');

      const resposta = await fetch(
        `${base}/manga/${id}`,
        {
          headers: {
            Accept: 'application/json'
          }
        }
      );

      if (!resposta.ok) {
        throw new Error(
          `Tenrai retornou HTTP ${resposta.status}`
        );
      }

      const dados = await resposta.json();
      const manga = dados.data;

      if (!manga) {
        return json(
          { erro: 'Mangá não encontrado.' },
          { status: 404 }
        );
      }

      const total = Number(manga.volumes);

      const quantidade =
        Number.isInteger(total) && total > 0
          ? total
          : null;

      return json(
        {
          titulo: manga.title_english || manga.title,
          tipo: 'Manga',
          quantidade,
          unidade: 'volumes',
          emPublicacao: manga.publishing === true,

          observacao:
            manga.publishing === true &&
            quantidade === null
              ? 'Mangá em publicação. A Tenrai não informou a quantidade de volumes.'
              : null
        },
        {
          headers: {
            'Cache-Control': 'public, max-age=300'
          }
        }
      );
    }

    // HQS - COMIC VINE
    //
    // Na Comic Vine, o recurso "volume" representa
    // uma série de HQs.
    // count_of_issues informa o número de edições.

    const chave = env.COMIC_VINE_API;

    if (!chave) {
      return json(
        {
          erro: 'COMIC_VINE_API não configurada no frontend.'
        },
        { status: 503 }
      );
    }

    const destino = new URL(
      `https://comicvine.gamespot.com/api/volume/4050-${id}/`
    );

    destino.searchParams.set('api_key', chave);
    destino.searchParams.set('format', 'json');

    destino.searchParams.set(
      'field_list',
      'id,name,count_of_issues'
    );

    const resposta = await fetch(
      destino.toString(),
      {
        headers: {
          Accept: 'application/json',
          'User-Agent': 'EstanteGeek/1.0'
        }
      }
    );

    if (!resposta.ok) {
      throw new Error(
        `Comic Vine retornou HTTP ${resposta.status}`
      );
    }

    const dados = await resposta.json();

    if (
      dados.status_code !== 1 ||
      !dados.results
    ) {
      return json(
        { erro: 'Série de HQ não encontrada.' },
        { status: 404 }
      );
    }

    const total = Number(
      dados.results.count_of_issues
    );

    return json(
      {
        titulo: dados.results.name,
        tipo: 'HQ',

        quantidade:
          Number.isInteger(total) && total > 0
            ? total
            : null,

        unidade: 'edições',

        observacao:
          'A quantidade representa as edições da série, não volumes encadernados.'
      },
      {
        headers: {
          'Cache-Control': 'public, max-age=300'
        }
      }
    );

  } catch (erro) {
    console.error(
      'Erro ao consultar os metadados:',
      erro.message
    );

    return json(
      {
        erro: 'Não foi possível consultar a quantidade na API externa.'
      },
      { status: 502 }
    );
  }
}
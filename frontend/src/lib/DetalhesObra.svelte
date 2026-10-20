<script>
  import { onMount } from 'svelte';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let { id } = $props();

  let obra = $state(null);
  let naEstante = $state(false);
  let statusLeitura = $state(null);

  let erro = $state('');
  let aviso = $state('');

  let carregando = $state(true);
  let processando = $state(false);
  let autenticado = $state(false);

  let sinopseTraduzida = $state('');
  let traduzindo = $state(false);
  let erroTraducao = $state(false);

  let quantidadeExterna = $state(null);
  let carregandoQuantidade = $state(false);
  let observacaoQuantidade = $state('');

  // ========================================
  // TRADUÇÃO DOS GÊNEROS
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

  function generoPTBR(nome) {
    return generosPTBR[nome] || nome;
  }

  // ========================================
  // CORES DO STATUS DE LEITURA
  // ========================================

  function corStatus(status) {
    const cores = {
      'Quero Ler': '#ffda0d',
      'Lendo': '#08bdf0',
      'Lido': '#b3e8c0',
      'Pausado': '#dac4ff'
    };

    return cores[status] || '#08bdf0';
  }

  // ========================================
  // TRADUÇÃO DA SINOPSE
  // ========================================

  async function traduzirSinopse(texto) {
    sinopseTraduzida = '';
    erroTraducao = false;

    if (!texto) return;

    traduzindo = true;

    try {
      const resposta = await fetch('/api/traduzir', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          texto: texto.slice(0, 4500)
        })
      });

      if (!resposta.ok) {
        throw new Error('Tradução indisponível.');
      }

      const dados = await resposta.json();

      sinopseTraduzida = dados.traducao || '';

    } catch {
      erroTraducao = true;

    } finally {
      traduzindo = false;
    }
  }

  // ========================================
  // IDENTIFICAR A OBRA NA API EXTERNA
  // ========================================

  function identificarObraExterna(obraAtual) {
    const endereco = String(
      obraAtual?.api_url || ''
    );

    if (obraAtual?.tipo_obra === 'HQ') {
      const encontrado = endereco.match(
        /4050-(\d+)/
      );

      return encontrado ? encontrado[1] : null;
    }

    const encontrado = endereco.match(
      /(?:myanimelist\.net|tenrai\.org)\/manga\/(\d+)/i
    );

    return encontrado ? encontrado[1] : null;
  }

  // ========================================
  // QUANTIDADE DE VOLUMES OU EDIÇÕES
  // ========================================

  let etiquetaQuantidade = $derived(
    obra?.tipo_obra === 'HQ'
      ? 'Edições'
      : 'Volumes'
  );

  let quantidadeExibida = $derived(
    quantidadeExterna?.quantidade ??
    (
      Number(obra?.total_volumes) > 0
        ? Number(obra.total_volumes)
        : null
    )
  );

  let anoPublicacao = $derived(
    obra?.data_publicacao
      ? new Date(
          obra.data_publicacao
        ).getFullYear()
      : null
  );

  let nota = $derived(
    typeof obra?.media_notas === 'number'
      ? obra.media_notas
      : null
  );

  async function consultarQuantidade(obraAtual) {
    quantidadeExterna = null;
    observacaoQuantidade = '';

    const idExterno = identificarObraExterna(
      obraAtual
    );

    if (!idExterno) return;

    carregandoQuantidade = true;

    try {
      const parametros = new URLSearchParams({
        tipo: obraAtual.tipo_obra,
        id: idExterno
      });

      const resposta = await fetch(
        `/api/metadados-obra?${parametros}`
      );

      if (!resposta.ok) {
        throw new Error('Consulta indisponível.');
      }

      quantidadeExterna = await resposta.json();

      observacaoQuantidade =
        quantidadeExterna.observacao || '';

    } catch {
      observacaoQuantidade =
        'Não foi possível atualizar a quantidade pela API externa.';

    } finally {
      carregandoQuantidade = false;
    }
  }

  // ========================================
  // CONSULTAR A MINHA ESTANTE
  // ========================================

  // Esta função verifica se a obra está na
  // estante e qual etiqueta foi selecionada.
  //
  // Não consulta o checklist.

  async function verificarEstante() {
    const itens = await requisicao('/estante');

    const registro = Array.isArray(itens)
      ? itens.find(
          (item) =>
            Number(item.obra?.id) === Number(obra?.id)
        )
      : null;

    naEstante = Boolean(registro);

    // O status vem do PostgreSQL,
    // pela API do backend.
    statusLeitura = registro?.status || null;
  }

  // ========================================
  // CARREGAR OS DETALHES
  // ========================================

  async function carregar() {
    erro = '';
    aviso = '';

    carregando = true;

    autenticado = Boolean(obterToken());

    obra = null;
    naEstante = false;
    statusLeitura = null;

    sinopseTraduzida = '';
    erroTraducao = false;

    quantidadeExterna = null;
    observacaoQuantidade = '';

    if (!autenticado) {
      carregando = false;
      return;
    }

    try {
      obra = await requisicao(
        `/obras/${encodeURIComponent(id)}`
      );

      // Essas consultas são independentes.

      void traduzirSinopse(obra.sinopse);
      void consultarQuantidade(obra);

      // Verificar se está na estante
      // e recuperar o status de leitura.

      try {
        await verificarEstante();

      } catch (falha) {
        console.warn(
          'Não foi possível consultar a estante:',
          falha.message
        );
      }

    } catch (falha) {
      erro = falha.message;

    } finally {
      carregando = false;
    }
  }

  // ========================================
  // ADICIONAR À MINHA ESTANTE
  // ========================================

  async function adicionar() {
    if (
      !obra ||
      processando ||
      naEstante
    ) {
      return;
    }

    processando = true;

    erro = '';
    aviso = '';

    try {
      const registro = await requisicao(
        '/estante',
        {
          metodo: 'POST',
          dados: {
            obras_id: obra.id
          }
        }
      );

      // O botão muda após a confirmação.
      naEstante = true;

      // O backend normalmente inicia
      // o status como Quero Ler.
      statusLeitura =
        registro?.status || 'Quero Ler';

      // Confirma o status salvo no banco.
      try {
        await verificarEstante();
      } catch {
        // A inclusão já foi confirmada.
        // Mantemos o botão como adicionado.
      }

      aviso =
        'Obra adicionada à sua estante!';

    } catch (falha) {
      if (
        falha.message.toLowerCase().includes('já está')
      ) {
        try {
          await verificarEstante();
        } catch {
          erro =
            'A obra já está na estante, mas não foi possível consultar seu status.';
        }

      } else {
        erro = falha.message;
      }

    } finally {
      processando = false;
    }
  }

  onMount(carregar);
</script>

<Cabecalho />

<main class="detalhes-pagina">

  <!-- Navegação -->

  <div class="trilha-navegacao">

    <a href="/catalogo">
      ← CATÁLOGO
    </a>

    {#if obra}
      <span>/ {obra.titulo}</span>
    {/if}

  </div>

  {#if carregando}

    <div class="estado-detalhes" role="status">
      CARREGANDO INFORMAÇÕES DA OBRA...
    </div>

  {:else if !autenticado}

    <div class="estado-detalhes">

      <h1>DESCUBRA OS DETALHES!</h1>

      <p>
        Faça login para consultar os detalhes
        das obras e organizar sua estante.
      </p>

      <a
        class="botao-comic azul"
        href="/login"
      >
        FAZER LOGIN
      </a>

    </div>

  {:else if !obra}

    <div class="estado-detalhes" role="alert">

      <h1>OBRA NÃO ENCONTRADA</h1>

      <p>
        {erro ||
          'Não foi possível carregar esta obra.'}
      </p>

      <a
        class="botao-comic azul"
        href="/catalogo"
      >
        VOLTAR AO CATÁLOGO
      </a>

    </div>

  {:else}

    <!-- INFORMAÇÕES PRINCIPAIS -->

    <section
      class="ficha-obra"
      aria-labelledby="nome-obra"
    >

      <!-- CAPA E BOTÃO -->

      <div class="coluna-capa">

        <div class="moldura-capa">

          {#if obra.capa_url}

            <img
              src={obra.capa_url}
              alt={`Capa de ${obra.titulo}`}
            />

          {:else}

            <div class="sem-capa">
              CAPA INDISPONÍVEL
            </div>

          {/if}

        </div>

        <!-- BOTÃO ADICIONADO À ESTANTE -->

        {#if naEstante}

          <span
            class="botao-comic adicionado"
            role="status"
          >
            ✓ ADICIONADO À ESTANTE
          </span>

        {:else}

          <button
            class="botao-comic rosa"
            type="button"
            disabled={processando}
            onclick={adicionar}
          >

            {processando
              ? 'ADICIONANDO...'
              : '✦ ADICIONAR À MINHA ESTANTE'}

          </button>

          <span class="indicacao-estante">
            GUARDE SUAS OBRAS FAVORITAS
          </span>

        {/if}

      </div>

      <!-- DADOS DA OBRA -->

      <div class="informacoes-obra">

        <p class="linha-categoria">

          ✦ {obra.tipo_obra === 'HQ'
            ? 'HQ'
            : 'MANGÁ'}

          {obra.editora
            ? `· ${obra.editora.toUpperCase()}`
            : ''}

          {anoPublicacao
            ? `· ${anoPublicacao}`
            : ''}

        </p>

        <h1 id="nome-obra">
          {obra.titulo}
        </h1>

        <p class="subinformacao">

          {obra.editora ||
            'Editora não informada'}

          ·

          {#if quantidadeExibida !== null}

            {quantidadeExibida}

            {obra.tipo_obra === 'HQ'
              ? 'edições'
              : quantidadeExibida === 1
                ? 'volume'
                : 'volumes'}

          {:else}

            Quantidade não informada

          {/if}

        </p>

        <!-- GÊNEROS -->

        {#if obra.generos?.length}

          <div
            class="generos"
            aria-label="Gêneros da obra"
          >

            {#each obra.generos as nome, indice (nome)}

              <span
                class:genero-roxo={indice % 4 === 1}
                class:genero-azul={indice % 4 === 2}
                class:genero-amarelo={indice % 4 === 3}
              >
                {generoPTBR(nome)}
              </span>

            {/each}

          </div>

        {/if}

        <!-- AVALIAÇÃO -->

        <div class="avaliacao-obra">

          {#if nota !== null}

            <span
              class="estrelas"
              aria-label={`Nota média ${nota} de 10`}
            >
              {'★'.repeat(Math.round(nota / 2))}
              {'☆'.repeat(
                5 - Math.round(nota / 2)
              )}
            </span>

            <strong>
              {nota.toFixed(1).replace('.', ',')}
            </strong>

            <small>
              / 10 ·
              {obra.total_avaliacoes || 0}
              avaliações
            </small>

          {:else}

            <span class="sem-avaliacoes">
              ☆ AINDA SEM AVALIAÇÕES
            </span>

          {/if}

        </div>

        <!-- ==================================
             INDICADORES DA OBRA
             ================================== -->

        <div class="indicadores">

          <!-- STATUS DE LEITURA -->

          {#if naEstante}

            <div
              class="indicador indicador-status"
              style:background={corStatus(statusLeitura)}
            >

              <strong>
                {statusLeitura || '—'}
              </strong>

              <small>
                Status da leitura
              </small>

            </div>

          {/if}

          <!-- VOLUMES OU EDIÇÕES -->

          <div class="indicador indicador-amarelo">

            <strong>

              {carregandoQuantidade
                ? '…'
                : quantidadeExibida ?? '—'}

            </strong>

            <small>
              {etiquetaQuantidade}
            </small>

          </div>

          <!-- EDITORA -->

          {#if obra.editora}

            <div class="indicador indicador-roxo">

              <strong>
                {obra.editora}
              </strong>

              <small>
                Editora
              </small>

            </div>

          {/if}

        </div>

        <!-- INFORMAÇÃO ADICIONAL -->

        {#if observacaoQuantidade}

          <p class="aviso-quantidade">
            {observacaoQuantidade}
          </p>

        {/if}

        {#if obra.api_url}

          <a
            class="link-origem"
            href={obra.api_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            VER FONTE DA OBRA ↗
          </a>

        {/if}

      </div>

    </section>

    <!-- MENSAGENS -->

    {#if aviso}

      <p
        class="feedback sucesso"
        role="status"
      >
        {aviso}
      </p>

    {/if}

    {#if erro}

      <p
        class="feedback falha"
        role="alert"
      >
        {erro}
      </p>

    {/if}

    <!-- SINOPSE -->

    <section class="painel-informativo">

      <h2>SINOPSE</h2>

      {#if traduzindo}

        <p
          class="traducao-status"
          role="status"
        >
          Traduzindo a sinopse
          para português (Brasil)...
        </p>

      {/if}

      {#if erroTraducao}

        <p class="traducao-status">
          A tradução está indisponível no momento.
          Exibindo o texto original.
        </p>

        <button
          class="tentar-traduzir"
          type="button"
          disabled={traduzindo}
          onclick={() =>
            traduzirSinopse(obra.sinopse)}
        >
          TENTAR TRADUÇÃO NOVAMENTE
        </button>

      {/if}

      <p>
        {sinopseTraduzida ||
          obra.sinopse ||
          'Sinopse indisponível para esta obra.'}
      </p>

    </section>

  {/if}

</main>

<style>
  .detalhes-pagina {
    width: min(100% - 40px, 1020px);
    margin: 28px auto 70px;
  }

  /* NAVEGAÇÃO */

  .trilha-navegacao {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    min-height: 26px;
    margin: 0 0 16px;
    font-size: 12px;
  }

  .trilha-navegacao a {
    font: 17px 'Bangers', Impact, sans-serif;
    border: 2px solid #292033;
    border-radius: 7px;
    padding: 7px 12px;
    box-shadow: 3px 3px #292033;
    background: #fff9f2;
    white-space: nowrap;
  }

  .trilha-navegacao span {
    text-align: right;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #847889;
  }

  /* PAINÉIS */

  .ficha-obra,
  .painel-informativo,
  .estado-detalhes {
    border: 3px solid #292033;
    border-radius: 12px;
    box-shadow: 6px 6px 0 #292033;
    background: #fff9f2;
  }

  .ficha-obra {
    display: grid;
    grid-template-columns: 185px minmax(0, 1fr);
    gap: 28px;
    padding: 22px;
  }

  /* CAPA */

  .coluna-capa {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    min-width: 0;
  }

  .moldura-capa {
    width: 100%;
    height: 266px;
    border-radius: 8px;
    border: 3px solid #292033;
    background: #30273b;
    overflow: hidden;
    box-shadow: 4px 5px 0 #292033;
  }

  .moldura-capa img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .sem-capa {
    height: 100%;
    display: grid;
    place-items: center;
    padding: 15px;
    color: white;
    text-align: center;
    font: 22px 'Bangers', Impact, sans-serif;
  }

  /* BOTÕES */

  .botao-comic {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    min-height: 42px;
    padding: 9px 10px;
    border: 3px solid #292033;
    border-radius: 8px;
    box-shadow: 4px 5px 0 #292033;
    font: 17px 'Bangers', Impact, sans-serif;
    cursor: pointer;
    text-decoration: none;
  }

  .botao-comic:disabled {
    opacity: .55;
    cursor: wait;
  }

  .botao-comic.rosa {
    color: white;
    background: #ff456f;
  }

  .botao-comic.azul {
    background: #02bffc;
  }

  .botao-comic.adicionado {
    background: #ffda0d;
    color: #292033;
    cursor: default;
  }

  .indicacao-estante {
    color: #837489;
    font-size: 10px;
    font-weight: 800;
    text-align: center;
  }

  /* INFORMAÇÕES */

  .informacoes-obra {
    min-width: 0;
    padding-top: 1px;
  }

  .linha-categoria {
    color: #ff456b;
    font: 14px 'Bangers', Impact, sans-serif;
    letter-spacing: 1px;
    margin-bottom: 3px;
  }

  h1,
  h2,
  .generos span,
  .indicador strong,
  .sem-avaliacoes {
    font-family: 'Bangers', Impact, sans-serif;
  }

  .informacoes-obra h1 {
    color: #823df0;
    font-size: clamp(36px, 5vw, 55px);
    line-height: 1;
    text-shadow: 4px 4px #ddc9eb;
    margin: 8px 0 6px;
    overflow-wrap: anywhere;
  }

  .subinformacao {
    color: #958a9b;
    font-size: 12px;
    margin: 0;
  }

  /* GÊNEROS */

  .generos {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 16px 0;
  }

  .generos span {
    padding: 5px 11px;
    background: #ff436e;
    color: white;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 2px 3px #292033;
    font-size: 15px;
  }

  .generos .genero-roxo {
    background: #803df0;
  }

  .generos .genero-azul {
    background: #00baf2;
    color: #21172c;
  }

  .generos .genero-amarelo {
    background: #ffda0d;
    color: #21172c;
  }

  /* AVALIAÇÃO */

  .avaliacao-obra {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 8px;
    margin: 18px 0 20px;
  }

  .estrelas {
    color: #ffbf00;
    font-size: 20px;
  }

  .avaliacao-obra strong {
    color: #f2b600;
    font-size: 22px;
  }

  .avaliacao-obra small {
    color: #94879b;
    font-size: 11px;
  }

  .sem-avaliacoes {
    color: #918495;
    font-size: 17px;
  }

  /* INDICADORES */

  .indicadores {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .indicador {
    min-width: 90px;
    min-height: 48px;
    max-width: 210px;

    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    padding: 5px 13px;

    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 4px #292033;

    text-align: center;
  }

  /* A cor do status vem da função corStatus() */

  .indicador-status {
    color: #292033;
  }

  .indicador strong {
    font-size: 20px;
    line-height: 1.1;
    overflow-wrap: anywhere;
  }

  .indicador small {
    font-size: 11px;
  }

  .indicador-amarelo {
    background: #ffdc08;
  }

  .indicador-roxo {
    background: #813cf0;
    color: white;
  }

  .aviso-quantidade {
    color: #75647d;
    font-size: 12px;
    margin-top: 12px;
    line-height: 1.4;
  }

  .link-origem {
    display: inline-block;
    font-size: 12px;
    margin-top: 24px;
    text-decoration: underline;
  }

  /* SINOPSE */

  .painel-informativo {
    padding: 20px 22px;
    margin-top: 28px;
  }

  .painel-informativo h2 {
    display: inline-block;
    padding: 6px 14px;
    background: #292033;
    border-radius: 6px;
    color: white;
    font-size: 23px;
    margin: 0 0 12px;
  }

  .painel-informativo p {
    line-height: 1.7;
    font-size: 14px;
    white-space: pre-line;
    overflow-wrap: anywhere;
    margin: 0 0 12px;
  }

  .traducao-status {
    font-size: 12px !important;
    color: #7b6487;
    font-style: italic;
  }

  .tentar-traduzir {
    padding: 8px 11px;
    background: #ffdc08;
    border: 2px solid #292033;
    border-radius: 7px;
    cursor: pointer;
    font: 16px 'Bangers', Impact, sans-serif;
    margin-bottom: 12px;
  }

  /* AVISOS */

  .feedback {
    margin: 25px 0 -10px;
    border: 2px solid;
    border-radius: 8px;
    padding: 12px 15px;
  }

  .feedback.sucesso {
    background: #e8ffee;
    border-color: #3ba361;
  }

  .feedback.falha {
    background: #ffe4e9;
    border-color: #fb4269;
  }

  /* TELA DE ESTADO */

  .estado-detalhes {
    padding: 40px 28px;
    text-align: center;
  }

  .estado-detalhes h1 {
    color: #823cf2;
    font-size: 35px;
  }

  .estado-detalhes p {
    margin: 15px auto 26px;
    max-width: 500px;
  }

  /* RESPONSIVIDADE */

  @media (max-width: 680px) {
    .detalhes-pagina {
      width: calc(100% - 28px);
    }

    .ficha-obra {
      grid-template-columns: 1fr;
      gap: 20px;
      padding: 17px;
    }

    .coluna-capa {
      max-width: 230px;
      width: 100%;
      margin: 0 auto;
    }

    .moldura-capa {
      height: 325px;
    }

    .informacoes-obra h1 {
      font-size: 41px;
    }

    .trilha-navegacao span {
      display: none;
    }
  }
</style>
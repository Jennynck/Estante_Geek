
<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let obras = $state([]);
  let estaLogado = $state(false);
  let busca = $state('');
  let pesquisaAtual = $state('');
  let tipo = $state('');
  let editora = $state('');
  let genero = $state('');
  let filtrosAbertos = $state(false);

  let carregando = $state(true);
  let executando = $state(null);
  let erro = $state('');
  let avisos = $state([]);
  let mensagem = $state('');
  let adicionadas = $state([]);

  let pagina = $state(1);
  let temProxima = $state(false);

  let abortController = null;
  let temporizadorMensagem;

  let editoras = $derived(
    [...new Set(
      obras.map((obra) => obra.editora).filter(Boolean)
    )].sort()
  );

  let generos = $derived(
    [...new Set(
      obras.flatMap((obra) => obra.generos || [])
    )].sort()
  );

  let obrasFiltradas = $derived(
    obras.filter((obra) =>
      (!editora || obra.editora === editora) &&
      (!genero || (obra.generos || []).includes(genero))
    )
  );

  function notificar(texto) {
    clearTimeout(temporizadorMensagem);

    mensagem = texto;

    temporizadorMensagem = setTimeout(() => {
      mensagem = '';
    }, 4500);
  }

  async function carregar(novaPagina = 1) {
    if (abortController) {
      abortController.abort();
    }

    abortController = new AbortController();
    const controller = abortController;

    carregando = true;
    erro = '';
    avisos = [];
    mensagem = '';

    try {
      const parametros = new URLSearchParams({
        busca: busca.trim(),
        tipo,
        pagina: String(novaPagina)
      });

      const resposta = await fetch(
        `/api/catalogo?${parametros}`,
        { signal: controller.signal }
      );

      if (!resposta.ok) {
        throw new Error(
          'Não foi possível carregar o catálogo.'
        );
      }

      const dados = await resposta.json();

      obras = dados.obras || [];
      pagina = dados.pagina || novaPagina;
      temProxima = Boolean(dados.temProxima);
      avisos = dados.avisos || [];
      pesquisaAtual = busca.trim();

      editora = '';
      genero = '';

      if (!obras.length && avisos.length) {
        erro = 'Não foi possível carregar as obras. Tente novamente.';
      }
    } catch (falha) {
      if (falha.name === 'AbortError') return;

      erro = falha.message;
      obras = [];
      temProxima = false;
    } finally {
      if (abortController === controller) {
        carregando = false;
      }
    }
  }

  function buscar(evento) {
    evento.preventDefault();
    void carregar(1);
  }

  function mudarTipo(novoTipo) {
    tipo = novoTipo;
    void carregar(1);
  }

  function trocarPagina(novaPagina) {
    if (
      carregando ||
      novaPagina < 1 ||
      (novaPagina > pagina && !temProxima)
    ) {
      return;
    }

    void carregar(novaPagina);

    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }

  function chaveDaObra(obra) {
    const origem = String(obra?.api_url || '')
      .toLowerCase()
      .replace(/\/+$/, '');

    const manga = origem.match(
      /(?:myanimelist\.net|tenrai\.org)\/manga\/(\d+)/
    );

    const hq = origem.match(/4050-(\d+)/);

    if (obra?.tipo_obra === 'Manga' && manga) {
      return `manga:${manga[1]}`;
    }

    if (obra?.tipo_obra === 'HQ' && hq) {
      return `hq:${hq[1]}`;
    }

    return `${obra?.tipo_obra}:${origem}`;
  }

  function estaAdicionada(obra) {
    return adicionadas.includes(chaveDaObra(obra));
  }

  async function carregarEstante() {
    estaLogado = Boolean(obterToken());

    if (!estaLogado) {
      adicionadas = [];
      return;
    }

    try {
      const itens = await requisicao('/estante');

      adicionadas = (Array.isArray(itens) ? itens : [])
        .filter((item) => item.obra)
        .map((item) => chaveDaObra(item.obra));
    } catch (falha) {
      console.warn(
        'Não foi possível carregar a estante:',
        falha.message
      );
    }
  }

  function textoComparavel(valor) {
    return String(valor || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }

  async function encontrarNoBackend(obra) {
    const caminho =
      `/obras?busca=${encodeURIComponent(obra.titulo)}` +
      `&tipo_obra=${encodeURIComponent(obra.tipo_obra)}`;

    const resultados = await requisicao(caminho);

    if (!Array.isArray(resultados)) {
      throw new Error(
        'O backend retornou dados inesperados.'
      );
    }

    const urlExterna = String(obra.api_url || '')
      .replace(/\/+$/, '');

    const encontrada =
      resultados.find((item) =>
        item.api_url &&
        String(item.api_url).replace(/\/+$/, '') === urlExterna
      ) ||
      resultados.find((item) =>
        textoComparavel(item.titulo) ===
        textoComparavel(obra.titulo)
      );

    if (!encontrada) {
      throw new Error(
        'Esta obra não foi localizada no banco. Tente outra obra.'
      );
    }

    return encontrada.id;
  }

  async function abrirDetalhes(obra) {
    if (!obterToken()) {
      await goto('/login');
      return;
    }

    if (executando !== null) return;

    executando = obra.id;
    erro = '';

    try {
      const idBanco = await encontrarNoBackend(obra);

      await goto(`/obra/${idBanco}`);
    } catch (falha) {
      erro = falha.message;
    } finally {
      executando = null;
    }
  }

  async function adicionar(obra) {
    if (!obterToken()) {
      await goto('/login');
      return;
    }

    if (
      executando !== null ||
      estaAdicionada(obra)
    ) {
      return;
    }

    executando = obra.id;
    erro = '';
    mensagem = '';

    try {
      const idBanco = await encontrarNoBackend(obra);

      await requisicao('/estante', {
        metodo: 'POST',
        dados: {
          obras_id: idBanco
        }
      });

      adicionadas = [
        ...new Set([
          ...adicionadas,
          chaveDaObra(obra)
        ])
      ];

      notificar(
        `“${obra.titulo}” foi adicionada à sua estante!`
      );
    } catch (falha) {
      if (
        falha.message.toLowerCase().includes('já está')
      ) {
        adicionadas = [
          ...new Set([
            ...adicionadas,
            chaveDaObra(obra)
          ])
        ];

        notificar('Essa obra já está na sua estante.');
      } else {
        erro = falha.message;
      }
    } finally {
      executando = null;
    }
  }

  onMount(() => {
    estaLogado = Boolean(obterToken());

    void carregar(1);
    void carregarEstante();

    return () => {
      abortController?.abort();
      clearTimeout(temporizadorMensagem);
    };
  });
</script>

<Cabecalho />

<main class="catalogo">
  <h1>CATÁLOGO &amp; BUSCA</h1>

  <div class="area-pesquisa">
    <form class="barra-busca" onsubmit={buscar}>
      <label class="oculto" for="catalogo-busca">
        Pesquisar mangás e HQs
      </label>

      <input
        id="catalogo-busca"
        bind:value={busca}
        placeholder="Pesquisar mangás e HQs..."
        maxlength="100"
      />

      <button
        class="botao-filtro"
        class:aberto={filtrosAbertos}
        type="button"
        aria-label={filtrosAbertos
          ? 'Ocultar filtros'
          : 'Mostrar filtros'}
        aria-expanded={filtrosAbertos}
        onclick={() => filtrosAbertos = !filtrosAbertos}
        title={filtrosAbertos
          ? 'Ocultar filtros'
          : 'Mostrar filtros'}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          width="23"
          height="23"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M4 5h16l-6.5 7.5V19l-3-1.6v-4.9L4 5Z" />
        </svg>
      </button>

      <button
        class="botao-buscar"
        type="submit"
        disabled={carregando}
      >
        {carregando ? 'CARREGANDO...' : '⌕ BUSCAR'}
      </button>
    </form>

    {#if filtrosAbertos}
      <div class="painel-filtros" id="filtros-catalogo">
        <strong>FILTRAR POR:</strong>

        <label>
          EDITORA

          <select
            bind:value={editora}
            disabled={!editoras.length}
          >
            <option value="">TODAS</option>

            {#each editoras as nome (nome)}
              <option value={nome}>
                {nome}
              </option>
            {/each}
          </select>
        </label>

        <label>
          GÊNERO

          <select
            bind:value={genero}
            disabled={!generos.length}
          >
            <option value="">TODOS</option>

            {#each generos as nome (nome)}
              <option value={nome}>
                {nome}
              </option>
            {/each}
          </select>
        </label>

        <button
          type="button"
          class="limpar-filtros"
          disabled={!editora && !genero}
          onclick={() => {
            editora = '';
            genero = '';
          }}
        >
          LIMPAR FILTROS
        </button>
      </div>
    {/if}
  </div>

  <div class="abas-tipo">
    <button
      type="button"
      class:ativa={tipo === ''}
      onclick={() => mudarTipo('')}
    >
      TODOS
    </button>

    <button
      type="button"
      class:ativa={tipo === 'Manga'}
      onclick={() => mudarTipo('Manga')}
    >
      MANGÁS
    </button>

    <button
      type="button"
      class:ativa={tipo === 'HQ'}
      onclick={() => mudarTipo('HQ')}
    >
      HQS
    </button>
  </div>

  <div class="titulo-secao">
    <h2>
      ✦ {pesquisaAtual
        ? `RESULTADOS PARA “${pesquisaAtual}”`
        : estaLogado
          ? 'SUGESTÕES PARA VOCÊ'
          : 'EXPLORE MANGÁS E HQS'}
    </h2>

    {#if estaLogado}
      <p>
        Descubra novas obras para adicionar à sua estante.
      </p>
    {:else}
      <p>
        Explore mangás e HQs sem precisar fazer login.
        Até 36 títulos por página.
      </p>
    {/if}
  </div>

  {#if mensagem}
    <p class="aviso positivo" role="status">
      {mensagem}
    </p>
  {/if}

  {#if erro}
    <p class="aviso negativo" role="alert">
      {erro}
    </p>
  {/if}

  {#each avisos as aviso}
    <p class="aviso" role="status">
      {aviso}
    </p>
  {/each}

  {#if carregando}
    <p class="estado">
      Carregando mangás e HQs...
    </p>

  {:else if obrasFiltradas.length === 0}
    <p class="estado">
      Nenhuma obra encontrada nesta página.
      Experimente outra busca ou categoria.
    </p>

  {:else}
    <section
      class="grade"
      aria-label="Obras do catálogo"
    >
      {#each obrasFiltradas as obra (obra.id)}
        <article class="card">
          <button
            class="capa"
            type="button"
            onclick={() => abrirDetalhes(obra)}
            aria-label={`Ver detalhes de ${obra.titulo}`}
          >
            {#if obra.capa_url}
              <img
                src={obra.capa_url}
                alt={`Capa de ${obra.titulo}`}
                loading="lazy"
              />
            {:else}
              <span class="sem-capa">
                CAPA INDISPONÍVEL
              </span>
            {/if}

            <span
              class="etiqueta"
              class:hq={obra.tipo_obra === 'HQ'}
            >
              {obra.tipo_obra === 'HQ' ? 'HQ' : 'MANGÁ'}
            </span>
          </button>

          <div class="informacoes">
            <h3>{obra.titulo}</h3>

            <p>
              {obra.editora || 'Editora não informada'}
            </p>

            <button
              type="button"
              class="adicionar"
              class:adicionada={estaAdicionada(obra)}
              disabled={
                executando === obra.id ||
                estaAdicionada(obra)
              }
              onclick={() => adicionar(obra)}
            >
              {#if estaAdicionada(obra)}
                ✓ ADICIONADO À ESTANTE
              {:else if executando === obra.id}
                AGUARDE...
              {:else}
                ✦ ADICIONAR À ESTANTE
              {/if}
            </button>

            <button
              class="detalhes"
              type="button"
              disabled={executando === obra.id}
              onclick={() => abrirDetalhes(obra)}
            >
              VER DETALHES →
            </button>
          </div>
        </article>
      {/each}
    </section>
  {/if}

  {#if !carregando && (obras.length > 0 || pagina > 1)}
    <nav
      class="paginacao"
      aria-label="Navegação pelas páginas"
    >
      <button
        type="button"
        disabled={pagina <= 1 || carregando}
        onclick={() => trocarPagina(pagina - 1)}
      >
        ← ANTERIOR
      </button>

      <span>PÁGINA {pagina}</span>

      <button
        type="button"
        disabled={!temProxima || carregando}
        onclick={() => trocarPagina(pagina + 1)}
      >
        PRÓXIMA →
      </button>
    </nav>
  {/if}

  <p class="nota-rodape">
    Detalhes e estante exigem login.
    Mangás: Tenrai. HQs: Comic Vine.
  </p>
</main>

<style>
  .catalogo {
    width: min(100% - 40px, 1220px);
    margin: 34px auto 75px;
  }

  h1, h2, button,
  .painel-filtros strong,
  .painel-filtros label,
  .etiqueta {
    font-family: 'Bangers', Impact, sans-serif;
    letter-spacing: .5px;
  }

  h1 {
    color: #823cf2;
    text-shadow: 4px 4px #d8cae6;
    font-size: clamp(40px, 5vw, 64px);
    line-height: 1.2;
    margin: 0 0 28px;
  }

  .area-pesquisa {
    margin-bottom: 16px;
  }

  .barra-busca {
    display: flex;
    align-items: stretch;
    gap: 12px;
  }

  .barra-busca input {
    min-width: 0;
    flex: 1;
    padding: 14px 18px;
    border: 2px solid #292033;
    border-radius: 8px;
    box-shadow: 4px 4px #292033;
    font-size: 16px;
    background: white;
  }

  .botao-filtro {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 54px;
    border: 2px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    background: #fffdf8;
    color: #292033;
    cursor: pointer;
  }

  .botao-filtro:hover,
  .botao-filtro:focus-visible {
    background: #f3e9ff;
  }

  .botao-filtro.aberto {
    background: #ffda0d;
  }

  .botao-buscar,
  .adicionar {
    border: 2px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    padding: 11px 16px;
    background: #ff416b;
    color: white;
    font-size: 19px;
    cursor: pointer;
  }

  .botao-buscar {
    min-width: 132px;
  }

  .botao-buscar:disabled {
    opacity: .7;
    cursor: wait;
  }

  .painel-filtros {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: 18px;
    margin-top: 17px;
    padding: 17px 20px;
    background: #fff9f3;
    border: 2px solid #292033;
    border-radius: 9px;
    box-shadow: 4px 4px #292033;
  }

  .painel-filtros strong {
    font-size: 21px;
    padding-right: 12px;
    align-self: center;
  }

  .painel-filtros label {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 190px;
    font-size: 16px;
    color: #ff426a;
  }

  .painel-filtros select {
    border: 2px solid #292033;
    border-radius: 6px;
    padding: 8px;
    background: white;
    font-size: 13px;
  }

  .limpar-filtros {
    padding: 9px 12px;
    background: #fffdf8;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 3px #292033;
    font-size: 15px;
    cursor: pointer;
  }

  .abas-tipo {
    display: flex;
    gap: 10px;
    margin: 21px 0 29px;
    flex-wrap: wrap;
  }

  .abas-tipo button {
    padding: 10px 21px;
    background: #fff9f3;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 4px #292033;
    font-size: 20px;
    cursor: pointer;
  }

  .abas-tipo button.ativa {
    background: #ffda0d;
  }

  .titulo-secao {
    border-bottom: 1px solid #d6cbdc;
    margin-bottom: 19px;
    padding-bottom: 9px;
  }

  .titulo-secao h2 {
    margin: 0;
    color: #823cf2;
    font-size: 30px;
    line-height: 1.2;
  }

  .titulo-secao p {
    margin: 6px 0 0;
    color: #8a8093;
    font-size: 13px;
  }

  .grade {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 20px;
  }

  .card {
    min-width: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    border: 3px solid #292033;
    border-radius: 11px;
    background: #fff9f3;
    box-shadow: 5px 5px #292033;
  }

  .capa {
    width: 100%;
    height: 265px;
    position: relative;
    border: 0;
    padding: 0;
    background: #e6deed;
    cursor: pointer;
  }

  .capa img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .sem-capa {
    display: grid;
    place-items: center;
    height: 100%;
    padding: 10px;
  }

  .etiqueta {
    position: absolute;
    right: 9px;
    top: 9px;
    background: #00c1f7;
    border: 2px solid #292033;
    border-radius: 5px;
    padding: 5px 7px;
    box-shadow: 2px 2px #292033;
    font-size: 15px;
  }

  .etiqueta.hq {
    background: #ff426a;
    color: white;
  }

  .informacoes {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 9px;
    flex: 1;
  }

  .informacoes h3 {
    margin: 0;
    font: 21px/1.05 'Bangers', Impact, sans-serif;
    overflow-wrap: anywhere;
  }

  .informacoes p {
    font-size: 12px;
    margin: 0 0 5px;
    color: #8a8093;
  }

  .adicionar {
    margin-top: auto;
    width: 100%;
    padding: 10px 5px;
    font-size: 15px;
  }

  .adicionar.adicionada,
  .adicionar.adicionada:disabled {
    background: #ffda0d;
    color: #292033;
    cursor: default;
    opacity: 1;
  }

  .detalhes {
    background: transparent;
    border: 0;
    color: #823cf2;
    text-decoration: underline;
    text-align: left;
    font-size: 16px;
    cursor: pointer;
    padding: 4px 0;
  }

  .estado {
    background: #fff9f3;
    border: 2px solid #292033;
    border-radius: 8px;
    text-align: center;
    padding: 28px;
  }

  .aviso {
    background: #fff3d7;
    border: 2px solid #d49e39;
    padding: 11px 14px;
    border-radius: 8px;
    margin: 0 0 15px;
  }

  .aviso.positivo {
    background: #e6ffef;
    border-color: #43a369;
  }

  .aviso.negativo {
    background: #ffe2e9;
    border-color: #fa4169;
  }

  .paginacao {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    margin: 31px 0 8px;
  }

  .paginacao button {
    border: 2px solid #292033;
    background: #ffda0d;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    padding: 11px 17px;
    cursor: pointer;
    font: 19px 'Bangers', Impact, sans-serif;
  }

  .paginacao button:disabled {
    opacity: .45;
    cursor: not-allowed;
  }

  .paginacao span {
    font: 20px 'Bangers', Impact, sans-serif;
    color: #823cf2;
    white-space: nowrap;
  }

  .nota-rodape {
    margin: 24px 0;
    font-size: 12px;
    color: #817688;
    text-align: center;
  }

  .oculto {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
  }

  @media (max-width: 900px) {
    .grade {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 660px) {
    .catalogo {
      width: calc(100% - 28px);
    }

    .barra-busca {
      gap: 8px;
      flex-wrap: wrap;
    }

    .barra-busca input {
      flex: 1 0 calc(100% - 60px);
      padding: 11px;
      font-size: 14px;
    }

    .botao-filtro {
      flex-basis: 48px;
    }

    .botao-buscar {
      flex: 1;
      min-height: 45px;
      font-size: 16px;
    }

    .grade {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 13px;
    }

    .capa {
      height: 215px;
    }

    .informacoes h3 {
      font-size: 17px;
    }

    .adicionar {
      font-size: 12px;
    }

    .painel-filtros label {
      flex: 1;
      min-width: 120px;
    }
  }

  @media (max-width: 360px) {
    .grade {
      grid-template-columns: 1fr;
    }
  }
</style>

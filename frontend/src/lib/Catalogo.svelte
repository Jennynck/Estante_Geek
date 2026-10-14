
<script>
  import Cabecalho from '$lib/Cabecalho.svelte';
  import CartaoObra from '$lib/CartaoObra.svelte';
  import { goto } from '$app/navigation';
  import { obterToken } from '$lib/api.js';

  // Etapa visual: nenhuma obra fictícia.
  // Na integração com a API, preencher 'obras' com os dados recebidos.
  let obras = $state([]);
  let busca = $state('');
  let tipo = $state('');
  let editora = $state('');
  let genero = $state('');
  let mensagem = $state('');

  const espacosReservados = [1, 2, 3, 4];

  let editoras = $derived(
    [...new Set(obras.map((obra) => obra.editora).filter(Boolean))].sort()
  );

  let generos = $derived(
    [...new Set(obras.flatMap((obra) => obra.generos || []))].sort()
  );

  let obrasFiltradas = $derived(
    obras.filter((obra) =>
      (!busca.trim() ||
        obra.titulo.toLowerCase().includes(busca.trim().toLowerCase())) &&
      (!tipo || obra.tipo_obra === tipo) &&
      (!editora || obra.editora === editora) &&
      (!genero || (obra.generos || []).includes(genero))
    )
  );

  function buscar(evento) {
    evento.preventDefault();

    if (obras.length === 0) {
      mensagem = 'A busca ficará disponível quando conectarmos o catálogo à API.';
    } else {
      mensagem = '';
    }
  }

  async function adicionar(obras_id) {
    // A estante é particular; visitantes precisam fazer login.
    if (!obterToken()) {
      await goto('/login');
      return;
    }

    mensagem = 'A função de adicionar será conectada ao backend em uma próxima etapa.';

    // Quando integrarmos:
    // POST /estante com { obras_id }
  }
</script>

<Cabecalho />

<main class="catalogo">
  <h1>CATÁLOGO &amp; BUSCA</h1>

  <form class="barra-busca" onsubmit={buscar}>
    <input
      bind:value={busca}
      aria-label="Pesquisar obras pelo título"
      placeholder="Busque por título..."
    />

    <button class="buscar" type="submit">
      ⌕ BUSCAR
    </button>
  </form>

  <div class="painel-filtros">
    <span class="titulo-filtros">
      FILTRAR POR:
    </span>

    <div class="filtro">
      <label for="editora">EDITORA</label>

      <select id="editora" bind:value={editora}>
        <option value="">TODAS AS EDITORAS</option>

        {#each editoras as nome}
          <option value={nome}>{nome}</option>
        {/each}
      </select>
    </div>

    <div class="filtro">
      <label for="genero">GÊNERO</label>

      <select id="genero" bind:value={genero}>
        <option value="">TODOS OS GÊNEROS</option>

        {#each generos as nome}
          <option value={nome}>{nome}</option>
        {/each}
      </select>
    </div>
  </div>

  <div class="abas-tipo" aria-label="Categorias de obras">
    <button
      type="button"
      class:selecionado={tipo === ''}
      onclick={() => tipo = ''}
    >
      TODOS
    </button>

    <button
      type="button"
      class:selecionado={tipo === 'Manga'}
      onclick={() => tipo = 'Manga'}
    >
      MANGÁS
    </button>

    <button
      type="button"
      class:selecionado={tipo === 'HQ'}
      onclick={() => tipo = 'HQ'}
    >
      HQS
    </button>
  </div>

  <div class="secao-titulo">
    <h2>✦ SUGESTÕES PARA VOCÊ</h2>
    <p>Obras disponíveis no catálogo</p>
  </div>

  {#if mensagem}
    <p class="mensagem" role="status">
      {mensagem}
    </p>
  {/if}

  <div class="grade-catalogo">
    {#if obras.length === 0}
      {#each espacosReservados as posicao (posicao)}
        <CartaoObra />
      {/each}

    {:else if obrasFiltradas.length === 0}
      <p class="sem-resultados">
        Nenhuma obra encontrada para os filtros selecionados.
      </p>

    {:else}
      {#each obrasFiltradas as obra (obra.id)}
        <CartaoObra {obra} {adicionar} />
      {/each}
    {/if}
  </div>

  {#if obras.length === 0}
    <p class="aviso-integracao">
      Exibição ilustrativa: os espaços serão preenchidos com capas
      e informações reais após a integração com as APIs.
    </p>
  {/if}
</main>

<style>
  .catalogo {
    width: min(100% - 40px, 1220px);
    margin: 34px auto 80px;
  }

  h1, h2, .titulo-filtros, .filtro label,
  .abas-tipo button, .buscar {
    font-family: 'Bangers', Impact, sans-serif;
    letter-spacing: .7px;
  }

  h1 {
    color: #823cf2;
    text-shadow: 4px 4px 0 #d8cae6;
    font-size: clamp(42px, 5.1vw, 65px);
    line-height: 1;
    margin: 0 0 30px;
  }

  .barra-busca {
    display: flex;
    gap: 14px;
    width: 100%;
    margin-bottom: 15px;
  }

  .barra-busca input {
    flex: 1;
    min-width: 0;
    height: 64px;
    background: white;
    border: 2px solid #292033;
    border-radius: 9px;
    box-shadow: 5px 5px 0 #292033;
    padding: 12px 20px;
    font-size: 16px;
  }

  .buscar {
    min-width: 162px;
    padding: 14px 18px;
    background: #ff426a;
    color: white;
    border: 2px solid #292033;
    border-radius: 9px;
    box-shadow: 5px 5px 0 #292033;
    font-size: 21px;
    cursor: pointer;
  }

  .painel-filtros {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 23px;
    min-height: 86px;
    padding: 16px 22px;
    background: #fff9f3;
    border: 2px solid #292033;
    border-radius: 9px;
    box-shadow: 5px 5px 0 #292033;
    margin-bottom: 16px;
  }

  .titulo-filtros {
    white-space: nowrap;
    font-size: 21px;
    border-right: 2px solid #292033;
    padding: 14px 22px 14px 0;
  }

  .filtro {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 205px;
  }

  .filtro label {
    color: #ff456f;
    font-size: 18px;
  }

  .filtro select {
    width: 100%;
    height: 42px;
    border: 2px solid #292033;
    border-radius: 6px;
    box-shadow: 3px 3px 0 #292033;
    background: #fff;
    padding: 6px 11px;
    font: 16px 'Bangers', Impact, sans-serif;
  }

  .abas-tipo {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 16px 0 29px;
  }

  .abas-tipo button {
    min-width: 107px;
    padding: 11px 22px;
    background: #fffaf4;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 4px 0 #292033;
    font-size: 21px;
    cursor: pointer;
  }

  .abas-tipo .selecionado {
    background: #ffdb0c;
  }

  .secao-titulo {
    padding: 0 0 8px;
    border-bottom: 1px solid #ddcfd9;
    margin-bottom: 19px;
  }

  .secao-titulo h2 {
    color: #813cef;
    font-size: 30px;
    margin: 0;
  }

  .secao-titulo p {
    margin: 0;
    color: #978a9b;
    font-size: 13px;
  }

  .grade-catalogo {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 20px;
  }

  .sem-resultados {
    grid-column: 1 / -1;
    padding: 20px;
    border: 2px solid #292033;
    background: #fff9f3;
    border-radius: 9px;
  }

  .mensagem {
    padding: 12px 16px;
    background: #fff6db;
    border: 2px solid #ddad31;
    border-radius: 7px;
    margin: 0 0 18px;
    font-size: 14px;
  }

  .aviso-integracao {
    margin: 22px 0 0;
    font-size: 13px;
    color: #877b8e;
    text-align: center;
  }

  @media (max-width: 900px) {
    .grade-catalogo {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 680px) {
    .catalogo {
      width: calc(100% - 28px);
      margin: 26px auto 60px;
    }

    .barra-busca input {
      height: 52px;
      padding: 10px;
      font-size: 14px;
    }

    .buscar {
      min-width: 95px;
      padding: 8px;
      font-size: 16px;
    }

    .painel-filtros {
      gap: 12px;
      padding: 14px;
    }

    .titulo-filtros {
      width: 100%;
      padding: 0 0 9px;
      border-right: 0;
      border-bottom: 1px solid #ddcfd9;
    }

    .filtro {
      flex: 1 1 140px;
      min-width: 0;
    }

    .filtro select {
      font-size: 13px;
    }

    .abas-tipo button {
      min-width: 0;
      padding: 9px 16px;
      font-size: 18px;
    }

    .grade-catalogo {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
  }

  @media (max-width: 360px) {
    .grade-catalogo {
      grid-template-columns: 1fr;
    }
  }
</style>


<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  const LIMITE = 20;

  let verificando = $state(true);
  let autorizado = $state(false);
  let carregando = $state(false);
  let processando = $state(false);
  let erro = $state('');
  let aviso = $state('');
  let busca = $state('');
  let filtro = $state('');
  let situacao = $state('todas');
  let pagina = $state(1);
  let resenhas = $state([]);
  let modal = $state(null);
  let temporizador;

  let visiveis = $derived(
    resenhas.filter((r) =>
      situacao === 'todas' ||
      (situacao === 'bloqueadas' && r.resenha_bloqueada) ||
      (situacao === 'publicadas' && !r.resenha_bloqueada)
    )
  );

  function formatarData(valor) {
    if (!valor) return 'Data não informada';
    const partes = String(valor).slice(0, 10).split('-');

    return partes.length === 3
      ? `${partes[2]}/${partes[1]}/${partes[0]}`
      : String(valor);
  }

  function iniciais(nome) {
    return (nome || 'EG')
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((v) => v[0])
      .join('')
      .toUpperCase();
  }

  function notificar(texto) {
    aviso = texto;
    clearTimeout(temporizador);
    temporizador = setTimeout(() => aviso = '', 4500);
  }

  async function carregar() {
    carregando = true;
    erro = '';

    try {
      const params = new URLSearchParams({
        pagina: String(pagina),
        limite: String(LIMITE)
      });

      if (filtro) params.set('busca', filtro);

      resenhas = await requisicao(`/admin/resenhas?${params}`);
    } catch (falha) {
      resenhas = [];
      erro = falha.message;
    } finally {
      carregando = false;
    }
  }

  onMount(() => {
    async function iniciar() {
      if (!obterToken()) {
        await goto('/login');
        return;
      }

      try {
        const usuario = await requisicao('/usuarios/me');
        autorizado = usuario.is_admin === true;

        if (autorizado) await carregar();
        else erro = 'Esta área é exclusiva para administradores.';
      } catch (falha) {
        erro = falha.message;
      } finally {
        verificando = false;
      }
    }

    void iniciar();
    return () => clearTimeout(temporizador);
  });

  async function pesquisar(evento) {
    evento.preventDefault();
    pagina = 1;
    filtro = busca.trim();
    await carregar();
  }

  async function limpar() {
    busca = '';
    filtro = '';
    pagina = 1;
    await carregar();
  }

  async function trocarPagina(direcao) {
    if (carregando || processando) return;

    if (
      pagina + direcao < 1 ||
      (direcao > 0 && resenhas.length < LIMITE)
    ) return;

    pagina += direcao;
    await carregar();
  }

  function perguntar(item) {
    if (processando) return;

    modal = {
      item,
      bloqueada: !item.resenha_bloqueada,
      acao: item.resenha_bloqueada
        ? 'desbloquear'
        : 'bloquear'
    };
  }

  function fecharModal() {
    if (!processando) modal = null;
  }

  function aoTeclar(evento) {
    if (evento.key === 'Escape') fecharModal();
  }

  async function confirmarAcao() {
    if (!modal || processando) return;

    const { item, bloqueada } = modal;
    processando = true;
    erro = '';

    try {
      const atualizado = await requisicao(
        `/admin/resenhas/${item.id}`,
        {
          metodo: 'PATCH',
          dados: { bloqueada }
        }
      );

      resenhas = resenhas.map((r) =>
        r.id === atualizado.id ? atualizado : r
      );

      notificar(
        bloqueada
          ? 'Resenha bloqueada com sucesso.'
          : 'Resenha desbloqueada com sucesso.'
      );

      modal = null;
    } catch (falha) {
      erro = falha.message;
      modal = null;
    } finally {
      processando = false;
    }
  }
</script>

<svelte:window onkeydown={aoTeclar} />
<Cabecalho />

<main class="admin-pagina">
  <a class="voltar" href="/admin">
    ← PAINEL ADMINISTRATIVO
  </a>

  <p class="sobretitulo">
    ✦ ESTANTE GEEK / ADMINISTRAÇÃO
  </p>

  <h1>MODERAÇÃO DE RESENHAS</h1>

  {#if verificando}
    <p role="status">Verificando permissões...</p>

  {:else if !autorizado}
    <p class="mensagem erro" role="alert">
      {erro || 'Acesso restrito.'}
    </p>

  {:else}
    <form class="busca" onsubmit={pesquisar}>
      <label class="oculto" for="pesquisa-resenhas">
        Pesquisar pelo texto da resenha
      </label>

      <input
        id="pesquisa-resenhas"
        type="search"
        bind:value={busca}
        placeholder="Pesquisar resenhas..."
      />

      <button
        class="botao-busca"
        type="submit"
        disabled={carregando || processando}
      >⌕ BUSCAR</button>

      {#if filtro}
        <button
          class="limpar"
          type="button"
          onclick={limpar}
          disabled={carregando || processando}
        >LIMPAR</button>
      {/if}
    </form>

    <div class="filtros" aria-label="Filtrar por situação">
      <button
        type="button"
        class:ativo={situacao === 'todas'}
        onclick={() => situacao = 'todas'}
      >TODAS</button>

      <button
        type="button"
        class:ativo={situacao === 'publicadas'}
        onclick={() => situacao = 'publicadas'}
      >PUBLICADAS</button>

      <button
        type="button"
        class:ativo={situacao === 'bloqueadas'}
        onclick={() => situacao = 'bloqueadas'}
      >BLOQUEADAS</button>
    </div>

    <p class="nota-filtro">
      A pesquisa é feita pelo texto. O filtro de situação
      considera as resenhas carregadas nesta página.
    </p>

    {#if erro}
      <p class="mensagem erro" role="alert">{erro}</p>
    {/if}

    {#if aviso}
      <p class="mensagem sucesso" role="status">{aviso}</p>
    {/if}

    <div class="resumo">
      <span>
        {carregando
          ? 'CARREGANDO...'
          : `${visiveis.length} RESENHA(S) EXIBIDA(S)`}
      </span>
      <span>PÁGINA {pagina}</span>
    </div>

    {#if !carregando && visiveis.length === 0}
      <p class="vazio">
        Nenhuma resenha encontrada nesta página
        para o filtro selecionado.
      </p>
    {/if}

    <div class="lista">
      {#each visiveis as item (item.id)}
        <article
          class:bloqueada={item.resenha_bloqueada}
          class="cartao"
        >
          <div class="topo-resenha">
            <div class="autor">
              <div class="avatar">
                {iniciais(item.usuario?.nome_perfil)}
              </div>

              <div class="dados">
                <strong>
                  {item.usuario?.nome_perfil || 'Leitor'}
                </strong>

                <span>
                  Obra: {item.obra?.titulo || 'Obra não informada'}
                </span>

                <small>
                  Resenha publicada em:
                  {formatarData(item.data_publicacao)}
                </small>
              </div>
            </div>

            <div class="etiquetas">
              <span class="tag tipo">
                {item.obra?.tipo_obra === 'HQ'
                  ? 'HQ'
                  : 'MANGÁ'}
              </span>

              <span class="tag nota">
                ★ NOTA {item.nota ?? '—'}
              </span>

              <span
                class:restrita={item.resenha_bloqueada}
                class="tag estado"
              >
                {item.resenha_bloqueada
                  ? 'BLOQUEADA'
                  : 'PUBLICADA'}
              </span>
            </div>
          </div>

          <div class="conteudo">
            <p>
              {item.resenha?.trim()
                || 'Avaliação enviada sem comentário.'}
            </p>
          </div>

          <div class="rodape">
            <button
              class:desbloquear={item.resenha_bloqueada}
              class="moderar"
              type="button"
              disabled={processando}
              onclick={() => perguntar(item)}
            >
              {item.resenha_bloqueada
                ? 'DESBLOQUEAR'
                : 'BLOQUEAR'}
            </button>
          </div>
        </article>
      {/each}
    </div>

    <nav class="paginacao" aria-label="Paginação de resenhas">
      <button
        type="button"
        onclick={() => trocarPagina(-1)}
        disabled={carregando || processando || pagina === 1}
      >← ANTERIOR</button>

      <span>PÁGINA {pagina}</span>

      <button
        type="button"
        onclick={() => trocarPagina(1)}
        disabled={carregando || processando || resenhas.length < LIMITE}
      >PRÓXIMA →</button>
    </nav>
  {/if}
</main>

{#if modal}
  <div class="fundo-modal">
    <section
      class="janela"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="titulo-modal"
      aria-describedby="texto-modal"
    >
      <h2 id="titulo-modal">CONFIRMAR MODERAÇÃO</h2>

      <p id="texto-modal">
        Deseja {modal.acao} a resenha de
        <strong>{modal.item.usuario.nome_perfil}</strong>
        sobre
        <strong>{modal.item.obra.titulo}</strong>?
      </p>

      <div class="acoes-modal">
        <button
          type="button"
          onclick={fecharModal}
          disabled={processando}
        >CANCELAR</button>

        <button
          type="button"
          class="confirmar"
          onclick={confirmarAcao}
          disabled={processando}
        >
          {processando ? 'AGUARDE...' : 'CONFIRMAR'}
        </button>
      </div>
    </section>
  </div>
{/if}

<style>
  .admin-pagina {
    max-width: 1250px;
    margin: auto;
    padding: 30px 22px 75px;
    color: #292033;
  }
  .voltar {
    display: inline-block;
    color: #813bea;
    font-weight: 800;
    font-size: 13px;
    line-height: 1.4;
  }
  .sobretitulo {
    margin: 24px 0 10px;
    color: #85659a;
    font-weight: 800;
    font-size: 13px;
    line-height: 1.4;
    letter-spacing: .6px;
  }
  h1, h2, .dados strong, .tag,
  .resumo, button, .paginacao {
    font-family: 'Bangers', Impact, sans-serif;
    letter-spacing: .5px;
  }
  h1 {
    font-size: clamp(36px, 5vw, 64px);
    line-height: 1.2;
    color: #8239ed;
    text-shadow: 3px 4px #dfcef8;
    margin: 0 0 30px;
  }
  .busca {
    display: flex;
    gap: 14px;
    margin-bottom: 19px;
    align-items: stretch;
  }
  .busca input {
    flex: 1;
    min-width: 0;
    border: 2px solid #292033;
    border-radius: 9px;
    background: white;
    box-shadow: 4px 5px #292033;
    padding: 14px 18px;
    font: inherit;
  }
  button {
    cursor: pointer;
    border: 2px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    padding: 10px 16px;
    font-size: 17px;
  }
  button:disabled {
    opacity: .55;
    cursor: not-allowed;
  }
  .botao-busca {
    background: #ff416b;
    color: white;
    min-width: 132px;
    font-size: 18px;
    box-shadow: 4px 5px #292033;
  }
  .limpar { background: #ffdc12; }
  .filtros {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 4px 0 10px;
  }
  .filtros button { background: #fffaf5; }
  .filtros button.ativo { background: #ffdc12; }
  .nota-filtro {
    color: #89768e;
    font-size: 13px;
    margin: 0 0 25px;
  }
  .resumo {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    color: #7d36d3;
    font-size: 21px;
    margin: 13px 0;
  }
  .lista {
    display: grid;
    gap: 18px;
  }
  .cartao {
    background: #fffaf5;
    border: 3px solid #292033;
    box-shadow: 5px 6px #292033;
    border-radius: 12px;
    padding: 22px;
  }
  .cartao.bloqueada { background: #f5edf1; }
  .topo-resenha {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 15px;
    flex-wrap: wrap;
  }
  .autor {
    display: flex;
    gap: 13px;
    align-items: center;
    flex: 1;
    min-width: 0;
  }
  .avatar {
    display: grid;
    place-items: center;
    flex: 0 0 51px;
    height: 51px;
    border: 2px solid #292033;
    border-radius: 50%;
    background: #8239ed;
    color: white;
    font: 21px 'Bangers', Impact, sans-serif;
  }
  .dados {
    display: grid;
    gap: 4px;
    min-width: 0;
  }
  .dados strong { font-size: 26px; }
  .dados span { overflow-wrap: anywhere; }
  .dados small { color: #927b95; }
  .etiquetas {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .tag {
    border: 1px solid #292033;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 14px;
  }
  .tag.tipo { background: #04bff2; }
  .tag.nota { background: #ffdc12; }
  .tag.estado { background: #c5ffe4; }
  .tag.restrita { background: #ffb9c7; }
  .conteudo {
    background: white;
    border: 2px solid #e6dae8;
    border-radius: 9px;
    margin-top: 20px;
    padding: 16px;
    min-height: 68px;
  }
  .conteudo p {
    margin: 0;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    line-height: 1.55;
  }
  .rodape {
    display: flex;
    justify-content: flex-end;
    margin-top: 17px;
  }
  .moderar {
    background: #ff416b;
    color: white;
    min-width: 135px;
  }
  .moderar.desbloquear {
    background: #7de7b3;
    color: #292033;
  }
  .paginacao {
    display: flex;
    gap: 15px;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 33px;
  }
  .paginacao button { background: #ffdc12; }
  .mensagem {
    padding: 13px 16px;
    margin: 15px 0;
    border: 2px solid #292033;
    border-radius: 8px;
  }
  .erro { background: #ffe0e8; }
  .sucesso { background: #d5fff0; }
  .vazio {
    border: 2px dashed #9e8ba1;
    padding: 22px;
    border-radius: 9px;
  }
  .fundo-modal {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: #271c3099;
    display: grid;
    place-items: center;
    padding: 18px;
  }
  .janela {
    width: min(100%, 530px);
    background: #fffaf4;
    border: 3px solid #292033;
    border-top: 10px solid #8239ed;
    border-radius: 13px;
    box-shadow: 6px 7px #292033;
    padding: 25px;
  }
  .janela h2 {
    color: #8239ed;
    font-size: 31px;
    line-height: 1.25;
    margin: 0 0 13px;
  }
  .janela p {
    line-height: 1.6;
    margin: 0 0 23px;
  }
  .acoes-modal {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  .acoes-modal button { background: #fffaf4; }
  .acoes-modal .confirmar {
    background: #ff416b;
    color: white;
  }
  .oculto {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
  }
  @media (max-width: 700px) {
    .admin-pagina { padding: 23px 13px 60px; }
    .busca { flex-wrap: wrap; }
    .busca input { flex: 1 0 100%; }
    .cartao { padding: 16px; }
  }
</style>


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
  let pagina = $state(1);
  let usuarios = $state([]);
  let detalhes = $state(null);
  let modal = $state(null);
  let temporizador;

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
      usuarios = await requisicao(`/admin/usuarios?${params}`);
    } catch (falha) {
      usuarios = [];
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
        const eu = await requisicao('/usuarios/me');
        autorizado = eu.is_admin === true;
        if (autorizado) await carregar();
        else erro = 'Acesso restrito a administradores.';
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
    detalhes = null;
    await carregar();
  }

  async function trocarPagina(direcao) {
    if (carregando || processando) return;
    if (
      pagina + direcao < 1 ||
      (direcao > 0 && usuarios.length < LIMITE)
    ) return;

    pagina += direcao;
    detalhes = null;
    await carregar();
  }

  async function abrirDetalhes(id) {
    if (detalhes?.id === id) {
      detalhes = null;
      return;
    }
    try {
      detalhes = await requisicao(`/admin/usuarios/${id}`);
      erro = '';
    } catch (falha) {
      erro = falha.message;
    }
  }

  function perguntar(usuario) {
    if (usuario.is_admin || processando) return;
    modal = {
      usuario,
      acao: usuario.usuario_bloqueado
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
    const { usuario, acao } = modal;
    processando = true;
    erro = '';

    try {
      const atualizado = await requisicao(
        `/admin/usuarios/${usuario.id}/${acao}`,
        { metodo: 'PATCH' }
      );

      usuarios = usuarios.map((u) =>
        u.id === atualizado.id ? atualizado : u
      );

      if (detalhes?.id === atualizado.id) {
        detalhes = atualizado;
      }

      notificar(
        `A conta de ${atualizado.nome_perfil} foi ${
          atualizado.usuario_bloqueado
            ? 'bloqueada'
            : 'desbloqueada'
        } com sucesso.`
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
  <a class="voltar" href="/admin">← PAINEL ADMINISTRATIVO</a>
  <p class="sobretitulo">✦ ESTANTE GEEK / ADMINISTRAÇÃO</p>
  <h1>GESTÃO DE USUÁRIOS</h1>

  {#if verificando}
    <p role="status">Verificando permissões...</p>
  {:else if !autorizado}
    <p class="mensagem erro" role="alert">
      {erro || 'Acesso restrito.'}
    </p>
  {:else}
    <form class="busca" onsubmit={pesquisar}>
      <label class="oculto" for="pesquisa-usuarios">
        Pesquisar usuários
      </label>
      <input
        id="pesquisa-usuarios"
        bind:value={busca}
        placeholder="Buscar por nome de perfil ou e-mail..."
      />
      <button
        class="botao-busca"
        type="submit"
        disabled={carregando}
      >⌕ BUSCAR</button>
    </form>

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
          : `${usuarios.length} USUÁRIO(S) NESTA PÁGINA`}
      </span>
      <span>PÁGINA {pagina}</span>
    </div>

    {#if !carregando && usuarios.length === 0}
      <p class="vazio">Nenhum usuário encontrado.</p>
    {/if}

    <div class="lista">
      {#each usuarios as usuario (usuario.id)}
        <article class="cartao">
          <div class="avatar">
            {usuario.nome_perfil?.slice(0, 2).toUpperCase() || 'EG'}
          </div>

          <div class="dados">
            <strong>{usuario.nome_perfil}</strong>
            <span class="email">{usuario.email}</span>

            <div class="etiquetas">
              {#if usuario.is_admin}
                <span class="tag admin">ADMINISTRADOR</span>
              {/if}
              <span
                class:bloqueada={usuario.usuario_bloqueado}
                class="tag"
              >
                {usuario.usuario_bloqueado
                  ? 'BLOQUEADO'
                  : 'ATIVO'}
              </span>
            </div>
          </div>

          <div class="acoes">
            <button
              class="botao detalhes"
              type="button"
              onclick={() => abrirDetalhes(usuario.id)}
            >
              DETALHES
            </button>

            {#if !usuario.is_admin}
              <button
                class:desbloquear={usuario.usuario_bloqueado}
                class="botao bloquear"
                type="button"
                disabled={processando}
                onclick={() => perguntar(usuario)}
              >
                {usuario.usuario_bloqueado
                  ? 'DESBLOQUEAR'
                  : 'BLOQUEAR'}
              </button>
            {/if}
          </div>
        </article>
      {/each}
    </div>

    {#if detalhes}
      <section
        class="painel-detalhes"
        aria-label="Detalhes do usuário"
      >
        <div class="cabeca-detalhes">
          <h2>DETALHES DA CONTA</h2>
          <button
            type="button"
            class="fechar"
            onclick={() => detalhes = null}
            aria-label="Fechar detalhes"
          >×</button>
        </div>

        <dl>
          <div>
            <dt>ID</dt><dd>{detalhes.id}</dd>
          </div>
          <div>
            <dt>Nome de perfil</dt>
            <dd>{detalhes.nome_perfil}</dd>
          </div>
          <div>
            <dt>Nome</dt><dd>{detalhes.nome_usuario}</dd>
          </div>
          <div>
            <dt>E-mail</dt><dd>{detalhes.email}</dd>
          </div>
          <div>
            <dt>E-mail confirmado?</dt>
            <dd>{detalhes.email_confirmado ? 'Sim' : 'Não'}</dd>
          </div>
          <div>
            <dt>Perfil</dt>
            <dd>{detalhes.perfil_publico ? 'Público' : 'Privado'}</dd>
          </div>
          <div>
            <dt>Situação</dt>
            <dd>
              {detalhes.usuario_bloqueado ? 'Bloqueado' : 'Ativo'}
            </dd>
          </div>
          <div>
            <dt>Permissão</dt>
            <dd>
              {detalhes.is_admin
                ? 'Administrador'
                : 'Usuário comum'}
            </dd>
          </div>
        </dl>
      </section>
    {/if}

    <nav class="paginacao" aria-label="Paginação de usuários">
      <button
        type="button"
        onclick={() => trocarPagina(-1)}
        disabled={carregando || pagina === 1}
      >← ANTERIOR</button>
      <span>PÁGINA {pagina}</span>
      <button
        type="button"
        onclick={() => trocarPagina(1)}
        disabled={carregando || usuarios.length < LIMITE}
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
      <h2 id="titulo-modal">CONFIRMAR AÇÃO</h2>
      <p id="texto-modal">
        Deseja realmente {modal.acao} a conta de
        <strong>{modal.usuario.nome_perfil}</strong>?
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
  h1, h2, .cartao strong, .tag, .resumo,
  .botao, .botao-busca, .paginacao,
  .acoes-modal button {
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
    margin-bottom: 24px;
    align-items: stretch;
  }
  .busca input {
    flex: 1;
    min-width: 0;
    background: white;
    border: 2px solid #292033;
    border-radius: 9px;
    box-shadow: 4px 5px #292033;
    padding: 14px 18px;
    font: inherit;
  }
  .botao-busca {
    border: 2px solid #292033;
    border-radius: 9px;
    box-shadow: 4px 5px #292033;
    background: #ff416b;
    color: white;
    min-width: 132px;
    font-size: 18px;
    padding: 12px 16px;
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
    gap: 16px;
  }
  .cartao {
    display: flex;
    align-items: center;
    gap: 16px;
    background: #fffaf5;
    border: 3px solid #292033;
    border-radius: 12px;
    box-shadow: 5px 6px #292033;
    padding: 17px 20px;
  }
  .avatar {
    display: grid;
    place-items: center;
    flex: 0 0 52px;
    height: 52px;
    border: 2px solid #292033;
    border-radius: 50%;
    background: #8239ed;
    color: white;
    font: 21px 'Bangers', Impact, sans-serif;
  }
  .dados {
    min-width: 0;
    flex: 1;
    display: grid;
    gap: 3px;
  }
  .dados strong {
    font-size: 26px;
  }
  .email {
    font-size: 13px;
    color: #7b6a80;
    overflow-wrap: anywhere;
  }
  .etiquetas {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin-top: 3px;
  }
  .tag {
    background: #c4ffec;
    border: 1px solid #292033;
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 13px;
  }
  .tag.admin { background: #ffdc12; }
  .tag.bloqueada { background: #ffb9c7; }
  .acoes {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  .botao {
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 4px 4px #292033;
    font-size: 17px;
    padding: 11px 15px;
  }
  .detalhes { background: #04bff2; }
  .bloquear {
    background: #ff416b;
    color: #fff;
  }
  .bloquear.desbloquear {
    background: #7de7b3;
    color: #292033;
  }
  button:disabled {
    opacity: .55;
    cursor: not-allowed;
  }
  .painel-detalhes {
    border: 3px solid #292033;
    border-radius: 12px;
    box-shadow: 5px 6px #292033;
    background: #fffaf5;
    padding: 22px;
    margin-top: 27px;
  }
  .cabeca-detalhes {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
  }
  .cabeca-detalhes h2 {
    color: #8239ed;
    font-size: 32px;
    line-height: 1.2;
    margin: 0;
  }
  .fechar {
    background: #ffdc12;
    border: 2px solid #292033;
    border-radius: 7px;
    font-size: 24px;
    width: 45px;
    height: 45px;
  }
  dl {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 16px;
  }
  dl div {
    border-bottom: 1px solid #e5d8e6;
    padding: 9px 0;
    min-width: 0;
  }
  dt {
    font-size: 13px;
    color: #796080;
    font-weight: 700;
  }
  dd {
    margin: 5px 0 0;
    overflow-wrap: anywhere;
  }
  .paginacao {
    display: flex;
    gap: 15px;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 33px;
  }
  .paginacao button {
    background: #ffdc12;
    border: 2px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    padding: 9px 15px;
    font: 17px 'Bangers', Impact, sans-serif;
  }
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
    width: min(100%, 490px);
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
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 12px;
  }
  .acoes-modal button {
    font-size: 18px;
    border: 2px solid #292033;
    box-shadow: 3px 4px #292033;
    border-radius: 8px;
    padding: 11px 16px;
    background: #fffaf4;
  }
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
    .cartao { flex-wrap: wrap; }
    .acoes { width: 100%; }
    .busca { flex-direction: column; }
    .botao-busca { min-height: 49px; }
    dl { grid-template-columns: 1fr; }
    .admin-pagina { padding: 23px 13px 60px; }
  }
</style>

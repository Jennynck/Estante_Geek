
<script>
  import { onMount } from 'svelte';
  import { afterNavigate, goto } from '$app/navigation';
  import AvatarUsuario from '$lib/AvatarUsuario.svelte';
  import { apagarToken, obterToken, requisicao } from '$lib/api.js';

  let autenticado = $state(false);
  let perfil = $state(null);
  let versaoFoto = $state(0);

  async function carregarPerfil() {
    try {
      perfil = await requisicao('/usuarios/me');
    } catch {
      perfil = null;
    }
  }

  function aoAtualizarPerfil() {
    versaoFoto += 1;
    void carregarPerfil();
  }

  onMount(() => {
    autenticado = Boolean(obterToken());

    if (autenticado) {
      void carregarPerfil();
    }

    window.addEventListener(
      'estante-perfil-atualizado',
      aoAtualizarPerfil
    );

    return () => {
      window.removeEventListener(
        'estante-perfil-atualizado',
        aoAtualizarPerfil
      );
    };
  });

  afterNavigate(() => {
    autenticado = Boolean(obterToken());

    if (autenticado) {
      void carregarPerfil();
    } else {
      perfil = null;
    }
  });

  async function sair() {
    apagarToken();
    autenticado = false;
    perfil = null;
    await goto('/login');
  }
</script>

<header class="topo">
  <div class="topo-conteudo">
    <a
      class="logo"
      href="/"
      aria-label="Estante Geek — voltar ao catálogo"
    >
      <span>ESTANTE</span> GEEK
    </a>

    <nav class="menu" aria-label="Navegação principal">
      <a href="/minha-estante">MINHA ESTANTE</a>
      <a href="/comunidade">COMUNIDADE</a>

      {#if autenticado && perfil?.is_admin}
        <a class="admin-link" href="/admin">
          PAINEL ADM
        </a>
      {/if}
    </nav>

    <div class="acoes">
      {#if autenticado}
        <a
          class="perfil-link"
          href="/minha-conta"
          aria-label="Meu perfil"
          title="Meu perfil"
        >
          <AvatarUsuario
            usuarioId="me"
            nome={perfil?.nome_perfil || ''}
            tamanho={42}
            versao={versaoFoto}
          />
        </a>

        <button
          class="acao-rosa"
          type="button"
          onclick={sair}
        >
          SAIR
        </button>
      {:else}
        <a class="acao-azul" href="/login">
          LOGIN
        </a>

        <a class="acao-amarela" href="/cadastro">
          CADASTRE-SE
        </a>
      {/if}
    </div>
  </div>
</header>

<style>
  .topo {
    background: #fff9f2;
    border-bottom: 6px solid #2b2032;
    width: 100%;
  }

  .topo-conteudo {
    max-width: 1260px;
    padding: 13px 22px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 24px;
  }

  .logo {
    flex-shrink: 0;
    font: 32px/1 'Bangers', Impact, sans-serif;
    letter-spacing: 0.5px;
    transform: skew(-7deg);
    text-shadow: 2px 3px #d7c9e6;
    white-space: nowrap;
  }

  .logo span {
    color: #813cea;
  }

  .menu {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .menu a,
  .acoes a,
  .acoes button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 35px;
    padding: 8px 13px;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 3px 0 #292033;
    font: 16px/1 'Bangers', Impact, sans-serif;
    letter-spacing: .45px;
    white-space: nowrap;
    text-decoration: none;
    color: #292033;
    cursor: pointer;
  }

  .menu a,
  .menu a.admin-link {
    background: #fffdf8;
  }

  .menu a:hover,
  .menu a:focus-visible,
  .menu a.admin-link:hover,
  .menu a.admin-link:focus-visible {
    background: #f3e9ff;
  }

  .menu a:focus-visible {
    outline: 2px solid #813cea;
    outline-offset: 3px;
  }

  .acoes {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
  }

  .acoes .acao-azul {
    background: #04bff2;
  }

  .acoes .acao-amarela {
    background: #ffdc12;
  }

  .acoes .acao-rosa {
    background: #ff456b;
    color: white;
  }

  .acoes a.perfil-link {
    min-height: 0;
    padding: 0;
    border: 0;
    border-radius: 50%;
    box-shadow: none;
    background: none;
  }

  .perfil-link :global(.cm-avatar) {
    box-shadow: 2px 3px 0 #292033;
    transition: transform 0.1s;
  }

  .perfil-link:hover :global(.cm-avatar),
  .perfil-link:focus-visible :global(.cm-avatar) {
    transform: translateY(-2px);
  }

  @media (max-width: 750px) {
    .topo-conteudo {
      flex-wrap: wrap;
      gap: 13px;
      padding: 12px 15px;
    }

    .logo {
      font-size: 29px;
    }

    .acoes {
      margin-left: auto;
    }

    .menu {
      order: 3;
      width: 100%;
    }
  }

  @media (max-width: 390px) {
    .menu a,
    .acoes a,
    .acoes button {
      padding: 7px 9px;
      font-size: 13px;
    }

    .acoes a.perfil-link {
      padding: 0;
    }
  }
</style>

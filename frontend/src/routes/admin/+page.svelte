
<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let verificando = $state(true);
  let autorizado = $state(false);
  let erro = $state('');

  onMount(() => {
    async function iniciar() {
      if (!obterToken()) {
        await goto('/login');
        return;
      }

      try {
        const usuario = await requisicao('/usuarios/me');
        autorizado = usuario.is_admin === true;

        if (!autorizado) {
          erro = 'Esta área é exclusiva para administradores.';
        }
      } catch (falha) {
        erro = falha.message;
      } finally {
        verificando = false;
      }
    }

    void iniciar();
  });
</script>

<Cabecalho />

<main class="admin-pagina">
  <p class="sobretitulo">
    ✦ ESTANTE GEEK / ADMINISTRAÇÃO
  </p>

  <h1>PAINEL ADMINISTRATIVO</h1>

  {#if verificando}
    <p role="status">Verificando permissões...</p>

  {:else if !autorizado}
    <section class="mensagem" role="alert">
      <h2>ACESSO RESTRITO</h2>
      <p>
        {erro || 'Você não tem permissão para acessar esta área.'}
      </p>
      <a href="/minha-estante">
        VOLTAR À MINHA ESTANTE
      </a>
    </section>

  {:else}
    <p class="intro">
      Escolha uma área para gerenciar.
    </p>

    <div class="atalhos">
      <a class="atalho" href="/admin/usuarios">
        <span class="simbolo" aria-hidden="true">👥</span>

        <strong>GESTÃO DE USUÁRIOS</strong>

        <span>
          Consulte contas e bloqueie ou desbloqueie usuários.
        </span>

        <b>ACESSAR</b>
      </a>

      <a class="atalho" href="/admin/resenhas">
        <span class="simbolo" aria-hidden="true">📝</span>

        <strong>MODERAÇÃO DE RESENHAS</strong>

        <span>
          Consulte, bloqueie e desbloqueie avaliações.
        </span>

        <b>ACESSAR</b>
      </a>

      <a class="atalho" href="/admin/termos">
        <span class="simbolo" aria-hidden="true">🛡️</span>

        <strong>FILTRO DE PALAVRAS</strong>

        <span>
          Cadastre, pesquise ou remova termos inadequados.
        </span>

        <b>ACESSAR</b>
      </a>
    </div>
  {/if}
</main>

<style>
  .admin-pagina {
    max-width: 1250px;
    margin: auto;
    padding: 34px 22px 75px;
    color: #292033;
  }
  .sobretitulo {
    margin: 0 0 10px;
    color: #85659a;
    font-size: 13px;
    font-weight: 800;
    line-height: 1.4;
    letter-spacing: .6px;
  }
  h1, h2, strong, b {
    font-family: 'Bangers', Impact, sans-serif;
    letter-spacing: .6px;
  }
  h1 {
    font-size: clamp(36px, 5vw, 64px);
    line-height: 1.2;
    color: #8239ed;
    text-shadow: 3px 4px #dfcef8;
    margin: 0 0 30px;
  }
  .intro {
    margin: 0 0 26px;
    font-size: 16px;
  }
  .atalhos {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 20px;
  }
  .atalho {
    display: flex;
    flex-direction: column;
    gap: 13px;
    background: #fffaf5;
    border: 3px solid #292033;
    box-shadow: 5px 6px #292033;
    border-radius: 13px;
    padding: 24px;
    color: inherit;
    text-decoration: none;
    min-height: 260px;
    transition: transform .15s, background .15s;
  }
  .atalho:hover {
    background: #f7eaff;
    transform: translateY(-3px);
  }
  .atalho:focus-visible {
    outline: 3px solid #8239ed;
    outline-offset: 4px;
  }
  .simbolo { font-size: 32px; }
  .atalho strong {
    color: #8239ed;
    font-size: 27px;
    line-height: 1.15;
  }
  .atalho span:not(.simbolo) {
    line-height: 1.5;
  }
  .atalho b {
    margin-top: auto;
    align-self: flex-start;
    background: #ffdc12;
    border: 2px solid #292033;
    border-radius: 6px;
    padding: 7px 13px;
    font-size: 18px;
  }
  .mensagem {
    border: 3px solid #292033;
    background: #fffaf5;
    border-radius: 12px;
    padding: 22px;
  }
  .mensagem h2 {
    color: #ff416b;
    font-size: 30px;
    margin: 0 0 8px;
  }
  .mensagem a {
    color: #8239ed;
    font-weight: 800;
  }
  @media (max-width: 800px) {
    .atalhos { grid-template-columns: 1fr; }
    .atalho { min-height: 0; }
    .admin-pagina { padding: 23px 13px 60px; }
  }
</style>

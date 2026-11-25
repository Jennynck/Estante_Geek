
<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let verificando = $state(true);
  let autorizado = $state(false);
  let carregando = $state(false);
  let salvando = $state(false);
  let removendo = $state(false);
  let erro = $state('');
  let aviso = $state('');
  let novoTermo = $state('');
  let busca = $state('');
  let termos = $state([]);
  let modal = $state(null);
  let temporizador;

  let termosFiltrados = $derived(
    termos.filter((termo) =>
      termo.termos_inadequados
        .toLocaleLowerCase('pt-BR')
        .includes(busca.trim().toLocaleLowerCase('pt-BR'))
    )
  );

  function ordenar(lista) {
    return [...lista].sort((a, b) =>
      a.termos_inadequados.localeCompare(
        b.termos_inadequados,
        'pt-BR'
      )
    );
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
      termos = ordenar(await requisicao('/admin/termos'));
    } catch (falha) {
      erro = falha.message;
      termos = [];
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

  async function adicionar(evento) {
    evento.preventDefault();
    if (salvando || removendo) return;

    erro = '';
    const texto = novoTermo.trim().toLocaleLowerCase('pt-BR');

    if (texto.length < 2) {
      erro = 'Digite um termo com pelo menos 2 caracteres.';
      return;
    }

    if (termos.some(
      (t) => t.termos_inadequados
        .toLocaleLowerCase('pt-BR') === texto
    )) {
      erro = 'Este termo já está cadastrado.';
      return;
    }

    salvando = true;

    try {
      const criado = await requisicao('/admin/termos', {
        metodo: 'POST',
        dados: { termos_inadequados: texto }
      });

      termos = ordenar([...termos, criado]);
      novoTermo = '';

      notificar(
        `Termo "${criado.termos_inadequados}" adicionado com sucesso.`
      );
    } catch (falha) {
      erro = falha.message;
    } finally {
      salvando = false;
    }
  }

  function fecharModal() {
    if (!removendo) modal = null;
  }

  function aoTeclar(evento) {
    if (evento.key === 'Escape') fecharModal();
  }

  async function confirmarRemocao() {
    if (!modal || removendo) return;

    const termo = modal;
    removendo = true;
    erro = '';

    try {
      await requisicao(`/admin/termos/${termo.id}`, {
        metodo: 'DELETE'
      });

      termos = termos.filter((item) => item.id !== termo.id);

      notificar(
        `Termo "${termo.termos_inadequados}" removido com sucesso.`
      );

      modal = null;
    } catch (falha) {
      erro = falha.message;
      modal = null;
    } finally {
      removendo = false;
    }
  }
</script>

<svelte:window onkeydown={aoTeclar} />
<Cabecalho />

<main class="admin-pagina">
  <a class="voltar" href="/admin">← PAINEL ADMINISTRATIVO</a>
  <p class="sobretitulo">✦ ESTANTE GEEK / ADMINISTRAÇÃO</p>
  <h1>FILTRO DE PALAVRAS</h1>

  {#if verificando}
    <p role="status">Verificando permissões...</p>
  {:else if !autorizado}
    <p class="mensagem erro" role="alert">
      {erro || 'Acesso restrito.'}
    </p>
  {:else}
    <section class="painel">
      <h2>+ ADICIONAR NOVO TERMO</h2>
      <p>
        Cadastre palavras ou expressões que não devem
        aparecer nas resenhas.
      </p>

      <form class="formulario" onsubmit={adicionar}>
        <label class="oculto" for="novo-termo">
          Novo termo inadequado
        </label>
        <input
          id="novo-termo"
          bind:value={novoTermo}
          maxlength="100"
          minlength="2"
          required
          placeholder="Digite uma palavra ou expressão..."
          disabled={salvando || removendo}
        />
        <button
          class="adicionar"
          type="submit"
          disabled={salvando || removendo}
        >
          {salvando ? 'ADICIONANDO...' : '+ ADICIONAR'}
        </button>
      </form>

      <small>
        Os termos são salvos em letras minúsculas
        e não podem ser repetidos.
      </small>
    </section>

    {#if erro}
      <p class="mensagem erro" role="alert">{erro}</p>
    {/if}
    {#if aviso}
      <p class="mensagem sucesso" role="status">{aviso}</p>
    {/if}

    <section class="secao-termos">
      <div class="cabecalho-termos">
        <h2>TERMOS BLOQUEADOS</h2>

        <label class="oculto" for="pesquisar-termos">
          Pesquisar termos cadastrados
        </label>
        <input
          id="pesquisar-termos"
          type="search"
          bind:value={busca}
          placeholder="Pesquisar termos..."
        />
      </div>

      {#if carregando}
        <p role="status">Carregando termos...</p>
      {:else if termos.length === 0}
        <div class="painel">
          <p>Nenhum termo cadastrado.</p>
        </div>
      {:else if termosFiltrados.length === 0}
        <div class="painel">
          <p>Nenhum termo encontrado para essa pesquisa.</p>
        </div>
      {:else}
        <div class="painel lista-termos">
          {#each termosFiltrados as termo (termo.id)}
            <div class="termo">
              <span>{termo.termos_inadequados}</span>
              <button
                type="button"
                aria-label={`Remover o termo ${termo.termos_inadequados}`}
                title="Remover termo"
                disabled={salvando || removendo}
                onclick={() => modal = termo}
              >×</button>
            </div>
          {/each}
        </div>
      {/if}

      <p class="total-termos">
        {termos.length}
        {termos.length === 1
          ? 'TERMO CADASTRADO'
          : 'TERMOS CADASTRADOS'}
      </p>
    </section>
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
      <h2 id="titulo-modal">REMOVER TERMO</h2>
      <p id="texto-modal">
        Tem certeza de que deseja remover
        <strong>"{modal.termos_inadequados}"</strong>
        da lista?
      </p>

      <div class="acoes-modal">
        <button
          type="button"
          onclick={fecharModal}
          disabled={removendo}
        >CANCELAR</button>
        <button
          type="button"
          class="confirmar"
          onclick={confirmarRemocao}
          disabled={removendo}
        >
          {removendo ? 'REMOVENDO...' : 'CONFIRMAR'}
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
  h1, h2, button, .total-termos, .acoes-modal button {
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
  h2 {
    font-size: 26px;
    line-height: 1.25;
    margin: 0;
    color: #8239ed;
  }
  .painel {
    background: #fffaf5;
    border: 3px solid #292033;
    border-radius: 12px;
    box-shadow: 5px 6px #292033;
    padding: 24px;
    margin-bottom: 30px;
  }
  .painel p {
    color: #78667b;
    margin: 9px 0 17px;
  }
  .formulario {
    display: flex;
    gap: 14px;
    margin-bottom: 12px;
  }
  input {
    background: white;
    border: 2px solid #292033;
    border-radius: 9px;
    padding: 13px 17px;
    font: inherit;
    min-width: 0;
  }
  .formulario input {
    flex: 1;
    box-shadow: 4px 5px #292033;
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
  .adicionar {
    background: #04bff2;
    white-space: nowrap;
  }
  small {
    color: #8c7e91;
    font-size: 12px;
  }
  .cabecalho-termos {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
    flex-wrap: wrap;
    margin: 10px 0 18px;
  }
  .cabecalho-termos h2 { color: #292033; }
  .cabecalho-termos input {
    width: 265px;
    max-width: 100%;
  }
  .lista-termos {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    min-height: 110px;
    align-items: flex-start;
  }
  .termo {
    display: inline-flex;
    align-items: center;
    gap: 11px;
    background: white;
    padding: 7px 8px 7px 13px;
    border: 2px solid #292033;
    border-radius: 7px;
    max-width: 100%;
    overflow-wrap: anywhere;
  }
  .termo button {
    width: 26px;
    height: 26px;
    display: grid;
    place-items: center;
    padding: 0;
    background: #ff416b;
    color: white;
    box-shadow: none;
    border: 1px solid #292033;
    font: bold 19px Arial, sans-serif;
  }
  .total-termos {
    display: inline-block;
    background: #8239ed;
    color: white;
    border: 2px solid #292033;
    border-radius: 7px;
    padding: 8px 13px;
    font-size: 18px;
  }
  .mensagem {
    padding: 14px 16px;
    margin: 14px 0;
    border: 2px solid #292033;
    border-radius: 8px;
  }
  .erro { background: #ffe0e8; }
  .sucesso { background: #d5fff0; }
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
  .acoes-modal button {
    font-size: 18px;
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
  @media (max-width: 680px) {
    .admin-pagina { padding: 23px 13px 60px; }
    .formulario { flex-direction: column; }
    .cabecalho-termos input { width: 100%; }
    .painel { padding: 17px; }
  }
</style>

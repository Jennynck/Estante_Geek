<script>
  import { onMount } from 'svelte';
  import { requisicao } from '$lib/api.js';

  let { obraId, naEstante = false } = $props();

  let resenhas = $state([]);
  let total = $state(0);
  let carregando = $state(true);
  let erroLista = $state('');
  let sucesso = $state('');

  // Janela de escrever resenha
  let aberto = $state(false);
  let estrelas = $state(0);
  let sobre = $state(0);
  let texto = $state('');
  let enviando = $state(false);
  let erroForm = $state('');

  const cores = ['#823cf2', '#ff456b', '#05bff2'];

  async function carregar() {
    erroLista = '';

    try {
      const dados = await requisicao(`/obras/${encodeURIComponent(obraId)}/resenhas`);

      resenhas = dados?.resenhas || [];
      total = dados?.total_avaliacoes ?? resenhas.length;
    } catch (falha) {
      erroLista = falha.message;
    } finally {
      carregando = false;
    }
  }

  function iniciais(nome) {
    return String(nome || '?').trim().slice(0, 2).toUpperCase();
  }

  function formatarData(valor) {
    if (!valor) return '';

    return new Date(valor)
      .toLocaleDateString('pt-BR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      })
      .replace(/ de /g, ' ')
      .replace('.', '');
  }

  // O backend guarda nota de 1 a 10; a tela usa 5 estrelas.
  function notaEmEstrelas(nota) {
    return Number(nota) / 2;
  }

  function textoNota(nota) {
    return notaEmEstrelas(nota).toLocaleString('pt-BR');
  }

  async function abrir() {
    erroForm = '';
    sucesso = '';
    estrelas = 0;
    texto = '';

    // Se já existe resenha, preenche para edição.
    try {
      const itens = await requisicao('/estante');

      const meu = Array.isArray(itens)
        ? itens.find((item) => Number(item.obra?.id) === Number(obraId))
        : null;

      if (meu?.nota) {
        estrelas = Math.round(meu.nota / 2);
        texto = meu.resenha || '';
      }
    } catch {
      // Segue com o formulário vazio.
    }

    aberto = true;
  }

  function fechar() {
    if (enviando) return;
    aberto = false;
  }

  async function publicar() {
    if (!estrelas || enviando) return;

    enviando = true;
    erroForm = '';

    try {
      await requisicao(`/estante/${encodeURIComponent(obraId)}/resenha`, {
        metodo: 'PUT',
        dados: {
          nota: estrelas * 2,
          resenha: texto.trim() || null
        }
      });

      aberto = false;
      sucesso = 'Sua resenha foi publicada!';

      await carregar();
    } catch (falha) {
      erroForm = falha.message;
    } finally {
      enviando = false;
    }
  }

  onMount(carregar);
</script>

<svelte:window
  onkeydown={(evento) => {
    if (evento.key === 'Escape' && aberto) fechar();
  }}
/>

<section class="resenhas" aria-labelledby="titulo-resenhas">
  <div class="cabecalho-secao">
    <h2 id="titulo-resenhas">RESENHAS DA COMUNIDADE</h2>
    <span class="linha"></span>
    <span class="contagem">
      {total} {total === 1 ? 'AVALIAÇÃO' : 'AVALIAÇÕES'}
    </span>
  </div>

  {#if sucesso}
    <p class="aviso sucesso" role="status">{sucesso}</p>
  {/if}

  {#if carregando}
    <p class="vazio" role="status">Carregando resenhas...</p>

  {:else if erroLista}
    <p class="aviso falha" role="alert">{erroLista}</p>

  {:else if resenhas.length === 0}
    <p class="vazio">Ainda não há resenhas para esta obra. Seja o primeiro!</p>

  {:else}
    <ul class="lista">
      {#each resenhas as resenha (resenha.id)}
        <li class="cartao">
          <div
            class="avatar"
            style:background={cores[resenha.usuario.id % cores.length]}
          >
            {iniciais(resenha.usuario.nome_perfil)}
          </div>

          <div class="corpo">
            <div class="topo">
              <strong class="autor">{resenha.usuario.nome_perfil}</strong>

              <span
                class="estrelas"
                aria-label={`Nota ${textoNota(resenha.nota)} de 5`}
              >
                {'★'.repeat(Math.round(notaEmEstrelas(resenha.nota)))}{'☆'.repeat(
                  5 - Math.round(notaEmEstrelas(resenha.nota))
                )}
              </span>

              <span class="nota">{textoNota(resenha.nota)}/5</span>

              <span class="data">{formatarData(resenha.data_publicacao)}</span>
            </div>

            {#if resenha.resenha}
              <p>{resenha.resenha}</p>
            {:else}
              <p class="sem-texto">Avaliou sem comentário.</p>
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}

  <div class="acao">
    <button
      class="botao-escrever"
      type="button"
      disabled={!naEstante}
      onclick={abrir}
    >
      ✎ ESCREVER RESENHA
    </button>

    {#if !naEstante}
      <p class="dica">
        Adicione a obra à sua estante para escrever uma resenha.
      </p>
    {/if}
  </div>
</section>

{#if aberto}
  <div
    class="fundo"
    role="presentation"
    onclick={(evento) => {
      if (evento.target === evento.currentTarget) fechar();
    }}
  >
    <div
      class="janela"
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-janela"
    >
      <h3 id="titulo-janela">ESCREVER RESENHA</h3>

      <p class="explicacao">
        Você pode registrar apenas uma avaliação por obra.
        O envio atualizará sua resenha já existente.
      </p>

      <div
        class="seletor-estrelas"
        role="radiogroup"
        aria-label="Sua nota de 1 a 5 estrelas"
        onmouseleave={() => (sobre = 0)}
      >
        {#each [1, 2, 3, 4, 5] as valor (valor)}
          <button
            type="button"
            role="radio"
            aria-checked={estrelas === valor}
            aria-label={`${valor} ${valor === 1 ? 'estrela' : 'estrelas'}`}
            class:ativa={valor <= (sobre || estrelas)}
            onmouseenter={() => (sobre = valor)}
            onclick={() => (estrelas = valor)}
          >
            {valor <= (sobre || estrelas) ? '★' : '☆'}
          </button>
        {/each}
      </div>

      <textarea
        bind:value={texto}
        maxlength="500"
        rows="5"
        placeholder="Escreva sua opinião sobre a obra..."
        aria-label="Texto da resenha"
      ></textarea>

      <p class="contador">{texto.length}/500 caracteres</p>

      <p class="aviso-termos">
        * Aviso: Resenhas contendo palavras inadequadas serão bloqueadas pelo sistema.
      </p>

      {#if erroForm}
        <p class="aviso falha" role="alert">{erroForm}</p>
      {/if}

      <div class="botoes">
        <button class="cancelar" type="button" onclick={fechar} disabled={enviando}>
          CANCELAR
        </button>

        <button
          class="publicar"
          type="button"
          disabled={!estrelas || enviando}
          onclick={publicar}
        >
          {enviando ? 'PUBLICANDO...' : '✦ PUBLICAR ✦'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .resenhas {
    margin-top: 34px;
  }

  h2,
  h3,
  .autor,
  .nota,
  .contagem,
  .botao-escrever,
  .cancelar,
  .publicar {
    font-family: 'Bangers', Impact, sans-serif;
  }

  /* CABEÇALHO */

  .cabecalho-secao {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 18px;
  }

  .cabecalho-secao h2 {
    margin: 0;
    font-size: 34px;
    white-space: nowrap;
  }

  .linha {
    flex: 1;
    height: 2px;
    background: #e1d8df;
  }

  .contagem {
    padding: 4px 10px;
    background: #ffda0d;
    border: 2px solid #292033;
    border-radius: 5px;
    box-shadow: 2px 2px #292033;
    font-size: 13px;
    white-space: nowrap;
  }

  /* LISTA */

  .lista {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .cartao {
    display: flex;
    gap: 14px;
    padding: 16px 18px;
    background: #fff9f2;
    border: 3px solid #292033;
    border-radius: 10px;
    box-shadow: 5px 5px 0 #292033;
  }

  .avatar {
    flex-shrink: 0;
    width: 46px;
    height: 46px;
    display: grid;
    place-items: center;
    border: 3px solid #292033;
    border-radius: 50%;
    color: white;
    font: 17px 'Bangers', Impact, sans-serif;
  }

  .corpo {
    min-width: 0;
    flex: 1;
  }

  .topo {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .autor {
    font-size: 18px;
    font-weight: 400;
  }

  .estrelas {
    color: #ffbf00;
    font-size: 15px;
    letter-spacing: 1px;
  }

  .nota {
    padding: 1px 7px;
    background: #ffda0d;
    border: 2px solid #292033;
    border-radius: 4px;
    font-size: 12px;
  }

  .data {
    margin-left: auto;
    color: #a1969f;
    font-size: 12px;
  }

  .corpo p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    overflow-wrap: anywhere;
    white-space: pre-line;
  }

  .sem-texto {
    color: #a1969f;
    font-style: italic;
  }

  .vazio {
    padding: 26px;
    text-align: center;
    background: #fff9f2;
    border: 2px solid #292033;
    border-radius: 9px;
  }

  /* BOTÃO ESCREVER */

  .acao {
    margin-top: 24px;
    text-align: center;
  }

  .botao-escrever {
    padding: 11px 20px;
    background: #823cf2;
    color: white;
    border: 3px solid #292033;
    border-radius: 9px;
    box-shadow: 4px 5px 0 #292033;
    font-size: 18px;
    cursor: pointer;
  }

  .botao-escrever:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .dica {
    margin: 10px 0 0;
    color: #8c7f96;
    font-size: 12px;
  }

  /* AVISOS */

  .aviso {
    margin: 0 0 16px;
    padding: 11px 14px;
    border: 2px solid;
    border-radius: 8px;
    font-size: 13px;
  }

  .aviso.sucesso {
    background: #e8ffee;
    border-color: #3ba361;
  }

  .aviso.falha {
    background: #ffe4e9;
    border-color: #fb4269;
  }

  /* JANELA */

  .fundo {
    position: fixed;
    inset: 0;
    z-index: 50;
    display: grid;
    place-items: center;
    padding: 16px;
    background: rgba(41, 32, 51, 0.6);
    overflow-y: auto;
  }

  .janela {
    width: min(100%, 480px);
    padding: 22px 26px 24px;
    background: #fff9f2;
    border: 3px solid #292033;
    border-top: 12px solid #823cf2;
    border-radius: 14px;
    box-shadow: 6px 7px 0 #292033;
  }

  .janela h3 {
    margin: 0 0 6px;
    color: #823cf2;
    font-size: 36px;
    text-align: center;
    text-shadow: 3px 3px #d7c9e6;
    font-weight: 400;
  }

  .explicacao {
    margin: 0 0 16px;
    color: #8c7f96;
    font-size: 12px;
    text-align: center;
  }

  .seletor-estrelas {
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-bottom: 16px;
  }

  .seletor-estrelas button {
    padding: 0 3px;
    background: none;
    border: 0;
    color: #292033;
    font-size: 40px;
    line-height: 1;
    cursor: pointer;
  }

  .seletor-estrelas button.ativa {
    color: #ffbf00;
  }

  textarea {
    display: block;
    width: 100%;
    padding: 12px 14px;
    border: 3px solid #292033;
    border-radius: 9px;
    background: white;
    font: 14px 'Nunito Sans', Arial, sans-serif;
    resize: vertical;
  }

  .contador {
    margin: 4px 4px 0;
    color: #aaa1ad;
    font-size: 11px;
    text-align: right;
  }

  .aviso-termos {
    margin: 10px 0 14px;
    color: #d6264b;
    font-size: 11px;
    line-height: 1.4;
  }

  .botoes {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }

  .cancelar,
  .publicar {
    padding: 10px 18px;
    border: 3px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px 0 #292033;
    font-size: 17px;
    cursor: pointer;
  }

  .cancelar {
    background: #fff9f2;
    color: #292033;
  }

  .publicar {
    background: #823cf2;
    color: white;
  }

  .publicar:disabled,
  .cancelar:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @media (max-width: 560px) {
    .cabecalho-secao h2 {
      font-size: 26px;
      white-space: normal;
    }

    .linha {
      display: none;
    }

    .cabecalho-secao {
      justify-content: space-between;
    }

    .data {
      margin-left: 0;
      width: 100%;
    }
  }
</style>    
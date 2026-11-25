
<script>
  import { onMount } from 'svelte';
  import { requisicao } from '$lib/api.js';

  let { obraId, naEstante = false } = $props();

  let resenhas = $state([]);
  let total = $state(0);
  let carregando = $state(true);
  let erroLista = $state('');
  let sucesso = $state('');

  let minhaResenha = $state(null);
  let meuUsuarioId = $state(null);
  let verificandoMinhaResenha = $state(false);

  let aberto = $state(false);
  let estrelas = $state(0);
  let sobre = $state(0);
  let texto = $state('');
  let enviando = $state(false);
  let erroForm = $state('');

  let modalExclusao = $state(false);
  let excluindo = $state(false);
  let erroExclusao = $state('');

  let temporizadorSucesso;
  let temporizadorErro;

  const cores = ['#823cf2', '#ff456b', '#05bff2'];

  let minhaBloqueada = $derived(
    minhaResenha?.resenha_bloqueada === true &&
    minhaResenha?.nota != null
  );

  let resenhasPublicas = $derived(
    resenhas.filter((resenha) => {
      if (resenha.resenha_bloqueada) return false;

      if (
        minhaBloqueada &&
        meuUsuarioId !== null &&
        Number(resenha.usuario?.id) === Number(meuUsuarioId)
      ) {
        return false;
      }

      return true;
    })
  );

  function notificar(mensagem) {
    clearTimeout(temporizadorSucesso);
    sucesso = mensagem;

    temporizadorSucesso = setTimeout(() => {
      sucesso = '';
    }, 4500);
  }

  function mostrarErro(mensagem) {
    clearTimeout(temporizadorErro);
    erroForm = mensagem;

    temporizadorErro = setTimeout(() => {
      erroForm = '';
    }, 5500);
  }

  function iniciais(nome) {
    return String(nome || '?')
      .trim()
      .slice(0, 2)
      .toUpperCase();
  }

  function formatarData(valor) {
    if (!valor) return 'Data não informada';

    const [ano, mes, dia] = String(valor)
      .slice(0, 10)
      .split('-');

    return ano && mes && dia
      ? `${dia}/${mes}/${ano}`
      : String(valor);
  }

  function notaEmEstrelas(nota) {
    return Number(nota || 0) / 2;
  }

  function textoNota(nota) {
    return notaEmEstrelas(nota).toLocaleString('pt-BR');
  }

  async function carregar() {
    erroLista = '';
    carregando = true;

    try {
      const dados = await requisicao(
        `/obras/${encodeURIComponent(obraId)}/resenhas`
      );

      resenhas = Array.isArray(dados?.resenhas)
        ? dados.resenhas
        : [];

      total = dados?.total_avaliacoes ??
        resenhas.filter((r) => !r.resenha_bloqueada).length;
    } catch (falha) {
      erroLista = falha.message;
    } finally {
      carregando = false;
    }
  }

  async function carregarMinhaResenha() {
    verificandoMinhaResenha = true;

    try {
      const [estante, usuario] = await Promise.all([
        requisicao('/estante'),
        requisicao('/usuarios/me')
      ]);

      meuUsuarioId = usuario?.id ?? null;

      minhaResenha = Array.isArray(estante)
        ? estante.find(
            (item) =>
              Number(item.obra?.id) === Number(obraId)
          ) || null
        : null;
    } catch {
      minhaResenha = null;
      meuUsuarioId = null;
    } finally {
      verificandoMinhaResenha = false;
    }
  }

  async function abrir() {
    if (!naEstante || enviando || verificandoMinhaResenha) {
      return;
    }

    erroForm = '';
    estrelas = 0;
    texto = '';

    try {
      const itens = await requisicao('/estante');

      const meu = Array.isArray(itens)
        ? itens.find(
            (item) =>
              Number(item.obra?.id) === Number(obraId)
          )
        : null;

      minhaResenha = meu || null;

      if (meu?.resenha_bloqueada) {
        mostrarErro(
          'Sua resenha foi bloqueada por infringir as diretrizes da comunidade. Exclua a resenha bloqueada antes de publicar outra.'
        );
        return;
      }

      if (meu?.nota != null) {
        estrelas = Math.round(Number(meu.nota) / 2);
        texto = meu.resenha || '';
      }
    } catch (falha) {
      mostrarErro(falha.message);
      return;
    }

    aberto = true;
  }

  function fechar() {
    if (!enviando) {
      aberto = false;
    }
  }

  async function publicar() {
    if (!estrelas || enviando || minhaBloqueada) return;

    enviando = true;
    erroForm = '';

    try {
      await requisicao(
        `/estante/${encodeURIComponent(obraId)}/resenha`,
        {
          metodo: 'PUT',
          dados: {
            nota: estrelas * 2,
            resenha: texto.trim() || null
          }
        }
      );

      aberto = false;
      notificar('Sua resenha foi publicada com sucesso!');

      await Promise.all([
        carregar(),
        carregarMinhaResenha()
      ]);
    } catch (falha) {
      mostrarErro(falha.message);
    } finally {
      enviando = false;
    }
  }

  function solicitarExclusao() {
    if (!minhaBloqueada || excluindo) return;

    erroExclusao = '';
    modalExclusao = true;
  }

  function fecharExclusao() {
    if (!excluindo) {
      modalExclusao = false;
    }
  }

  async function excluirMinhaResenha() {
    if (excluindo || !minhaBloqueada) return;

    excluindo = true;
    erroExclusao = '';

    try {
      await requisicao(
        `/estante/${encodeURIComponent(obraId)}/resenha`,
        { metodo: 'DELETE' }
      );

      modalExclusao = false;
      minhaResenha = null;

      notificar(
        'Sua resenha foi excluída. Agora você pode escrever uma nova avaliação.'
      );

      await Promise.all([
        carregar(),
        carregarMinhaResenha()
      ]);
    } catch (falha) {
      erroExclusao = falha.message;
    } finally {
      excluindo = false;
    }
  }

  function aoPressionarTecla(evento) {
    if (evento.key !== 'Escape') return;

    if (modalExclusao) {
      fecharExclusao();
    } else if (aberto) {
      fechar();
    }
  }

  onMount(() => {
    void Promise.all([
      carregar(),
      carregarMinhaResenha()
    ]);

    return () => {
      clearTimeout(temporizadorSucesso);
      clearTimeout(temporizadorErro);
    };
  });
</script>

<svelte:window onkeydown={aoPressionarTecla} />

<section class="resenhas" aria-labelledby="titulo-resenhas">
  <div class="cabecalho-secao">
    <h2 id="titulo-resenhas">RESENHAS DA COMUNIDADE</h2>
    <span class="linha"></span>
    <span class="contagem">
      {total} {total === 1 ? 'AVALIAÇÃO' : 'AVALIAÇÕES'}
    </span>
  </div>

  {#if sucesso}
    <p class="aviso sucesso" role="status">
      {sucesso}
    </p>
  {/if}

  {#if minhaBloqueada}
    <section class="resenha-bloqueada" aria-label="Sua resenha bloqueada">
      <div class="cabecalho-bloqueio">
        <h3>SUA RESENHA FOI BLOQUEADA</h3>
        <span class="etiqueta-bloqueio">VISÍVEL SOMENTE PARA VOCÊ</span>
      </div>

      <p class="motivo">
        Sua resenha foi bloqueada por infringir as diretrizes
        da comunidade. Ela não está visível para os demais
        leitores e não pode ser editada.
      </p>

      <div class="minha-avaliacao">
        <strong>MINHA AVALIAÇÃO</strong>

        <span class="estrelas">
          {'★'.repeat(Math.round(notaEmEstrelas(minhaResenha.nota)))}
          {'☆'.repeat(5 - Math.round(notaEmEstrelas(minhaResenha.nota)))}
        </span>

        <span class="nota">
          {textoNota(minhaResenha.nota)}/5
        </span>
      </div>

      <p class="texto-bloqueado">
        {minhaResenha.resenha || 'Avaliação sem comentário.'}
      </p>

      <p class="data-bloqueada">
        Resenha publicada em:
        {formatarData(minhaResenha.data_publicacao)}
      </p>

      <p class="orientacao-bloqueio">
        Para publicar uma nova resenha, exclua primeiro
        a avaliação bloqueada.
      </p>

      <button
        class="botao-excluir"
        type="button"
        onclick={solicitarExclusao}
        disabled={excluindo}
      >
        EXCLUIR MINHA RESENHA
      </button>
    </section>
  {/if}

  {#if carregando}
    <p class="vazio" role="status">Carregando resenhas...</p>

  {:else if erroLista}
    <p class="aviso falha" role="alert">
      {erroLista}
    </p>

  {:else if resenhasPublicas.length === 0 && !minhaBloqueada}
    <p class="vazio">
      Ainda não há resenhas para esta obra. Seja o primeiro!
    </p>

  {:else if resenhasPublicas.length > 0}
    <ul class="lista">
      {#each resenhasPublicas as resenha (resenha.id)}
        <li class="cartao">
          <div
            class="avatar"
            style:background={cores[
              Number(resenha.usuario?.id || 0) % cores.length
            ]}
          >
            {iniciais(resenha.usuario?.nome_perfil)}
          </div>

          <div class="corpo">
            <div class="topo">
              <strong class="autor">
                {resenha.usuario?.nome_perfil || 'Leitor'}
              </strong>

              <span
                class="estrelas"
                aria-label={`Nota ${textoNota(resenha.nota)} de 5`}
              >
                {'★'.repeat(Math.round(notaEmEstrelas(resenha.nota)))}
                {'☆'.repeat(5 - Math.round(notaEmEstrelas(resenha.nota)))}
              </span>

              <span class="nota">
                {textoNota(resenha.nota)}/5
              </span>

              <span class="data">
                Resenha publicada em:
                {formatarData(resenha.data_publicacao)}
              </span>
            </div>

            {#if resenha.resenha}
              <p>{resenha.resenha}</p>
            {:else}
              <p class="sem-texto">
                Avaliou sem comentário.
              </p>
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}

  <div class="acao">
    {#if minhaBloqueada}
      <p class="dica-bloqueio">
        A edição de uma resenha bloqueada não é permitida.
      </p>
    {:else}
      <button
        class="botao-escrever"
        type="button"
        disabled={!naEstante || verificandoMinhaResenha}
        onclick={abrir}
      >
        ✎ ESCREVER RESENHA
      </button>

      {#if !naEstante}
        <p class="dica">
          Adicione a obra à sua estante para escrever uma resenha.
        </p>
      {/if}
    {/if}

    {#if erroForm && !aberto}
      <p class="aviso falha" role="alert">
        {erroForm}
      </p>
    {/if}
  </div>
</section>

{#if aberto}
  <div class="fundo">
    <section
      class="janela"
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-janela"
    >
      <h3 id="titulo-janela">
        ESCREVER RESENHA
      </h3>

      <p class="explicacao">
        Você pode registrar apenas uma avaliação por obra.
        O envio atualizará sua resenha já existente.
      </p>

      <div
        class="seletor-estrelas"
        role="radiogroup"
        aria-label="Sua nota de 1 a 5 estrelas"
        onmouseleave={() => sobre = 0}
      >
        {#each [1, 2, 3, 4, 5] as valor (valor)}
          <button
            type="button"
            role="radio"
            aria-checked={estrelas === valor}
            aria-label={`${valor} ${valor === 1 ? 'estrela' : 'estrelas'}`}
            class:ativa={valor <= (sobre || estrelas)}
            onmouseenter={() => sobre = valor}
            onclick={() => estrelas = valor}
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

      <p class="contador">
        {texto.length}/500 caracteres
      </p>

      <p class="aviso-termos">
        Resenhas com termos inadequados não poderão ser publicadas.
      </p>

      {#if erroForm}
        <p class="aviso falha" role="alert">
          {erroForm}
        </p>
      {/if}

      <div class="botoes">
        <button
          class="cancelar"
          type="button"
          onclick={fechar}
          disabled={enviando}
        >
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
    </section>
  </div>
{/if}

{#if modalExclusao}
  <div class="fundo">
    <section
      class="janela"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="titulo-exclusao"
      aria-describedby="texto-exclusao"
    >
      <h3 id="titulo-exclusao">
        EXCLUIR RESENHA?
      </h3>

      <p id="texto-exclusao" class="explicacao">
        Sua avaliação bloqueada será excluída.
        Depois você poderá escrever uma nova.
      </p>

      {#if erroExclusao}
        <p class="aviso falha" role="alert">
          {erroExclusao}
        </p>
      {/if}

      <div class="botoes">
        <button
          class="cancelar"
          type="button"
          onclick={fecharExclusao}
          disabled={excluindo}
        >
          CANCELAR
        </button>

        <button
          class="botao-excluir"
          type="button"
          onclick={excluirMinhaResenha}
          disabled={excluindo}
        >
          {excluindo
            ? 'EXCLUINDO...'
            : 'CONFIRMAR EXCLUSÃO'}
        </button>
      </div>
    </section>
  </div>
{/if}

<style>
  .resenhas {
    margin-top: 34px;
  }

  h2, h3, .autor, .nota, .contagem,
  .botao-escrever, .cancelar, .publicar,
  .botao-excluir, .etiqueta-bloqueio,
  .minha-avaliacao strong {
    font-family: 'Bangers', Impact, sans-serif;
  }

  .cabecalho-secao {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 18px;
  }

  .cabecalho-secao h2 {
    margin: 0;
    font-size: 34px;
    line-height: 1.2;
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
    font-size: 17px;
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

  .resenha-bloqueada {
    padding: 20px;
    margin: 0 0 20px;
    background: #fff2f4;
    border: 3px solid #ff456b;
    border-radius: 11px;
    box-shadow: 5px 5px 0 #292033;
  }

  .cabecalho-bloqueio {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 12px;
  }

  .cabecalho-bloqueio h3 {
    color: #da2952;
    font-size: 26px;
    line-height: 1.2;
    margin: 0;
  }

  .etiqueta-bloqueio {
    border: 2px solid #292033;
    border-radius: 5px;
    padding: 4px 8px;
    background: #ffcfdb;
    font-size: 12px;
  }

  .motivo,
  .orientacao-bloqueio {
    font-size: 13px;
    line-height: 1.6;
    color: #70334c;
  }

  .minha-avaliacao {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin: 15px 0;
  }

  .texto-bloqueado {
    padding: 15px;
    border: 2px solid #e9cad1;
    border-radius: 8px;
    background: white;
    overflow-wrap: anywhere;
    white-space: pre-wrap;
    line-height: 1.5;
  }

  .data-bloqueada {
    color: #887080;
    font-size: 12px;
  }

  .botao-excluir {
    padding: 10px 16px;
    background: #ff456b;
    color: white;
    border: 3px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    font-size: 17px;
    cursor: pointer;
  }

  .botao-excluir:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .dica-bloqueio {
    color: #9c3650;
    font-size: 13px;
    font-weight: 700;
  }

  .fundo {
    position: fixed;
    inset: 0;
    z-index: 1000;
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
    line-height: 1.2;
    text-align: center;
    text-shadow: 3px 3px #d7c9e6;
    font-weight: 400;
  }

  .explicacao {
    margin: 0 0 16px;
    color: #8c7f96;
    font-size: 12px;
    text-align: center;
    line-height: 1.6;
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
    flex-wrap: wrap;
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
    }

    .linha {
      display: none;
    }

    .cabecalho-secao {
      justify-content: space-between;
      flex-wrap: wrap;
    }

    .data {
      margin-left: 0;
      width: 100%;
    }

    .cartao {
      padding: 13px;
    }

    .resenha-bloqueada {
      padding: 15px;
    }
  }
</style>

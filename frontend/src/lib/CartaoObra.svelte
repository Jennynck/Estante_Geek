
<script>
  // Aceita dados de obras da API.
  // Sem obra, mostra apenas o modelo visual do card.
  // Mantém as propriedades usadas também na página Minha Estante.

  let {
    obra = null,
    naEstante = false,
    status = null,
    progresso = null,
    adicionar = null,
    remover = null
  } = $props();

  let executando = $state(false);

  async function executar(acao) {
    if (!obra || !acao || executando) return;

    executando = true;

    try {
      await acao(obra.id);
    } finally {
      executando = false;
    }
  }
</script>

<article
  class="obra-card"
  aria-label={obra ? obra.titulo : 'Espaço reservado para uma obra'}
>
  {#if obra}
    <a
      class="area-capa"
      href={`/obra/${obra.id}`}
      aria-label={`Ver detalhes de ${obra.titulo}`}
    >
      {#if obra.capa_url}
        <img
          src={obra.capa_url}
          alt={`Capa de ${obra.titulo}`}
          loading="lazy"
        />
      {:else}
        <div class="capa-ausente">
          <span>CAPA INDISPONÍVEL</span>
        </div>
      {/if}

      <span
        class="tipo"
        class:tipo-hq={obra.tipo_obra === 'HQ'}
      >
        {obra.tipo_obra === 'HQ' ? 'HQ' : 'MANGÁ'}
      </span>

      {#if status}
        <span class="status">
          {status}
        </span>
      {/if}
    </a>

    <div class="informacoes">
      <h3>{obra.titulo}</h3>

      <p>
        {obra.editora || 'Editora não informada'}
      </p>

      {#if progresso !== null}
        <div class="progresso-legenda">
          <span>PROGRESSO</span>
          <span>{Math.round(Number(progresso))}%</span>
        </div>

        <div class="trilha">
          <div
            style={`width: ${Math.max(
              0,
              Math.min(100, Number(progresso))
            )}%`}
          ></div>
        </div>
      {/if}

      {#if remover}
        <a
          class="botao-primario botao-azul"
          href={`/obra/${obra.id}`}
        >
          VER CHECKLIST
        </a>

        <button
          class="botao-secundario"
          type="button"
          disabled={executando}
          onclick={() => executar(remover)}
        >
          REMOVER
        </button>
      {:else}
        <button
          class="botao-primario"
          type="button"
          disabled={executando || naEstante}
          onclick={() => executar(adicionar)}
        >
          {naEstante
            ? '✓ ADICIONADO!'
            : executando
              ? 'AGUARDE...'
              : '✦ ADICIONAR NA ESTANTE'}
        </button>

        <a
          class="ver-detalhes"
          href={`/obra/${obra.id}`}
        >
          VER DETALHES →
        </a>
      {/if}
    </div>

  {:else}
    <!-- Espaços visuais para os dados que virão da API. -->

    <div
      class="area-capa area-placeholder"
      aria-hidden="true"
    >
      <span class="icone-livro">▤</span>
      <span class="capa-legenda">CAPA DA OBRA</span>
    </div>

    <div
      class="informacoes placeholder-informacoes"
      aria-hidden="true"
    >
      <div class="linha-placeholder titulo-placeholder"></div>
      <div class="linha-placeholder editora-placeholder"></div>
      <div class="botao-placeholder"></div>
      <div class="linha-placeholder detalhes-placeholder"></div>
    </div>
  {/if}
</article>

<style>
  .obra-card {
    background: #fffaf3;
    border: 3px solid #292033;
    box-shadow: 5px 6px 0 #292033;
    border-radius: 12px;
    overflow: hidden;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }

  .area-capa {
    height: 268px;
    display: block;
    position: relative;
    background: #eee8f4;
    overflow: hidden;
  }

  .area-capa img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .area-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: repeating-linear-gradient(
      135deg,
      #f4eef8,
      #f4eef8 14px,
      #eee5f4 14px,
      #eee5f4 28px
    );
    border-bottom: 2px solid #292033;
  }

  .icone-livro {
    color: #bda6d5;
    font: 60px/1 'Bangers', Impact, sans-serif;
  }

  .capa-legenda {
    color: #836d99;
    font: 18px 'Bangers', Impact, sans-serif;
    letter-spacing: 1px;
  }

  .capa-ausente {
    height: 100%;
    display: grid;
    place-items: center;
    padding: 16px;
    background: #e5d9ed;
    color: #635372;
    font: 20px 'Bangers', Impact, sans-serif;
  }

  .tipo,
  .status {
    position: absolute;
    top: 10px;
    right: 10px;
    border: 2px solid #292033;
    border-radius: 5px;
    box-shadow: 2px 2px 0 #292033;
    background: #05bdf3;
    padding: 4px 8px;
    font: 14px 'Bangers', Impact, sans-serif;
  }

  .tipo-hq {
    background: #ff466f;
    color: white;
  }

  .status {
    left: 10px;
    right: auto;
    top: auto;
    bottom: 10px;
    background: #ffda10;
  }

  .informacoes {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 7px;
    padding: 12px;
  }

  h3 {
    margin: 0;
    font: 20px/1.05 'Bangers', Impact, sans-serif;
    letter-spacing: .4px;
    min-height: 22px;
    overflow-wrap: anywhere;
  }

  p {
    font-size: 12px;
    color: #928497;
    margin: 0 0 5px;
    min-height: 17px;
  }

  .botao-primario,
  .botao-secundario {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ff436a;
    color: white;
    padding: 10px 6px;
    width: 100%;
    min-height: 42px;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 3px 0 #292033;
    text-align: center;
    font: 15px/1 'Bangers', Impact, sans-serif;
  }

  .botao-primario:disabled {
    opacity: .7;
    cursor: default;
  }

  .botao-azul {
    background: #05bff2;
    color: #292033;
  }

  .botao-secundario {
    background: #fffaf3;
    color: #292033;
    cursor: pointer;
  }

  .ver-detalhes {
    align-self: flex-start;
    margin-top: 6px;
    font: 15px 'Bangers', Impact, sans-serif;
    color: #843df0;
    text-decoration: underline;
  }

  .progresso-legenda {
    display: flex;
    justify-content: space-between;
    font: 13px 'Bangers', Impact, sans-serif;
  }

  .trilha {
    width: 100%;
    height: 11px;
    border: 2px solid #292033;
    border-radius: 5px;
    overflow: hidden;
    background: #f0eaf3;
  }

  .trilha > div {
    background: #05bff2;
    height: 100%;
  }

  .placeholder-informacoes {
    gap: 12px;
  }

  .linha-placeholder {
    background: #e9deed;
    border-radius: 4px;
    height: 13px;
  }

  .titulo-placeholder {
    width: 82%;
    height: 18px;
  }

  .editora-placeholder {
    width: 58%;
  }

  .botao-placeholder {
    margin-top: auto;
    height: 42px;
    background: #f4cad7;
    border: 2px solid #d5aebc;
    border-radius: 7px;
  }

  .detalhes-placeholder {
    height: 10px;
    width: 46%;
    background: #e3d5f1;
  }

  @media (max-width: 550px) {
    .area-capa {
      height: 210px;
    }

    h3 {
      font-size: 17px;
    }

    .informacoes {
      padding: 9px;
    }

    .botao-primario,
    .botao-secundario {
      font-size: 12px;
    }
  }
</style>

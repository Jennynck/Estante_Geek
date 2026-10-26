<script>
  import { onMount } from 'svelte';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let { id } = $props();

  let dados = $state(null);
  let carregando = $state(true);
  let autenticado = $state(false);
  let erro = $state('');
  let salvando = $state(null);

  const generosPTBR = {
    Action: 'Ação',
    Adventure: 'Aventura',
    Comedy: 'Comédia',
    Drama: 'Drama',
    Fantasy: 'Fantasia',
    Horror: 'Terror',
    Mystery: 'Mistério',
    Romance: 'Romance',
    'Sci-Fi': 'Ficção científica',
    'Slice of Life': 'Cotidiano',
    Sports: 'Esportes',
    Supernatural: 'Sobrenatural',
    Suspense: 'Suspense',
    Historical: 'Histórico',
    Psychological: 'Psicológico',
    School: 'Escolar',
    'Award Winning': 'Premiado'
  };

  function corStatus(status) {
    const cores = {
      'Quero Ler': '#ffda0d',
      'Lendo': '#08bdf0',
      'Lido': '#b3e8c0',
      'Pausado': '#dac4ff'
    };
    return cores[status] || '#08bdf0';
  }

  let obra = $derived(dados?.obra ?? null);
  let volumes = $derived(dados?.volumes ?? []);
  let ehHQ = $derived(obra?.tipo_obra === 'HQ');

  let total = $derived(volumes.length);
  let lidos = $derived(volumes.filter((v) => v.lido).length);
  let possuidos = $derived(volumes.filter((v) => v.possui_volume).length);
  let naoLidos = $derived(total - lidos);
  let progresso = $derived(total ? Math.round((lidos / total) * 100) : 0);

  let rotulo = $derived(ehHQ ? 'ED.' : 'VOL.');
  let textoLidos = $derived(ehHQ ? 'edições lidas' : 'volumes lidos');
  let titulosSecao = $derived(ehHQ ? 'EDIÇÕES DA SÉRIE' : 'VOLUMES DA SÉRIE');

  async function carregar() {
    autenticado = Boolean(obterToken());

    if (!autenticado) {
      carregando = false;
      return;
    }

    try {
      dados = await requisicao(
        `/estante/${encodeURIComponent(id)}/checklist`
      );
    } catch (falha) {
      erro = falha.message;
    } finally {
      carregando = false;
    }
  }

  function atualizarLocal(volumeId, mudancas) {
    dados.volumes = dados.volumes.map((linha) =>
      linha.volume.id === volumeId ? { ...linha, ...mudancas } : linha
    );
  }

  // campo: 'lido' ou 'possui_volume'
  async function alterar(linha, campo) {
    if (salvando !== null) return;

    const volumeId = linha.volume.id;
    const novoValor = !linha[campo];

    salvando = volumeId;
    erro = '';

    // Atualiza na hora e desfaz se o backend falhar.
    atualizarLocal(volumeId, { [campo]: novoValor });

    try {
      const salvo = await requisicao(
        `/estante/${encodeURIComponent(id)}/volumes/${volumeId}`,
        {
          metodo: 'PATCH',
          dados: { [campo]: novoValor }
        }
      );

      atualizarLocal(volumeId, {
        lido: salvo.lido,
        possui_volume: salvo.possui_volume
      });
    } catch (falha) {
      atualizarLocal(volumeId, { [campo]: !novoValor });
      erro = falha.message;
    } finally {
      salvando = null;
    }
  }

  onMount(carregar);
</script>

<Cabecalho />

<main class="pagina-checklist">
  <div class="trilha-navegacao">
    <a href="/minha-estante">← MINHA ESTANTE</a>
    <a href={`/obra/${id}`}>VER DETALHES →</a>
  </div>

  {#if carregando}
    <div class="estado" role="status">CARREGANDO CHECKLIST...</div>

  {:else if !autenticado}
    <div class="estado">
      <h1>FAÇA LOGIN!</h1>
      <p>Entre na sua conta para acompanhar o progresso de leitura.</p>
      <a class="botao-comic azul" href="/login">FAZER LOGIN</a>
    </div>

  {:else if !dados}
    <div class="estado" role="alert">
      <h1>CHECKLIST INDISPONÍVEL</h1>
      <p>{erro || 'Não foi possível carregar o checklist.'}</p>
      <a class="botao-comic azul" href={`/obra/${id}`}>VER DETALHES DA OBRA</a>
    </div>

  {:else}
    <!-- CABEÇALHO DA OBRA -->

    <section class="painel ficha">
      <div class="capa">
        {#if obra.capa_url}
          <img src={obra.capa_url} alt={`Capa de ${obra.titulo}`} />
        {:else}
          <div class="sem-capa">SEM CAPA</div>
        {/if}
      </div>

      <div class="ficha-info">
        <p class="chamada">★ CHECKLIST &amp; PROGRESSO DE LEITURA ★</p>

        <h1>{obra.titulo}</h1>

        <div class="etiquetas">
          {#if obra.editora}
            <span class="et-roxa">{obra.editora}</span>
          {/if}

          <span class="et-azul">{ehHQ ? 'HQ' : 'MANGÁ'}</span>

          {#if obra.generos?.length}
            <span class="et-amarela">
              {obra.generos
                .slice(0, 3)
                .map((g) => generosPTBR[g] || g)
                .join(' / ')}
            </span>
          {/if}
        </div>

        <div class="linha-progresso">
          <p class="texto-progresso">
            PROGRESSO: {progresso}% — <b>{lidos}</b> DE <b class="roxo">{total}</b>
            {textoLidos.toUpperCase()}
          </p>

          <span
            class="status"
            style:background={corStatus(dados.status)}
          >
            {dados.status}
          </span>
        </div>

        <div
          class="barra"
          role="progressbar"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-valuenow={progresso}
        >
          <div style:width={`${progresso}%`}></div>
        </div>

        <p class="contadores">
          <span class="c-roxo">{lidos} {lidos === 1 ? 'Lido' : 'Lidos'}</span>
          <span class="c-rosa">{naoLidos} Não {naoLidos === 1 ? 'lido' : 'lidos'}</span>
          <span class="c-azul">{possuidos} Na coleção</span>
          <span>{total} Total</span>
        </p>
      </div>
    </section>

    <!-- LEGENDA -->

    <section class="painel legenda">
      <h2>COMO LER O CHECKLIST</h2>

      <div class="itens-legenda">
        <div>
          <span class="amostra roxo"></span>
          Roxo = Lido
        </div>

        <div>
          <span class="amostra cinza"></span>
          Cinza = Não lido
        </div>

        <div>
          <span class="amostra amarelo"></span>
          Amarelo = Você tem o exemplar
        </div>
      </div>
    </section>

    <!-- VOLUMES -->

    <div class="titulo-secao">
      <h2>{titulosSecao}</h2>
      <span class="linha"></span>
      <small>CLIQUE NO NÚMERO PARA MARCAR COMO LIDO</small>
    </div>

    {#if erro}
      <p class="feedback" role="alert">{erro}</p>
    {/if}

    <ul class="grade-volumes">
      {#each volumes as linha (linha.volume.id)}
        <li
          class="volume"
          class:lido={linha.lido}
          class:salvando={salvando === linha.volume.id}
        >
          <button
            type="button"
            class="volume-botao"
            aria-pressed={linha.lido}
            aria-label={`${rotulo} ${linha.volume.numero_volume}: ${
              linha.lido ? 'lido' : 'não lido'
            }. Clique para alternar.`}
            onclick={() => alterar(linha, 'lido')}
          >
            <small>{rotulo}</small>
            <strong>{linha.volume.numero_volume}</strong>
            <span>{linha.lido ? '✓ LIDO' : '○ NÃO LIDO'}</span>
          </button>

          <button
            type="button"
            class="possuo"
            class:ativo={linha.possui_volume}
            aria-pressed={linha.possui_volume}
            onclick={() => alterar(linha, 'possui_volume')}
          >
            {linha.possui_volume ? '📚 TENHO' : 'NÃO TENHO'}
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</main>

<style>
  .pagina-checklist {
    width: min(100% - 40px, 1020px);
    margin: 28px auto 70px;
  }

  h1,
  h2,
  .chamada,
  .etiquetas span,
  .texto-progresso,
  .status,
  .volume strong,
  .volume small,
  .volume span,
  .possuo,
  .botao-comic {
    font-family: 'Bangers', Impact, sans-serif;
  }

  /* NAVEGAÇÃO */

  .trilha-navegacao {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
  }

  .trilha-navegacao a {
    font: 17px 'Bangers', Impact, sans-serif;
    border: 2px solid #292033;
    border-radius: 7px;
    padding: 7px 12px;
    box-shadow: 3px 3px #292033;
    background: #fff9f2;
    white-space: nowrap;
  }

  /* PAINÉIS */

  .painel,
  .estado {
    border: 3px solid #292033;
    border-radius: 12px;
    box-shadow: 6px 6px 0 #292033;
    background: #fff9f2;
  }

  .ficha {
    display: grid;
    grid-template-columns: 150px minmax(0, 1fr);
    gap: 24px;
    padding: 22px;
  }

  .capa {
    height: 215px;
    border: 3px solid #292033;
    border-radius: 7px;
    box-shadow: 4px 5px 0 #292033;
    background: #30273b;
    overflow: hidden;
  }

  .capa img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .sem-capa {
    height: 100%;
    display: grid;
    place-items: center;
    color: white;
    font: 18px 'Bangers', Impact, sans-serif;
  }

  .ficha-info {
    min-width: 0;
  }

  .chamada {
    margin: 0 0 4px;
    color: #ff456b;
    font-size: 14px;
    letter-spacing: 1px;
  }

  .ficha-info h1 {
    margin: 4px 0 12px;
    color: #823df0;
    font-size: clamp(34px, 5vw, 54px);
    line-height: 1;
    text-shadow: 4px 4px #ddc9eb;
    overflow-wrap: anywhere;
  }

  .etiquetas {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
  }

  .etiquetas span {
    padding: 4px 10px;
    border: 2px solid #292033;
    border-radius: 6px;
    box-shadow: 2px 2px #292033;
    font-size: 14px;
  }

  .et-roxa {
    background: #823cf2;
    color: white;
  }

  .et-azul {
    background: #05bff2;
  }

  .et-amarela {
    background: #ffda0d;
  }

  .linha-progresso {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
  }

  .texto-progresso {
    margin: 0;
    font-size: 18px;
    letter-spacing: 0.4px;
  }

  .texto-progresso b {
    color: #05bff2;
    font-weight: 400;
  }

  .texto-progresso b.roxo {
    color: #823cf2;
  }

  .status {
    flex-shrink: 0;
    padding: 4px 10px;
    border: 2px solid #292033;
    border-radius: 5px;
    box-shadow: 2px 2px #292033;
    font-size: 14px;
  }

  .barra {
    height: 18px;
    border: 3px solid #292033;
    border-radius: 6px;
    background: #ece6ee;
    overflow: hidden;
  }

  .barra div {
    height: 100%;
    background: #05bff2;
    transition: width 0.3s;
  }

  .contadores {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    margin: 8px 0 0;
    font-size: 12px;
    font-weight: 800;
  }

  .c-roxo {
    color: #823cf2;
  }

  .c-rosa {
    color: #ff456b;
  }

  .c-azul {
    color: #05a6d6;
  }

  /* LEGENDA */

  .legenda {
    margin-top: 26px;
    padding: 18px 22px;
  }

  .legenda h2 {
    margin: 0 0 14px;
    font-size: 26px;
  }

  .itens-legenda {
    display: flex;
    flex-wrap: wrap;
    gap: 14px 30px;
    font-size: 13px;
    font-weight: 700;
  }

  .itens-legenda div {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .amostra {
    width: 30px;
    height: 30px;
    border: 2px solid #292033;
    border-radius: 6px;
    box-shadow: 2px 2px #292033;
  }

  .amostra.roxo {
    background: #823cf2;
  }

  .amostra.cinza {
    background: #dcd8de;
  }

  .amostra.amarelo {
    background: #ffda0d;
  }

  /* VOLUMES */

  .titulo-secao {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 34px 0 16px;
  }

  .titulo-secao h2 {
    margin: 0;
    font-size: 34px;
    white-space: nowrap;
  }

  .titulo-secao .linha {
    flex: 1;
    height: 2px;
    background: #e1d8df;
  }

  .titulo-secao small {
    color: #a398a8;
    font: 13px 'Bangers', Impact, sans-serif;
    letter-spacing: 0.5px;
    text-align: right;
  }

  .grade-volumes {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
    gap: 14px;
  }

  .volume {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 0;
  }

  .volume.salvando {
    opacity: 0.6;
  }

  .volume-botao {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 8px 4px 7px;
    background: #dcd8de;
    color: #8b8390;
    border: 3px solid #8b8390;
    border-radius: 9px;
    box-shadow: 3px 4px 0 #8b8390;
    cursor: pointer;
    transition: transform 0.1s;
  }

  .volume-botao:hover {
    transform: translateY(-2px);
  }

  .volume.lido .volume-botao {
    background: #823cf2;
    color: white;
    border-color: #292033;
    box-shadow: 3px 4px 0 #292033;
  }

  .volume-botao small {
    font-size: 13px;
    letter-spacing: 1px;
    opacity: 0.85;
  }

  .volume-botao strong {
    font-size: 34px;
    line-height: 1;
    font-weight: 400;
  }

  .volume-botao span {
    margin-top: 4px;
    font-size: 12px;
    letter-spacing: 0.5px;
  }

  .possuo {
    padding: 4px 2px;
    background: #fff9f2;
    color: #8b8390;
    border: 2px solid #b8b0bc;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
  }

  .possuo.ativo {
    background: #ffda0d;
    color: #292033;
    border-color: #292033;
  }

  /* AVISOS */

  .feedback {
    margin: 0 0 16px;
    padding: 12px 15px;
    background: #ffe4e9;
    border: 2px solid #fb4269;
    border-radius: 8px;
  }

  .estado {
    padding: 40px 28px;
    text-align: center;
  }

  .estado h1 {
    margin: 0;
    color: #823cf2;
    font: 35px 'Bangers', Impact, sans-serif;
  }

  .estado p {
    margin: 15px auto 26px;
    max-width: 500px;
  }

  .botao-comic {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 42px;
    padding: 9px 16px;
    border: 3px solid #292033;
    border-radius: 8px;
    box-shadow: 4px 5px 0 #292033;
    font-size: 17px;
    text-decoration: none;
  }

  .botao-comic.azul {
    background: #02bffc;
  }

  @media (max-width: 680px) {
    .pagina-checklist {
      width: calc(100% - 28px);
    }

    .ficha {
      grid-template-columns: 1fr;
    }

    .capa {
      width: 150px;
      margin: 0 auto;
    }

    .linha-progresso {
      flex-direction: column;
      align-items: flex-start;
    }

    .titulo-secao small {
      display: none;
    }

    .grade-volumes {
      grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    }
  }
</style>
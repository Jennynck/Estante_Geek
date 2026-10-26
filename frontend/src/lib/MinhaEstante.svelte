<script>
  import { onMount } from 'svelte';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let perfil = $state(null);
  let itens = $state([]);

  let filtro = $state('TODOS');
  let carregando = $state(true);
  let autenticado = $state(false);

  let salvandoId = $state(null);
  let removendoId = $state(null);

  let erro = $state('');
  let aviso = $state('');

  const etiquetas = ['Quero Ler', 'Lendo', 'Lido', 'Pausado'];

  const filtros = ['TODOS', ...etiquetas];

  // RN07 - Regras de transição dos status.
  const transicoes = {
    'Quero Ler': ['Lendo'],
    'Lendo': ['Lido', 'Pausado'],
    'Pausado': ['Lendo', 'Lido'],
    'Lido': ['Lendo']
  };

  let itensFiltrados = $derived(
    filtro === 'TODOS'
      ? itens
      : itens.filter((item) => item.status === filtro)
  );

  // Redes sociais cadastradas no perfil.

  function semArroba(valor) {
    return String(valor || '').trim().replace(/^@+/, '');
  }

  let redes = $derived.by(() => {
    if (!perfil) return [];

    const lista = [];

    const instagram = semArroba(perfil.instagram);
    const discord = String(perfil.discord || '').trim();
    const x = semArroba(perfil.x);

    if (instagram) {
      lista.push({
        chave: 'instagram',
        icone: '📷',
        texto: `@${instagram}`,
        href: `https://instagram.com/${encodeURIComponent(instagram)}`
      });
    }

    if (discord) {
      lista.push({
        chave: 'discord',
        icone: '🎮',
        texto: discord,
        href: null
      });
    }

    if (x) {
      lista.push({
        chave: 'x',
        icone: '✕',
        texto: `@${x}`,
        href: `https://x.com/${encodeURIComponent(x)}`
      });
    }

    return lista;
  });

  function podeAlterar(atual, proximo) {
    return (
      atual === proximo ||
      (transicoes[atual] || []).includes(proximo)
    );
  }

  function quantidade(opcao) {
    if (opcao === 'TODOS') return itens.length;
    return itens.filter((item) => item.status === opcao).length;
  }

  function nomeDaEtiqueta(status) {
    return String(status || '').toUpperCase();
  }

  function porcentagem(item) {
    return Math.max(0, Math.min(100, Number(item.progresso) || 0));
  }

  function unidade(item) {
    return item.obra.tipo_obra === 'HQ' ? 'edições' : 'volumes';
  }

  async function carregar() {
    autenticado = Boolean(obterToken());

    erro = '';
    aviso = '';

    if (!autenticado) {
      carregando = false;
      return;
    }

    carregando = true;

    try {
      const dados = await requisicao('/estante');

      itens = Array.isArray(dados) ? dados : [];

      try {
        perfil = await requisicao('/usuarios/me');
      } catch {
        perfil = null;
      }
    } catch (falha) {
      erro = falha.message || 'Não foi possível carregar a estante.';
    } finally {
      carregando = false;
    }
  }

  async function alterarEtiqueta(item, evento) {
    const seletor = evento.currentTarget;

    const novoStatus = seletor.value;
    const statusAnterior = item.status;

    if (novoStatus === statusAnterior) return;

    if (!podeAlterar(statusAnterior, novoStatus)) {
      seletor.value = statusAnterior;

      erro =
        `Não é permitido mudar de ` +
        `"${statusAnterior}" para "${novoStatus}".`;

      return;
    }

    if (salvandoId !== null || removendoId !== null) {
      seletor.value = statusAnterior;
      return;
    }

    const obraId = item.obra.id;

    salvandoId = obraId;
    erro = '';
    aviso = '';

    try {
      const atualizado = await requisicao(`/estante/${obraId}`, {
        metodo: 'PATCH',
        dados: { status: novoStatus }
      });

      const statusSalvo = atualizado?.status || novoStatus;

      itens = itens.map((registro) =>
        registro.obra.id === obraId
          ? { ...registro, status: statusSalvo }
          : registro
      );

      if (statusAnterior === 'Lido' && novoStatus === 'Lendo') {
        aviso = `Releitura de "${item.obra.titulo}" iniciada!`;
      } else {
        aviso =
          `Status de "${item.obra.titulo}" ` +
          `alterado para "${statusSalvo}".`;
      }
    } catch (falha) {
      seletor.value = statusAnterior;

      erro = 'Não foi possível salvar o status: ' + falha.message;
    } finally {
      salvandoId = null;
    }
  }

  async function remover(obra) {
    if (salvandoId !== null || removendoId !== null) return;

    const confirmou = window.confirm(
      `Deseja remover "${obra.titulo}" da sua estante?`
    );

    if (!confirmou) return;

    removendoId = obra.id;

    erro = '';
    aviso = '';

    try {
      await requisicao(`/estante/${obra.id}`, { metodo: 'DELETE' });

      itens = itens.filter((item) => item.obra.id !== obra.id);

      aviso = `"${obra.titulo}" foi removida da estante.`;
    } catch (falha) {
      erro = falha.message;
    } finally {
      removendoId = null;
    }
  }

  onMount(() => {
    void carregar();
  });
</script>

<Cabecalho />

<main class="pagina-estante">

  <!-- Perfil do usuário -->

  {#if perfil}
    <section class="painel-perfil">
      <div class="avatar">
        {(perfil.nome_perfil ||
          perfil.nome_usuario ||
          'GE').slice(0, 2).toUpperCase()}
      </div>

      <div class="dados-perfil">
        <h2>
          {perfil.nome_perfil || perfil.nome_usuario || 'Colecionador'}
        </h2>

        {#if redes.length}
          <div class="redes" aria-label="Redes sociais">
            {#each redes as rede (rede.chave)}
              {#if rede.href}
                <a
                  class={`rede ${rede.chave}`}
                  href={rede.href}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span aria-hidden="true">{rede.icone}</span>
                  {rede.texto}
                </a>
              {:else}
                <span class={`rede ${rede.chave}`}>
                  <span aria-hidden="true">{rede.icone}</span>
                  {rede.texto}
                </span>
              {/if}
            {/each}
          </div>
        {:else}
          <p>✦ PERFIL DO COLECIONADOR</p>
        {/if}
      </div>
    </section>
  {/if}

  <p class="subtitulo">✦ SUA COLEÇÃO PESSOAL ✦</p>

  <h1>MINHA ESTANTE</h1>

  <p class="descricao">
    Organize seus mangás e HQs com um status de leitura por obra.
  </p>

  <div class="filtros-estante" aria-label="Filtrar por status">
    {#each filtros as opcao (opcao)}
      <button
        type="button"
        class:ativo={filtro === opcao}
        onclick={() => (filtro = opcao)}
      >
        {opcao.toUpperCase()}

        <span class="contador">{quantidade(opcao)}</span>
      </button>
    {/each}
  </div>

  {#if aviso}
    <p class="mensagem sucesso" role="status">{aviso}</p>
  {/if}

  {#if erro}
    <p class="mensagem falha" role="alert">{erro}</p>
  {/if}

  {#if carregando}
    <div class="estado-vazio">Carregando sua estante...</div>

  {:else if !autenticado}
    <div class="estado-vazio">
      <p>Faça login para visualizar sua estante.</p>

      <a class="botao-catalogo" href="/login">FAZER LOGIN</a>
    </div>

  {:else if itensFiltrados.length === 0}
    <div class="estado-vazio">
      <p>Nenhuma obra encontrada neste filtro.</p>

      <a class="botao-catalogo" href="/catalogo">EXPLORAR CATÁLOGO →</a>
    </div>

  {:else}
    <section class="grade-estante" aria-label="Obras da minha estante">

      {#each itensFiltrados as item (item.id)}
        <article
          class="cartao-estante"
          class:s-quero-ler={item.status === 'Quero Ler'}
          class:s-lendo={item.status === 'Lendo'}
          class:s-lido={item.status === 'Lido'}
          class:s-pausado={item.status === 'Pausado'}
        >

          <a
            class="capa-obra"
            href={`/obra/${item.obra.id}`}
            aria-label={`Ver detalhes de ${item.obra.titulo}`}
          >
            {#if item.obra.capa_url}
              <img
                src={item.obra.capa_url}
                alt={`Capa de ${item.obra.titulo}`}
                loading="lazy"
              />
            {:else}
              <div class="capa-ausente">CAPA INDISPONÍVEL</div>
            {/if}

            <span class="etiqueta-status">{nomeDaEtiqueta(item.status)}</span>

            <span
              class="tipo-obra"
              class:hq={item.obra.tipo_obra === 'HQ'}
            >
              {item.obra.tipo_obra === 'HQ' ? 'HQ' : 'MANGÁ'}
            </span>
          </a>

          <div class="conteudo-cartao">

            <h3>{item.obra.titulo}</h3>

            <p class="editora">
              {item.obra.editora || 'Editora não informada'}
            </p>

            <!-- Progresso -->

            <div class="progresso">
              <div class="progresso-linha">
                <span>PROGRESSO</span>
                <strong>{Math.round(porcentagem(item))}%</strong>
              </div>

              <div class="trilha">
                <div style:width={`${porcentagem(item)}%`}></div>
              </div>

              <small>
                {item.volumes_lidos ?? 0}/{item.obra.total_volumes ?? 0}
                {unidade(item)}
              </small>
            </div>

            <!-- Status de leitura -->

            <div class="area-status">
              <label for={`status-${item.obra.id}`}>✦ STATUS DA LEITURA</label>

              <select
                id={`status-${item.obra.id}`}
                class="seletor-status"
                class:quero-ler={item.status === 'Quero Ler'}
                class:lendo={item.status === 'Lendo'}
                class:lido={item.status === 'Lido'}
                class:pausado={item.status === 'Pausado'}
                value={item.status}
                disabled={salvandoId !== null || removendoId !== null}
                onchange={(evento) => alterarEtiqueta(item, evento)}
              >
                {#each etiquetas as etiqueta (etiqueta)}
                  <option
                    value={etiqueta}
                    disabled={!podeAlterar(item.status, etiqueta)}
                  >
                    {etiqueta === 'Lendo' && item.status === 'Lido'
                      ? 'LENDO — RELEITURA'
                      : nomeDaEtiqueta(etiqueta)}
                  </option>
                {/each}
              </select>

              {#if salvandoId === item.obra.id}
                <p class="salvando" role="status">Salvando status...</p>
              {/if}

              {#if item.status === 'Lido'}
                <p class="ajuda-status">Você pode iniciar uma releitura.</p>
              {/if}
            </div>

            <!-- Ações -->

            <div class="acoes-cartao">
              <a
                class="botao-checklist"
                href={`/obra/${item.obra.id}/checklist`}
              >
                ☑ VER CHECKLIST
              </a>

              <a class="ver-detalhes" href={`/obra/${item.obra.id}`}>
                VER DETALHES →
              </a>

              <button
                class="remover"
                type="button"
                disabled={removendoId !== null || salvandoId !== null}
                onclick={() => remover(item.obra)}
              >
                {removendoId === item.obra.id ? 'REMOVENDO...' : '🗑 REMOVER'}
              </button>
            </div>

          </div>
        </article>
      {/each}

    </section>
  {/if}

</main>

<style>
  .pagina-estante {
    width: min(100% - 40px, 1220px);
    margin: 32px auto 75px;
  }

  /* Perfil */

  .painel-perfil {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 16px 20px;
    margin-bottom: 25px;
    background: #fff9f2;
    border: 3px solid #292033;
    border-radius: 10px;
    box-shadow: 5px 5px #292033;
  }

  .avatar {
    width: 58px;
    height: 58px;
    display: grid;
    place-items: center;
    flex-shrink: 0;
    background: #823cf2;
    color: white;
    border: 3px solid #292033;
    border-radius: 50%;
    font: 25px 'Bangers', Impact, sans-serif;
  }

  .dados-perfil {
    min-width: 0;
  }

  .dados-perfil h2 {
    margin: 0;
    font: 27px 'Bangers', Impact, sans-serif;
    overflow-wrap: anywhere;
  }

  .dados-perfil p {
    margin: 4px 0 0;
    font-size: 11px;
    color: #94879b;
  }

  .redes {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 7px;
  }

  .rede {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border: 2px solid #292033;
    border-radius: 6px;
    box-shadow: 2px 2px #292033;
    color: white;
    font: 12px 'Nunito Sans', Arial, sans-serif;
    font-weight: 800;
    text-decoration: none;
    overflow-wrap: anywhere;
  }

  .rede.instagram {
    background: #ff416b;
  }

  .rede.discord {
    background: #6652ed;
  }

  .rede.x {
    background: #292033;
  }

  a.rede:hover {
    transform: translateY(-1px);
  }

  /* Título */

  .subtitulo {
    margin: 0;
    color: #ff426a;
    font: 18px 'Bangers', Impact, sans-serif;
  }

  h1 {
    margin: 5px 0 8px;
    color: #823cf2;
    text-shadow: 4px 4px #d8cae6;
    font: 58px 'Bangers', Impact, sans-serif;
  }

  .descricao {
    color: #8c7f96;
    font-size: 13px;
    margin: 0 0 24px;
  }

  /* Filtros */

  .filtros-estante {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 28px;
  }

  .filtros-estante button {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 18px;
    background: #fff9f2;
    border: 2px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    cursor: pointer;
    font: 19px 'Bangers', Impact, sans-serif;
  }

  .filtros-estante button.ativo {
    background: #ffda0d;
  }

  .contador {
    background: #e6e1e9;
    padding: 4px 7px;
    border-radius: 4px;
    font: 12px Arial, sans-serif;
  }

  /* Grade */

  .grade-estante {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 22px;
  }

  .cartao-estante {
    --cor: #05bff2;
    --cor-texto: #292033;

    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
    background: #fff9f2;
    border: 3px solid #292033;
    border-radius: 12px;
    box-shadow: 5px 6px #292033;
  }

  .cartao-estante.s-quero-ler {
    --cor: #823cf2;
    --cor-texto: white;
  }

  .cartao-estante.s-lendo {
    --cor: #05bff2;
    --cor-texto: #292033;
  }

  .cartao-estante.s-lido {
    --cor: #ff456b;
    --cor-texto: white;
  }

  .cartao-estante.s-pausado {
    --cor: #dac4ff;
    --cor-texto: #292033;
  }

  /* Capa */

  .capa-obra {
    display: block;
    width: 100%;
    height: 275px;
    position: relative;
    background: #e9dfed;
    overflow: hidden;
    border-bottom: 3px solid #292033;
  }

  .capa-obra img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .capa-ausente {
    display: grid;
    place-items: center;
    height: 100%;
    padding: 15px;
    text-align: center;
    font: 20px 'Bangers', Impact, sans-serif;
  }

  .etiqueta-status,
  .tipo-obra {
    position: absolute;
    top: 10px;
    padding: 4px 8px;
    border: 2px solid #292033;
    border-radius: 6px;
    box-shadow: 2px 2px #292033;
    font: 14px 'Bangers', Impact, sans-serif;
    color: #292033;
  }

  .etiqueta-status {
    left: 10px;
    background: #ffda0d;
  }

  .s-lendo .etiqueta-status {
    background: #08bdf0;
  }

  .s-lido .etiqueta-status {
    background: #b3e8c0;
  }

  .s-pausado .etiqueta-status {
    background: #dac4ff;
  }

  .tipo-obra {
    right: 10px;
    background: #00bdf3;
  }

  .tipo-obra.hq {
    background: #ff456e;
    color: white;
  }

  /* Informações */

  .conteudo-cartao {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 10px;
    padding: 13px;
  }

  .conteudo-cartao h3 {
    font: 23px/1.05 'Bangers', Impact, sans-serif;
    margin: 0;
    overflow-wrap: anywhere;
  }

  .editora {
    margin: 0;
    font-size: 12px;
    color: #978b9c;
  }

  /* Progresso */

  .progresso-linha {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
    font: 14px 'Bangers', Impact, sans-serif;
  }

  .progresso-linha strong {
    color: var(--cor);
    font-weight: 400;
  }

  .trilha {
    height: 12px;
    border: 2px solid #292033;
    border-radius: 6px;
    background: #ece6ee;
    overflow: hidden;
  }

  .trilha div {
    height: 100%;
    background: var(--cor);
    transition: width 0.3s;
  }

  .progresso small {
    display: block;
    margin-top: 3px;
    color: #978b9c;
    font-size: 11px;
  }

  /* Status */

  .area-status {
    padding-top: 12px;
    border-top: 1px solid #dfd3dd;
  }

  .area-status label {
    display: block;
    margin-bottom: 8px;
    color: #823cf2;
    font: 17px 'Bangers', Impact, sans-serif;
  }

  .seletor-status {
    width: 100%;
    min-height: 42px;
    padding: 9px 12px;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 3px #292033;
    color: #292033;
    font: 17px 'Bangers', Impact, sans-serif;
    cursor: pointer;
  }

  .seletor-status.quero-ler {
    background: #ffda0d;
  }

  .seletor-status.lendo {
    background: #08bdf0;
  }

  .seletor-status.lido {
    background: #b3e8c0;
  }

  .seletor-status.pausado {
    background: #dac4ff;
  }

  .seletor-status:disabled {
    opacity: 0.65;
    cursor: wait;
  }

  .ajuda-status,
  .salvando {
    margin: 8px 0 0;
    font-size: 11px;
    color: #766882;
  }

  /* Ações */

  .acoes-cartao {
    display: flex;
    flex-direction: column;
    gap: 9px;
    margin-top: auto;
    padding-top: 8px;
  }

  .botao-checklist {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 42px;
    padding: 9px 6px;
    background: var(--cor);
    color: var(--cor-texto);
    border: 3px solid #292033;
    border-radius: 8px;
    box-shadow: 3px 4px #292033;
    font: 17px 'Bangers', Impact, sans-serif;
    text-align: center;
  }

  .botao-checklist:hover {
    transform: translateY(-1px);
  }

  .ver-detalhes {
    align-self: flex-start;
    color: #823cf2;
    font: 15px 'Bangers', Impact, sans-serif;
    text-decoration: underline;
  }

  .remover {
    width: 100%;
    padding: 8px 10px;
    background: #fff9f2;
    color: #ff426a;
    border: 2px solid #ff426a;
    border-radius: 7px;
    cursor: pointer;
    font: 16px 'Bangers', Impact, sans-serif;
  }

  .remover:hover:not(:disabled) {
    background: #ffe0e7;
  }

  /* Mensagens */

  .mensagem {
    padding: 12px 15px;
    margin: 0 0 22px;
    border: 2px solid;
    border-radius: 8px;
  }

  .mensagem.sucesso {
    background: #efffea;
    border-color: #4fa66e;
  }

  .mensagem.falha {
    background: #ffe4e9;
    border-color: #ff426a;
  }

  .estado-vazio {
    padding: 35px;
    text-align: center;
    background: #fff9f2;
    border: 2px solid #292033;
    border-radius: 9px;
  }

  .botao-catalogo {
    display: inline-block;
    margin-top: 12px;
    padding: 10px 18px;
    background: #ffda0d;
    color: #292033;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 3px #292033;
    font: 19px 'Bangers', Impact, sans-serif;
    text-decoration: none;
  }

  /* Responsividade */

  @media (max-width: 1000px) {
    .grade-estante {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 760px) {
    .grade-estante {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 15px;
    }
  }

  @media (max-width: 480px) {
    .pagina-estante {
      width: calc(100% - 28px);
    }

    .grade-estante {
      grid-template-columns: 1fr;
    }

    .capa-obra {
      height: 330px;
    }

    h1 {
      font-size: 45px;
    }
  }
</style>
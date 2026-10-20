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

  // Etiquetas definidas no projeto.

  const etiquetas = [
    'Quero Ler',
    'Lendo',
    'Lido',
    'Pausado'
  ];

  const filtros = [
    'TODOS',
    ...etiquetas
  ];

  // RN07 - Regras de transição dos status.
  //
  // Quero Ler -> Lendo
  // Lendo -> Lido ou Pausado
  // Pausado -> Lendo ou Lido
  // Lido -> Lendo (releitura)

  const transicoes = {
    'Quero Ler': ['Lendo'],
    'Lendo': ['Lido', 'Pausado'],
    'Pausado': ['Lendo', 'Lido'],
    'Lido': ['Lendo']
  };

  // Filtrar obras por status.

  let itensFiltrados = $derived(
    filtro === 'TODOS'
      ? itens
      : itens.filter(
          (item) => item.status === filtro
        )
  );

  // Verificar se uma alteração é permitida.

  function podeAlterar(atual, proximo) {
    return (
      atual === proximo ||
      (transicoes[atual] || []).includes(proximo)
    );
  }

  // Contar obras em cada categoria.

  function quantidade(opcao) {
    if (opcao === 'TODOS') {
      return itens.length;
    }

    return itens.filter(
      (item) => item.status === opcao
    ).length;
  }

  function nomeDaEtiqueta(status) {
    return String(status || '').toUpperCase();
  }

  // Carregar perfil e estante.

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

      itens = Array.isArray(dados)
        ? dados
        : [];

      // Caso o perfil falhe, a estante continua.

      try {
        perfil = await requisicao('/usuarios/me');
      } catch {
        perfil = null;
      }

    } catch (falha) {
      erro =
        falha.message ||
        'Não foi possível carregar a estante.';

    } finally {
      carregando = false;
    }
  }

  // Alterar o status usando as regras RN07.

  async function alterarEtiqueta(item, evento) {
    const seletor = evento.currentTarget;

    const novoStatus = seletor.value;
    const statusAnterior = item.status;

    if (novoStatus === statusAnterior) {
      return;
    }

    // Não permite mudanças fora das regras.

    if (!podeAlterar(statusAnterior, novoStatus)) {
      seletor.value = statusAnterior;

      erro =
        `Não é permitido mudar de ` +
        `"${statusAnterior}" para "${novoStatus}".`;

      return;
    }

    // Evita alterações simultâneas.

    if (
      salvandoId !== null ||
      removendoId !== null
    ) {
      seletor.value = statusAnterior;
      return;
    }

    const obraId = item.obra.id;

    salvandoId = obraId;
    erro = '';
    aviso = '';

    try {
      const atualizado = await requisicao(
        `/estante/${obraId}`,
        {
          metodo: 'PATCH',
          dados: {
            status: novoStatus
          }
        }
      );

      const statusSalvo =
        atualizado?.status || novoStatus;

      // Atualiza os cards sem recarregar a página.

      itens = itens.map((registro) => {
        if (registro.obra.id === obraId) {
          return {
            ...registro,
            status: statusSalvo
          };
        }

        return registro;
      });

      // Mensagem específica para releitura.

      if (
        statusAnterior === 'Lido' &&
        novoStatus === 'Lendo'
      ) {
        aviso =
          `Releitura de "${item.obra.titulo}" iniciada!`;
      } else {
        aviso =
          `Status de "${item.obra.titulo}" ` +
          `alterado para "${statusSalvo}".`;
      }

    } catch (falha) {
      // Se o backend falhar, retorna ao status anterior.

      seletor.value = statusAnterior;

      erro =
        'Não foi possível salvar o status: ' +
        falha.message;

    } finally {
      salvandoId = null;
    }
  }

  // Remover uma obra da estante.

  async function remover(obra) {
    if (
      salvandoId !== null ||
      removendoId !== null
    ) {
      return;
    }

    const confirmou = window.confirm(
      `Deseja remover "${obra.titulo}" da sua estante?`
    );

    if (!confirmou) {
      return;
    }

    removendoId = obra.id;

    erro = '';
    aviso = '';

    try {
      await requisicao(
        `/estante/${obra.id}`,
        {
          metodo: 'DELETE'
        }
      );

      itens = itens.filter(
        (item) => item.obra.id !== obra.id
      );

      aviso =
        `"${obra.titulo}" foi removida da estante.`;

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
          {perfil.nome_perfil ||
            perfil.nome_usuario ||
            'Colecionador'}
        </h2>

        <p>
          ✦ PERFIL DO COLECIONADOR
        </p>

      </div>

    </section>

  {/if}

  <!-- Título da página -->

  <p class="subtitulo">
    ✦ SUA COLEÇÃO PESSOAL ✦
  </p>

  <h1>MINHA ESTANTE</h1>

  <p class="descricao">
    Organize seus mangás e HQs com um status
    de leitura por obra.
  </p>

  <!-- Filtros superiores -->

  <div
    class="filtros-estante"
    aria-label="Filtrar por status"
  >

    {#each filtros as opcao (opcao)}

      <button
        type="button"
        class:ativo={filtro === opcao}
        onclick={() => filtro = opcao}
      >

        {opcao.toUpperCase()}

        <span class="contador">
          {quantidade(opcao)}
        </span>

      </button>

    {/each}

  </div>

  <!-- Mensagens -->

  {#if aviso}

    <p
      class="mensagem sucesso"
      role="status"
    >
      {aviso}
    </p>

  {/if}

  {#if erro}

    <p
      class="mensagem falha"
      role="alert"
    >
      {erro}
    </p>

  {/if}

  <!-- Carregamento -->

  {#if carregando}

    <div class="estado-vazio">
      Carregando sua estante...
    </div>

  {:else if !autenticado}

    <div class="estado-vazio">

      <p>
        Faça login para visualizar sua estante.
      </p>

      <a
        class="botao-catalogo"
        href="/login"
      >
        FAZER LOGIN
      </a>

    </div>

  {:else if itensFiltrados.length === 0}

    <div class="estado-vazio">

      <p>
        Nenhuma obra encontrada neste filtro.
      </p>

      <a
        class="botao-catalogo"
        href="/catalogo"
      >
        EXPLORAR CATÁLOGO →
      </a>

    </div>

  {:else}

    <!-- Grade de obras -->

    <section
      class="grade-estante"
      aria-label="Obras da minha estante"
    >

      {#each itensFiltrados as item (item.id)}

        <article class="cartao-estante">

          <!-- Capa da obra -->

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

              <div class="capa-ausente">
                CAPA INDISPONÍVEL
              </div>

            {/if}

            <!-- Tipo da obra -->

            <span
              class="tipo-obra"
              class:hq={item.obra.tipo_obra === 'HQ'}
            >
              {item.obra.tipo_obra === 'HQ'
                ? 'HQ'
                : 'MANGÁ'}
            </span>

          </a>

          <!-- Informações -->

          <div class="conteudo-cartao">

            <h3>
              {item.obra.titulo}
            </h3>

            <p class="editora">
              {item.obra.editora ||
                'Editora não informada'}
            </p>

            <!-- Status de leitura -->

            <div class="area-status">

              <label for={`status-${item.obra.id}`}>
                ✦ STATUS DA LEITURA
              </label>

              <select
                id={`status-${item.obra.id}`}
                class="seletor-status"
                class:quero-ler={item.status === 'Quero Ler'}
                class:lendo={item.status === 'Lendo'}
                class:lido={item.status === 'Lido'}
                class:pausado={item.status === 'Pausado'}
                value={item.status}
                disabled={
                  salvandoId !== null ||
                  removendoId !== null
                }
                onchange={(evento) =>
                  alterarEtiqueta(item, evento)
                }
              >

                {#each etiquetas as etiqueta (etiqueta)}

                  <option
                    value={etiqueta}
                    disabled={
                      !podeAlterar(item.status, etiqueta)
                    }
                  >

                    {etiqueta === 'Lendo' &&
                    item.status === 'Lido'
                      ? 'LENDO — RELEITURA'
                      : nomeDaEtiqueta(etiqueta)}

                  </option>

                {/each}

              </select>

              {#if salvandoId === item.obra.id}

                <p
                  class="salvando"
                  role="status"
                >
                  Salvando status...
                </p>

              {/if}

              {#if item.status === 'Lido'}

                <p class="ajuda-status">
                  Você pode iniciar uma releitura.
                </p>

              {/if}

            </div>

            <!-- Ações inferiores -->

            <div class="acoes-cartao">

              <a
                class="ver-detalhes"
                href={`/obra/${item.obra.id}`}
              >
                VER DETALHES →
              </a>

              <button
                class="remover"
                type="button"
                disabled={
                  removendoId !== null ||
                  salvandoId !== null
                }
                onclick={() => remover(item.obra)}
              >
                {removendoId === item.obra.id
                  ? 'REMOVENDO...'
                  : 'REMOVER'}
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

  .dados-perfil h2 {
    margin: 0;
    font: 27px 'Bangers', Impact, sans-serif;
  }

  .dados-perfil p {
    margin: 4px 0 0;
    font-size: 11px;
    color: #94879b;
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

  /* Filtros superiores */

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
    grid-template-columns: repeat(
      4,
      minmax(0, 1fr)
    );
    gap: 22px;
  }

  .cartao-estante {
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
    background: #fff9f2;
    border: 3px solid #292033;
    border-radius: 12px;
    box-shadow: 5px 6px #292033;
  }

  /* Capa */

  .capa-obra {
    display: block;
    width: 100%;
    height: 275px;
    position: relative;
    background: #e9dfed;
    overflow: hidden;
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

  .tipo-obra {
    position: absolute;
    right: 10px;
    top: 10px;
    padding: 5px 9px;
    background: #00bdf3;
    border: 2px solid #292033;
    border-radius: 6px;
    box-shadow: 2px 2px #292033;
    color: #292033;
    font: 15px 'Bangers', Impact, sans-serif;
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

  /* Menu de seleção */

  .area-status {
    margin-top: 8px;
    padding-top: 13px;
    border-top: 1px solid #dfd3dd;
  }

  .area-status label {
    display: block;
    margin-bottom: 9px;
    color: #823cf2;
    font: 18px 'Bangers', Impact, sans-serif;
  }

  .seletor-status {
    width: 100%;
    min-height: 43px;
    padding: 10px 12px;
    border: 2px solid #292033;
    border-radius: 7px;
    box-shadow: 3px 3px #292033;
    color: #292033;
    font: 18px 'Bangers', Impact, sans-serif;
    cursor: pointer;
  }

  /* Cores das etiquetas */

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
    opacity: .65;
    cursor: wait;
  }

  .ajuda-status,
  .salvando {
    margin: 9px 0 0;
    font-size: 11px;
    color: #766882;
  }

  /* Botões inferiores */

  .acoes-cartao {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-top: auto;
    padding-top: 18px;
  }

  .ver-detalhes {
    color: #823cf2;
    font: 16px 'Bangers', Impact, sans-serif;
    text-decoration: underline;
  }

  .remover {
    padding: 7px 10px;
    background: #fff9f2;
    border: 2px solid #292033;
    border-radius: 6px;
    cursor: pointer;
    font: 15px 'Bangers', Impact, sans-serif;
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
      grid-template-columns: repeat(
        3,
        minmax(0, 1fr)
      );
    }
  }

  @media (max-width: 760px) {
    .grade-estante {
      grid-template-columns: repeat(
        2,
        minmax(0, 1fr)
      );
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
<script>
  import { onMount } from 'svelte';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import AvatarUsuario from '$lib/AvatarUsuario.svelte';
  import { obterToken, requisicao } from '$lib/api.js';
  import { montarRedes } from '$lib/contatos.js';

  const LIMITE = 12;
  const OBRAS_VISIVEIS = 4;

  let autenticado = $state(false);
  let leitores = $state([]);
  let pagina = $state(1);
  let temProxima = $state(false);
  let carregando = $state(true);
  let erro = $state('');
  let semEstante = $state(false);

  async function carregar(novaPagina = 1) {
    erro = '';
    semEstante = false;
    carregando = true;

    try {
      const dados = await requisicao(
        `/leitores?pagina=${novaPagina}&limite=${LIMITE}`
      );

      leitores = Array.isArray(dados) ? dados : [];
      pagina = novaPagina;
      temProxima = leitores.length === LIMITE;
    } catch (falha) {
      // O backend recusa quando a estante de quem consulta está vazia.
      if (falha.message.includes('Adicione pelo menos uma obra')) {
        semEstante = true;
      } else {
        erro = falha.message;
      }

      leitores = [];
      temProxima = false;
    } finally {
      carregando = false;
    }
  }

  function trocarPagina(novaPagina) {
    if (carregando || novaPagina < 1) return;

    carregar(novaPagina);

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function textoEmComum(total) {
    return `${total} ${total === 1 ? 'obra em comum' : 'obras em comum'}`;
  }

  onMount(() => {
    autenticado = Boolean(obterToken());

    if (!autenticado) {
      carregando = false;
      return;
    }

    carregar(1);
  });
</script>

<Cabecalho />

<main class="cm-pagina">
  <p class="cm-subtitulo">✦ LEITORES COM O SEU GOSTO ✦</p>

  <h1 class="cm-titulo">COMUNIDADE</h1>

  <p class="cm-descricao">
    Descubra leitores que têm obras em comum com a sua estante,
    do mais ao menos parecido.
  </p>

  {#if carregando}
    <div class="cm-estado" role="status">
      PROCURANDO LEITORES...
    </div>

  {:else if !autenticado}
    <div class="cm-estado">
      <h2>ENTRE PARA CONHECER A COMUNIDADE!</h2>

      <p>
        Faça login para descobrir leitores com gostos parecidos com os seus.
      </p>

      <a class="cm-botao azul" href="/login">FAZER LOGIN</a>
    </div>

  {:else if semEstante}
    <div class="cm-estado">
      <h2>SUA ESTANTE AINDA ESTÁ VAZIA</h2>

      <p>
        Adicione pelo menos uma obra à sua estante para descobrir
        leitores com o mesmo gosto.
      </p>

      <a class="cm-botao amarelo" href="/catalogo">EXPLORAR CATÁLOGO →</a>
    </div>

  {:else if erro}
    <p class="cm-aviso erro" role="alert">{erro}</p>

  {:else if leitores.length === 0}
    <div class="cm-estado">
      <h2>NENHUM LEITOR POR AQUI</h2>

      <p>
        {pagina > 1
          ? 'Não há mais leitores nesta página.'
          : 'Ainda não encontramos leitores com obras em comum com a sua estante. Adicione mais obras e volte aqui!'}
      </p>

      {#if pagina > 1}
        <button
          class="cm-botao claro"
          type="button"
          onclick={() => trocarPagina(pagina - 1)}
        >
          ← VOLTAR
        </button>
      {:else}
        <a class="cm-botao amarelo" href="/catalogo">EXPLORAR CATÁLOGO →</a>
      {/if}
    </div>

  {:else}
    <section class="cm-grade-leitores" aria-label="Leitores com obras em comum">
      {#each leitores as leitor (leitor.id)}
        {@const redes = montarRedes(leitor)}
        {@const obras = leitor.obras_em_comum || []}

        <article class="cm-leitor">
          <div class="cm-leitor-topo">
            <AvatarUsuario
              usuarioId={leitor.id}
              nome={leitor.nome_perfil}
              tamanho={58}
            />

            <div>
              <h3>{leitor.nome_perfil}</h3>

              <p class="cm-em-comum">
                ★ {textoEmComum(leitor.total_em_comum)}
              </p>

              {#if leitor.perfil_publico === false}
                <span class="cm-selo">PERFIL PRIVADO</span>
              {/if}
            </div>
          </div>

          {#if obras.length}
            <div class="cm-chips" aria-label="Obras em comum">
              {#each obras.slice(0, OBRAS_VISIVEIS) as titulo (titulo)}
                <span class="cm-chip" title={titulo}>{titulo}</span>
              {/each}

              {#if obras.length > OBRAS_VISIVEIS}
                <span class="cm-chip mais">
                  +{obras.length - OBRAS_VISIVEIS}
                </span>
              {/if}
            </div>
          {/if}

          {#if redes.length}
            <div class="cm-redes" aria-label="Redes sociais">
              {#each redes as rede (rede.chave)}
                {#if rede.href}
                  <a
                    class={`cm-rede ${rede.chave}`}
                    href={rede.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <span aria-hidden="true">{rede.icone}</span>
                    {rede.texto}
                  </a>
                {:else}
                  <span class={`cm-rede ${rede.chave}`}>
                    <span aria-hidden="true">{rede.icone}</span>
                    {rede.texto}
                  </span>
                {/if}
              {/each}
            </div>
          {/if}

          <a class="cm-botao azul" href={`/perfil/${leitor.id}`}>
            VER PERFIL →
          </a>
        </article>
      {/each}
    </section>

    {#if pagina > 1 || temProxima}
      <nav class="cm-paginacao" aria-label="Navegação pelas páginas">
        <button
          class="cm-botao amarelo"
          type="button"
          disabled={pagina <= 1 || carregando}
          onclick={() => trocarPagina(pagina - 1)}
        >
          ← ANTERIOR
        </button>

        <span>PÁGINA {pagina}</span>

        <button
          class="cm-botao amarelo"
          type="button"
          disabled={!temProxima || carregando}
          onclick={() => trocarPagina(pagina + 1)}
        >
          PRÓXIMA →
        </button>
      </nav>
    {/if}
  {/if}
</main>
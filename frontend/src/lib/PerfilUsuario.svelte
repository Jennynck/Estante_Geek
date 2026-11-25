<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import AvatarUsuario from '$lib/AvatarUsuario.svelte';
  import { obterToken, requisicao } from '$lib/api.js';
  import { montarRedes } from '$lib/contatos.js';
  import { unidadeObra } from '$lib/rotulos.js';

  let { id } = $props();

  let autenticado = $state(false);
  let carregando = $state(true);

  let perfil = $state(null);
  let itens = $state([]);
  let emComum = $state([]);

  let privada = $state(false);
  let aba = $state('estante');

  let erro = $state('');
  let aviso = $state('');

  let redes = $derived(montarRedes(perfil));

  function corStatus(status) {
    const cores = {
      'Quero Ler': '#ffda0d',
      'Lendo': '#08bdf0',
      'Lido': '#b3e8c0',
      'Pausado': '#dac4ff'
    };

    return cores[status] || '#08bdf0';
  }

  function porcentagem(item) {
    return Math.max(0, Math.min(100, Number(item.progresso) || 0));
  }

  async function carregar() {
    autenticado = Boolean(obterToken());

    if (!autenticado) {
      carregando = false;
      return;
    }

    try {
      // O próprio perfil é a Minha Estante.
      const eu = await requisicao('/usuarios/me');

      if (Number(eu.id) === Number(id)) {
        await goto('/minha-estante', { replaceState: true });
        return;
      }

      const idSeguro = encodeURIComponent(id);

      perfil = await requisicao(`/usuarios/${idSeguro}`);
      privada = perfil.perfil_publico === false;

      // A estante de perfil privado devolve 403, então nem pedimos.
      const [estante, comum] = await Promise.allSettled([
        privada
          ? Promise.resolve([])
          : requisicao(`/usuarios/${idSeguro}/estante`),
        requisicao(`/usuarios/${idSeguro}/obras-em-comum`)
      ]);

      if (estante.status === 'fulfilled') {
        itens = Array.isArray(estante.value) ? estante.value : [];
      } else {
        aviso = estante.reason?.message || 'Não foi possível carregar a estante.';
      }

      if (comum.status === 'fulfilled') {
        emComum = Array.isArray(comum.value) ? comum.value : [];
      } else {
        aviso = comum.reason?.message || 'Não foi possível carregar as obras em comum.';
      }

      if (privada) aba = 'comum';
    } catch (falha) {
      erro = falha.message;
    } finally {
      carregando = false;
    }
  }

  onMount(carregar);
</script>

{#snippet cartao(obra, item)}
  <article class="cm-obra">
    <a
      class="cm-obra-capa"
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
        <span>CAPA INDISPONÍVEL</span>
      {/if}

      <span class="cm-tag" class:hq={obra.tipo_obra === 'HQ'}>
        {obra.tipo_obra === 'HQ' ? 'HQ' : 'MANGÁ'}
      </span>

      {#if item}
        <span
          class="cm-status"
          style:background={corStatus(item.status)}
        >
          {String(item.status).toUpperCase()}
        </span>
      {/if}
    </a>

    <div class="cm-obra-info">
      <h3>{obra.titulo}</h3>

      <p>{obra.editora || 'Editora não informada'}</p>

      {#if item}
        <div>
          <div class="cm-progresso">
            <span>PROGRESSO</span>
            <span>{Math.round(porcentagem(item))}%</span>
          </div>

          <div class="cm-trilha">
            <div style:width={`${porcentagem(item)}%`}></div>
          </div>
        </div>

        <p>
          {item.volumes_lidos ?? 0}/{obra.total_volumes ?? 0}
          {unidadeObra(obra.tipo_obra, obra.total_volumes)}
        </p>

        {#if item.nota}
          <p class="cm-nota">
            ★ {(item.nota / 2).toLocaleString('pt-BR')}/5
          </p>
        {/if}

        {#if item.resenha}
          <p class="cm-resenha">“{item.resenha}”</p>
        {/if}
      {/if}

      {#if obra.na_estante}
        <span class="cm-selo ok">✓ NA SUA ESTANTE</span>
      {/if}

      <a class="cm-link" href={`/obra/${obra.id}`}>VER DETALHES →</a>
    </div>
  </article>
{/snippet}

<Cabecalho />

<main class="cm-pagina">
  <div class="cm-voltar">
    <a class="cm-botao" href="/comunidade">← COMUNIDADE</a>
  </div>

  {#if carregando}
    <div class="cm-estado" role="status">
      CARREGANDO PERFIL...
    </div>

  {:else if !autenticado}
    <div class="cm-estado">
      <h2>FAÇA LOGIN!</h2>

      <p>Entre na sua conta para ver o perfil dos outros leitores.</p>

      <a class="cm-botao azul" href="/login">FAZER LOGIN</a>
    </div>

  {:else if !perfil}
    <div class="cm-estado" role="alert">
      <h2>PERFIL INDISPONÍVEL</h2>

      <p>{erro || 'Não foi possível carregar este perfil.'}</p>

      <a class="cm-botao azul" href="/comunidade">VOLTAR À COMUNIDADE</a>
    </div>

  {:else}
    <!-- CABEÇALHO DO PERFIL -->

    <section class="cm-perfil">
      <AvatarUsuario
        usuarioId={perfil.id}
        nome={perfil.nome_perfil}
        tamanho={84}
      />

      <div class="cm-perfil-info">
        <h1>{perfil.nome_perfil}</h1>

        {#if privada}
          <span class="cm-selo">PERFIL PRIVADO</span>
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
      </div>
    </section>

    {#if privada}
      <p class="cm-aviso" role="status">
        Este perfil é privado. Você só pode ver as obras em comum.
      </p>
    {/if}

    {#if aviso}
      <p class="cm-aviso erro" role="alert">{aviso}</p>
    {/if}

    <!-- ABAS -->

    <div class="cm-abas" role="tablist">
      <button
        type="button"
        role="tab"
        aria-selected={aba === 'estante'}
        class:ativa={aba === 'estante'}
        disabled={privada}
        onclick={() => (aba = 'estante')}
      >
        ESTANTE ({itens.length})
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={aba === 'comum'}
        class:ativa={aba === 'comum'}
        onclick={() => (aba = 'comum')}
      >
        OBRAS EM COMUM ({emComum.length})
      </button>
    </div>

    <!-- CONTEÚDO -->

    {#if aba === 'estante'}
      {#if itens.length === 0}
        <div class="cm-estado">
          <p>Este leitor ainda não adicionou obras à estante.</p>
        </div>
      {:else}
        <section class="cm-grade-obras" aria-label="Estante do leitor">
          {#each itens as item (item.id)}
            {@render cartao(item.obra, item)}
          {/each}
        </section>
      {/if}

    {:else}
      {#if emComum.length === 0}
        <div class="cm-estado">
          <p>Vocês ainda não têm obras em comum.</p>
        </div>
      {:else}
        <section class="cm-grade-obras" aria-label="Obras em comum">
          {#each emComum as obra (obra.id)}
            {@render cartao(obra, null)}
          {/each}
        </section>
      {/if}
    {/if}
  {/if}
</main>
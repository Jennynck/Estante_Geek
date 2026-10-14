<script>
  import { onMount } from 'svelte';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import CartaoObra from '$lib/CartaoObra.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let perfil = $state(null);
  let itens = $state([]);
  let filtro = $state('TODOS');
  let carregando = $state(false);
  let erro = $state('');
  let aviso = $state('');
  const filtros = ['TODOS', 'QUERO LER', 'LENDO', 'LIDO', 'PAUSADO'];
  let itensFiltrados = $derived(filtro === 'TODOS' ? itens : itens.filter((item) => item.status.toUpperCase() === filtro));

  async function carregar() {
    if (!obterToken()) { erro = 'Faça login para acessar a sua estante.'; return; }
    carregando = true;
    erro = '';
    try {
      [perfil, itens] = await Promise.all([requisicao('/usuarios/me'), requisicao('/estante')]);
    } catch (falha) { erro = falha.message; }
    finally { carregando = false; }
  }
  async function remover(obras_id) {
    aviso = '';
    erro = '';
    if (!confirm('Deseja realmente remover esta obra da estante?')) return;
    try {
      await requisicao(`/estante/${obras_id}`, { metodo: 'DELETE' });
      itens = itens.filter((item) => item.obra.id !== obras_id);
      aviso = 'Obra removida da estante.';
    } catch (falha) { erro = falha.message; }
  }
  function quantidade(opcao) {
    return opcao === 'TODOS' ? itens.length : itens.filter((item) => item.status.toUpperCase() === opcao).length;
  }
  onMount(() => { carregar(); });
</script>

<Cabecalho />
<main class="area-conteudo pagina-estante">
  {#if perfil}
    <section class="painel-perfil">
      <div class="avatar">{perfil.nome_perfil.slice(0, 2).toUpperCase()}</div>
      <div class="painel-perfil__informacoes"><h2>{perfil.nome_perfil}</h2><div class="chips-perfil">{#if perfil.instagram}<span>▣ {perfil.instagram}</span>{/if}{#if perfil.discord}<span>♬ {perfil.discord}</span>{/if}{#if perfil.x}<span>𝕏 {perfil.x}</span>{/if}</div></div>
      <span class="etiqueta-perfil">PERFIL DO COLECIONADOR</span>
    </section>
  {/if}
  <p class="subtitulo-pagina">✦ SUA COLEÇÃO PESSOAL ✦</p>
  <h1 class="titulo-pagina">MINHA ESTANTE</h1>
  <div class="abas abas-estante">{#each filtros as opcao}<button class:ativa={filtro === opcao} onclick={() => filtro = opcao}>{opcao} <span class="contador">{quantidade(opcao)}</span></button>{/each}</div>
  {#if aviso}<p class="mensagem sucesso" role="status">{aviso}</p>{/if}
  {#if erro}<div class="estado-vazio erro" role="alert">{erro} {#if !obterToken()}<a class="botao azul" href="/login">FAZER LOGIN</a>{/if}</div>{/if}
  {#if carregando}<p class="estado-vazio">Carregando sua estante...</p>{:else if !erro && itensFiltrados.length === 0}<div class="estado-vazio">Sua estante está vazia neste filtro. <a href="/catalogo">Conhecer o catálogo →</a></div>{:else if !erro}<div class="grade-obras">{#each itensFiltrados as item (item.id)}<CartaoObra obra={item.obra} status={item.status} progresso={item.progresso} {remover} />{/each}</div>{/if}
</main>

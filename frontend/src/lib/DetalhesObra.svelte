<script>
  import { onMount } from 'svelte';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import { obterToken, requisicao } from '$lib/api.js';

  let { id } = $props();
  let obra = $state(null);
  let checklist = $state(null);
  let erro = $state('');
  let aviso = $state('');
  let carregando = $state(true);
  let processando = $state(false);

  async function carregar() {
    carregando = true;
    erro = '';
    if (!obterToken()) {
      erro = 'O backend atual exige login para ver os detalhes das obras.';
      carregando = false;
      return;
    }
    try {
      obra = await requisicao(`/obras/${id}`);
      try { checklist = await requisicao(`/estante/${id}/checklist`); }
      catch { checklist = null; }
    } catch (falha) { erro = falha.message; }
    finally { carregando = false; }
  }
  async function adicionar() {
    processando = true;
    erro = '';
    try {
      await requisicao('/estante', { metodo: 'POST', dados: { obras_id: obra.id } });
      aviso = 'Obra adicionada à sua estante!';
      checklist = await requisicao(`/estante/${obra.id}/checklist`);
    } catch (falha) { erro = falha.message; }
    finally { processando = false; }
  }
  async function alterarVolume(volume_id, possui_volume, status_leitura) {
    erro = '';
    try {
      await requisicao(`/estante/${obra.id}/volumes/${volume_id}`, {
        metodo: 'PATCH', dados: { possui_volume, status_leitura }
      });
      checklist = await requisicao(`/estante/${obra.id}/checklist`);
    } catch (falha) { erro = falha.message; }
  }
  onMount(() => { carregar(); });
</script>

<Cabecalho />
<main class="area-conteudo pagina-detalhes">
  <a class="botao pequeno contorno voltar" href="/catalogo">← CATÁLOGO</a>
  {#if carregando}<p class="estado-vazio">Carregando informações...</p>{:else if erro && !obra}<div class="estado-vazio erro">{erro} <a href="/login">Fazer login</a></div>{:else if obra}
    <section class="painel-detalhes">
      <div class="coluna-capa"><div class="capa-detalhes">{#if obra.capa_url}<img src={obra.capa_url} alt={`Capa de ${obra.titulo}`} />{:else}<div class="capa-sem-imagem">{obra.titulo}</div>{/if}</div>
        {#if checklist}<div class="botao amarelo largura-total desabilitado">✓ NA MINHA ESTANTE</div>{:else}<button class="botao rosa largura-total" disabled={processando} onclick={adicionar}>✦ ADICIONAR À ESTANTE</button>{/if}
      </div>
      <div class="dados-detalhes"><p class="subtitulo-pagina">✦ {obra.tipo_obra === 'HQ' ? 'HQ' : 'MANGÁ'} ✦</p><h1 class="titulo-pagina">{obra.titulo}</h1><p class="detalhes-editora">{obra.editora || 'Editora não informada'} · {obra.total_volumes} volumes</p>
        {#if obra.generos?.length}<div class="tags">{#each obra.generos as genero}<span>{genero}</span>{/each}</div>{/if}
        <div class="detalhes-indicadores"><div class="indicador azul">{checklist?.status || '—'}<small>Status</small></div><div class="indicador amarelo">{obra.total_volumes}<small>Volumes</small></div><div class="indicador violeta">{obra.media_notas === null || obra.media_notas === undefined ? '—' : obra.media_notas.toFixed(1)}<small>Nota média</small></div></div>
      </div>
    </section>
    <section class="painel-texto"><h2>SINOPSE</h2><p>{obra.sinopse || 'Sinopse não disponível para esta obra.'}</p></section>
    {#if checklist}<section class="painel-texto"><h2>CHECKLIST DE VOLUMES</h2><p>{checklist.possuidos} de {checklist.total_volumes} volumes na sua coleção · {checklist.progresso.toFixed(0)}% lidos</p>
      <div class="grade-checklist">{#each checklist.volumes as item (item.volume.id)}<div class="volume"><strong>Volume {item.volume.numero_volume}</strong><label><input type="checkbox" checked={item.possui_volume} onchange={(evento) => alterarVolume(item.volume.id, evento.currentTarget.checked, null)} /> Possuo este volume</label><span>Status: {item.status_leitura}</span><div class="acoes-volume">{#each ({'Quero Ler':['Lendo'], 'Lendo':['Lido','Pausado'], 'Pausado':['Lendo','Lido'], 'Lido':['Lendo']}[item.status_leitura] || []) as opcao}<button onclick={() => alterarVolume(item.volume.id, null, opcao)}>{opcao}</button>{/each}</div></div>{/each}</div>
    </section>{/if}
    {#if aviso}<p class="mensagem sucesso">{aviso}</p>{/if}
    {#if erro}<p class="mensagem erro" role="alert">{erro}</p>{/if}
  {/if}
</main>

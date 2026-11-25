<script>
  import { buscarFoto } from '$lib/api.js';

  // usuarioId: número do usuário, ou 'me' para a própria foto.
  // versao: mude o valor para forçar o recarregamento (ex.: depois de trocar a foto).
  let { usuarioId, nome = '', tamanho = 56, versao = 0 } = $props();

  let url = $state(null);

  const cores = ['#823cf2', '#ff456b', '#05bff2'];

  let cor = $derived(
    typeof usuarioId === 'number'
      ? cores[usuarioId % cores.length]
      : cores[0]
  );

  let iniciais = $derived(
    String(nome || '?').trim().slice(0, 2).toUpperCase()
  );

  $effect(() => {
    const caminho =
      usuarioId === 'me'
        ? '/usuarios/me/foto'
        : `/usuarios/${usuarioId}/foto`;

    void versao;

    let ativo = true;
    let criada = null;

    url = null;

    buscarFoto(caminho).then((resultado) => {
      if (!ativo) {
        if (resultado) URL.revokeObjectURL(resultado);
        return;
      }

      criada = resultado;
      url = resultado;
    });

    return () => {
      ativo = false;
      if (criada) URL.revokeObjectURL(criada);
    };
  });
</script>

<div
  class="cm-avatar"
  style:width={`${tamanho}px`}
  style:height={`${tamanho}px`}
  style:background={cor}
  style:font-size={`${Math.round(tamanho * 0.4)}px`}
>
  {#if url}
    <img src={url} alt={`Foto de ${nome}`} />
  {:else}
    <span aria-hidden="true">{iniciais}</span>
  {/if}
</div>
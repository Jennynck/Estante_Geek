<script>
  import { page } from '$app/state';
  import DetalhesObra from '$lib/DetalhesObra.svelte';
</script>

{#key page.params.id}
  <DetalhesObra id={page.params.id} />
{/key}

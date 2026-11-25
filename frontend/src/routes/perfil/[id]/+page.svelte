<script>
  import { page } from '$app/state';
  import PerfilUsuario from '$lib/PerfilUsuario.svelte';
</script>

{#key page.params.id}
  <PerfilUsuario id={page.params.id} />
{/key}
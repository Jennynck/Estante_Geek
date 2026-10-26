<script>
  import { page } from '$app/state';
  import ChecklistObra from '$lib/ChecklistObra.svelte';
</script>

{#key page.params.id}
  <ChecklistObra id={page.params.id} />
{/key}
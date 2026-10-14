
<script>
  import Cabecalho from '$lib/Cabecalho.svelte';
</script>

<Cabecalho />

<main class="comunidade">
  <h1>COMUNIDADE</h1>

  <p>
    Esta área será desenvolvida em uma próxima etapa
    do Estante Geek.
  </p>

  <a href="/">← VOLTAR AO CATÁLOGO</a>
</main>

<style>
  .comunidade {
    max-width: 1100px;
    margin: 45px auto;
    padding: 0 22px;
  }

  h1 {
    color: #813cf2;
    font: 54px 'Bangers', Impact, sans-serif;
    margin: 0 0 14px;
  }

  p {
    color: #61526d;
    font-size: 16px;
  }

  a {
    display: inline-block;
    margin-top: 15px;
    color: #813cf2;
    font: 21px 'Bangers', Impact, sans-serif;
    text-decoration: underline;
  }
</style>

<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { requisicao } from '$lib/api.js';

  let carregando = $state(true);
  let erro = $state('');
  let sucesso = $state('');

  onMount(async () => {
    const token = page.url.searchParams.get('token');

    if (!token) {
      erro = 'Link de confirmação inválido.';
      carregando = false;
      return;
    }

    try {
      const resposta = await requisicao('/auth/confirmar-email', {
        metodo: 'POST',
        autenticar: false,
        dados: { token }
      });

      sucesso = resposta.mensagem;
    } catch (falha) {
      erro = falha.message;
    } finally {
      carregando = false;
    }
  });
</script>

<main class="pagina-autenticacao">
  <a class="marca marca-grande" href="/catalogo">
    <span>ESTANTE</span> GEEK
  </a>

  <section class="painel-autenticacao">
    <div class="painel-autenticacao__conteudo">
      <h1>Confirmação de e-mail</h1>

      {#if carregando}
        <p class="descricao-autenticacao" role="status">
          Confirmando seu e-mail...
        </p>
      {:else if sucesso}
        <p class="mensagem sucesso" role="status">{sucesso}</p>

        <a class="botao rosa principal largura-total" href="/login">
          ✦ IR PARA O LOGIN ✦
        </a>
      {:else}
        <p class="mensagem erro" role="alert">{erro}</p>

        <p class="descricao-autenticacao">
          Tente entrar com seu e-mail e senha: se a conta ainda estiver
          pendente, você poderá pedir um novo link.
        </p>

        <a class="botao azul largura-total" href="/login">VOLTAR AO LOGIN</a>
      {/if}
    </div>
  </section>
</main>
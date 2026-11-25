<script>
  import { requisicao } from '$lib/api.js';

  let email = $state('');
  let carregando = $state(false);
  let erro = $state('');
  let sucesso = $state('');

  async function enviar(evento) {
    evento.preventDefault();

    erro = '';
    sucesso = '';
    carregando = true;

    try {
      const resposta = await requisicao('/auth/esqueci-senha', {
        metodo: 'POST',
        autenticar: false,
        dados: { email: email.trim() }
      });

      sucesso = resposta.mensagem;
    } catch (falha) {
      erro = falha.message;
    } finally {
      carregando = false;
    }
  }
</script>

<main class="pagina-autenticacao">
  <a class="marca marca-grande" href="/catalogo">
    <span>ESTANTE</span> GEEK
  </a>

  <section class="painel-autenticacao">
    <div class="painel-autenticacao__conteudo">
      <h1>Esqueceu a senha?</h1>

      <p class="descricao-autenticacao">
        Informe o e-mail da sua conta e enviaremos um link para
        criar uma nova senha.
      </p>

      <form onsubmit={enviar}>
        <label for="esqueci-email">E-MAIL</label>

        <input
          id="esqueci-email"
          type="email"
          bind:value={email}
          placeholder="seu@email.com"
          autocomplete="email"
          required
        />

        {#if erro}
          <p class="mensagem erro" role="alert">{erro}</p>
        {/if}

        {#if sucesso}
          <p class="mensagem sucesso" role="status">{sucesso}</p>
        {/if}

        <button
          type="submit"
          disabled={carregando}
          class="botao rosa principal largura-total"
        >
          ✦ {carregando ? 'ENVIANDO...' : 'ENVIAR LINK'} ✦
        </button>
      </form>
    </div>

    <div class="painel-autenticacao__rodape">
      Lembrou a senha?
      <a href="/login" class="texto-azul">VOLTAR AO LOGIN</a>
    </div>
  </section>

  <p class="rodape-logo">★ ESTANTE GEEK ★</p>
</main>
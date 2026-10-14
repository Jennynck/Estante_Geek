
<script>
  import { guardarToken, requisicao } from '$lib/api.js';
  import { goto } from '$app/navigation';

  let email = $state('');
  let senha = $state('');
  let mostrarSenha = $state(false);
  let carregando = $state(false);
  let erro = $state('');

  async function entrar(evento) {
    evento.preventDefault();

    erro = '';
    carregando = true;

    try {
      const resposta = await requisicao('/auth/login', {
        metodo: 'POST',
        autenticar: false,
        dados: {
          email: email.trim(),
          senha
        }
      });

      guardarToken(resposta.access_token);

      await goto('/minha-estante');
    } catch (falha) {
      erro = falha.message;
    } finally {
      carregando = false;
    }
  }
</script>

<main class="pagina-autenticacao login">
  <a class="marca marca-grande" href="/catalogo">
    <span>ESTANTE</span> GEEK
  </a>

  <div class="baloon">
    Faça login para acessar o seu acervo!
  </div>

  <section class="painel-autenticacao">
    <div class="painel-autenticacao__conteudo">
      <h1>Acesse sua conta na Estante Geek</h1>

      <p class="descricao-autenticacao">
        Bem-vindo de volta, colecionador!
      </p>

      <form onsubmit={entrar}>
        <label for="login-email">E-MAIL</label>

        <input
          id="login-email"
          type="email"
          bind:value={email}
          placeholder="seu@email.com"
          autocomplete="email"
          required
        />

        <label for="login-senha">SENHA</label>

        <div class="campo-com-icone">
          <input
            id="login-senha"
            type={mostrarSenha ? 'text' : 'password'}
            bind:value={senha}
            placeholder="Sua senha secreta"
            autocomplete="current-password"
            required
          />

          <button
            type="button"
            class="icone-senha"
            aria-label="Mostrar ou ocultar senha"
            onclick={() => mostrarSenha = !mostrarSenha}
          >
            {mostrarSenha ? '🙈' : '👁'}
          </button>
        </div>

        <div class="ajuda-login">
          <span title="Requer rota de recuperação no backend">
            Esqueceu a senha? (em breve)
          </span>
        </div>

        {#if erro}
          <p class="mensagem erro" role="alert">
            {erro}
          </p>
        {/if}

        <button
          type="submit"
          disabled={carregando}
          class="botao rosa principal largura-total"
        >
          ✦ {carregando ? 'ENTRANDO...' : 'ENTRAR'} ✦
        </button>

        <p class="observacao-login">
          Acesse sua estante e continue de onde parou
        </p>
      </form>
    </div>

    <div class="painel-autenticacao__rodape">
      Ainda não tem conta?
      <a href="/cadastro" class="texto-azul">CADASTRE-SE</a>
    </div>
  </section>

  <p class="rodape-logo">★ ESTANTE GEEK ★</p>
</main>

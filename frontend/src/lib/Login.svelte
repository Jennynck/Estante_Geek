
<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { guardarToken, requisicao } from '$lib/api.js';

  const CHAVE_EMAIL_PENDENTE =
    'estante_geek_email_pendente';

  let email = $state('');
  let senha = $state('');
  let mostrarSenha = $state(false);
  let carregando = $state(false);

  let erro = $state('');
  let aviso = $state('');
  let precisaConfirmar = $state(false);

  let cadastroRecente = $state(false);
  let sessaoExpirada = $state(false);

  let temporizadorErro;
  let temporizadorAviso;

  function mostrarErro(mensagem) {
    clearTimeout(temporizadorErro);

    const texto = String(mensagem || '');

    erro =
      /conta.*bloquead|bloquead.*conta/i.test(texto)
        ? 'Sua conta foi bloqueada porque você infringiu as regras da plataforma.'
        : texto;

    temporizadorErro = setTimeout(() => {
      erro = '';
    }, 5500);
  }

  function mostrarAviso(mensagem) {
    clearTimeout(temporizadorAviso);

    aviso = mensagem;

    temporizadorAviso = setTimeout(() => {
      aviso = '';
    }, 5500);
  }

  onMount(() => {
    const parametros = page.url.searchParams;

    // Identifica o redirecionamento após sessão expirada.
    sessaoExpirada =
      parametros.get('sessao') === 'expirada';

    // Preserva o comportamento após criar uma conta.
    if (parametros.get('cadastro') === 'ok') {
      cadastroRecente = true;

      try {
        const guardado = sessionStorage.getItem(
          CHAVE_EMAIL_PENDENTE
        );

        if (guardado) {
          email = guardado;

          sessionStorage.removeItem(
            CHAVE_EMAIL_PENDENTE
          );
        }
      } catch {
        // O login funciona mesmo sem sessionStorage.
      }
    }

    return () => {
      clearTimeout(temporizadorErro);
      clearTimeout(temporizadorAviso);
    };
  });

  async function entrar(evento) {
    evento.preventDefault();

    erro = '';
    aviso = '';
    precisaConfirmar = false;
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

      sessaoExpirada = false;
      cadastroRecente = false;

      await goto('/minha-estante');
    } catch (falha) {
      mostrarErro(falha.message);

      precisaConfirmar = /confirme seu e-mail/i.test(
        falha.message
      );
    } finally {
      carregando = false;
    }
  }

  async function reenviar() {
    erro = '';
    aviso = '';

    if (!email.trim()) {
      mostrarErro(
        'Informe o e-mail para reenviar o link.'
      );
      return;
    }

    try {
      const resposta = await requisicao(
        '/auth/reenviar-confirmacao',
        {
          metodo: 'POST',
          autenticar: false,
          dados: {
            email: email.trim()
          }
        }
      );

      mostrarAviso(
        resposta.mensagem ||
          'Se o e-mail estiver cadastrado, enviaremos um novo link.'
      );
    } catch (falha) {
      mostrarErro(falha.message);
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

      {#if sessaoExpirada}
        <p class="mensagem erro" role="status">
          Sua sessão expirou. Entre novamente para continuar.
        </p>
      {/if}

      {#if cadastroRecente}
        <p class="mensagem sucesso" role="status">
          Conta criada! Enviamos um link de confirmação
          para o seu e-mail. Confirme-o para poder fazer login.
        </p>
      {/if}

      <form onsubmit={entrar}>
        <label for="login-email">
          E-MAIL
        </label>

        <input
          id="login-email"
          type="email"
          bind:value={email}
          placeholder="seu@email.com"
          autocomplete="email"
          required
        />

        <label for="login-senha">
          SENHA
        </label>

        <div class="campo-com-icone">
          <input
            id="login-senha"
            type={mostrarSenha ? 'text' : 'password'}
            bind:value={senha}
            placeholder="Digite sua senha"
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
          <a href="/esqueci-senha">
            Esqueceu a senha?
          </a>
        </div>

        {#if erro}
          <p class="mensagem erro" role="alert">
            {erro}
          </p>
        {/if}

        {#if precisaConfirmar || cadastroRecente}
          <button
            type="button"
            class="botao azul pequeno largura-total"
            onclick={reenviar}
          >
            REENVIAR LINK DE CONFIRMAÇÃO
          </button>
        {/if}

        {#if aviso}
          <p class="mensagem sucesso" role="status">
            {aviso}
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

      <a href="/cadastro" class="texto-azul">
        CADASTRE-SE
      </a>
    </div>
  </section>

  <p class="rodape-logo">
    ★ ESTANTE GEEK ★
  </p>
</main>

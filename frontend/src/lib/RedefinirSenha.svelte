
<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { requisicao } from '$lib/api.js';

  let token = $derived(page.url.searchParams.get('token'));

  let senha = $state('');
  let confirmar = $state('');
  let mostrarSenha = $state(false);
  let carregando = $state(false);
  let erro = $state('');
  let sucesso = $state('');
  let linkInvalido = $state(false);
  let temporizadorErro;

  function mostrarErro(mensagem) {
    clearTimeout(temporizadorErro);
    erro = mensagem;

    temporizadorErro = setTimeout(() => {
      erro = '';
    }, 5500);
  }

  onMount(() => {
    return () => clearTimeout(temporizadorErro);
  });

  async function redefinir(evento) {
    evento.preventDefault();

    erro = '';
    sucesso = '';
    linkInvalido = false;

    if (senha !== confirmar) {
      mostrarErro('As senhas informadas não são iguais.');
      return;
    }

    if (senha.length < 8) {
      mostrarErro('A senha deve ter pelo menos 8 caracteres.');
      return;
    }

    carregando = true;

    try {
      const resposta = await requisicao(
        '/auth/redefinir-senha',
        {
          metodo: 'POST',
          autenticar: false,
          dados: {
            token,
            nova_senha: senha
          }
        }
      );

      sucesso = resposta.mensagem ||
        'Sua senha foi redefinida com sucesso.';

      senha = '';
      confirmar = '';
    } catch (falha) {
      const mensagem = falha.message || '';

      linkInvalido =
        /link.*expir|link.*inválid|link.*usado/i.test(mensagem);

      if (linkInvalido) {
        erro = mensagem;
      } else {
        mostrarErro(mensagem);
      }
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
      <h1>Criar nova senha</h1>

      {#if !token}
        <p class="mensagem erro" role="alert">
          Link de redefinição inválido.
        </p>

        <a
          class="botao azul largura-total"
          href="/esqueci-senha"
        >
          PEDIR UM NOVO LINK
        </a>

      {:else if sucesso}
        <p class="mensagem sucesso" role="status">
          {sucesso}
        </p>

        <a
          class="botao rosa principal largura-total"
          href="/login"
        >
          ✦ IR PARA O LOGIN ✦
        </a>

      {:else if linkInvalido}
        <p class="mensagem erro" role="alert">
          {erro}
        </p>

        <a
          class="botao azul largura-total"
          href="/esqueci-senha"
        >
          PEDIR UM NOVO LINK
        </a>

      {:else}
        <p class="descricao-autenticacao">
          Escolha uma nova senha para a sua conta.
        </p>

        <form onsubmit={redefinir}>
          <label for="nova-senha">
            NOVA SENHA
          </label>

          <div class="campo-com-icone">
            <input
              id="nova-senha"
              type={mostrarSenha ? 'text' : 'password'}
              bind:value={senha}
              minlength="8"
              maxlength="72"
              required
              placeholder="Digite sua nova senha"
              autocomplete="new-password"
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

          <label for="nova-senha-confirmar">
            CONFIRMAR NOVA SENHA
          </label>

          <input
            id="nova-senha-confirmar"
            type={mostrarSenha ? 'text' : 'password'}
            bind:value={confirmar}
            required
            placeholder="Repita a nova senha"
            autocomplete="new-password"
          />

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
            ✦ {carregando
              ? 'SALVANDO...'
              : 'SALVAR NOVA SENHA'} ✦
          </button>
        </form>
      {/if}
    </div>

    <div class="painel-autenticacao__rodape">
      <a href="/login" class="texto-azul">
        VOLTAR AO LOGIN
      </a>
    </div>
  </section>

  <p class="rodape-logo">★ ESTANTE GEEK ★</p>
</main>

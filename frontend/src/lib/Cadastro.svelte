
<script>
  import { requisicao } from '$lib/api.js';

  let nome_usuario = $state('');
  let nome_perfil = $state('');
  let email = $state('');
  let senha = $state('');
  let confirmar = $state('');
  let instagram = $state('');
  let discord = $state('');
  let x = $state('');

  let mostrarSenha = $state(false);
  let mostrarConfirmacao = $state(false);
  let mostrarContatos = $state(false);
  let carregando = $state(false);
  let erro = $state('');
  let sucesso = $state('');

  async function cadastrar(evento) {
    evento.preventDefault();

    erro = '';
    sucesso = '';

    if (senha !== confirmar) {
      erro = 'As senhas informadas não são iguais.';
      return;
    }

    carregando = true;

    try {
      await requisicao('/auth/cadastro', {
        metodo: 'POST',
        autenticar: false,
        dados: {
          nome_usuario: nome_usuario.trim(),
          nome_perfil: nome_perfil.trim(),
          email: email.trim(),
          senha,
          instagram: instagram.trim() || null,
          discord: discord.trim() || null,
          x: x.trim() || null
        }
      });

      sucesso =
        'Conta criada nesta versão de desenvolvimento. Agora você pode fazer login.';
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
      <h1>Crie sua conta na Estante Geek</h1>

      <p class="descricao-autenticacao">
        Prepare sua estante e comece sua coleção!
      </p>

      <form onsubmit={cadastrar}>
        <label for="cadastro-nome">NOME</label>

        <input
          id="cadastro-nome"
          bind:value={nome_usuario}
          maxlength="50"
          required
          placeholder="Seu nome de herói"
          autocomplete="name"
        />

        <label for="cadastro-perfil">NOME DE PERFIL</label>

        <input
          id="cadastro-perfil"
          bind:value={nome_perfil}
          maxlength="50"
          required
          placeholder="Como os colecionadores verão você"
        />

        <label for="cadastro-email">E-MAIL</label>

        <input
          id="cadastro-email"
          type="email"
          bind:value={email}
          maxlength="100"
          required
          placeholder="seu@email.com"
          autocomplete="email"
        />

        <label for="cadastro-senha">SENHA</label>

        <div class="campo-com-icone">
          <input
            id="cadastro-senha"
            type={mostrarSenha ? 'text' : 'password'}
            bind:value={senha}
            minlength="8"
            maxlength="72"
            required
            placeholder="Mínimo 8 caracteres"
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

        <label for="cadastro-confirmar">CONFIRMAR SENHA</label>

        <div class="campo-com-icone">
          <input
            id="cadastro-confirmar"
            type={mostrarConfirmacao ? 'text' : 'password'}
            bind:value={confirmar}
            required
            placeholder="Repita sua senha"
            autocomplete="new-password"
          />

          <button
            type="button"
            class="icone-senha"
            aria-label="Mostrar ou ocultar confirmação de senha"
            onclick={() => mostrarConfirmacao = !mostrarConfirmacao}
          >
            {mostrarConfirmacao ? '🙈' : '👁'}
          </button>
        </div>

        <div class="divisor-legenda">
          CONTATOS EXTERNOS
        </div>

        <button
          type="button"
          class="botao-contatos"
          onclick={() => mostrarContatos = !mostrarContatos}
        >
          {mostrarContatos
            ? '− Ocultar contatos opcionais'
            : '+ Adicionar rede social ou contato'}
        </button>

        {#if mostrarContatos}
          <div class="contatos-opcionais">
            <label for="instagram">INSTAGRAM</label>

            <input
              id="instagram"
              bind:value={instagram}
              placeholder="@seu_usuario"
              maxlength="50"
            />

            <label for="discord">DISCORD</label>

            <input
              id="discord"
              bind:value={discord}
              placeholder="Seu usuário"
              maxlength="50"
            />

            <label for="x">X (TWITTER)</label>

            <input
              id="x"
              bind:value={x}
              placeholder="@seu_usuario"
              maxlength="50"
            />
          </div>
        {/if}

        {#if erro}
          <p class="mensagem erro" role="alert">
            {erro}
          </p>
        {/if}

        {#if sucesso}
          <p class="mensagem sucesso" role="status">
            {sucesso}
            <a href="/login">Ir para login →</a>
          </p>
        {/if}

        <button
          type="submit"
          disabled={carregando}
          class="botao rosa principal largura-total"
        >
          ✦ {carregando ? 'CADASTRANDO...' : 'CADASTRAR'} ✦
        </button>
      </form>
    </div>

    <div class="painel-autenticacao__rodape">
      Já tem uma conta?
      <a href="/login" class="texto-azul">FAÇA LOGIN</a>
    </div>
  </section>

  <p class="rodape-logo">★ ESTANTE GEEK ★</p>
</main>

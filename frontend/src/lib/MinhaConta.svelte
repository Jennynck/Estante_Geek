
<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Cabecalho from '$lib/Cabecalho.svelte';
  import AvatarUsuario from '$lib/AvatarUsuario.svelte';
  import {
    apagarToken,
    enviarArquivo,
    obterToken,
    requisicao
  } from '$lib/api.js';

  const TIPOS_FOTO = ['image/jpeg', 'image/png', 'image/webp'];
  const FOTO_MAX_BYTES = 2 * 1024 * 1024;

  let autenticado = $state(false);
  let carregando = $state(true);
  let perfil = $state(null);

  let nomePerfil = $state('');
  let nomeUsuario = $state('');
  let instagram = $state('');
  let discord = $state('');
  let x = $state('');
  let perfilPublico = $state(true);

  let salvando = $state(false);
  let enviandoFoto = $state(false);
  let excluindo = $state(false);
  let versaoFoto = $state(0);

  let erro = $state('');
  let aviso = $state('');
  let erroFoto = $state('');
  let avisoFoto = $state('');

  let confirmandoExclusao = $state(false);
  let modalExclusao = $state(false);
  let senhaExclusao = $state('');
  let erroExclusao = $state('');

  let temporizadores = {};

  function mensagemTemporaria(campo, texto) {
    clearTimeout(temporizadores[campo]);

    if (campo === 'aviso') aviso = texto;
    if (campo === 'erro') erro = texto;
    if (campo === 'avisoFoto') avisoFoto = texto;
    if (campo === 'erroFoto') erroFoto = texto;
    if (campo === 'erroExclusao') erroExclusao = texto;

    temporizadores[campo] = setTimeout(() => {
      if (campo === 'aviso') aviso = '';
      if (campo === 'erro') erro = '';
      if (campo === 'avisoFoto') avisoFoto = '';
      if (campo === 'erroFoto') erroFoto = '';
      if (campo === 'erroExclusao') erroExclusao = '';
    }, 5000);
  }

  function preencher(dados) {
    nomePerfil = dados.nome_perfil || '';
    nomeUsuario = dados.nome_usuario || '';
    instagram = dados.instagram || '';
    discord = dados.discord || '';
    x = dados.x || '';
    perfilPublico = dados.perfil_publico !== false;
  }

  function avisarCabecalho() {
    window.dispatchEvent(
      new CustomEvent('estante-perfil-atualizado')
    );
  }

  async function carregar() {
    autenticado = Boolean(obterToken());

    if (!autenticado) {
      carregando = false;
      return;
    }

    try {
      perfil = await requisicao('/usuarios/me');
      preencher(perfil);
    } catch (falha) {
      erro = falha.message;
    } finally {
      carregando = false;
    }
  }

  async function salvar(evento) {
    evento.preventDefault();
    if (salvando) return;

    erro = '';
    aviso = '';
    salvando = true;

    try {
      const atualizado = await requisicao('/usuarios/me', {
        metodo: 'PATCH',
        dados: {
          nome_perfil: nomePerfil.trim(),
          nome_usuario: nomeUsuario.trim(),
          instagram: instagram.trim(),
          discord: discord.trim(),
          x: x.trim(),
          perfil_publico: perfilPublico
        }
      });

      perfil = atualizado;
      preencher(atualizado);

      mensagemTemporaria(
        'aviso',
        'Perfil atualizado com sucesso!'
      );

      avisarCabecalho();
    } catch (falha) {
      mensagemTemporaria('erro', falha.message);
    } finally {
      salvando = false;
    }
  }

  async function trocarFoto(evento) {
    const campo = evento.currentTarget;
    const arquivo = campo.files?.[0];

    campo.value = '';

    if (!arquivo || enviandoFoto) return;

    erroFoto = '';
    avisoFoto = '';

    if (!TIPOS_FOTO.includes(arquivo.type)) {
      mensagemTemporaria(
        'erroFoto',
        'Envie uma imagem JPEG, PNG ou WebP.'
      );
      return;
    }

    if (arquivo.size > FOTO_MAX_BYTES) {
      mensagemTemporaria(
        'erroFoto',
        'A foto deve ter no máximo 2 MB.'
      );
      return;
    }

    enviandoFoto = true;

    try {
      await enviarArquivo('/usuarios/me/foto', arquivo);

      versaoFoto += 1;
      mensagemTemporaria('avisoFoto', 'Foto atualizada!');
      avisarCabecalho();
    } catch (falha) {
      mensagemTemporaria('erroFoto', falha.message);
    } finally {
      enviandoFoto = false;
    }
  }

  async function removerFoto() {
    if (enviandoFoto) return;

    erroFoto = '';
    avisoFoto = '';
    enviandoFoto = true;

    try {
      await requisicao('/usuarios/me/foto', {
        metodo: 'DELETE'
      });

      versaoFoto += 1;
      mensagemTemporaria('avisoFoto', 'Foto removida.');
      avisarCabecalho();
    } catch (falha) {
      mensagemTemporaria('erroFoto', falha.message);
    } finally {
      enviandoFoto = false;
    }
  }

  function iniciarExclusao() {
    senhaExclusao = '';
    erroExclusao = '';
    modalExclusao = false;
    confirmandoExclusao = true;
  }

  function cancelarExclusao() {
    if (excluindo) return;

    senhaExclusao = '';
    erroExclusao = '';
    confirmandoExclusao = false;
    modalExclusao = false;
  }

  function prepararExclusao(evento) {
    evento.preventDefault();

    if (!senhaExclusao.trim() || excluindo) return;

    erroExclusao = '';
    modalExclusao = true;
  }

  function fecharModal() {
    if (!excluindo) modalExclusao = false;
  }

  function aoTeclar(evento) {
    if (evento.key === 'Escape') fecharModal();
  }

  async function excluirConta() {
    if (excluindo || !senhaExclusao || !modalExclusao) {
      return;
    }

    erroExclusao = '';
    excluindo = true;

    try {
      await requisicao('/usuarios/me', {
        metodo: 'DELETE',
        dados: { senha: senhaExclusao }
      });

      apagarToken();
      senhaExclusao = '';
      modalExclusao = false;

      await goto('/cadastro');
    } catch (falha) {
      modalExclusao = false;
      mensagemTemporaria('erroExclusao', falha.message);
    } finally {
      excluindo = false;
    }
  }

  onMount(() => {
    void carregar();

    return () => {
      Object.values(temporizadores).forEach(clearTimeout);
    };
  });
</script>

<svelte:window onkeydown={aoTeclar} />

<Cabecalho />

<main class="cm-pagina estreita">
  <p class="cm-subtitulo">✦ SUA CONTA ✦</p>

  <h1 class="cm-titulo">MEU PERFIL</h1>

  <p class="cm-descricao">
    Edite seus dados, sua foto e a visibilidade da sua estante.
  </p>

  {#if carregando}
    <div class="cm-estado" role="status">
      CARREGANDO...
    </div>

  {:else if !autenticado}
    <div class="cm-estado">
      <h2>FAÇA LOGIN!</h2>

      <p>Entre na sua conta para editar o seu perfil.</p>

      <a class="cm-botao azul" href="/login">
        FAZER LOGIN
      </a>
    </div>

  {:else if !perfil}
    <div class="cm-estado" role="alert">
      <h2>PERFIL INDISPONÍVEL</h2>

      <p>
        {erro || 'Não foi possível carregar o seu perfil.'}
      </p>
    </div>

  {:else}
    <section class="cm-painel">
      <h2>FOTO DE PERFIL</h2>

      <div class="cm-foto">
        <AvatarUsuario
          usuarioId="me"
          nome={perfil.nome_perfil}
          tamanho={96}
          versao={versaoFoto}
        />

        <div>
          <div class="cm-foto-acoes">
            <label
              class="cm-botao azul"
              class:desativado={enviandoFoto}
            >
              {enviandoFoto
                ? 'AGUARDE...'
                : '📷 ESCOLHER FOTO'}

              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                hidden
                disabled={enviandoFoto}
                onchange={trocarFoto}
              />
            </label>

            <button
              class="cm-botao"
              type="button"
              disabled={enviandoFoto}
              onclick={removerFoto}
            >
              REMOVER FOTO
            </button>
          </div>

          <p class="cm-dica">
            JPEG, PNG ou WebP, com até 2 MB.
          </p>
        </div>
      </div>

      {#if avisoFoto}
        <p class="cm-aviso ok" role="status">
          {avisoFoto}
        </p>
      {/if}

      {#if erroFoto}
        <p class="cm-aviso erro" role="alert">
          {erroFoto}
        </p>
      {/if}
    </section>

    <form class="cm-painel" onsubmit={salvar}>
      <h2>DADOS DO PERFIL</h2>

      <div class="cm-campo">
        <label for="conta-email">E-MAIL</label>

        <input
          id="conta-email"
          type="text"
          value={perfil.email}
          readonly
        />

        <p class="cm-dica">
          {perfil.email_confirmado
            ? '✓ E-mail confirmado.'
            : 'E-mail ainda não confirmado.'}
        </p>
      </div>

      <div class="cm-linha-campos">
        <div class="cm-campo">
          <label for="conta-nome">NOME</label>

          <input
            id="conta-nome"
            type="text"
            bind:value={nomeUsuario}
            maxlength="50"
            required
          />
        </div>

        <div class="cm-campo">
          <label for="conta-perfil">
            NOME DE PERFIL
          </label>

          <input
            id="conta-perfil"
            type="text"
            bind:value={nomePerfil}
            maxlength="50"
            required
          />
        </div>
      </div>

      <div class="cm-linha-campos">
        <div class="cm-campo">
          <label for="conta-instagram">
            INSTAGRAM
          </label>

          <input
            id="conta-instagram"
            type="text"
            bind:value={instagram}
            maxlength="50"
            placeholder="@seu_usuario"
          />
        </div>

        <div class="cm-campo">
          <label for="conta-discord">
            DISCORD
          </label>

          <input
            id="conta-discord"
            type="text"
            bind:value={discord}
            maxlength="50"
            placeholder="Seu usuário"
          />
        </div>
      </div>

      <div class="cm-campo">
        <label for="conta-x">
          X (TWITTER)
        </label>

        <input
          id="conta-x"
          type="text"
          bind:value={x}
          maxlength="50"
          placeholder="@seu_usuario"
        />

        <p class="cm-dica">
          Deixe um contato em branco para removê-lo.
        </p>
      </div>

      <label class="cm-check">
        <input
          type="checkbox"
          bind:checked={perfilPublico}
        />

        <span>
          Perfil público

          <small>
            Outros leitores veem sua estante e seus contatos.
            Com o perfil privado, só aparecem as obras em comum.
          </small>
        </span>
      </label>

      {#if aviso}
        <p class="cm-aviso ok" role="status">
          {aviso}
        </p>
      {/if}

      {#if erro}
        <p class="cm-aviso erro" role="alert">
          {erro}
        </p>
      {/if}

      <button
        class="cm-botao rosa cheio"
        type="submit"
        disabled={salvando}
      >
        ✦ {salvando ? 'SALVANDO...' : 'SALVAR ALTERAÇÕES'} ✦
      </button>
    </form>

    <section class="cm-painel perigo">
      <h2>EXCLUIR CONTA</h2>

      <p class="cm-descricao" style="margin-bottom: 14px">
        Isso apaga sua conta, sua estante, seus checklists
        e suas resenhas. Não dá para desfazer.
      </p>

      {#if !confirmandoExclusao}
        <button
          class="cm-botao rosa cheio"
          type="button"
          onclick={iniciarExclusao}
        >
          🗑 EXCLUIR MINHA CONTA
        </button>
      {:else}
        <form onsubmit={prepararExclusao}>
          <div class="cm-campo">
            <label for="conta-senha-exclusao">
              DIGITE SUA SENHA
            </label>

            <input
              id="conta-senha-exclusao"
              type="password"
              bind:value={senhaExclusao}
              autocomplete="current-password"
              placeholder="Digite sua senha"
              required
            />
          </div>

          {#if erroExclusao}
            <p class="cm-aviso erro" role="alert">
              {erroExclusao}
            </p>
          {/if}

          <div class="cm-foto-acoes">
            <button
              class="cm-botao"
              type="button"
              disabled={excluindo}
              onclick={cancelarExclusao}
            >
              CANCELAR
            </button>

            <button
              class="cm-botao rosa"
              type="submit"
              disabled={excluindo || !senhaExclusao.trim()}
            >
              CONTINUAR
            </button>
          </div>
        </form>
      {/if}
    </section>
  {/if}
</main>

{#if modalExclusao}
  <div class="fundo-exclusao">
    <section
      class="janela-exclusao"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="titulo-confirmar-exclusao"
      aria-describedby="texto-confirmar-exclusao"
    >
      <h2 id="titulo-confirmar-exclusao">
        TEM CERTEZA?
      </h2>

      <p id="texto-confirmar-exclusao">
        Sua conta, estante, checklists e resenhas serão
        excluídos permanentemente. Esta ação não pode ser desfeita.
      </p>

      <div class="botoes-exclusao">
        <button
          class="cm-botao"
          type="button"
          onclick={fecharModal}
          disabled={excluindo}
        >
          CANCELAR
        </button>

        <button
          class="cm-botao rosa"
          type="button"
          onclick={excluirConta}
          disabled={excluindo}
        >
          {excluindo
            ? 'EXCLUINDO...'
            : 'CONFIRMAR EXCLUSÃO'}
        </button>
      </div>
    </section>
  </div>
{/if}

<style>
  .desativado {
    opacity: 0.55;
    cursor: wait;
  }

  .fundo-exclusao {
    position: fixed;
    inset: 0;
    z-index: 1000;
    display: grid;
    place-items: center;
    padding: 18px;
    background: rgba(41, 32, 51, 0.65);
  }

  .janela-exclusao {
    width: min(100%, 500px);
    background: #fff9f2;
    border: 3px solid #292033;
    border-top: 10px solid #ff416b;
    border-radius: 14px;
    box-shadow: 6px 7px 0 #292033;
    padding: 25px;
  }

  .janela-exclusao h2 {
    font: 33px/1.2 'Bangers', Impact, sans-serif;
    color: #ff416b;
    margin: 0 0 15px;
  }

  .janela-exclusao p {
    line-height: 1.6;
    margin: 0 0 24px;
  }

  .botoes-exclusao {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: flex-end;
  }

  .botoes-exclusao .cm-botao {
    cursor: pointer;
  }
</style>

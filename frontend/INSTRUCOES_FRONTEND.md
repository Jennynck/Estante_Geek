# Estante Geek — frontend adaptado ao modelo Favoritar (SvelteKit)

## Como executar no Windows (VS Code / PowerShell)

Na pasta do projeto:

```powershell
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`. Endereços:
- `http://localhost:5173/cadastro`
- `http://localhost:5173/login`
- `http://localhost:5173/catalogo`
- `http://localhost:5173/minha-estante`
- `http://localhost:5173/obra/1` (quando existir uma obra com ID 1)

> **Importante:** no SvelteKit, as rotas são formadas por pastas e não usam `#/`.

## Entendendo as pastas

- `src/routes/+layout.svelte`: carrega o CSS geral.
- `src/routes/<pagina>/+page.svelte`: seleciona o componente da página.
- `src/lib/Cadastro.svelte`, `Login.svelte`, `Catalogo.svelte`, `MinhaEstante.svelte` e `DetalhesObra.svelte`: páginas visuais.
- `src/lib/CartaoObra.svelte`: card reutilizável, como `ActorsCard.svelte` no Favoritar.
- `src/lib/Cabecalho.svelte`: barra de navegação.
- `src/lib/api.js`: `fetch` para o FastAPI, tratamento de erros e token.
- `src/app.css`: estilos baseados nos protótipos Figma.


## Pontos que precisam ser alinhados no backend

1. A rota `/obras` exige login. O catálogo ainda não é público.
2. `/obras` retorna o schema `ObraResponse`, sem editora/gêneros/nota; os filtros do Figma só funcionarão quando a resposta for ampliada. O serviço calcula esses campos, mas a rota os descarta no `response_model` atual.
3. Embora o serviço aceite paginação, `GET /obras` não recebe `pagina`/`limite`. Não foi incluída paginação fictícia.
4. Busca por nome de autor e volume específico ainda não está exposta nessa rota.
5. A verificação de e-mail e a recuperação de senha ainda não foram implementadas no backend.
6. Editar perfil e alterar status geral de obra são rotas que precisarão de interface em etapa posterior.



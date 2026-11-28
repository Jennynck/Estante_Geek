# 📚 Estante Geek

> **Organize. Controle. Conecte-se.**

Plataforma Web voltada a leitores e colecionadores de Histórias em Quadrinhos (HQs) e mangás, desenvolvida como projeto acadêmico no Instituto Federal do Paraná (IFPR) - Campus Foz do Iguaçu.

O Estante Geek tem como propósito reunir, em um único ambiente, recursos para organização de coleções, acompanhamento da leitura e descoberta de leitores com interesses semelhantes.

---

## Sobre o projeto

A proposta surgiu a partir da ideia de uma plataforma dedicada ao público geek. Inicialmente concebido como Geek Match, o projeto foi reformulado para priorizar a catalogação de HQs e mangás e a interação entre colecionadores.

A plataforma busca facilitar o controle de acervos, ajudar o usuário a identificar os volumes que já possui ou leu e aproximar pessoas que compartilham gostos de leitura.

---

## Funcionalidades

### Para usuários

- Cadastro de conta com confirmação por e-mail;
- Autenticação e recuperação de senha;
- Pesquisa e filtragem de obras por nome, editora e tipo (HQ ou mangá);
- Estante virtual para organizar as obras adicionadas;
- Status de leitura: *Quero Ler*, *Lendo*, *Lido* e *Pausado*;
- Checklist individual dos volumes de cada obra;
- Acompanhamento do progresso de leitura;
- Consulta aos detalhes das obras;
- Criação e visualização de resenhas e avaliações;
- Descoberta de leitores com interesses em comum;
- Visualização de perfis e estantes de outros usuários;
- Configurações de privacidade do perfil;
- Campo opcional para contato externo.

### Para administradores

- Moderação de resenhas;
- Gerenciamento de usuários;
- Gerenciamento da lista de termos inadequados.

---

## Tecnologias utilizadas

| Camada | Tecnologia |
|---|---|
| Frontend | Svelte |
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL |
| Comunicação | API REST com respostas em JSON |
| Execução | Docker Desktop e Docker Compose |

---

## Estrutura do repositório

```
Estante-Geek/
├── backend/            # API REST em FastAPI
│   ├── models/         # Modelos do banco (SQLAlchemy)
│   ├── schemas/        # Schemas de entrada e saída (Pydantic)
│   ├── services/       # Regras de negócio e integração com as APIs
│   ├── main.py         # Rotas da aplicação
│   └── database.py     # Conexão com o PostgreSQL
├── frontend/           # Interface Web em SvelteKit
│   └── src/
│       ├── lib/        # Componentes e comunicação com o backend
│       └── routes/     # Páginas e rotas do servidor
├── docker-compose.yml
└── .env                # Variáveis de ambiente
```

## Integrações

O catálogo utiliza fontes externas para obter informações sobre as obras:

- **Comic Vine** - dados de Histórias em Quadrinhos (HQs);
- **Tenrai** - dados de mangás, com informações provenientes do MyAnimeList.

Os dados obtidos pelas integrações são utilizados para complementar o catálogo da plataforma.

---

## Organização do sistema

De forma geral, a aplicação é composta por:

- **Frontend:** interface utilizada pelos leitores e administradores;
- **Backend:** responsável pela lógica da aplicação e pela comunicação com o banco de dados;
- **Banco de dados:** armazenamento das informações de usuários, obras, volumes, estantes, avaliações e demais dados da plataforma;
- **Integrações externas:** obtenção de informações para o catálogo de obras.

---

## Pré-requisitos

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e **aberto** (o ícone da baleia deve indicar que o Docker está em execução)
- [VS Code](https://code.visualstudio.com/) ou outro editor, para criar o arquivo `.env`
- Chave gratuita da API do [Comic Vine](https://comicvine.gamespot.com/api/)
- Conta gratuita no [Mailtrap](https://mailtrap.io), para receber os e-mails de confirmação

> No Windows, o Docker Desktop usa o WSL 2. Se o instalador pedir, aceite a ativação e reinicie o computador.

---

## Configuração

1. Clone o repositório:

   ```bash
   git clone https://github.com/Jennynck/Estante-Geek.git
   cd Estante-Geek
   ```

2. Crie um arquivo `.env` na **raiz** do projeto (mesma pasta do `docker-compose.yml`) com as variáveis abaixo:

   ```env
   # Banco de dados (o serviço "db" usa a porta 5433)
   DATABASE_URL=postgresql://postgres:postgres@db:5433/estante_geek

   # Chave para assinar os tokens (use um texto longo e aleatório)
   SECRET_KEY=troque-por-um-texto-longo-e-aleatorio

   # APIs externas
   COMIC_VINE_API=sua_chave_do_comic_vine
   TENRAI_BASE_URL=https://api.tenrai.org/v1

   # E-mail (Mailtrap > Email Testing > SMTP Settings)
   MAILTRAP_HOST=sandbox.smtp.mailtrap.io
   MAILTRAP_PORT=2525
   MAILTRAP_USER=seu_usuario_mailtrap
   MAILTRAP_PASSWORD=sua_senha_mailtrap
   MAIL_FROM=Estante Geek <nao-responda@estantegeek.local>

   # Endereços da aplicação
   FRONTEND_URL=http://localhost:5173
   VITE_API_URL=http://localhost:8000
   ```

---

## Como executar

1. Abra o **Docker Desktop** e aguarde ele terminar de iniciar.
2. No terminal, na raiz do projeto, execute:

   ```bash
   docker compose up --build
   ```

   Na primeira vez, o download das imagens pode demorar alguns minutos. As tabelas do banco são criadas automaticamente.

3. Acesse os serviços:

   | Serviço | Endereço |
   |---|---|
   | Frontend | http://localhost:5173 |
   | Backend (API) | http://localhost:8000 |
   | Documentação da API (Swagger) | http://localhost:8000/docs |
   | PostgreSQL | `localhost:5433` |

4. Para parar, pressione `Ctrl + C` no terminal e depois execute:

   ```bash
   docker compose down
   ```

   Os dados do banco ficam guardados no volume `pgdata`. Para apagá-los e começar do zero, use `docker compose down -v`.

---

## Primeiros passos

1. Acesse http://localhost:5173/cadastro e crie uma conta.
2. Abra o inbox do **Mailtrap** e copie o `token` do link de confirmação recebido (os e-mails ficam no sandbox do Mailtrap e não chegam ao e-mail real).
3. Confirme o e-mail enviando o token para `POST /auth/confirmar-email` pela documentação da API, em http://localhost:8000/docs.
4. Faça login em http://localhost:5173/login.
5. Explore o catálogo, adicione obras à estante e marque os volumes lidos no checklist.

---

## 🔗 Repositório

O código-fonte do Estante Geek está disponível no GitHub:

[Jennynck/Estante_Geek](https://github.com/Jennynck/Estante_Geek)

---

## Projeto acadêmico

Desenvolvido por **Agatha Andressa de Souza** e **Jhennifer Nicole F. dos Santos**, no Instituto Federal do Paraná (IFPR) - Campus Foz do Iguaçu.

*Estante Geek - organize sua coleção, acompanhe sua leitura e encontre leitores com interesses semelhantes.*
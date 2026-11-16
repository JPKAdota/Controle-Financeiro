This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

Este projeto roda 100% local: Postgres via Docker, backend FastAPI via `uvicorn` e frontend Next.js via `next dev`. Não há dependência de Vercel nem Supabase.

### Atalho: subir tudo de uma vez

```powershell
.\scripts\start-all.ps1
```

Isso garante o Docker Desktop ligado, sobe o Postgres (`docker compose up -d`) e abre backend e frontend cada um em sua própria janela do PowerShell. Depois da primeira vez (ambiente já configurado com `.env`, `.venv` e `node_modules`), esse é o único comando necessário no dia a dia.

### Passo a passo manual

### 1. Banco de dados (Postgres local via Docker)

```bash
docker compose up -d
```

Isso sobe um Postgres na porta `5432` e já aplica o schema (`api/scripts/init_local.sql`) na primeira inicialização. Os dados ficam persistidos no volume Docker `controle_financeiro_data` entre reinícios.

### 2. Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste se necessário. Por padrão:

```env
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/controle_financeiro
```

### 3. Backend (FastAPI)

```bash
cd api
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn index:app --reload --host 127.0.0.1 --port 8000
```

### 4. Frontend (Next.js)

Em outro terminal, na raiz do projeto:

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000) with your browser to see the result. Em desenvolvimento, o Next já faz proxy de `/api/*` para `http://127.0.0.1:8000` (ver `next.config.mjs`).

O app não tem tela de login: é uso pessoal, single-user, tudo roda na sua máquina.

Por isso, Postgres (`127.0.0.1:5432`), backend (`127.0.0.1:8000`) e frontend (`127.0.0.1:3000`) aceitam conexões **só da própria máquina**. Não troque para `0.0.0.0` nem remova o `-H 127.0.0.1` do `npm run dev`: sem login, qualquer pessoa na mesma rede (Wi-Fi de casa, café, trabalho) conseguiria ler ou apagar suas transações.

### Backup e restauração do banco

Como os dados agora vivem só no seu Postgres local (sem Supabase cuidando disso), gere backups com:

```powershell
.\scripts\backup-db.ps1
```

Isso salva um dump em `backups\controle_financeiro_<data>.sql` (mantém os 30 mais recentes). Para restaurar:

```powershell
.\scripts\restore-db.ps1 -BackupFile .\backups\controle_financeiro_2026-09-07_10-00-00.sql
```

`backups/` não é versionado (contém dados financeiros pessoais) — guarde uma cópia fora do PC de vez em quando (pendrive, nuvem pessoal, etc).

Além disso, o botão "Excluir tudo" (página Transações) gera automaticamente um snapshot `backups/pre_delete_all_<data>.json` com todas as transações e categorias antes de apagar — mesmo sem rodar `backup-db.ps1` manualmente, esse clique específico sempre deixa uma cópia de segurança.

## Agente IA local com Ollama

O agente usa Ollama por padrão, sem chave de API externa. Instale o Ollama, inicie o serviço e baixe um modelo:

```bash
ollama pull llama3.2:3b
ollama serve
```

No arquivo `.env`, mantenha:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:3b
```

Para usar Gemini como alternativa, defina `AI_PROVIDER=gemini` e configure `GEMINI_API_KEY`.

> ⚠️ **Privacidade com Gemini:** com o Ollama nada sai do seu computador. Com `AI_PROVIDER=gemini`, cada mensagem do chat vai para os servidores do Google junto com um resumo dos seus dados (receitas, despesas, saldo e até 10 investimentos com descrição, valor e data). No plano gratuito da API Gemini, o Google pode usar esse conteúdo para melhorar seus produtos. O app mostra um aviso vermelho na tela do chat e no log do backend enquanto o Gemini estiver ativo.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

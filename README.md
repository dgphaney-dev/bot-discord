# Bot Discord Modular & Profissional

Bot completo para Discord em Python, desenvolvido com arquitetura modular de **Cogs**, interface rica com **Discord UI (Modais, Seletores, Botões Interativos)**, integração com **Google Gemini AI**, badges oficiais e sistema de permissões estritas por cargo.

---

## Funcionalidades Principais

- **Gestão de Staff & Permissões Estritas (`!staff`):**
  - Painel interativo com 3 páginas para configurar cargos autorizados em cada módulo.
  - Botão de aplicação em lote (*Aplicar nesta Página*).
  - Modo 100% estrito: somente quem possui os cargos cadastrados pode usar as ações do bot.

- **Sistema VIP Avançado (`!setvip`, `!vip`, `!painelvip`):**
  - Atribuição com seleção de dias via Modal interativo (`30`, `60`, `365` ou `0` para permanente).
  - Verificação e expiração automática de VIPs em segundo plano (remove cargos, call privada e avisa na DM).
  - Cargos personalizados com nome e cor hex editáveis pelo próprio membro VIP.
  - Vagas de amigos configuráveis por plano.

- **Informações & Perfis (`!userinfo`, `!serverinfo`, `!avatar`, `!userbanner`):**
  - Busca de qualquer usuário no Discord por **ID direto**, menção ou nome.
  - Exibição de **Badges Oficiais do Discord** lado a lado no perfil (*Server Booster, Nitro, Legacy Username, HypeSquad, Active Developer, etc.*).
  - Cálculo exato da evolução do Server Booster: distintivo atual, próximo nível, dias restantes e barra de progresso.

- **Moderação Completa & Auditoria:**
  - `!ban`, `!unban`, `!kick`, `!mute`, `!unmute`.
  - Sistema de advertências (`!warn`, `!warns`, `!unwarn`).
  - Canal de registros e auditoria da Staff (`!setlogs`).

- **Gestão de Canais & Suporte:**
  - `!lock` e `!unlock` para trancar/destrancar canais de texto.
  - `!slowmode` para controle de fluxo.
  - Central de tickets privada com criação de canais em categoria e encerramento com botão (`!painelticket`).

- **Boas-Vindas & Auto-Role:**
  - Mensagens de entrada customizadas (`!setwelcome`).
  - Entrega automática de cargo inicial para novos membros (`!setautorole`).

- **Inteligência Artificial (Google Gemini):**
  - Respostas descontraídas e sem textão marcando o bot ou respondendo mensagens.
  - Gerenciamento de personagens e personalidades (`!personagem`).

- **AutoMod:**
  - Proteção automática contra convites não autorizados, links suspeitos e spam.

---

## Estrutura do Projeto

```text
├── cogs/                  # Módulos independentes do bot
│   ├── automod.py         # Proteção contra links, convites e spam
│   ├── canais.py          # Controle de canais (lock, unlock, slowmode)
│   ├── cargos.py          # Criação e gestão interativa de cargos
│   ├── chat_ia.py         # Conversação inteligente com Google Gemini
│   ├── custom_bot.py      # Customização de avatar, banner e nome do bot
│   ├── info.py            # Informações detalhadas de perfil, badges e servidor
│   ├── logs.py            # Canal oficial de auditoria e registros da Staff
│   ├── moderacao.py       # Punições (ban, kick, mute temporário)
│   ├── painel.py          # Central interativa de ajuda e comandos (!painel)
│   ├── permissoes.py      # Painel de permissões por cargo (!staff)
│   ├── purge.py           # Limpeza em lote de mensagens (!clear)
│   ├── slash_commands.py  # Comandos de barra (/ping, etc.)
│   ├── tickets.py         # Sistema de tickets de atendimento privado
│   ├── vip.py             # Sistema VIP completo com cargos, calls e validade
│   ├── warns.py           # Sistema de advertências e histórico
│   └── welcome.py         # Boas-vindas e auto-role
│
├── data/                  # Armazenamento de dados e configurações JSON
├── utils/                 # Funções utilitárias e checagem de permissões
├── config.py              # Centralização de configurações e cores
├── main.py                # Ponto de entrada e inicialização do bot
├── requirements.txt       # Dependências Python
├── .env.example           # Modelo de variáveis de ambiente
└── .gitignore             # Proteção de arquivos confidenciais
```

---

## Instalação e Execução

### 1. Clonar o repositório
```bash
git clone https://github.com/dgphaney-dev/bot-discord.git
cd bot-discord
```

### 2. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar as variáveis de ambiente
Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```
Preencha o `.env` com suas credenciais:
- `DISCORD_TOKEN`: Token do seu bot no [Discord Developer Portal](https://discord.com/developers/applications).
- `GEMINI_API_KEY`: Chave gratuita de IA do [Google AI Studio](https://aistudio.google.com/) *(opcional)*.

### 4. Iniciar o Bot
```bash
python main.py
```

---

## Segurança & Privacidade
O arquivo `.env` está incluído no `.gitignore` e **nunca** deve ser versionado ou compartilhado publicamente para proteger suas credenciais e tokens.

import discord
from discord.ext import commands
from config import Cores, PREFIXO, TEMPO_DELETE_ERRO, VIP_CORES
from utils.helpers import tentar_deletar_mensagem


class MenuPainel(discord.ui.Select):
    def __init__(self):
        opcoes = [
            discord.SelectOption(
                label="Página Inicial",
                description="Retorna à visão geral do painel",
                emoji="🏡",
                value="inicio"
            ),
            discord.SelectOption(
                label="Banimento (Ban/Unban)",
                description="Comandos para banir e desbanir membros",
                emoji="🔨",
                value="ban"
            ),
            discord.SelectOption(
                label="Expulsão (Kick)",
                description="Comando para expulsar membros do servidor",
                emoji="👢",
                value="kick"
            ),
            discord.SelectOption(
                label="Silenciamento (Mute/Unmute)",
                description="Comandos para silenciar e remover silêncio",
                emoji="🔇",
                value="mute"
            ),
            discord.SelectOption(
                label="Limpeza de Chat (Clear)",
                description="Comandos de remoção de mensagens em massa",
                emoji="🧹",
                value="purge"
            ),
            discord.SelectOption(
                label="Gestão de Cargos",
                description="Criar e atribuir cargos interativamente",
                emoji="🏷️",
                value="cargos"
            ),
            discord.SelectOption(
                label="Aparência do Bot",
                description="Alterar nome e avatar do bot",
                emoji="⚙️",
                value="customizacao"
            ),
            discord.SelectOption(
                label="Sistema VIP",
                description="Painel exclusivo e vantagens VIP",
                emoji="💎",
                value="vip"
            ),
            discord.SelectOption(
                label="Permissões por Cargos",
                description="Configurar cargos para cada comando/módulo",
                emoji="🛡️",
                value="permissoes"
            ),
            discord.SelectOption(
                label="Inteligência Artificial (Gemini)",
                description="Conversar com o bot no estilo ChatGPT com respostas curtas",
                emoji="🤖",
                value="ia"
            ),
            discord.SelectOption(
                label="Advertências (Warns)",
                description="Aplicar, listar e remover advertências de membros",
                emoji="⚠️",
                value="warns"
            ),
            discord.SelectOption(
                label="Gestão de Canais",
                description="Trancar canais (lock/unlock) e modo lento",
                emoji="🔒",
                value="canais"
            ),
            discord.SelectOption(
                label="Sistema de Tickets",
                description="Painel de suporte e atendimento privado",
                emoji="🎟️",
                value="tickets"
            ),
            discord.SelectOption(
                label="Boas-Vindas & Auto-Role",
                description="Canal de entrada e cargo automático para novos membros",
                emoji="👋",
                value="welcome"
            ),
            discord.SelectOption(
                label="Auditoria & Logs",
                description="Canal oficial para registros e histórico da Staff",
                emoji="📋",
                value="logs"
            ),
            discord.SelectOption(
                label="Informações & Perfil",
                description="Consultar userinfo, serverinfo, avatar, banner e booster",
                emoji="👤",
                value="info"
            ),
        ]
        super().__init__(
            placeholder="Selecione uma categoria para explorar os comandos...",
            min_values=1,
            max_values=1,
            options=opcoes,
            custom_id="select_painel_ajuda"
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ Você precisa de permissão de `Gerenciar Mensagens` para navegar neste painel.",
                ephemeral=True
            )
            return

        opcao = self.values[0]
        embed_resposta = None

        if opcao == "inicio":
            embed_resposta = discord.Embed(
                title="⚡  CENTRAL DE COMANDOS & AJUDA",
                description=(
                    f"Olá {interaction.user.mention}, seja bem-vindo à central oficial de comandos!\n\n"
                    "Navegue através do **menu de seleção abaixo** para consultar a sintaxe, "
                    "permissões e exemplos práticos de cada categoria.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.INFO
            )
            embed_resposta.add_field(
                name="📁  Categorias do Sistema",
                value=(
                    "• 🔨 **Banimento:** Punições e desbanimentos com GIF\n"
                    "• 🔇 **Silenciamento:** Mute temporário configurável (`10m`, `2h`)\n"
                    f"• 🧹 **Limpeza:** Remoção de mensagens em lote (`{PREFIXO}clear`)\n"
                    "• ⚠️ **Advertências:** Registro e histórico de warns (`!warn`)\n"
                    "• 🔒 **Canais:** Trancar (`!lock`), liberar (`!unlock`) e slowmode\n"
                    "• 🎟️ **Tickets:** Atendimento privado interativo (`!painelticket`)\n"
                    "• 👋 **Boas-Vindas:** Mensagens de entrada e cargo automático (`!setwelcome`)\n"
                    "• 📋 **Auditoria:** Canal de registros da Staff (`!setlogs`)\n"
                    f"• 🏷️ **Cargos:** Criação via Modal e gestão interativa\n"
                    "• ⚙️ **Aparência:** Troca de avatar, banner e nome do bot\n"
                    f"• 💎 **VIP:** Painel interativo com calls, cargos e amigos (`{PREFIXO}vip`)\n"
                    f"• 🛡️ **Permissões:** Cargos personalizados para cada módulo (`{PREFIXO}staff`)\n"
                    "• 🤖 **Inteligência Artificial:** Gemini ultra rápido sem prefixo"
                ),
                inline=False
            )
            embed_resposta.set_footer(text=f"Prefixo oficial: {PREFIXO} • Selecione uma categoria abaixo.")

        elif opcao == "ban":
            embed_resposta = discord.Embed(
                title="🔨  MODERAÇÃO: BANIMENTO",
                description=(
                    "Mantenha o servidor protegido aplicando punições severas a infratores.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.ERRO
            )
            embed_resposta.add_field(
                name="🔨  Banir Membro",
                value=(
                    f"```fix\n{PREFIXO}ban <@membro> [motivo]\n```"
                    f"• **Exemplo:** `{PREFIXO}ban @Infrator Divulgação indevida no chat`"
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🕊️  Desbanir Membro",
                value=(
                    f"```fix\n{PREFIXO}unban <ID_do_usuario> [motivo]\n```"
                    f"• **Exemplo:** `{PREFIXO}unban 123456789012345678 Revisão aprovada`"
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🖼️  Imagens & GIFs de Punição",
                value=(
                    f"• `{PREFIXO}setimg ban [link/anexo]` — Seu GIF/imagem próprio de ban\n"
                    f"• `{PREFIXO}setimg unban [link/anexo]` — Seu GIF/imagem próprio de unban\n"
                    f"• `{PREFIXO}minhasimagens` — Lista todas as suas imagens salvas"
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Banir Membros ou Cargo Autorizado")

        elif opcao == "kick":
            embed_resposta = discord.Embed(
                title="👢  MODERAÇÃO: EXPULSÃO (KICK)",
                description=(
                    "Remova membros que descumprem as regras, respeitando a hierarquia de cargos.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.AVISO
            )
            embed_resposta.add_field(
                name="👢  Expulsar Membro",
                value=(
                    f"```fix\n{PREFIXO}kick <@membro> [motivo]\n```"
                    f"• **Aliases:** `{PREFIXO}expulsar`\n"
                    f"• **Exemplo:** `{PREFIXO}kick @Infrator Desrespeito às regras do canal`"
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="👑  Regras de Hierarquia",
                value=(
                    "• Não é possível expulsar Administradores ou Donos.\n"
                    "• O moderador não pode expulsar quem tiver cargo igual ou superior.\n"
                    "• O bot precisa ter cargo acima do membro a ser expulso."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🖼️  Imagens & GIFs de Expulsão",
                value=f"• `{PREFIXO}setimg kick [link/anexo]` — Seu GIF/imagem próprio de kick",
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Expulsar Membros ou Cargo Autorizado")

        elif opcao == "mute":
            embed_resposta = discord.Embed(
                title="🔇  MODERAÇÃO: SILENCIAMENTO (MUTE)",
                description=(
                    "Retire temporariamente o acesso de fala e chat de membros bagunceiros.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.MODERACAO
            )
            embed_resposta.add_field(
                name="🔇  Silenciar Membro",
                value=(
                    f"```fix\n{PREFIXO}mute <@membro> <tempo> [motivo]\n```"
                    f"• **Exemplo:** `{PREFIXO}mute @Membro 30m Flood de mensagens`"
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🔊  Desmutar Manualmente",
                value=(
                    f"```fix\n{PREFIXO}unmute <@membro>\n```"
                    f"• **Exemplo:** `{PREFIXO}unmute @Membro`"
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="⏱️  Formatos de Duração Suportados",
                value="`s` (segundos)  |  `m` (minutos)  |  `h` (horas)  |  `d` (dias)",
                inline=True
            )
            embed_resposta.add_field(
                name="🖼️  GIFs de Mute",
                value=f"`{PREFIXO}setimg mute` / `{PREFIXO}setimg unmute`",
                inline=True
            )
            embed_resposta.set_footer(text="Permissão necessária: Gerenciar Cargos ou Cargo Autorizado")

        elif opcao == "purge":
            embed_resposta = discord.Embed(
                title="🧹  UTILITÁRIOS: LIMPEZA DE CHAT",
                description=(
                    "Apague mensagens em massa para manter os canais organizados.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.INFO
            )
            embed_resposta.add_field(
                name="🧹  Limpar Mensagens",
                value=(
                    f"```fix\n{PREFIXO}clear <quantidade>\n```"
                    f"• **Aliases:** `{PREFIXO}limpar`, `{PREFIXO}clean`\n"
                    f"• **Exemplo:** `{PREFIXO}clear 50` *(apaga as últimas 50 mensagens)*"
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Gerenciar Mensagens")

        elif opcao == "cargos":
            embed_resposta = discord.Embed(
                title="🏷️  GERENCIAMENTO: SISTEMA DE CARGOS",
                description=(
                    "Crie cargos com interface moderna ou atribua cargos a membros facilmente.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.SUCESSO
            )
            embed_resposta.add_field(
                name="🎨  Criar Novo Cargo (Modal Interativo)",
                value=(
                    f"```fix\n{PREFIXO}cargos\n```"
                    "• Abre um formulário popup direto no Discord para configurar Nome, Cor e Permissões."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="👤  Atribuir ou Remover Cargo de Membro",
                value=(
                    f"```fix\n{PREFIXO}setcargo <@membro>\n```"
                    "• Abre um menu dropdown interativo com os cargos do servidor para dar ou tirar com 1 clique."
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Gerenciar Cargos")

        elif opcao == "customizacao":
            embed_resposta = discord.Embed(
                title="⚙️  CUSTOMIZAÇÃO: APARÊNCIA DO BOT",
                description=(
                    "Personalize o visual e a identidade do bot diretamente pelo servidor.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.AVISO
            )
            embed_resposta.add_field(
                name="🖼️  Foto de Perfil (Avatar)",
                value=f"`{PREFIXO}avatar_bot [link ou anexo]`\n*Define a nova foto do bot instantaneamente.*",
                inline=False
            )
            embed_resposta.add_field(
                name="🎨  Banner do Perfil",
                value=f"`{PREFIXO}banner_bot [link ou anexo]`\n*Define o novo banner que aparece no card do bot.*",
                inline=False
            )
            embed_resposta.add_field(
                name="📛  Nome do Bot",
                value=f"`{PREFIXO}nome_bot <novo_nome>`\n*Altera o username global do bot no Discord.*",
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Administrador")

        elif opcao == "vip":
            embed_resposta = discord.Embed(
                title="💎  VANTAGENS: SISTEMA VIP",
                description=(
                    "Painel interativo e benefícios exclusivos para membros VIP.\n"
                    "──────────────────────────────────────────────"
                ),
                color=discord.Color.from_str("#00E5FF")
            )
            embed_resposta.add_field(
                name="👑  Painel Interativo VIP",
                value=(
                    f"```fix\n{PREFIXO}vip\n```"
                    "• **Configurar Cargo:** Abre modal para nome e cor hexadecimal\n"
                    "• **Ícone do Cargo:** Escolha qualquer emoji do servidor para ser badge\n"
                    "• **Configurar Call:** Define nome e limite de participantes\n"
                    "• **Amigos do VIP:** Selecione amigos para compartilhar seu cargo"
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🛡️  Comandos da Staff (VIP)",
                value=(
                    f"• `{PREFIXO}setvip <@membro>` — Abre botões para escolher o VIP\n"
                    f"• `{PREFIXO}removervip <@membro>` — Revoga o plano VIP do membro"
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Aproveite seus benefícios VIP!")

        elif opcao == "permissoes":
            embed_resposta = discord.Embed(
                title="🛡️  SEGURANÇA: PERMISSÕES POR CARGOS",
                description=(
                    "Configure quais cargos da sua equipe podem executar cada módulo.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.PADRAO
            )
            embed_resposta.add_field(
                name="📋  Painel Interativo de Permissões",
                value=(
                    f"```fix\n{PREFIXO}permissoes\n```"
                    "• Escolha o módulo no dropdown e selecione o cargo correspondente."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="⚡  Atalhos Rápidos",
                value=(
                    f"• `{PREFIXO}setperm <modulo> <@cargo>` — Vincula cargo ao módulo\n"
                    f"• `{PREFIXO}remperm <modulo>` — Reseta permissão do módulo"
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Administrador")

        elif opcao == "ia":
            embed_resposta = discord.Embed(
                title="🤖  INTELIGÊNCIA ARTIFICIAL (GEMINI)",
                description=(
                    "Converse com o bot naturalmente com respostas curtas, descontraídas e sem textão!\n\n"
                    "✨ **NÃO PRECISA DE PREFIXO!**\n"
                    "Basta **marcar o bot** ou **responder (reply)** a mensagem dele no chat.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.INFO
            )
            embed_resposta.add_field(
                name="🎭  Personalidade & Personagem",
                value=(
                    f"```fix\n{PREFIXO}personagem\n```"
                    "• Escolha presets como **Aspas**, **Cazé**, **Coringa**, **Dev Nerd** "
                    "ou crie seu próprio personagem customizado!"
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="📍  Canais & Memória",
                value=(
                    f"• `{PREFIXO}setcanalia #chat` — Torna o canal 100% livre para a IA falar\n"
                    f"• `{PREFIXO}limparconversa` — Reseta a memória recente da conversa"
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Powered by Google Gemini • Respostas instantâneas")

        elif opcao == "warns":
            embed_resposta = discord.Embed(
                title="⚠️  SISTEMA DE ADVERTÊNCIAS (WARNS)",
                description=(
                    "Gerencie advertências e histórico disciplinar de membros do servidor.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.AVISO
            )
            embed_resposta.add_field(
                name="📌  Comando: Advertir Membro",
                value=(
                    f"```fix\n{PREFIXO}warn @Membro <motivo>\n```"
                    "• Registra advertência com ID único e notifica o usuário via DM."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="📋  Comando: Consultar Histórico",
                value=(
                    f"```fix\n{PREFIXO}warns [@Membro]\n```"
                    "• Lista todas as advertências ativas, datas, motivos e moderadores."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🗑️  Comando: Remover Advertência",
                value=(
                    f"```fix\n{PREFIXO}unwarn @Membro [id]\n```"
                    "• Remove uma advertência específica ou a mais recente caso omitido o ID."
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Cargo de Advertências ou Staff")

        elif opcao == "canais":
            embed_resposta = discord.Embed(
                title="🔒  GESTÃO & CONTROLE DE CANAIS",
                description=(
                    "Comandos rápidos para controle de fluxo e segurança nos chats de texto.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.PADRAO
            )
            embed_resposta.add_field(
                name="🔒  Trancar Canal (Lock)",
                value=(
                    f"```fix\n{PREFIXO}lock [#canal] [motivo]\n```"
                    "• Impede membros comuns de enviarem mensagens no canal."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🔓  Destrancar Canal (Unlock)",
                value=(
                    f"```fix\n{PREFIXO}unlock [#canal]\n```"
                    "• Libera o envio de mensagens novamente para todos os membros."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="⏱️  Modo Lento (Slowmode)",
                value=(
                    f"```fix\n{PREFIXO}slowmode <segundos> [#canal]\n```"
                    "• Define intervalo entre mensagens (ex: `!slowmode 5` ou `0` para desativar)."
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Cargo de Gestão de Canais ou Staff")

        elif opcao == "tickets":
            embed_resposta = discord.Embed(
                title="🎟️  CENTRAL DE TICKETS & ATENDIMENTO",
                description=(
                    "Sistema profissional de atendimento privado individualizado com suporte a categorias.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.INFO
            )
            embed_resposta.add_field(
                name="📩  Enviar Painel de Atendimento",
                value=(
                    f"```fix\n{PREFIXO}painelticket\n```"
                    "• Envia no canal o embed oficial com o botão `Abrir Atendimento`."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="⚙️  Como Funciona",
                value=(
                    "• O usuário clica e um canal privado `ticket-nome` é gerado.\n"
                    "• Apenas o membro e os cargos autorizados de Staff têm acesso.\n"
                    "• Botão vermelho dentro do ticket encerra e deleta a sala em 5s."
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Cargo de Tickets ou Staff")

        elif opcao == "welcome":
            embed_resposta = discord.Embed(
                title="👋  BOAS-VINDAS & AUTO-ROLE",
                description=(
                    "Recepcione novos membros automaticamente e defina cargo inicial de entrada.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.SUCESSO
            )
            embed_resposta.add_field(
                name="👋  Canal de Boas-Vindas",
                value=(
                    f"```fix\n{PREFIXO}setwelcome [#canal]\n```"
                    "• Define o canal onde o bot dará as boas-vindas com embed e avatar."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🏷️  Cargo Automático (Auto-Role)",
                value=(
                    f"```fix\n{PREFIXO}setautorole [@Cargo]\n```"
                    "• Novos membros recebem este cargo instantaneamente ao entrar (ou passe sem cargo para desativar)."
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Cargo de Boas-Vindas ou Staff")

        elif opcao == "logs":
            embed_resposta = discord.Embed(
                title="📋  AUDITORIA & LOGS DE STAFF",
                description=(
                    "Monitore todas as ações administrativas executadas pela moderação em tempo real.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.INFO
            )
            embed_resposta.add_field(
                name="📋  Definir Canal de Registros",
                value=(
                    f"```fix\n{PREFIXO}setlogs [#canal]\n```"
                    "• Define o canal onde todos os relatórios de auditoria serão postados."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="⚡  Ações Monitoradas Automaticamente",
                value=(
                    "• Banimentos e desbanimentos\n"
                    "• Silenciamentos (Mute e Unmute)\n"
                    "• Expulsões (Kick)\n"
                    "• Advertências (Warn e Unwarn)\n"
                    "• Trancamento e liberação de canais (Lock / Unlock)\n"
                    "• Concessão e expiração automática de VIPs"
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Permissão necessária: Cargo de Logs ou Staff")

        elif opcao == "info":
            embed_resposta = discord.Embed(
                title="👤  INFORMAÇÕES DE USUÁRIO & SERVIDOR",
                description=(
                    "Consulte perfis completos, badges do Discord, tempo de booster e estatísticas do servidor.\n"
                    "──────────────────────────────────────────────"
                ),
                color=Cores.INFO
            )
            embed_resposta.add_field(
                name="👤  Perfil Completo & Badges (Userinfo)",
                value=(
                    f"```fix\n{PREFIXO}userinfo [@Membro]\n```"
                    "• **Distintivos:** Todas as Badges do Discord, Nitro, Bot e VIPs.\n"
                    "• **Booster:** Tempo impulsionando, nível do distintivo, barra de evolução e quanto tempo falta para o próximo nível upar!\n"
                    "• **Presença:** Status, dispositivos (PC/Celular), Spotify e Jogos.\n"
                    "• **Servidor:** Posição de entrada, data de criação e cargos."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🏰  Estatísticas do Servidor (Serverinfo)",
                value=(
                    f"```fix\n{PREFIXO}serverinfo\n```"
                    "• Total de membros, bots, canais, cargos, emojis, nível de boost e dono."
                ),
                inline=False
            )
            embed_resposta.add_field(
                name="🖼️  Avatar & Banner",
                value=(
                    f"• `{PREFIXO}avatar [@Membro]` — Ver e baixar foto de perfil em 1024px\n"
                    f"• `{PREFIXO}userbanner [@Membro]` — Ver e baixar banner do perfil em HD"
                ),
                inline=False
            )
            embed_resposta.set_footer(text="Comandos públicos disponíveis para todos os membros")

        if embed_resposta:
            if interaction.guild.icon:
                embed_resposta.set_thumbnail(url=interaction.guild.icon.url)
            await interaction.response.edit_message(embed=embed_resposta)


class PainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuPainel())


class Painel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painel", aliases=["ajuda"])
    @commands.has_permissions(manage_messages=True)
    async def painel(self, ctx):
        """Envia o painel interativo de ajuda e comandos no chat."""
        await tentar_deletar_mensagem(ctx)

        embed = discord.Embed(
            title="⚡  CENTRAL DE COMANDOS & AJUDA",
            description=(
                f"Olá {ctx.author.mention}, seja bem-vindo à central oficial de comandos!\n\n"
                "Navegue através do **menu de seleção abaixo** para consultar a sintaxe, "
                "permissões e exemplos práticos de cada categoria.\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.INFO
        )
        embed.add_field(
            name="📁  Categorias do Sistema",
            value=(
                "• 🔨 **Banimento:** Punições e desbanimentos com GIF\n"
                "• 🔇 **Silenciamento:** Mute temporário configurável (`10m`, `2h`)\n"
                f"• 🧹 **Limpeza:** Remoção de mensagens em lote (`{PREFIXO}clear`)\n"
                "• ⚠️ **Advertências:** Registro e histórico de warns (`!warn`)\n"
                "• 🔒 **Canais:** Trancar (`!lock`), liberar (`!unlock`) e slowmode\n"
                "• 🎟️ **Tickets:** Atendimento privado interativo (`!painelticket`)\n"
                "• 👋 **Boas-Vindas:** Mensagens de entrada e cargo automático (`!setwelcome`)\n"
                "• 📋 **Auditoria:** Canal de registros da Staff (`!setlogs`)\n"
                f"• 🏷️ **Cargos:** Criação via Modal e gestão interativa\n"
                "• ⚙️ **Aparência:** Troca de avatar, banner e nome do bot\n"
                f"• 💎 **VIP:** Painel interativo com calls, cargos e amigos (`{PREFIXO}vip`)\n"
                f"• 🛡️ **Permissões:** Cargos personalizados para cada módulo (`{PREFIXO}staff`)\n"
                "• 🤖 **Inteligência Artificial:** Gemini ultra rápido sem prefixo"
            ),
            inline=False
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(text=f"Prefixo oficial: {PREFIXO} • Selecione uma categoria abaixo.")

        await ctx.send(embed=embed, view=PainelView(), delete_after=180)

    @painel.error
    async def painel_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Gerenciar Mensagens` para abrir o painel de ajuda.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    @commands.command(name="cores", aliases=["paleta", "cor"])
    @commands.has_permissions(administrator=True)
    async def cores(self, ctx):
        """Exibe a paleta atual de cores configurada para os embeds."""
        await tentar_deletar_mensagem(ctx)

        embed = discord.Embed(
            title="🎨  PALETA DE CORES DOS EMBEDS",
            description=(
                "Aqui estão as cores atualmente configuradas no arquivo `.env` para cada tipo de mensagem:\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.PADRAO
        )
        embed.add_field(name="✅ Sucesso", value=f"`{str(Cores.SUCESSO)}`", inline=True)
        embed.add_field(name="❌ Erro", value=f"`{str(Cores.ERRO)}`", inline=True)
        embed.add_field(name="⚠️ Aviso", value=f"`{str(Cores.AVISO)}`", inline=True)
        embed.add_field(name="ℹ️ Informações", value=f"`{str(Cores.INFO)}`", inline=True)
        embed.add_field(name="🔨 Moderação", value=f"`{str(Cores.MODERACAO)}`", inline=True)
        embed.add_field(name="💠 Padrão", value=f"`{str(Cores.PADRAO)}`", inline=True)
        embed.add_field(
            name="💎 Cores dos Planos VIP",
            value=(
                f"• 🥈 Prata: `{str(VIP_CORES['prata'])}`\n"
                f"• 🥇 Gold: `{str(VIP_CORES['gold'])}`\n"
                f"• 💎 Diamante: `{str(VIP_CORES['diamante'])}`"
            ),
            inline=False
        )
        embed.set_footer(text="Para alterar qualquer cor, edite as variáveis COR_EMBED_* no arquivo .env!")
        await ctx.send(embed=embed, delete_after=30)

    @cores.error
    async def cores_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Apenas Administradores podem visualizar a paleta de cores técnica.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)


async def setup(bot):
    await bot.add_cog(Painel(bot))
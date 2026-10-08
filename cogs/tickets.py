import json
from pathlib import Path
import discord
from discord.ext import commands
from config import Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem

ARQUIVO_TICKETS = Path(__file__).resolve().parent.parent / "data" / "tickets_config.json"


def carregar_config_tickets() -> dict:
    if not ARQUIVO_TICKETS.exists():
        return {}
    try:
        with open(ARQUIVO_TICKETS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_config_tickets(dados: dict):
    ARQUIVO_TICKETS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_TICKETS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


class ViewBotaoTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Atendimento", style=discord.ButtonStyle.primary, emoji="📩", custom_id="btn_abrir_ticket_geral")
    async def abrir_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # Verifica se o membro já tem ticket aberto
        canal_nome = f"ticket-{user.name.lower()[:15]}"
        existente = discord.utils.get(guild.text_channels, name=canal_nome)
        if existente:
            await interaction.response.send_message(f"⚠️ Você já possui um atendimento aberto em {existente.mention}!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Categoria de tickets
        categoria = discord.utils.get(guild.categories, name="🎟️・ATENDIMENTO")
        if not categoria:
            try:
                categoria = await guild.create_category(name="🎟️・ATENDIMENTO")
            except Exception:
                categoria = None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        # Permissão para cargos de staff e tickets
        from utils.helpers import obter_cargo_permissao
        c_id = obter_cargo_permissao(guild.id, "staff")
        if c_id:
            role_staff = guild.get_role(c_id)
            if role_staff:
                overwrites[role_staff] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        c_tick_id = obter_cargo_permissao(guild.id, "tickets")
        if c_tick_id:
            role_tick = guild.get_role(c_tick_id)
            if role_tick:
                overwrites[role_tick] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        try:
            canal = await guild.create_text_channel(
                name=canal_nome,
                category=categoria,
                overwrites=overwrites,
                topic=f"Atendimento privado de {user.name} (ID: {user.id})",
                reason=f"Ticket aberto por {user.name}"
            )

            embed = discord.Embed(
                title="📩  ATENDIMENTO INICIADO",
                description=(
                    f"> Olá {user.mention}, seja muito bem-vindo ao seu canal privado de suporte!\n\n"
                    "• Descreva detalhadamente sua dúvida, problema ou comprovante de VIP.\n"
                    "• Um membro da nossa equipe de Staff responderá em breve.\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.INFO
            )
            embed.set_author(name=f"Ticket #{ticket_num} • {user.display_name}", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="Para encerrar o atendimento, clique no botão vermelho abaixo.")
            embed.timestamp = discord.utils.utcnow()

            view_fechar = ViewFecharTicket()
            await canal.send(content=f"{user.mention}", embed=embed, view=view_fechar)
            await interaction.followup.send(f"✅ Seu atendimento foi criado com sucesso em {canal.mention}!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Não foi possível criar seu ticket: `{e}`", ephemeral=True)


class ViewFecharTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Atendimento", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_fechar_ticket_geral")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Este ticket será excluído em **5 segundos**...", ephemeral=False)
        import asyncio
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket encerrado por {interaction.user.name}")
        except Exception:
            pass


class Tickets(commands.Cog):
    """Sistema completo de tickets e suporte."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painelticket", aliases=["ticketpainel", "criarticket", "ticket"])
    async def painelticket(self, ctx):
        """Envia o painel interativo de abertura de tickets no canal."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "tickets"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa possuir cargo de Staff ou Tickets configurado para enviar o painel de tickets.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        embed = discord.Embed(
            title="🎟️  CENTRAL DE SUPORTE & ATENDIMENTO",
            description=(
                "> Precisa de ajuda, suporte sobre VIPs ou deseja falar com a Staff?\n\n"
                "• Clique no botão **`📩 Abrir Atendimento`** abaixo para iniciar um chat privado.\n"
                "• Apenas você e a equipe de Staff terão acesso ao canal.\n\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            ),
            color=Cores.PADRAO
        )
        embed.set_author(name=f"Atendimento Oficial • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"{ctx.guild.name} • Suporte 24/7", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.timestamp = discord.utils.utcnow()

        view = ViewBotaoTicket()
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Tickets(bot))

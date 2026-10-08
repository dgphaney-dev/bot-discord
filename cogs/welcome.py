import json
from pathlib import Path
import discord
from discord.ext import commands
from config import Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem

ARQUIVO_WELCOME = Path(__file__).resolve().parent.parent / "data" / "welcome_config.json"


def carregar_config_welcome() -> dict:
    if not ARQUIVO_WELCOME.exists():
        return {}
    try:
        with open(ARQUIVO_WELCOME, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_config_welcome(dados: dict):
    ARQUIVO_WELCOME.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_WELCOME, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


class Welcome(commands.Cog):
    """Sistema de Boas-Vindas e Auto-Role."""

    def __init__(self, bot):
        self.bot = bot
        self.config_welcome = carregar_config_welcome()

    @commands.command(name="setwelcome", aliases=["configwelcome", "canalboasvindas"])
    async def setwelcome(self, ctx, canal: discord.TextChannel = None):
        """Define o canal onde as mensagens de boas-vindas serão enviadas."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "welcome"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de cargo de Staff ou Boas-Vindas configurado para esta ação.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        canal_alvo = canal or ctx.channel
        guild_id_str = str(ctx.guild.id)

        if guild_id_str not in self.config_welcome:
            self.config_welcome[guild_id_str] = {}

        self.config_welcome[guild_id_str]["canal_id"] = canal_alvo.id
        salvar_config_welcome(self.config_welcome)

        embed = discord.Embed(
            title="👋 Canal de Boas-Vindas Definido",
            description=f"O canal {canal_alvo.mention} agora receberá as boas-vindas de novos membros!",
            color=Cores.SUCESSO
        )
        await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)

    @commands.command(name="setautorole", aliases=["autorole", "cargoinicial"])
    async def setautorole(self, ctx, cargo: discord.Role = None):
        """Define o cargo inicial que novos membros recebem automaticamente ao entrar."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "welcome"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de cargo de Staff ou Boas-Vindas configurado para esta ação.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in self.config_welcome:
            self.config_welcome[guild_id_str] = {}

        if cargo is None:
            self.config_welcome[guild_id_str].pop("autorole_id", None)
            salvar_config_welcome(self.config_welcome)
            await ctx.send("🗑️ Auto-Role desativado com sucesso.", delete_after=TEMPO_DELETE_SUCESSO)
            return

        self.config_welcome[guild_id_str]["autorole_id"] = cargo.id
        salvar_config_welcome(self.config_welcome)

        embed = discord.Embed(
            title="🏷️ Auto-Role Configurado",
            description=f"Novos membros receberão automaticamente o cargo {cargo.mention} ao entrar no servidor!",
            color=Cores.SUCESSO
        )
        await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        cfg = self.config_welcome.get(str(guild.id), {})

        # 1. Atribui Auto-Role se configurado
        autorole_id = cfg.get("autorole_id")
        if autorole_id:
            role = guild.get_role(autorole_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-Role de boas-vindas")
                except Exception:
                    pass

        # 2. Envia mensagem de boas-vindas se canal estiver configurado
        canal_id = cfg.get("canal_id")
        if canal_id:
            canal = guild.get_channel(canal_id)
            if canal:
                criado_ts = int(member.created_at.timestamp())
                embed = discord.Embed(
                    title=f"🎉  BEM-VINDO(A) AO {guild.name.upper()}!",
                    description=(
                        f"> Olá {member.mention}, estamos muito felizes com a sua chegada!\n\n"
                        f"• 👥 **Posição de Entrada:** Você é o membro **#{guild.member_count}**\n"
                        f"• 📅 **Conta Criada:** <t:{criado_ts}:R>\n\n"
                        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                        "✨ *Leia as regras e divirta-se nos canais de texto e voz!*"
                    ),
                    color=Cores.PADRAO
                )
                embed.set_author(name=f"Novo Membro • {member.name}", icon_url=member.display_avatar.url)
                if member.display_avatar:
                    embed.set_thumbnail(url=member.display_avatar.url)
                if guild.icon:
                    embed.set_footer(text=f"{guild.name} • Comunidade Oficial", icon_url=guild.icon.url)
                embed.timestamp = discord.utils.utcnow()
                try:
                    await canal.send(content=f"👋 Olá {member.mention}!", embed=embed)
                except Exception:
                    pass


async def setup(bot):
    await bot.add_cog(Welcome(bot))

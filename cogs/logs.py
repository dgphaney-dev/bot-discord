import json
from pathlib import Path
import discord
from discord.ext import commands
from config import Cores, EMOJIS, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem

ARQUIVO_CANAL_LOGS = Path(__file__).resolve().parent.parent / "data" / "logs_config.json"


def carregar_config_logs() -> dict:
    if not ARQUIVO_CANAL_LOGS.exists():
        return {}
    try:
        with open(ARQUIVO_CANAL_LOGS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_config_logs(dados: dict):
    ARQUIVO_CANAL_LOGS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_CANAL_LOGS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


class Logs(commands.Cog):
    """Módulo de logs e auditoria da Staff."""

    def __init__(self, bot):
        self.bot = bot
        self.config_logs = carregar_config_logs()

    @commands.command(name="setlogs", aliases=["canallogs", "configlogs", "setlog"])
    async def setlogs(self, ctx, canal: discord.TextChannel = None):
        """Define o canal onde todos os logs de ações de moderação e eventos serão enviados."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "logs"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa possuir cargo de Staff ou Logs configurado para definir o canal de auditoria.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        canal_alvo = canal or ctx.channel
        guild_id_str = str(ctx.guild.id)

        self.config_logs[guild_id_str] = canal_alvo.id
        salvar_config_logs(self.config_logs)

        embed = discord.Embed(
            title=f"{EMOJIS['logs']}  Canal de Logs Configurado",
            description=(
                f"O canal {canal_alvo.mention} agora é o canal oficial de **Auditoria & Logs** da Staff!\n\n"
                "Todas as ações de moderação (ban, kick, mute, warn, lock) serão registradas lá automaticamente."
            ),
            color=Cores.SUCESSO
        )
        embed.set_footer(text=f"Configurado por {ctx.author.name}")
        await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)

    async def enviar_log(self, guild: discord.Guild, embed: discord.Embed):
        """Envia um log para o canal configurado da guilda se houver."""
        if not guild:
            return
        canal_id = self.config_logs.get(str(guild.id))
        if not canal_id:
            return
        canal = guild.get_channel(canal_id)
        if canal:
            try:
                await canal.send(embed=embed)
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(Logs(bot))

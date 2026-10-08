import json
from pathlib import Path
import time
import discord
from discord.ext import commands
from config import Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem

ARQUIVO_WARNS = Path(__file__).resolve().parent.parent / "data" / "warns.json"


def carregar_warns() -> dict:
    if not ARQUIVO_WARNS.exists():
        return {}
    try:
        with open(ARQUIVO_WARNS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_warns(dados: dict):
    ARQUIVO_WARNS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_WARNS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


class Warns(commands.Cog):
    """Sistema de avisos e advertências para membros."""

    def __init__(self, bot):
        self.bot = bot
        self.warns = carregar_warns()

    @commands.command(name="warn", aliases=["advertir", "aviso"])
    async def warn(self, ctx, membro: discord.Member, *, motivo: str = "Não especificado"):
        """Aplica uma advertência oficial a um membro."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "warn") and not tem_permissao_acao(ctx, "mute"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa possuir cargo de Staff ou Advertências configurado para aplicar advertências.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro == ctx.author:
            await ctx.send("❌ Você não pode advertir a si mesmo.", delete_after=TEMPO_DELETE_ERRO)
            return

        if membro.guild_permissions.administrator:
            await ctx.send("❌ Você não pode advertir um Administrador.", delete_after=TEMPO_DELETE_ERRO)
            return

        guild_id_str = str(ctx.guild.id)
        user_id_str = str(membro.id)

        if guild_id_str not in self.warns:
            self.warns[guild_id_str] = {}
        if user_id_str not in self.warns[guild_id_str]:
            self.warns[guild_id_str][user_id_str] = []

        nova_warn = {
            "id": len(self.warns[guild_id_str][user_id_str]) + 1,
            "motivo": motivo,
            "mod_id": ctx.author.id,
            "mod_nome": ctx.author.name,
            "timestamp": int(time.time())
        }
        self.warns[guild_id_str][user_id_str].append(nova_warn)
        salvar_warns(self.warns)

        total_warns = len(self.warns[guild_id_str][user_id_str])

        # Envia aviso na DM
        try:
            embed_dm = discord.Embed(
                title=f"⚠️ Você recebeu uma advertência em {ctx.guild.name}",
                description=f"**Motivo:** {motivo}\n**Total de Advertências:** `{total_warns}`",
                color=Cores.AVISO
            )
            await membro.send(embed=embed_dm)
        except Exception:
            pass

        embed = discord.Embed(
            title="⚠️  ADVERTÊNCIA REGISTRADA",
            description=(
                f"O membro {membro.mention} recebeu uma advertência oficial.\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.AVISO
        )
        embed.add_field(name="👤  Membro", value=f"{membro.mention}\n`@{membro.name}`", inline=True)
        embed.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)
        embed.add_field(name="📊  Total Acumulado", value=f"```fix\n{total_warns} advertência(s)\n```", inline=True)
        embed.add_field(name="📋  Motivo", value=f"```yaml\n{motivo}\n```", inline=False)
        embed.set_footer(text=f"ID do Usuário: {membro.id}")
        await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)

        # Log
        cog_logs = self.bot.get_cog("Logs")
        if cog_logs:
            embed_log = discord.Embed(
                title="⚠️ Membro Advertido (Warn)",
                description=f"{membro.mention} recebeu a advertência #{nova_warn['id']} de {ctx.author.mention}.\n**Motivo:** {motivo}",
                color=Cores.AVISO
            )
            await cog_logs.enviar_log(ctx.guild, embed_log)

    @commands.command(name="warns", aliases=["advertencias", "verwarns"])
    async def warns(self, ctx, membro: discord.Member = None):
        """Consulta as advertências de um membro ou as suas próprias."""
        await tentar_deletar_mensagem(ctx)

        alvo = membro or ctx.author
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(alvo.id)

        lista = self.warns.get(guild_id_str, {}).get(user_id_str, [])

        embed = discord.Embed(
            title=f"📋 Histórico de Advertências de {alvo.name}",
            description=f"Total de advertências ativas: **{len(lista)}**\n──────────────────────────────────────────────",
            color=Cores.INFO
        )

        if not lista:
            embed.description += "\n*Nenhuma advertência registrada para este usuário.*"
        else:
            for w in lista[-10:]:
                data_str = f"<t:{w['timestamp']}:R>"
                embed.add_field(
                    name=f"Advertência #{w['id']} • {data_str}",
                    value=f"• **Motivo:** {w['motivo']}\n• **Moderador:** {w['mod_nome']}",
                    inline=False
                )

        await ctx.send(embed=embed, delete_after=30)

    @commands.command(name="unwarn", aliases=["removerwarn", "tirarwarn"])
    async def unwarn(self, ctx, membro: discord.Member, indice: int = None):
        """Remove a última advertência ou uma específica pelo número (#)."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "warn") and not tem_permissao_acao(ctx, "mute"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de cargo de Staff ou Advertências configurado para remover advertências.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        guild_id_str = str(ctx.guild.id)
        user_id_str = str(membro.id)

        lista = self.warns.get(guild_id_str, {}).get(user_id_str, [])
        if not lista:
            await ctx.send(f"⚠️ {membro.mention} não possui advertências registradas.", delete_after=TEMPO_DELETE_ERRO)
            return

        if indice is None:
            removida = lista.pop()
        else:
            removida = None
            for i, w in enumerate(lista):
                if w["id"] == indice:
                    removida = lista.pop(i)
                    break
            if not removida:
                await ctx.send(f"❌ Advertência com ID #{indice} não encontrada.", delete_after=TEMPO_DELETE_ERRO)
                return

        salvar_warns(self.warns)
        embed = discord.Embed(
            title="🗑️ Advertência Removida",
            description=f"A advertência #{removida['id']} de {membro.mention} foi removida por {ctx.author.mention}.\nRestam: `{len(lista)}`",
            color=Cores.SUCESSO
        )
        await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)


async def setup(bot):
    await bot.add_cog(Warns(bot))

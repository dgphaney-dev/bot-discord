import discord
from discord.ext import commands
from config import Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem


class Canais(commands.Cog):
    """Controle de canais: lock, unlock e slowmode."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lock", aliases=["trancar", "fecharcanal"])
    async def lock(self, ctx, canal: discord.TextChannel = None, *, motivo: str = "Não especificado"):
        """Tranca o canal de texto para membros comuns não enviarem mensagens."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "canais") and not tem_permissao_acao(ctx, "clear"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa possuir cargo de Staff ou Gestão de Canais para trancar canais.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        canal_alvo = canal or ctx.channel

        try:
            overwrites = canal_alvo.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = False
            await canal_alvo.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Trancado por {ctx.author.name}: {motivo}")

            embed = discord.Embed(
                title="🔒  CANAL TRANCADO",
                description=(
                    f"> O canal {canal_alvo.mention} foi temporariamente trancado pela moderação.\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.AVISO
            )
            embed.set_author(name=f"Controle de Canais • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.add_field(name="🛡️  Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="📋  Motivo", value=f"```fix\n{motivo}\n```", inline=False)
            embed.set_footer(text="Apenas a equipe de Staff pode digitar aqui no momento.", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await canal_alvo.send(embed=embed)

            # Notifica log
            cog_logs = self.bot.get_cog("Logs")
            if cog_logs:
                embed_log = discord.Embed(
                    title="🔒 Canal Trancado (Lock)",
                    description=f"O canal {canal_alvo.mention} foi trancado por {ctx.author.mention}.\n**Motivo:** {motivo}",
                    color=Cores.AVISO
                )
                embed_log.timestamp = discord.utils.utcnow()
                await cog_logs.enviar_log(ctx.guild, embed_log)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Falha ao Trancar",
                description="O bot não tem permissão para gerenciar permissões deste canal.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @commands.command(name="unlock", aliases=["destrancar", "abrircanal"])
    async def unlock(self, ctx, canal: discord.TextChannel = None):
        """Destranca o canal de texto permitindo o envio de mensagens novamente."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "canais") and not tem_permissao_acao(ctx, "clear"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa possuir cargo de Staff ou Gestão de Canais para destrancar canais.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        canal_alvo = canal or ctx.channel

        try:
            overwrites = canal_alvo.overwrites_for(ctx.guild.default_role)
            overwrites.send_messages = None
            await canal_alvo.set_permissions(ctx.guild.default_role, overwrite=overwrites, reason=f"Destrancado por {ctx.author.name}")

            embed = discord.Embed(
                title="🔓  CANAL DESTRANCADO",
                description=(
                    f"> O canal {canal_alvo.mention} foi destrancado com sucesso!\n\n"
                    "• O envio de mensagens foi liberado para todos os membros.\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.SUCESSO
            )
            embed.set_author(name=f"Controle de Canais • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"Liberado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await canal_alvo.send(embed=embed)

            # Notifica log
            cog_logs = self.bot.get_cog("Logs")
            if cog_logs:
                embed_log = discord.Embed(
                    title="🔓 Canal Destrancado (Unlock)",
                    description=f"O canal {canal_alvo.mention} foi liberado por {ctx.author.mention}.",
                    color=Cores.SUCESSO
                )
                embed_log.timestamp = discord.utils.utcnow()
                await cog_logs.enviar_log(ctx.guild, embed_log)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Falha ao Destrancar",
                description="O bot não tem permissão para gerenciar permissões deste canal.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @commands.command(name="slowmode", aliases=["modolento", "slow"])
    async def slowmode(self, ctx, segundos: int, canal: discord.TextChannel = None):
        """Define o modo lento do canal em segundos (0 para desligar)."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "canais") and not tem_permissao_acao(ctx, "clear"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa possuir cargo de Staff ou Gestão de Canais para alterar o modo lento.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        canal_alvo = canal or ctx.channel
        segundos_clamped = max(0, min(21600, segundos))

        try:
            await canal_alvo.edit(slowmode_delay=segundos_clamped)
            status_txt = "desativado" if segundos_clamped == 0 else f"definido para **{segundos_clamped} segundos**"
            embed = discord.Embed(
                title="⏱️  MODO LENTO ATUALIZADO",
                description=(
                    f"> O modo lento em {canal_alvo.mention} foi {status_txt}.\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.INFO
            )
            embed.set_author(name=f"Controle de Canais • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"Definido por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro",
                description=f"Não foi possível alterar o modo lento:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)


async def setup(bot):
    await bot.add_cog(Canais(bot))

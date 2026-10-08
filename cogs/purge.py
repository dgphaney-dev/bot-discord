import discord
from discord.ext import commands
from config import Cores, LIMITE_PURGE_MAX, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem


class Limpar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear", aliases=["clean", "limpar"])
    async def clear(self, ctx, quantidade: int):
        """Limpa uma quantidade específica de mensagens do canal atual."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "clear"):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Gerenciar Mensagens` ou do cargo configurado para limpar o chat.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if quantidade <= 0:
            embed = discord.Embed(
                title="⚠️ Quantidade Inválida",
                description="Você precisa informar um número maior que **0** para limpar.",
                color=Cores.AVISO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if quantidade > LIMITE_PURGE_MAX:
            embed = discord.Embed(
                title="⚠️ Limite Excedido",
                description=f"Por segurança, o limite máximo de mensagens para apagar de uma vez é **{LIMITE_PURGE_MAX}**.",
                color=Cores.AVISO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        try:
            apagadas = await ctx.channel.purge(limit=quantidade)
            total_apagadas = len(apagadas)

            embed = discord.Embed(
                title="🧹  LIMPEZA DE CHAT CONCLUÍDA",
                description=(
                    f"> Foram removidas **{total_apagadas} mensagens** no canal {ctx.channel.mention}!\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.SUCESSO
            )
            embed.set_author(name=f"Faxina de Mensagens • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.add_field(name="🗑️  Mensagens Apagadas", value=f"```fix\n{total_apagadas} msgs\n```", inline=True)
            embed.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)

            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)

            embed.set_footer(text=f"{ctx.guild.name} • Apaga em {TEMPO_DELETE_SUCESSO}s", icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_SUCESSO)

        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permissão Insuficiente do Bot",
                description="Eu não tenho a permissão de `Gerenciar Mensagens` neste canal para realizar a limpeza.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        except discord.HTTPException as e:
            if "14 days old" in str(e):
                embed = discord.Embed(
                    title="⚠️ Limitação do Discord",
                    description="O Discord impede a remoção em massa de mensagens enviadas há mais de **14 dias**.",
                    color=Cores.AVISO
                )
                await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            else:
                embed = discord.Embed(
                    title="❌ Erro Inesperado",
                    description=f"Ocorreu um erro ao tentar limpar o chat:\n`{e}`",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    @clear.error
    async def clear_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)

        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Gerenciar Mensagens` para usar este comando.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa definir a quantidade de mensagens que deseja apagar.\n\n**Exemplo:** `!clear 50`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Argumento Inválido",
                description="Por favor, digite um número inteiro válido para a limpeza.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)


async def setup(bot):
    await bot.add_cog(Limpar(bot))
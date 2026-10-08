import time
import discord
from discord import app_commands
from discord.ext import commands

from config import Cores, PREFIXO, TEMPO_DELETE_SUCESSO
from utils.helpers import tentar_deletar_mensagem


class SlashCommands(commands.Cog):
    """Módulo com Comandos de Barra (Slash Commands) para ativar as insígnias do Discord."""

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # COMANDO SLASH: /ping
    # ========================================================
    @app_commands.command(
        name="ping",
        description="Verifica a latência e o tempo de resposta do bot (ativa insígnia de Dev)."
    )
    async def ping_slash(self, interaction: discord.Interaction):
        """Responde com a latência do bot no Discord."""
        t0 = time.time()
        # Responde primeiro
        await interaction.response.defer(ephemeral=False)
        t1 = time.time()

        latencia_ms = round(self.bot.latency * 1000)
        api_ms = round((t1 - t0) * 1000)

        embed = discord.Embed(
            title="🏓 Pong! Tudo Tranquilo por Aqui!",
            description=(
                f"Fala {interaction.user.mention}, tô suave e 100% online!\n\n"
                f"📡 **Latência do WebSocket:** `{latencia_ms}ms`\n"
                f"⚡ **Tempo de Resposta da API:** `{api_ms}ms`\n\n"
                f"🎯 *Esse comando valida o bot para as insígnias de Slash Commands `{{/}}` e Active Developer 🤖!*"
            ),
            color=Cores.SUCESSO
        )
        if interaction.client.user.display_avatar:
            embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
        embed.set_footer(text="Desenvolvido para o servidor valorant dos crias")

        await interaction.followup.send(embed=embed)

    # ========================================================
    # COMANDO SLASH: /ajuda
    # ========================================================
    @app_commands.command(
        name="ajuda",
        description="Exibe os comandos disponíveis e as informações do servidor."
    )
    async def ajuda_slash(self, interaction: discord.Interaction):
        """Mostra informações sobre os comandos e módulos do bot."""
        embed = discord.Embed(
            title="📖 Central de Comandos - Aspas",
            description=(
                f"Seja bem-vindo! Aqui estão as principais funções do bot no servidor:\n\n"
                f"• 🤖 **Conversar com o Aspas:** Basta me mencionar no chat (`@{self.bot.user.name} sua pergunta`) sem prefixo nenhum!\n"
                f"• 💎 **Sistema VIP:** Digite `{PREFIXO}vip` para ver seus benefícios.\n"
                f"• ⚙️ **Painel Completo:** Digite `{PREFIXO}painel` para abrir a central interativa.\n"
                f"• 🛡️ **Permissões:** Digite `{PREFIXO}permissoes` para gerenciar cargos.\n"
                f"• 🧹 **Limpeza:** Digite `{PREFIXO}clear <qtd>` para limpar mensagens."
            ),
            color=Cores.INFO
        )
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text=f"Prefixo dos comandos de texto: {PREFIXO}")

        await interaction.response.send_message(embed=embed)

    # ========================================================
    # COMANDO SLASH: /perfil
    # ========================================================
    @app_commands.command(
        name="perfil",
        description="Mostra suas informações e dados da sua conta no servidor."
    )
    async def perfil_slash(self, interaction: discord.Interaction, membro: discord.Member = None):
        """Exibe o perfil do usuário no servidor."""
        alvo = membro or interaction.user

        embed = discord.Embed(
            title=f"👤 Perfil de {alvo.display_name}",
            color=alvo.color if alvo.color.value != 0 else Cores.PADRAO
        )
        embed.set_thumbnail(url=alvo.display_avatar.url)
        embed.add_field(name="Nome de Usuário", value=f"`{alvo.name}`", inline=True)
        embed.add_field(name="ID", value=f"`{alvo.id}`", inline=True)
        embed.add_field(name="Conta Criada", value=f"<t:{int(alvo.created_at.timestamp())}:D>", inline=True)
        if isinstance(alvo, discord.Member):
            embed.add_field(name="Entrou no Servidor", value=f"<t:{int(alvo.joined_at.timestamp())}:D>", inline=True)
            cargos_str = " ".join([r.mention for r in alvo.roles if r.name != "@everyone"])
            embed.add_field(name="Cargos", value=cargos_str or "*Nenhum cargo*", inline=False)

        await interaction.response.send_message(embed=embed)

    # ========================================================
    # COMANDO DE PREFIXO: !sync (Administrador)
    # ========================================================
    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_comandos(self, ctx):
        """Sincroniza manualmente todos os comandos de barra (Slash) com o Discord."""
        await tentar_deletar_mensagem(ctx)

        msg_aviso = await ctx.send(
            embed=discord.Embed(
                title="🔄 Sincronizando...",
                description="Enviando a lista de comandos Slash para a API do Discord...",
                color=Cores.INFO
            )
        )

        try:
            # Sincroniza tanto para o servidor atual (imediato) quanto globalmente
            self.bot.tree.copy_global_to(guild=ctx.guild)
            sincronizados_guild = await self.bot.tree.sync(guild=ctx.guild)
            sincronizados_global = await self.bot.tree.sync()

            await msg_aviso.delete()

            embed_sucesso = discord.Embed(
                title="✨ Comandos Slash Sincronizados!",
                description=(
                    f"Foram sincronizados **{len(sincronizados_guild)} comandos** neste servidor e **{len(sincronizados_global)} comandos globalmente**!\n\n"
                    "🎉 Os comandos já estão disponíveis digitando `/` no chat.\n"
                    "Ao usar `/ping`, você já se qualifica para a insígnia de **Desenvolvedor Ativo**!"
                ),
                color=Cores.SUCESSO
            )
            await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)

        except Exception as e:
            await msg_aviso.delete()
            embed_erro = discord.Embed(
                title="❌ Erro na Sincronização",
                description=f"Ocorreu um erro ao sincronizar os comandos:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=10)


async def setup(bot):
    await bot.add_cog(SlashCommands(bot))

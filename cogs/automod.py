import discord
from discord.ext import commands
from config import Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tentar_deletar_mensagem


class AutoModCog(commands.Cog, name="AutoMod"):
    """Módulo responsável pelo gerenciamento de regras oficiais do AutoMod do Discord."""

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # COMANDO: PAINEL / CRIAR REGRAS DE AUTOMOD (!automod)
    # ========================================================
    @commands.command(name="automod", aliases=["configautomod", "regrasautomod"])
    @commands.has_permissions(manage_guild=True)
    async def automod(self, ctx):
        """Abre o painel interativo de configuração de regras oficiais do AutoMod."""
        await tentar_deletar_mensagem(ctx)

        guild = ctx.guild
        try:
            regras = await guild.fetch_automod_rules()
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="O bot precisa da permissão de **Gerenciar Servidor (Manage Server)** para gerenciar o AutoMod.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        embed = discord.Embed(
            title="🛡️  GERENCIADOR OFICIAL DE AUTOMOD",
            description=(
                f"Olá {ctx.author.mention}, configure as regras de moderação automática nativas do Discord!\n\n"
                "Ao criar regras oficiais através do bot, ele passa a moderar ativamente o servidor "
                "e qualifica para a **Insígnia de AutoMod** no perfil do aplicativo!\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.PADRAO
        )

        if regras:
            regras_txt = "\n".join([f"• 🔒 **{r.name}** (`{'Ativo' if r.enabled else 'Desativado'}`)" for r in regras[:10]])
            embed.add_field(name=f"📋  Regras Ativas no Servidor ({len(regras)})", value=regras_txt, inline=False)
        else:
            embed.add_field(
                name="📋  Regras Ativas no Servidor",
                value="*Nenhuma regra oficial criada ainda. Use os botões abaixo para instalar as proteções recomendadas!*",
                inline=False
            )

        embed.add_field(
            name="⚡  Ações Rápidas Disponíveis",
            value=(
                "• 🚫 **Anti-Convites:** Bloqueia links de outros servidores (`discord.gg`)\n"
                "• 📢 **Anti-Mass Mention:** Bloqueia mensagens com mais de 5 menções\n"
                "• 🤬 **Anti-Palavrões:** Bloqueia ofensas e termos tóxicos selecionados\n"
                "• 🗑️ **Limpar Regras:** Exclui regras criadas pelo bot"
            ),
            inline=False
        )
        embed.set_footer(text="Requer permissão de Gerenciar Servidor • Discord AutoMod API")

        view = ViewPainelAutoMod(self, ctx.author)
        await ctx.send(embed=embed, view=view, delete_after=120)

    @automod.error
    async def automod_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa ter permissão de `Gerenciar Servidor` para configurar o AutoMod.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)


class ViewPainelAutoMod(discord.ui.View):
    def __init__(self, cog: AutoModCog, autor: discord.Member):
        super().__init__(timeout=120)
        self.cog = cog
        self.autor = autor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor.id and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Apenas quem abriu o painel pode interagir.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Ativar Anti-Convites", emoji="🚫", style=discord.ButtonStyle.primary)
    async def btn_anti_convites(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        try:
            # Verifica se já existe
            regras = await guild.fetch_automod_rules()
            nome_regra = "🛡️・Anti-Convites (Aspas Bot)"
            if any(r.name == nome_regra for r in regras):
                await interaction.followup.send("⚠️ Esta regra já está ativa no servidor!", ephemeral=True)
                return

            await guild.create_automod_rule(
                name=nome_regra,
                event_type=discord.AutoModRuleEventType.message_send,
                trigger=discord.AutoModTrigger(
                    type=discord.AutoModRuleTriggerType.keyword,
                    keyword_filter=["*discord.gg/*", "*discord.com/invite/*"]
                ),
                actions=[
                    discord.AutoModRuleAction(
                        type=discord.AutoModRuleActionType.block_message,
                        custom_message="Divulgação de outros servidores não é permitida aqui."
                    )
                ],
                enabled=True,
                reason="AutoMod configurado pelo painel"
            )

            await interaction.followup.send("✅ Regra oficial de **Anti-Convites** instalada com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Não foi possível criar a regra: `{e}`", ephemeral=True)

    @discord.ui.button(label="Ativar Anti-Menção em Massa", emoji="📢", style=discord.ButtonStyle.primary)
    async def btn_anti_mencao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        try:
            regras = await guild.fetch_automod_rules()
            nome_regra = "🛡️・Anti-Mass Mention (Aspas Bot)"
            if any(r.name == nome_regra for r in regras):
                await interaction.followup.send("⚠️ Esta regra já está ativa no servidor!", ephemeral=True)
                return

            await guild.create_automod_rule(
                name=nome_regra,
                event_type=discord.AutoModRuleEventType.message_send,
                trigger=discord.AutoModTrigger(
                    type=discord.AutoModRuleTriggerType.mention_spam,
                    mention_limit=5
                ),
                actions=[
                    discord.AutoModRuleAction(
                        type=discord.AutoModRuleActionType.block_message,
                        custom_message="Você mencionou muitos membros de uma vez."
                    )
                ],
                enabled=True,
                reason="AutoMod configurado pelo painel"
            )

            await interaction.followup.send("✅ Regra oficial de **Anti-Menção em Massa** (limite: 5) instalada com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Não foi possível criar a regra: `{e}`", ephemeral=True)

    @discord.ui.button(label="Remover Regras do Bot", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def btn_limpar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        try:
            regras = await guild.fetch_automod_rules()
            removidas = 0
            for r in regras:
                if "Aspas Bot" in r.name:
                    await r.delete(reason="Regra removida pelo moderador")
                    removidas += 1

            if removidas > 0:
                await interaction.followup.send(f"🗑️ Foram removidas **{removidas}** regras criadas pelo bot.", ephemeral=True)
            else:
                await interaction.followup.send("ℹ️ Nenhuma regra criada pelo bot foi encontrada para remover.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Falha ao limpar regras: `{e}`", ephemeral=True)


async def setup(bot):
    await bot.add_cog(AutoModCog(bot))

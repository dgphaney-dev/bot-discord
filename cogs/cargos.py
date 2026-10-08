import asyncio
import discord
from discord.ext import commands
from config import Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem


class ModalCriarCargo(discord.ui.Modal, title="Criar Novo Cargo"):
    nome_cargo = discord.ui.TextInput(
        label="Nome do Cargo",
        placeholder="Digite o nome do cargo...",
        required=True,
        max_length=100
    )
    cor_cargo = discord.ui.TextInput(
        label="Cor do Cargo (Hexadecimal)",
        placeholder="#FF0000 ou FF0000 (Opcional)",
        required=False,
        max_length=7
    )
    permissoes_cargo = discord.ui.TextInput(
        label="Permissões (separe por vírgula)",
        placeholder="admin, ban, kick, mensagens, gerenciar_canais, gerenciar_cargos",
        style=discord.TextStyle.paragraph,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        nome = self.nome_cargo.value.strip()
        cor_hex = self.cor_cargo.value.strip() if self.cor_cargo.value else ""
        perms_texto = self.permissoes_cargo.value.lower() if self.permissoes_cargo.value else ""

        # Parser para cor hexadecimal
        cor = discord.Color.default()
        if cor_hex:
            if not cor_hex.startswith("#"):
                cor_hex = f"#{cor_hex}"
            try:
                cor = discord.Color.from_str(cor_hex)
            except ValueError:
                embed_aviso = discord.Embed(
                    title="⚠️ Cor Inválida",
                    description="O código hexadecimal fornecido é inválido. O cargo será criado com a cor padrão.",
                    color=Cores.AVISO
                )
                await interaction.followup.send(embed=embed_aviso, ephemeral=True)

        # Mapeamento de permissões
        perms = discord.Permissions.none()
        if perms_texto:
            lista_perms = [p.strip() for p in perms_texto.split(",")]
            if "admin" in lista_perms or "administrador" in lista_perms:
                perms.administrator = True
            if "ban" in lista_perms or "banir" in lista_perms:
                perms.ban_members = True
            if "kick" in lista_perms or "expulsar" in lista_perms:
                perms.kick_members = True
            if "mensagens" in lista_perms or "enviar_mensagens" in lista_perms:
                perms.send_messages = True
            if "gerenciar_canais" in lista_perms:
                perms.manage_channels = True
            if "gerenciar_cargos" in lista_perms:
                perms.manage_roles = True

        try:
            novo_cargo = await guild.create_role(
                name=nome,
                color=cor,
                permissions=perms,
                reason=f"Criado via painel por {interaction.user.name}"
            )

            embed = discord.Embed(
                title="✅ Cargo Criado com Sucesso!",
                description=f"O cargo {novo_cargo.mention} foi gerado com as configurações solicitadas.",
                color=novo_cargo.color if novo_cargo.color.value != 0 else Cores.SUCESSO
            )
            embed.add_field(name="Nome", value=f"`{novo_cargo.name}`", inline=True)
            embed.add_field(name="Cor Hex", value=f"`{str(novo_cargo.color)}`", inline=True)
            embed.add_field(name="Administrador", value="`Sim`" if perms.administrator else "`Não`", inline=False)

            msg = await interaction.followup.send(embed=embed, ephemeral=False, wait=True)

            await asyncio.sleep(TEMPO_DELETE_SUCESSO)
            try:
                await msg.delete()
            except (discord.NotFound, discord.HTTPException):
                pass

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Eu não tenho a permissão de `Gerenciar Cargos` necessária para criar este cargo.",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro ao Criar Cargo",
                description=f"Ocorreu um erro inesperado ao tentar gerar o cargo:\n`{e}`",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)


class ViewCriarCargo(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Criar Cargo", style=discord.ButtonStyle.green, custom_id="btn_criar_cargo", emoji="➕")
    async def botao_criar_cargo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            embed_erro = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Gerenciar Cargos` para usar este recurso.",
                color=Cores.ERRO
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return

        await interaction.response.send_modal(ModalCriarCargo())


class SelectSetCargo(discord.ui.RoleSelect):
    def __init__(self, membro: discord.Member):
        self.membro = membro
        super().__init__(
            placeholder="Selecione o cargo que deseja atribuir/remover...",
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_roles:
            embed_erro = discord.Embed(
                title="❌ Permissão Negada",
                description="Você não tem a permissão de `Gerenciar Cargos` necessária para realizar essa ação.",
                color=Cores.ERRO
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return

        cargo_selecionado = self.values[0]

        # Hierarquia do bot
        if cargo_selecionado >= interaction.guild.me.top_role:
            embed_erro = discord.Embed(
                title="❌ Hierarquia do Bot",
                description="Este cargo é igual ou superior ao meu cargo mais alto. Não posso gerenciá-lo.",
                color=Cores.ERRO
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return

        # Hierarquia do usuário
        if cargo_selecionado >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            embed_erro = discord.Embed(
                title="❌ Hierarquia de Membro",
                description="Você não pode gerenciar um cargo que seja superior ou igual ao seu próprio cargo mais alto.",
                color=Cores.ERRO
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return

        try:
            if cargo_selecionado in self.membro.roles:
                await self.membro.remove_roles(cargo_selecionado, reason=f"Alterado por {interaction.user.name}")
                embed_sucesso = discord.Embed(
                    title="🗑️ Cargo Removido",
                    description=f"O cargo {cargo_selecionado.mention} foi removido com sucesso de {self.membro.mention}!",
                    color=Cores.ERRO
                )
                await interaction.response.send_message(embed=embed_sucesso, ephemeral=True)
            else:
                await self.membro.add_roles(cargo_selecionado, reason=f"Alterado por {interaction.user.name}")
                embed_sucesso = discord.Embed(
                    title="✅ Cargo Adicionado",
                    description=f"O cargo {cargo_selecionado.mention} foi atribuído com sucesso a {self.membro.mention}!",
                    color=Cores.SUCESSO
                )
                await interaction.response.send_message(embed=embed_sucesso, ephemeral=True)
        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Erro de Permissão",
                description="Não tenho permissões suficientes no servidor para alterar este cargo específico.",
                color=Cores.ERRO
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)


class ViewSetCargo(discord.ui.View):
    def __init__(self, membro: discord.Member):
        super().__init__(timeout=60)
        self.add_item(SelectSetCargo(membro))


class Cargos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cargos", aliases=["painel_cargos"])
    async def cargos(self, ctx):
        """Envia um botão no chat que abre o formulário interativo de criação de cargos."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "cargos"):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa de permissão de `Gerenciar Cargos` ou do cargo autorizado para criar cargos.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        embed = discord.Embed(
            title="🏷️ Painel de Criação de Cargos",
            description=(
                "Clique no botão abaixo para abrir o formulário interativo (Modal) "
                "e configurar um novo cargo diretamente pelo chat."
            ),
            color=Cores.SUCESSO
        )
        embed.set_footer(text="Apenas membros autorizados podem usar este painel.")
        await ctx.send(embed=embed, view=ViewCriarCargo(), delete_after=30)

    @cargos.error
    async def cargos_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você não tem permissão para usar este comando.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    @commands.command(name="setcargo")
    async def setcargo(self, ctx, membro: discord.Member):
        """Abre um menu interativo de seleção de cargos para adicionar ou remover do usuário mencionado."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "cargos"):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa de permissão de `Gerenciar Cargos` ou do cargo autorizado para alterar cargos.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        embed = discord.Embed(
            title="🏷️ Gerenciar Cargos de Membro",
            description=f"Selecione no menu abaixo o cargo que você deseja adicionar ou remover de {membro.mention}.",
            color=Cores.MODERACAO
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text="O menu de seleção expira automaticamente em 60 segundos.")
        await ctx.send(embed=embed, view=ViewSetCargo(membro), delete_after=60)

    @setcargo.error
    async def setcargo_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)

        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Gerenciar Cargos` para usar este comando.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa mencionar o membro para gerenciar cargos!\n\n**Exemplo:** `!setcargo @Usuario`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Membro Não Encontrado",
                description="O membro informado não foi encontrado neste servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)


async def setup(bot):
    await bot.add_cog(Cargos(bot))
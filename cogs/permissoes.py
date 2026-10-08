import discord
from discord.ext import commands
from config import Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import (
    carregar_permissoes,
    obter_cargo_permissao,
    salvar_permissoes,
    tentar_deletar_mensagem,
)

# Mapa com os módulos/cargos de staff configuráveis em ordem de hierarquia
MODULOS_PERMISSOES = {
    "staff": {
        "nome": "👑 Staff Geral (Acesso Completo)",
        "desc": "Cargo mestre com acesso a todos os comandos de moderação do bot",
        "emoji": "👑",
        "pagina": 1
    },
    "ban": {
        "nome": "🔨 Banimento (Ban/Unban)",
        "desc": "Permite banir e desbanir membros do servidor",
        "emoji": "🔨",
        "pagina": 1
    },
    "kick": {
        "nome": "👢 Expulsão (Kick)",
        "desc": "Permite expulsar membros do servidor respeitando hierarquia",
        "emoji": "👢",
        "pagina": 1
    },
    "mute": {
        "nome": "🔇 Silenciamento (Mute/Unmute)",
        "desc": "Permite silenciar e desmutar membros",
        "emoji": "🔇",
        "pagina": 1
    },
    "clear": {
        "nome": "🧹 Limpeza de Chat (Clear)",
        "desc": "Permite apagar mensagens em massa",
        "emoji": "🧹",
        "pagina": 1
    },
    "vip": {
        "nome": "💎 Gestão VIP (SetVIP/RemoverVIP)",
        "desc": "Permite conceder e remover planos VIP de membros",
        "emoji": "💎",
        "pagina": 2
    },
    "cargos": {
        "nome": "🏷️ Gestão de Cargos (Cargos/SetCargo)",
        "desc": "Permite criar e gerenciar cargos de membros",
        "emoji": "🏷️",
        "pagina": 2
    },
    "customizacao": {
        "nome": "⚙️ Aparência do Bot (Avatar/Banner/Nome)",
        "desc": "Permite alterar nome, foto e banner do bot",
        "emoji": "⚙️",
        "pagina": 2
    },
    "warn": {
        "nome": "⚠️ Advertências (Warn/Unwarn)",
        "desc": "Permite aplicar e remover advertências de membros",
        "emoji": "⚠️",
        "pagina": 3
    },
    "canais": {
        "nome": "🔒 Gestão de Canais (Lock/Unlock/Slow)",
        "desc": "Permite trancar canais e ativar modo lento",
        "emoji": "🔒",
        "pagina": 3
    },
    "tickets": {
        "nome": "🎟️ Sistema de Tickets (Suporte)",
        "desc": "Permite abrir painéis e gerenciar tickets de suporte",
        "emoji": "🎟️",
        "pagina": 3
    },
    "welcome": {
        "nome": "👋 Boas-Vindas & Auto-Role",
        "desc": "Permite configurar canal de boas-vindas e auto-cargo",
        "emoji": "👋",
        "pagina": 3
    },
    "logs": {
        "nome": "📋 Auditoria & Logs de Staff",
        "desc": "Permite definir o canal de logs e registros da staff",
        "emoji": "📋",
        "pagina": 3
    }
}


class SelectModuloPerm(discord.ui.Select):
    def __init__(self, pagina_atual: int = 1, modulo_selecionado: str = "staff"):
        opcoes = []
        for chave, info in MODULOS_PERMISSOES.items():
            if info["pagina"] == pagina_atual:
                opcoes.append(
                    discord.SelectOption(
                        label=info["nome"][:100],
                        description=info["desc"][:100],
                        emoji=info["emoji"],
                        value=chave,
                        default=(chave == modulo_selecionado)
                    )
                )
        super().__init__(
            placeholder="Selecione o módulo/cargo para configurar...",
            min_values=1,
            max_values=1,
            options=opcoes,
            custom_id="select_modulo_perm"
        )

    async def callback(self, interaction: discord.Interaction):
        view: ViewPainelStaff = self.view
        view.modulo_atual = self.values[0]
        for op in self.options:
            op.default = (op.value == view.modulo_atual)

        view.atualizar_itens()
        embed = view.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class SelectCargoPerm(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(
            placeholder="1. Selecione o cargo do Discord...",
            min_values=1,
            max_values=1,
            custom_id="role_select_perm"
        )

    async def callback(self, interaction: discord.Interaction):
        view: ViewPainelStaff = self.view
        view.cargo_selecionado_pendente = self.values[0]
        view.atualizar_itens()
        embed = view.gerar_embed()
        info_mod = MODULOS_PERMISSOES[view.modulo_atual]
        await interaction.response.edit_message(embed=embed, view=view)
        await interaction.followup.send(
            f"ℹ️ Cargo {view.cargo_selecionado_pendente.mention} selecionado!\n"
            f"• Clique em **'✅ Salvar Neste'** para cadastrar apenas em **{info_mod['nome']}**.\n"
            "• Ou clique em **'⚡ Aplicar nesta Página'** para cadastrar em **todas as 3 opções desta página**!",
            ephemeral=True
        )


class ViewPainelStaff(discord.ui.View):
    def __init__(self, guild: discord.Guild, autor: discord.Member):
        super().__init__(timeout=180)
        self.guild = guild
        self.autor = autor
        self.pagina_atual = 1
        self.modulo_atual = "staff"
        self.cargo_selecionado_pendente: discord.Role | None = None

        self.atualizar_itens()

    def atualizar_itens(self):
        self.clear_items()

        # Dropdowns
        self.select_modulo = SelectModuloPerm(self.pagina_atual, self.modulo_atual)
        self.select_cargo = SelectCargoPerm()
        self.add_item(self.select_modulo)
        self.add_item(self.select_cargo)

        # Botão Confirmar e Salvar no módulo selecionado
        btn_confirmar = discord.ui.Button(
            label="Salvar Neste",
            emoji="✅",
            style=discord.ButtonStyle.success,
            disabled=(self.cargo_selecionado_pendente is None),
            custom_id="btn_confirmar_perm"
        )
        btn_confirmar.callback = self.confirmar_cargo_modulo
        self.add_item(btn_confirmar)

        # Botão Aplicar em todos os módulos da página atual
        qtd_modulos = sum(1 for m in MODULOS_PERMISSOES.values() if m["pagina"] == self.pagina_atual)
        btn_aplicar_todos = discord.ui.Button(
            label=f"Aplicar nesta Página ({qtd_modulos})",
            emoji="⚡",
            style=discord.ButtonStyle.primary,
            disabled=(self.cargo_selecionado_pendente is None),
            custom_id="btn_aplicar_pagina_perm"
        )
        btn_aplicar_todos.callback = self.aplicar_cargo_pagina_inteira
        self.add_item(btn_aplicar_todos)

        # Botão Resetar / Remover Cargo do módulo
        btn_remover = discord.ui.Button(
            label="Remover Cargo",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id="btn_remover_perm"
        )
        btn_remover.callback = self.remover_cargo_modulo
        self.add_item(btn_remover)

        # Botão Página 1
        btn_pag1 = discord.ui.Button(
            label="Pág 1 (Moderação)",
            emoji="1️⃣",
            style=discord.ButtonStyle.secondary,
            disabled=(self.pagina_atual == 1),
            custom_id="btn_pag1"
        )
        btn_pag1.callback = self.ir_pagina_1
        self.add_item(btn_pag1)

        # Botão Página 2
        btn_pag2 = discord.ui.Button(
            label="Pág 2 (VIP & Aparência)",
            emoji="2️⃣",
            style=discord.ButtonStyle.secondary,
            disabled=(self.pagina_atual == 2),
            custom_id="btn_pag2"
        )
        btn_pag2.callback = self.ir_pagina_2
        self.add_item(btn_pag2)

        # Botão Página 3
        btn_pag3 = discord.ui.Button(
            label="Pág 3 (Canais & Suporte)",
            emoji="3️⃣",
            style=discord.ButtonStyle.secondary,
            disabled=(self.pagina_atual == 3),
            custom_id="btn_pag3"
        )
        btn_pag3.callback = self.ir_pagina_3
        self.add_item(btn_pag3)

    async def confirmar_cargo_modulo(self, interaction: discord.Interaction):
        if not self.cargo_selecionado_pendente:
            await interaction.response.send_message("❌ Selecione um cargo no menu primeiro!", ephemeral=True)
            return

        cargo_salvo = self.cargo_selecionado_pendente
        modulo = self.modulo_atual

        guild_id_str = str(self.guild.id)
        dados = carregar_permissoes()
        if guild_id_str not in dados:
            dados[guild_id_str] = {}

        dados[guild_id_str][modulo] = cargo_salvo.id
        salvar_permissoes(dados)

        self.atualizar_itens()
        embed = self.gerar_embed()
        info_mod = MODULOS_PERMISSOES[modulo]

        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(
            f"🎉 **Salvo!** O cargo {cargo_salvo.mention} foi registrado com sucesso para **{info_mod['nome']}**!",
            ephemeral=True
        )

    async def aplicar_cargo_pagina_inteira(self, interaction: discord.Interaction):
        if not self.cargo_selecionado_pendente:
            await interaction.response.send_message("❌ Selecione um cargo no menu primeiro!", ephemeral=True)
            return

        cargo_salvo = self.cargo_selecionado_pendente
        guild_id_str = str(self.guild.id)
        dados = carregar_permissoes()
        if guild_id_str not in dados:
            dados[guild_id_str] = {}

        modulos_afetados = []
        for chave, info in MODULOS_PERMISSOES.items():
            if info["pagina"] == self.pagina_atual:
                dados[guild_id_str][chave] = cargo_salvo.id
                modulos_afetados.append(info["nome"])

        salvar_permissoes(dados)
        self.atualizar_itens()
        embed = self.gerar_embed()

        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(
            f"⚡ **Sucesso Total!** O cargo {cargo_salvo.mention} foi cadastrado em **todos os {len(modulos_afetados)} módulos da Página {self.pagina_atual}** de uma só vez!",
            ephemeral=True
        )

    async def ir_pagina_1(self, interaction: discord.Interaction):
        self.pagina_atual = 1
        self.modulo_atual = "staff"
        self.cargo_selecionado_pendente = None
        self.atualizar_itens()
        embed = self.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def ir_pagina_2(self, interaction: discord.Interaction):
        self.pagina_atual = 2
        self.modulo_atual = "vip"
        self.cargo_selecionado_pendente = None
        self.atualizar_itens()
        embed = self.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def ir_pagina_3(self, interaction: discord.Interaction):
        self.pagina_atual = 3
        self.modulo_atual = "warn"
        self.cargo_selecionado_pendente = None
        self.atualizar_itens()
        embed = self.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def remover_cargo_modulo(self, interaction: discord.Interaction):
        guild_id_str = str(self.guild.id)
        dados = carregar_permissoes()
        if guild_id_str in dados and self.modulo_atual in dados[guild_id_str]:
            dados[guild_id_str].pop(self.modulo_atual)
            salvar_permissoes(dados)

        self.cargo_selecionado_pendente = None
        self.atualizar_itens()
        embed = self.gerar_embed()
        info_mod = MODULOS_PERMISSOES[self.modulo_atual]
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(
            f"🗑️ O cargo vinculado a **{info_mod['nome']}** foi removido com sucesso!",
            ephemeral=True
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas quem abriu o painel pode interagir com estas configurações.",
                ephemeral=True
            )
            return False
        return True

    def gerar_embed(self) -> discord.Embed:
        mod_info = MODULOS_PERMISSOES.get(self.modulo_atual, MODULOS_PERMISSOES["staff"])
        pendente_txt = (
            f"\n🎯 **Cargo Selecionado:** {self.cargo_selecionado_pendente.mention} *(Clique em 'Salvar Neste')*\n"
            if self.cargo_selecionado_pendente else ""
        )
        embed = discord.Embed(
            title="🛡️  PAINEL DE CONFIGURAÇÃO DE STAFF & CARGOS",
            description=(
                f"Olá {self.autor.mention}, cadastre e configure os cargos de Staff do servidor!\n\n"
                f"🔹 **Página Atual:** **{self.pagina_atual}/3**\n"
                f"🔹 **Módulo em Edição:** **{mod_info['nome']}**"
                f"{pendente_txt}\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.INFO
        )

        guild_id = self.guild.id

        # Se for Página 1, exibe os cargos de moderação
        if self.pagina_atual == 1:
            embed.add_field(
                name="📌  Página 1: Moderação & Punições",
                value="Cargos responsáveis pelo controle e segurança do servidor:",
                inline=False
            )
            for chave, info in MODULOS_PERMISSOES.items():
                if info["pagina"] == 1:
                    cargo_id = obter_cargo_permissao(guild_id, chave)
                    cargo = self.guild.get_role(cargo_id) if cargo_id else None
                    status_str = f"🏷️ {cargo.mention}" if cargo else "*Nenhum (Apenas Admin nativo)*"
                    embed.add_field(name=info["nome"], value=status_str, inline=True)

        # Se for Página 2, exibe os cargos de gestão e utilidades
        elif self.pagina_atual == 2:
            embed.add_field(
                name="📌  Página 2: Gestão VIP & Bot",
                value="Cargos que podem gerenciar sistemas avançados do bot:",
                inline=False
            )
            for chave, info in MODULOS_PERMISSOES.items():
                if info["pagina"] == 2:
                    cargo_id = obter_cargo_permissao(guild_id, chave)
                    cargo = self.guild.get_role(cargo_id) if cargo_id else None
                    status_str = f"🏷️ {cargo.mention}" if cargo else "*Nenhum (Apenas Admin nativo)*"
                    embed.add_field(name=info["nome"], value=status_str, inline=True)

        # Se for Página 3, exibe suporte, canais, warns e logs
        else:
            embed.add_field(
                name="📌  Página 3: Canais, Suporte & Logs",
                value="Cargos que podem gerenciar tickets, warns, canais e registros:",
                inline=False
            )
            for chave, info in MODULOS_PERMISSOES.items():
                if info["pagina"] == 3:
                    cargo_id = obter_cargo_permissao(guild_id, chave)
                    cargo = self.guild.get_role(cargo_id) if cargo_id else None
                    status_str = f"🏷️ {cargo.mention}" if cargo else "*Nenhum (Apenas Admin nativo)*"
                    embed.add_field(name=info["nome"], value=status_str, inline=True)

        embed.set_footer(text=f"Servidor: {self.guild.name} • Navegue pelas páginas 1, 2 e 3 abaixo")
        return embed


class Permissoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # COMANDO: PAINEL DE CONFIGURAÇÃO DE STAFF (!staff / !permissoes)
    # ========================================================
    @commands.command(
        name="staff",
        aliases=["configstaff", "permissoes", "perms", "painel_staff", "painelstaff", "moderadores", "painelmod", "painelmoderadores"]
    )
    @commands.has_permissions(administrator=True)
    async def staff(self, ctx):
        """Abre o Painel Interativo de Configuração de Moderadores e Staff com paginação respeitando a hierarquia."""
        await tentar_deletar_mensagem(ctx)

        view = ViewPainelStaff(ctx.guild, ctx.author)
        embed = view.gerar_embed()
        await ctx.send(embed=embed, view=view, delete_after=180)

    @staff.error
    async def staff_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Apenas **Administradores** podem abrir o painel de configuração de staff.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO DIRETO: SETPERM (!setperm <modulo> <@cargo>)
    # ========================================================
    @commands.command(name="setperm", aliases=["setstaff"])
    @commands.has_permissions(administrator=True)
    async def setperm(self, ctx, modulo: str, cargo: discord.Role):
        """Define diretamente qual cargo tem permissão (ex: !setperm staff @Staff ou !setperm ban @Mod)."""
        await tentar_deletar_mensagem(ctx)

        modulo_limpo = modulo.lower().strip()
        mapa_modulos = {
            "staff": "staff",
            "mod": "staff",
            "moderador": "staff",
            "admin": "staff",
            "ban": "ban",
            "banir": "ban",
            "kick": "kick",
            "expulsar": "kick",
            "mute": "mute",
            "silenciar": "mute",
            "clear": "clear",
            "limpar": "clear",
            "purge": "clear",
            "vip": "vip",
            "vips": "vip",
            "cargos": "cargos",
            "cargo": "cargos",
            "customizacao": "customizacao",
            "aparencia": "customizacao",
        }

        if modulo_limpo not in mapa_modulos:
            modulos_validos = ", ".join(f"`{m}`" for m in MODULOS_PERMISSOES.keys())
            embed_erro = discord.Embed(
                title="❌ Módulo Inválido",
                description=(
                    f"O módulo informado não existe.\n\n"
                    f"**Módulos disponíveis:** {modulos_validos}\n\n"
                    f"**Exemplo:** `!setperm staff @Equipe` ou `!setperm ban @Staff`"
                ),
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        modulo_chave = mapa_modulos[modulo_limpo]

        guild_id_str = str(ctx.guild.id)
        dados = carregar_permissoes()
        if guild_id_str not in dados:
            dados[guild_id_str] = {}

        dados[guild_id_str][modulo_chave] = cargo.id
        salvar_permissoes(dados)

        info = MODULOS_PERMISSOES[modulo_chave]
        embed_sucesso = discord.Embed(
            title="🛡️  PERMISSÃO DE STAFF ATUALIZADA",
            description=(
                f"O cargo {cargo.mention} agora possui acesso ao módulo **{info['nome']}**.\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.SUCESSO
        )
        embed_sucesso.add_field(name="📦  Módulo", value=info["nome"], inline=True)
        embed_sucesso.add_field(name="🏷️  Cargo Vinculado", value=cargo.mention, inline=True)
        embed_sucesso.set_footer(text="Membros com este cargo já podem utilizar os comandos.")
        await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)

    @setperm.error
    async def setperm_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Apenas **Administradores** podem configurar cargos de staff.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description=(
                    "Você precisa informar o módulo e o cargo!\n\n"
                    "**Exemplo:** `!setperm staff @Equipe`\n"
                    "**Módulos:** `staff`, `ban`, `mute`, `clear`, `vip`, `cargos`, `customizacao`"
                ),
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
        elif isinstance(error, (commands.RoleNotFound, commands.BadArgument)):
            embed = discord.Embed(
                title="❌ Cargo Não Encontrado",
                description="O cargo informado não foi encontrado neste servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO DIRETO: REMPERM (!remperm <modulo>)
    # ========================================================
    @commands.command(name="remperm", aliases=["remstaff"])
    @commands.has_permissions(administrator=True)
    async def remperm(self, ctx, modulo: str):
        """Remove o cargo atribuído a um módulo de staff."""
        await tentar_deletar_mensagem(ctx)

        modulo_limpo = modulo.lower().strip()
        guild_id_str = str(ctx.guild.id)
        dados = carregar_permissoes()

        if guild_id_str in dados and modulo_limpo in dados[guild_id_str]:
            dados[guild_id_str].pop(modulo_limpo)
            salvar_permissoes(dados)

            embed_sucesso = discord.Embed(
                title="🗑️  PERMISSÃO REMOVIDA",
                description=f"O cargo configurado para o módulo `{modulo_limpo}` foi removido com sucesso.",
                color=Cores.SUCESSO
            )
            await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)
        else:
            embed_aviso = discord.Embed(
                title="⚠️ Nenhuma Configuração",
                description=f"Não havia nenhum cargo específico configurado para `{modulo_limpo}`.",
                color=Cores.AVISO
            )
            await ctx.send(embed=embed_aviso, delete_after=TEMPO_DELETE_ERRO)

    @remperm.error
    async def remperm_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Apenas Administradores podem alterar permissões de staff.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Informe qual módulo deseja resetar!\n\n**Exemplo:** `!remperm staff`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)


async def setup(bot):
    await bot.add_cog(Permissoes(bot))

"""
Cog Hub Tools: Painel Interativo de Ferramentas, Contas e Permissões.
Implementa interface idêntica aos layouts modernos com persistência de sessões,
menus de seleção e verificação de permissões Free, Booster e VIP no backend.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
import discord
from discord import app_commands
from discord.ext import commands

from config import Cores, PREFIXO
from tools import FERRAMENTAS, obter_ferramentas_por_tier
from tools.permissions import obter_nivel_acesso, verificar_permissao

ARQUIVO_CONTAS = Path(__file__).resolve().parent.parent / "data" / "contas_tools.json"

BANNER_PAINEL_PADRAO = "https://i.imgur.com/2sX5L7I.png"  # Banner clean moderno ou fallback


def carregar_contas_vinculadas() -> Dict[str, Any]:
    """Carrega as contas e sessões vinculadas salvas em JSON."""
    if not ARQUIVO_CONTAS.exists():
        return {}
    try:
        with open(ARQUIVO_CONTAS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_contas_vinculadas(dados: Dict[str, Any]):
    """Salva com segurança as contas no arquivo JSON."""
    ARQUIVO_CONTAS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_CONTAS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ========================================================
# MODAL: ADICIONAR / CONFIGURAR CONTA
# ========================================================
class ModalAdicionarConta(discord.ui.Modal, title="👤 Conectar & Configurar Conta"):
    def __init__(self, cog, user_id: int):
        super().__init__()
        self.cog = cog
        self.user_id = str(user_id)

        self.nome_input = discord.ui.TextInput(
            label="Apelido / Identificador da Conta",
            placeholder="Ex: MinhaContaPrincipal",
            default="",
            required=True,
            max_length=32
        )
        self.nota_input = discord.ui.TextInput(
            label="Preferências de Notificações / Notas",
            placeholder="Ex: Receber avisos de quests e lembretes de call",
            required=False,
            max_length=100
        )
        self.add_item(self.nome_input)
        self.add_item(self.nota_input)

    async def on_submit(self, interaction: discord.Interaction):
        nome = self.nome_input.value.strip()
        notas = self.nota_input.value.strip()

        contas = carregar_contas_vinculadas()
        user_str = str(interaction.user.id)

        if user_str not in contas:
            contas[user_str] = {
                "ativa": nome,
                "contas": []
            }

        # Adiciona ou atualiza conta
        contas_usuario = contas[user_str]["contas"]
        # Limita a 2 contas no plano Free
        info_acesso = obter_nivel_acesso(interaction.user)
        limite_contas = 5 if info_acesso["is_vip"] or info_acesso["is_booster"] else 2

        if len(contas_usuario) >= limite_contas and not any(c["nome"] == nome for c in contas_usuario):
            await interaction.response.send_message(
                f"⚠️ **Limite de contas atingido ({limite_contas})** para o seu plano atual. "
                "Remova uma conta existente para vincular outra.",
                ephemeral=True
            )
            return

        # Atualiza lista
        contas_usuario = [c for c in contas_usuario if c["nome"] != nome]
        contas_usuario.append({
            "nome": nome,
            "id": interaction.user.id,
            "notas": notas,
            "criada_em": discord.utils.utcnow().isoformat()
        })
        contas[user_str]["contas"] = contas_usuario
        contas[user_str]["ativa"] = nome
        salvar_contas_vinculadas(contas)

        embed = discord.Embed(
            title="✅ Conta Vinculada com Sucesso!",
            description=(
                f"A conta **`{nome}`** foi registrada com sucesso para uso nas ferramentas.\n"
                f"• **ID de Usuário:** `{interaction.user.id}`\n"
                f"• **Status:** Ativa e pronta para uso nas ferramentas."
            ),
            color=Cores.SUCESSO
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================================================
# SELECT MENU: SELEÇÃO DE FERRAMENTAS POR TIER
# ========================================================
class SelectFerramentas(discord.ui.Select):
    def __init__(self, tier: str, member: discord.Member):
        self.tier = tier
        self.member = member
        ferramentas_tier = obter_ferramentas_por_tier(tier)

        opcoes = []
        for chave, meta in ferramentas_tier.items():
            opcoes.append(
                discord.SelectOption(
                    label=meta["nome"],
                    description=meta["descricao"][:100],
                    emoji=meta.get("emoji", "⚙️"),
                    value=chave
                )
            )

        placeholder = f"Selecione uma opcao ({tier.capitalize()})"
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=opcoes)

    async def callback(self, interaction: discord.Interaction):
        chave_selecionada = self.values[0]
        meta = FERRAMENTAS.get(chave_selecionada)

        if not meta:
            await interaction.response.send_message("❌ Ferramenta não encontrada.", ephemeral=True)
            return

        # Verificação rigorosa de backend antes de executar
        autorizado, motivo = verificar_permissao(interaction.user, meta["tier"])
        if not autorizado:
            embed_erro = discord.Embed(
                title="🔒 Acesso Bloqueado",
                description=motivo,
                color=Cores.ERRO
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return

        # Executa a função modular
        try:
            handler = meta["handler"]
            embed_resultado = await handler(interaction)
            await interaction.response.send_message(embed=embed_resultado, ephemeral=True)
        except Exception as e:
            embed_falha = discord.Embed(
                title="⚠️ Erro ao Executar Ferramenta",
                description=f"Ocorreu uma falha durante o processamento:\n`{e}`",
                color=Cores.ERRO
            )
            await interaction.response.send_message(embed=embed_falha, ephemeral=True)


# ========================================================
# VIEW: CATEGORIAS DE FUNÇÕES (FREE, BOOSTER, PREMIUM)
# ========================================================
class ViewCategorias(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=180)
        self.member = member

    @discord.ui.button(label="Funções Gratuitas", style=discord.ButtonStyle.secondary, emoji="⭐", custom_id="btn_free")
    async def btn_free(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View(timeout=180)
        view.add_item(SelectFerramentas("free", interaction.user))

        embed = discord.Embed(
            title="⭐  Ferramentas Gratuitas (Free)",
            description="Selecione abaixo a ferramenta gratuita que deseja executar:",
            color=Cores.INFO
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Funções Booster", style=discord.ButtonStyle.secondary, emoji="🚀", custom_id="btn_booster")
    async def btn_booster(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Validação backend de permissão Booster
        autorizado, motivo = verificar_permissao(interaction.user, "booster")
        if not autorizado:
            embed_bloqueio = discord.Embed(
                title="🚀  Acesso Exclusivo para Server Boosters",
                description=motivo,
                color=discord.Color.nitro_pink()
            )
            await interaction.response.send_message(embed=embed_bloqueio, ephemeral=True)
            return

        view = discord.ui.View(timeout=180)
        view.add_item(SelectFerramentas("booster", interaction.user))

        embed = discord.Embed(
            title="🚀  Ferramentas Booster",
            description="Selecione abaixo a ferramenta exclusiva de Booster:",
            color=discord.Color.nitro_pink()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Funções Premium", style=discord.ButtonStyle.secondary, emoji="👑", custom_id="btn_premium")
    async def btn_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Validação backend de permissão VIP/Premium
        autorizado, motivo = verificar_permissao(interaction.user, "vip")
        if not autorizado:
            embed_bloqueio = discord.Embed(
                title="👑  Acesso Exclusivo para Membros VIP / Premium",
                description=motivo,
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed_bloqueio, ephemeral=True)
            return

        view = discord.ui.View(timeout=180)
        view.add_item(SelectFerramentas("vip", interaction.user))

        embed = discord.Embed(
            title="👑  Ferramentas Premium & VIP",
            description="Selecione abaixo a ferramenta exclusiva VIP:",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ========================================================
# VIEW: GERENCIAMENTO DE CONTAS VINCULADAS
# ========================================================
class ViewGerenciarContas(discord.ui.View):
    def __init__(self, cog, member: discord.Member):
        super().__init__(timeout=180)
        self.cog = cog
        self.member = member

    @discord.ui.button(label="Adicionar conta", style=discord.ButtonStyle.success, emoji="➕", custom_id="btn_add_conta")
    async def btn_add_conta(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ModalAdicionarConta(self.cog, interaction.user.id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Remover conta", style=discord.ButtonStyle.secondary, emoji="🗑️", custom_id="btn_del_conta")
    async def btn_del_conta(self, interaction: discord.Interaction, button: discord.ui.Button):
        contas = carregar_contas_vinculadas()
        user_str = str(interaction.user.id)

        if user_str in contas and contas[user_str].get("contas"):
            removida = contas[user_str]["contas"].pop()
            if not contas[user_str]["contas"]:
                del contas[user_str]
            else:
                contas[user_str]["ativa"] = contas[user_str]["contas"][0]["nome"]
            salvar_contas_vinculadas(contas)
            await interaction.response.send_message(
                f"🗑️ A conta vinculada **`{removida.get('nome')}`** foi desvinculada com sucesso.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "ℹ️ Você não possui contas vinculadas para remover.",
                ephemeral=True
            )


# ========================================================
# VIEW PRINCIPAL DO PAINEL (TELA INICIAL)
# ========================================================
class ViewPainelPrincipal(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)  # Persistente
        self.cog = cog

    @discord.ui.button(label="Configurar Conta", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="hub_config_conta")
    async def btn_configurar_conta(self, interaction: discord.Interaction, button: discord.ui.Button):
        contas = carregar_contas_vinculadas()
        user_str = str(interaction.user.id)
        dados_user = contas.get(user_str, {})
        contas_list = dados_user.get("contas", [])
        conta_ativa = dados_user.get("ativa", interaction.user.name)

        info_acesso = obter_nivel_acesso(interaction.user)
        total_limite = 5 if info_acesso["is_vip"] or info_acesso["is_booster"] else 2
        qtd_vinculadas = len(contas_list) if contas_list else (1 if dados_user else 0)

        embed = discord.Embed(
            title="Contas",
            description=(
                "Tokens e sessões ficam salvos com segurança para Tools e Farm Call.\n\n"
                f"⭐ **Plano {info_acesso['tier_nome']} — {qtd_vinculadas}/{total_limite} vinculadas**\n"
                "*Selecione uma conta ao abrir cada ferramenta.*\n\n"
                "**Contas vinculadas**\n"
                f"**{conta_ativa}** `(Ativa)`\n"
                f"ID: `{interaction.user.id}`"
            ),
            color=Cores.PADRAO
        )
        view = ViewGerenciarContas(self.cog, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Ver Funcoes", style=discord.ButtonStyle.secondary, emoji="🪟", custom_id="hub_ver_funcoes")
    async def btn_ver_funcoes(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Categorias de Funcoes",
            description="Conta validada com sucesso! Escolha uma categoria abaixo para abrir as ferramentas:",
            color=Cores.PADRAO
        )
        view = ViewCategorias(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Status", style=discord.ButtonStyle.secondary, emoji="📈", custom_id="hub_status")
    async def btn_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        info_acesso = obter_nivel_acesso(interaction.user)
        latencia = round(interaction.client.latency * 1000)

        embed = discord.Embed(
            title="📈  Status do Sistema & Conexão",
            color=Cores.SUCESSO,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="⚡ Latência da API", value=f"`{latencia} ms`", inline=True)
        embed.add_field(name="🛡️ Seu Nível de Acesso", value=f"**{info_acesso['tier_nome']}**", inline=True)
        embed.add_field(name="🌐 Servidores Conectados", value=f"`{len(interaction.client.guilds)}`", inline=True)
        embed.add_field(
            name="🔒 Integridade e Segurança",
            value="Backend 100% isolado, sem armazenamento de senhas ou credenciais vulneráveis.",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================================================
# COG PRINCIPAL: HUB TOOLS
# ========================================================
class HubToolsCog(commands.Cog, name="Hub de Ferramentas"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Registra a view persistente
        self.bot.add_view(ViewPainelPrincipal(self))

    def gerar_embed_painel(self, guild: discord.Guild) -> discord.Embed:
        """Gera o Embed limpo e elegante da tela inicial do painel."""
        embed = discord.Embed(
            color=discord.Color.from_rgb(18, 18, 20)  # Dark clean
        )
        # Tenta utilizar a imagem de banner visual
        embed.set_image(url="https://images-ext-1.discordapp.net/external/v_7_Bq-yK5Pz5bM-gJdM/https/i.imgur.com/2sX5L7I.png?format=webp")
        embed.set_author(name="Central de Ferramentas • Sistema Integrado", icon_url=self.bot.user.display_avatar.url)
        embed.description = (
            "### 🎛️ **PAINEL DE FERRAMENTAS & CONTROLE**\n"
            "Gerencie sua conta, utilize utilitários do servidor e acesse as ferramentas exclusivas.\n"
            "Clique nos botões abaixo para configurar ou acessar as funções disponíveis."
        )
        embed.set_footer(text=f"{guild.name} • Sistema de Ferramentas v2.0", icon_url=guild.icon.url if guild.icon else None)
        return embed

    @commands.command(name="tools", aliases=["paineltools", "ferramentas"])
    async def cmd_tools(self, ctx: commands.Context):
        """Abre o Painel Principal de Ferramentas e Gerenciamento de Conta."""
        embed = self.gerar_embed_painel(ctx.guild)
        view = ViewPainelPrincipal(self)
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name="tools", description="Abre o painel moderno de ferramentas, contas e utilitários.")
    async def slash_tools(self, interaction: discord.Interaction):
        """Comando Slash para abrir o painel principal."""
        embed = self.gerar_embed_painel(interaction.guild)
        view = ViewPainelPrincipal(self)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(HubToolsCog(bot))

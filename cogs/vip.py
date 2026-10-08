import asyncio
import io
import json
import urllib.request
from pathlib import Path
import time
import discord
from discord.ext import commands, tasks
from config import (
    Cores,
    TEMPO_DELETE_ERRO,
    TEMPO_DELETE_SUCESSO,
    TEMPO_DELETE_VIP,
    VIP_CARGOS,
    VIP_CATEGORIA_CALLS,
    VIP_CORES,
    VIP_LIMITES_AMIGOS,
)
from utils.helpers import tem_permissao_acao, tentar_deletar_mensagem

# Caminho para armazenamento de dados persistentes dos VIPs
ARQUIVO_DADOS_VIP = Path(__file__).resolve().parent.parent / "data" / "vips.json"


def carregar_dados_vips() -> dict:
    """Carrega os dados de cargos e amigos customizados de VIPs do JSON."""
    if not ARQUIVO_DADOS_VIP.exists():
        return {}
    try:
        with open(ARQUIVO_DADOS_VIP, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_dados_vips(dados: dict):
    """Salva os dados persistentes no JSON."""
    ARQUIVO_DADOS_VIP.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_DADOS_VIP, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ========================================================
# MODAL: CONFIGURAR CARGO VIP (NOME E COR)
# ========================================================
class ModalConfigurarCargoVIP(discord.ui.Modal, title="🏷️ Configurar Meu Cargo VIP"):
    def __init__(self, cog, nome_atual: str = "", cor_atual: str = ""):
        super().__init__()
        self.cog = cog

        self.nome_input = discord.ui.TextInput(
            label="Nome do Seu Cargo",
            placeholder="Ex: › Espectro Lunar",
            default=nome_atual,
            required=True,
            max_length=64
        )
        self.cor_input = discord.ui.TextInput(
            label="Cor do Cargo (Hexadecimal)",
            placeholder="Ex: #FF0055 ou #00C3FF",
            default=cor_atual or "#FF0055",
            required=False,
            max_length=7
        )
        self.add_item(self.nome_input)
        self.add_item(self.cor_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        membro = interaction.user
        nivel = self.cog.obter_nivel_vip(membro)

        if not nivel:
            embed_erro = discord.Embed(
                title="❌ Recurso Exclusivo",
                description="Você precisa possuir um plano **VIP** ativo para personalizar seu cargo.",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)
            return

        nome = self.nome_input.value.strip()
        cor_hex = self.cor_input.value.strip()

        # Parse da cor
        cor = VIP_CORES.get(nivel, discord.Color.default())
        if cor_hex:
            if not cor_hex.startswith("#"):
                cor_hex = f"#{cor_hex}"
            try:
                cor = discord.Color.from_str(cor_hex)
            except ValueError:
                pass

        guild_id_str = str(guild.id)
        user_id_str = str(membro.id)

        if guild_id_str not in self.cog.dados_vips:
            self.cog.dados_vips[guild_id_str] = {}

        dados_user = self.cog.dados_vips[guild_id_str].get(user_id_str, {})
        cargo_id = dados_user.get("cargo_id")
        cargo_existente = guild.get_role(cargo_id) if cargo_id else None

        try:
            if cargo_existente:
                await cargo_existente.edit(
                    name=nome,
                    color=cor,
                    reason=f"Cargo VIP editado por {membro.name}"
                )
                if cargo_existente not in membro.roles:
                    await membro.add_roles(cargo_existente)
                cargo_final = cargo_existente
            else:
                novo_cargo = await guild.create_role(
                    name=nome,
                    color=cor,
                    reason=f"Cargo VIP criado por {membro.name}"
                )
                await membro.add_roles(novo_cargo)
                self.cog.dados_vips[guild_id_str][user_id_str] = {
                    "cargo_id": novo_cargo.id,
                    "amigos": dados_user.get("amigos", [])
                }
                salvar_dados_vips(self.cog.dados_vips)
                cargo_final = novo_cargo

            # Posiciona o cargo personalizado exatamente abaixo do cargo base do VIP
            try:
                cargo_base = None
                for nome_b in ["VIP Diamante", "VIP Gold", "VIP Prata"]:
                    r_b = discord.utils.get(guild.roles, name=nome_b)
                    if r_b and r_b in membro.roles:
                        cargo_base = r_b
                        break

                if cargo_base:
                    pos_alvo = max(1, cargo_base.position - 1)
                    await guild.edit_role_positions({cargo_final: pos_alvo})
                else:
                    pos_maxima = max(1, guild.me.top_role.position - 1)
                    await guild.edit_role_positions({cargo_final: pos_maxima})
            except Exception:
                pass

            embed_sucesso = discord.Embed(
                title="✨  CARGO VIP ATUALIZADO",
                description=(
                    f"Seu cargo pessoal {cargo_final.mention} foi salvo com sucesso!\n"
                    "──────────────────────────────────────────────"
                ),
                color=cor
            )
            embed_sucesso.add_field(name="🏷️  Nome", value=f"`{cargo_final.name}`", inline=True)
            embed_sucesso.add_field(name="🎨  Cor Hex", value=f"`{str(cargo_final.color)}`", inline=True)
            embed_sucesso.add_field(
                name="💡  Dica Extra",
                value="Use o botão **'🎨 Ícone do Cargo'** para escolher qualquer emoji do servidor e colocar como badge ao lado do nome!",
                inline=False
            )
            await interaction.followup.send(embed=embed_sucesso, ephemeral=True)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="O bot não tem permissão de `Gerenciar Cargos` para criar ou editar cargos.",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro ao Atualizar",
                description=f"Não foi possível salvar seu cargo:\n`{e}`",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)


# ========================================================
# MODAL: CONFIGURAR CALL VIP (NOME E LIMITE)
# ========================================================
class ModalConfigurarCallVIP(discord.ui.Modal, title="🔊 Configurar Minha Call VIP"):
    def __init__(self, cog, nome_sugerido: str = ""):
        super().__init__()
        self.cog = cog

        self.nome_input = discord.ui.TextInput(
            label="Nome da Sala de Voz",
            placeholder="Ex: 🔊・Call do Fulano",
            default=nome_sugerido,
            required=True,
            max_length=32
        )
        self.limite_input = discord.ui.TextInput(
            label="Limite de Pessoas na Call",
            placeholder="Digite um número de 0 a 99 (0 = Ilimitado)",
            default="0",
            required=False,
            max_length=2
        )
        self.add_item(self.nome_input)
        self.add_item(self.limite_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        membro = interaction.user
        nivel = self.cog.obter_nivel_vip(membro)

        if not nivel:
            embed_erro = discord.Embed(
                title="❌ Recurso Exclusivo",
                description="Você precisa possuir um plano **VIP** ativo para criar calls privadas.",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)
            return

        guild_id_str = str(guild.id)
        user_id_str = str(membro.id)
        dados_user = self.cog.dados_vips.get(guild_id_str, {}).get(user_id_str, {})
        cargo_id = dados_user.get("cargo_id")
        cargo_pessoal = guild.get_role(cargo_id) if cargo_id else None

        if not cargo_pessoal:
            embed_aviso = discord.Embed(
                title="⚠️ Cargo VIP Não Criado",
                description=(
                    "Você precisa primeiro criar o seu **Cargo VIP** no botão **'🏷️ Configurar Cargo'**!\n\n"
                    "🔒 *Por segurança e privacidade, a sua call só permite a entrada de quem possui o seu cargo VIP pessoal!*"
                ),
                color=Cores.AVISO
            )
            await interaction.followup.send(embed=embed_aviso, ephemeral=True)
            return

        nome_call = self.nome_input.value.strip()[:32]
        limite_str = self.limite_input.value.strip() if self.limite_input.value else "0"
        try:
            limite = max(0, min(99, int(limite_str)))
        except ValueError:
            limite = 0

        # Localiza a categoria VIP existente ou cria
        categoria = discord.utils.get(guild.categories, name="👑・ÁREA VIP") or discord.utils.get(guild.categories, name=VIP_CATEGORIA_CALLS)
        if not categoria:
            try:
                categoria = await guild.create_category(name="👑・ÁREA VIP")
            except discord.Forbidden:
                embed_perm = discord.Embed(
                    title="❌ Permissão Insuficiente",
                    description="O bot não tem permissão para criar categorias de canais.",
                    color=Cores.ERRO
                )
                await interaction.followup.send(embed=embed_perm, ephemeral=True)
                return

        # Permissões ESTRITAS: Só entra quem tem o cargo_pessoal ou o dono
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False, speak=False, view_channel=True),
            cargo_pessoal: discord.PermissionOverwrite(connect=True, speak=True, view_channel=True),
            membro: discord.PermissionOverwrite(
                connect=True,
                speak=True,
                mute_members=True,
                move_members=True,
                manage_channels=True,
                view_channel=True
            ),
            guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True)
        }

        # Verifica se o membro já tem uma call existente gravada ou nessa categoria
        call_salva_id = dados_user.get("call_id")
        canal_existente = guild.get_channel(call_salva_id) if call_salva_id else None

        if not canal_existente:
            for canal in categoria.voice_channels:
                if canal.name.endswith(f"Call de {membro.display_name}") or canal.name == nome_call:
                    canal_existente = canal
                    break

        if canal_existente:
            try:
                await canal_existente.edit(name=nome_call, user_limit=limite, overwrites=overwrites)
                if guild_id_str not in self.cog.dados_vips:
                    self.cog.dados_vips[guild_id_str] = {}
                if user_id_str not in self.cog.dados_vips[guild_id_str]:
                    self.cog.dados_vips[guild_id_str][user_id_str] = {}
                self.cog.dados_vips[guild_id_str][user_id_str]["call_id"] = canal_existente.id
                salvar_dados_vips(self.cog.dados_vips)

                embed_up = discord.Embed(
                    title="🔊  CALL VIP ATUALIZADA",
                    description=(
                        f"Sua call permanente {canal_existente.mention} foi atualizada com sucesso!\n"
                        "──────────────────────────────────────────────"
                    ),
                    color=VIP_CORES.get(nivel, Cores.SUCESSO)
                )
                embed_up.add_field(name="🏷️  Nome", value=f"`{nome_call}`", inline=True)
                embed_up.add_field(name="👥  Capacidade", value=f"`{limite if limite > 0 else 'Ilimitado'}` pessoas", inline=True)
                embed_up.add_field(name="🔒  Acesso Restrito", value=f"Apenas quem tem o cargo {cargo_pessoal.mention}", inline=False)
                await interaction.followup.send(embed=embed_up, ephemeral=True)
                return
            except Exception:
                pass

        try:
            canal_voz = await guild.create_voice_channel(
                name=nome_call,
                category=categoria,
                user_limit=limite,
                overwrites=overwrites,
                reason=f"Call VIP permanente criada por {membro.name}"
            )

            # Salva o ID da call nas configurações do VIP
            if guild_id_str not in self.cog.dados_vips:
                self.cog.dados_vips[guild_id_str] = {}
            if user_id_str not in self.cog.dados_vips[guild_id_str]:
                self.cog.dados_vips[guild_id_str][user_id_str] = {}
            self.cog.dados_vips[guild_id_str][user_id_str]["call_id"] = canal_voz.id
            salvar_dados_vips(self.cog.dados_vips)

            limite_txt = f"{limite} pessoas" if limite > 0 else "Ilimitado"
            embed_sucesso = discord.Embed(
                title="🔊  CALL VIP PRIVADA CRIADA",
                description=(
                    f"Sua sala de voz permanente {canal_voz.mention} está ativa e protegida!\n"
                    "──────────────────────────────────────────────"
                ),
                color=VIP_CORES.get(nivel, Cores.SUCESSO)
            )
            embed_sucesso.add_field(name="📁  Categoria", value=f"`{categoria.name}`", inline=True)
            embed_sucesso.add_field(name="👥  Limite", value=f"`{limite_txt}`", inline=True)
            embed_sucesso.add_field(
                name="🔒  Controle de Acesso Exclusivo",
                value=f"Apenas você e quem tiver o seu cargo {cargo_pessoal.mention} podem entrar!",
                inline=False
            )
            embed_sucesso.add_field(
                name="👑  Permanência da Call",
                value="Esta call é **permanente** durante o período do seu VIP e não será apagada ao sair.",
                inline=False
            )
            await interaction.followup.send(embed=embed_sucesso, ephemeral=True)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Permissão Negada",
                description="O bot não possui permissão para criar canais de voz no servidor.",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro ao Criar Call",
                description=f"Ocorreu um erro:\n`{e}`",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)


# ========================================================
# SELECT / VIEW: ESCOLHER EMOJI DO SERVIDOR PARA O CARGO
# ========================================================
class SelectEmojiCargo(discord.ui.Select):
    def __init__(self, cog, emojis_servidor: list[discord.Emoji]):
        self.cog = cog
        opcoes = []
        for em in emojis_servidor[:25]:
            opcoes.append(
                discord.SelectOption(
                    label=em.name[:50],
                    value=str(em.id),
                    emoji=em,
                    description="Emoji personalizado do servidor"
                )
            )
        super().__init__(
            placeholder="Selecione um emoji do servidor para o seu cargo...",
            min_values=1,
            max_values=1,
            custom_id="select_emoji_cargo_vip"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        membro = interaction.user
        emoji_id = int(self.values[0])
        emoji_obj = discord.utils.get(guild.emojis, id=emoji_id)

        if not emoji_obj:
            await interaction.followup.send("❌ Emoji não encontrado.", ephemeral=True)
            return

        guild_id_str = str(guild.id)
        user_id_str = str(membro.id)
        dados_user = self.cog.dados_vips.get(guild_id_str, {}).get(user_id_str, {})
        cargo_id = dados_user.get("cargo_id")
        cargo = guild.get_role(cargo_id) if cargo_id else None

        if not cargo:
            embed_aviso = discord.Embed(
                title="⚠️ Cargo Não Encontrado",
                description="Você precisa criar o seu cargo primeiro no botão **'🏷️ Configurar Cargo'** antes de colocar um ícone!",
                color=Cores.AVISO
            )
            await interaction.followup.send(embed=embed_aviso, ephemeral=True)
            return

        try:
            req = urllib.request.Request(
                emoji_obj.url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            img_bytes = urllib.request.urlopen(req).read()

            await cargo.edit(display_icon=img_bytes, reason=f"Ícone VIP definido por {membro.name}")

            embed_sucesso = discord.Embed(
                title="🎨  ÍCONE DO CARGO APLICADO",
                description=(
                    f"O emoji {emoji_obj} foi definido com sucesso como o ícone do seu cargo {cargo.mention}!\n"
                    "──────────────────────────────────────────────\n"
                    "Ele agora aparece ao lado do seu nome no chat e na lista de membros!"
                ),
                color=cargo.color if cargo.color.value != 0 else Cores.SUCESSO
            )
            embed_sucesso.set_thumbnail(url=emoji_obj.url)
            await interaction.followup.send(embed=embed_sucesso, ephemeral=True)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Permissão Insuficiente ou Limite de Nível",
                description=(
                    "O Discord exige que o servidor tenha **Nível de Impulso 2 (Server Boost Nível 2)** "
                    "para suportar ícones em cargos, ou o bot precisa de permissão de `Gerenciar Cargos`."
                ),
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro ao Aplicar Ícone",
                description=f"Ocorreu um erro ao aplicar o ícone:\n`{e}`",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)


class ViewEscolherEmojiCargo(discord.ui.View):
    def __init__(self, cog, emojis_servidor: list[discord.Emoji], autor_id: int):
        super().__init__(timeout=90)
        self.autor_id = autor_id
        self.add_item(SelectEmojiCargo(cog, emojis_servidor))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌ Apenas você pode escolher o emoji.", ephemeral=True)
            return False
        return True


# ========================================================
# SELECT / VIEW: GERENCIAR AMIGOS DO VIP
# ========================================================
class UserSelectAddAmigo(discord.ui.UserSelect):
    def __init__(self, cog):
        self.cog = cog
        super().__init__(
            placeholder="Selecione um amigo para receber seu cargo VIP...",
            min_values=1,
            max_values=1,
            custom_id="user_select_add_amigo_vip"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        membro = interaction.user
        amigo = self.values[0]

        if not isinstance(amigo, discord.Member):
            amigo = guild.get_member(amigo.id)
            if not amigo:
                await interaction.followup.send("❌ Membro não encontrado no servidor.", ephemeral=True)
                return

        nivel = self.cog.obter_nivel_vip(membro)
        if not nivel:
            await interaction.followup.send("❌ Você não possui um VIP ativo.", ephemeral=True)
            return

        guild_id_str = str(guild.id)
        user_id_str = str(membro.id)
        dados_user = self.cog.dados_vips.get(guild_id_str, {}).get(user_id_str, {})
        cargo_id = dados_user.get("cargo_id")
        cargo = guild.get_role(cargo_id) if cargo_id else None

        if not cargo:
            await interaction.followup.send(
                "❌ Você precisa criar o seu cargo primeiro no botão **'🏷️ Configurar Cargo'**!",
                ephemeral=True
            )
            return

        if amigo.id == membro.id:
            await interaction.followup.send("❌ Você já possui o seu próprio cargo.", ephemeral=True)
            return
        if amigo.bot:
            await interaction.followup.send("❌ Bots não podem receber cargos VIP.", ephemeral=True)
            return

        amigos_atuais = dados_user.get("amigos", [])
        limite = VIP_LIMITES_AMIGOS.get(nivel, 1)

        if amigo.id in amigos_atuais:
            await interaction.followup.send(f"⚠️ {amigo.mention} já possui o seu cargo.", ephemeral=True)
            return
        if len(amigos_atuais) >= limite:
            await interaction.followup.send(
                f"⚠️ Limite atingido! Seu VIP permite até **{limite} amigo(s)**. Remova um para liberar vaga.",
                ephemeral=True
            )
            return

        try:
            await amigo.add_roles(cargo, reason=f"Cargo VIP compartilhado por {membro.name}")
            amigos_atuais.append(amigo.id)
            dados_user["amigos"] = amigos_atuais
            self.cog.dados_vips[guild_id_str][user_id_str] = dados_user
            salvar_dados_vips(self.cog.dados_vips)

            embed = discord.Embed(
                title="👥  AMIGO ADICIONADO AO SEU CARGO",
                description=(
                    f"O seu cargo pessoal {cargo.mention} foi concedido a {amigo.mention}!\n"
                    "──────────────────────────────────────────────\n"
                    f"Ele agora tem acesso à sua call privada e às suas cores de cargo!"
                ),
                color=Cores.SUCESSO
            )
            embed.add_field(name="📊  Vagas Utilizadas", value=f"`{len(amigos_atuais)} / {limite}` amigos", inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ O bot não tem permissão para gerenciar este cargo.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao adicionar: `{e}`", ephemeral=True)


class ViewAmigosVIP(discord.ui.View):
    def __init__(self, cog, autor_id: int):
        super().__init__(timeout=90)
        self.cog = cog
        self.autor_id = autor_id
        self.add_item(UserSelectAddAmigo(cog))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌ Apenas você pode gerenciar seus amigos VIP.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Remover Amigo (Liberar Vaga)", style=discord.ButtonStyle.danger, emoji="❌")
    async def botao_remover_amigo(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        membro = interaction.user
        guild_id_str = str(guild.id)
        user_id_str = str(membro.id)

        dados_user = self.cog.dados_vips.get(guild_id_str, {}).get(user_id_str, {})
        amigos_atuais = dados_user.get("amigos", [])
        cargo_id = dados_user.get("cargo_id")
        cargo = guild.get_role(cargo_id) if cargo_id else None

        if not amigos_atuais:
            await interaction.response.send_message("ℹ️ Você ainda não adicionou nenhum amigo.", ephemeral=True)
            return

        amigo_id_removido = amigos_atuais.pop(0)
        dados_user["amigos"] = amigos_atuais
        self.cog.dados_vips[guild_id_str][user_id_str] = dados_user
        salvar_dados_vips(self.cog.dados_vips)

        amigo_obj = guild.get_member(amigo_id_removido)
        if amigo_obj and cargo and cargo in amigo_obj.roles:
            try:
                await amigo_obj.remove_roles(cargo, reason=f"Vaga VIP liberada por {membro.name}")
            except Exception:
                pass

        nome_removido = amigo_obj.mention if amigo_obj else f"<@{amigo_id_removido}>"
        await interaction.response.send_message(
            f"✅ {nome_removido} foi removido do seu cargo VIP! Vaga liberada com sucesso.",
            ephemeral=True
        )


# ========================================================
# VIEW PRINCIPAL DO USUÁRIO VIP (!vip)
# ========================================================
class ViewPainelUsuarioVIP(discord.ui.View):
    def __init__(self, cog, membro: discord.Member):
        super().__init__(timeout=180)
        self.cog = cog
        self.membro = membro

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.membro.id:
            await interaction.response.send_message(
                "❌ Este painel de controle VIP pertence a outro membro.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Configurar Cargo", style=discord.ButtonStyle.primary, emoji="🏷️")
    async def botao_cargo(self, interaction: discord.Interaction, button: discord.ui.Button):
        nivel = self.cog.obter_nivel_vip(self.membro)
        if not nivel:
            await interaction.response.send_message(
                "❌ Você não possui um plano **VIP** ativo no servidor.",
                ephemeral=True
            )
            return

        guild_id_str = str(interaction.guild.id)
        user_id_str = str(self.membro.id)
        dados_user = self.cog.dados_vips.get(guild_id_str, {}).get(user_id_str, {})
        cargo_id = dados_user.get("cargo_id")
        cargo = interaction.guild.get_role(cargo_id) if cargo_id else None

        nome_atual = cargo.name if cargo else f"VIP de {self.membro.display_name}"
        cor_atual = str(cargo.color) if cargo and cargo.color.value != 0 else ""

        modal = ModalConfigurarCargoVIP(self.cog, nome_atual, cor_atual)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Ícone do Cargo", style=discord.ButtonStyle.secondary, emoji="🎨")
    async def botao_icone_cargo(self, interaction: discord.Interaction, button: discord.ui.Button):
        nivel = self.cog.obter_nivel_vip(self.membro)
        if not nivel:
            await interaction.response.send_message(
                "❌ Você não possui um plano **VIP** ativo no servidor.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        emojis_servidor = [e for e in guild.emojis if not e.animated]
        if not emojis_servidor:
            emojis_servidor = list(guild.emojis)

        if not emojis_servidor:
            embed_aviso = discord.Embed(
                title="⚠️ Nenhum Emoji Encontrado",
                description="Este servidor ainda não possui emojis personalizados cadastrados nas configurações do servidor.",
                color=Cores.AVISO
            )
            await interaction.response.send_message(embed=embed_aviso, ephemeral=True)
            return

        embed_escolha = discord.Embed(
            title="🎨  ESCOLHA O ÍCONE DO SEU CARGO",
            description=(
                "Selecione no menu abaixo qual emoji do servidor você deseja colocar como o "
                "**ícone oficial do seu cargo**.\n\n"
                "*(Ele aparecerá com destaque ao lado do seu nome, igual nas badges de cargos!)*"
            ),
            color=Cores.INFO
        )
        view_emojis = ViewEscolherEmojiCargo(self.cog, emojis_servidor, self.membro.id)
        await interaction.response.send_message(embed=embed_escolha, view=view_emojis, ephemeral=True)

    @discord.ui.button(label="Configurar Call", style=discord.ButtonStyle.success, emoji="🔊")
    async def botao_call(self, interaction: discord.Interaction, button: discord.ui.Button):
        nivel = self.cog.obter_nivel_vip(self.membro)
        if not nivel:
            await interaction.response.send_message(
                "❌ Você não possui um plano **VIP** ativo no servidor.",
                ephemeral=True
            )
            return

        nome_sugerido = f"🔊・Call de {self.membro.display_name}"
        modal = ModalConfigurarCallVIP(self.cog, nome_sugerido)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Amigos do VIP", style=discord.ButtonStyle.secondary, emoji="👥")
    async def botao_amigos(self, interaction: discord.Interaction, button: discord.ui.Button):
        nivel = self.cog.obter_nivel_vip(self.membro)
        if not nivel:
            await interaction.response.send_message(
                "❌ Você não possui um plano **VIP** ativo no servidor.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        guild_id_str = str(guild.id)
        user_id_str = str(self.membro.id)
        dados_user = self.cog.dados_vips.get(guild_id_str, {}).get(user_id_str, {})
        amigos_atuais = dados_user.get("amigos", [])
        limite = VIP_LIMITES_AMIGOS.get(nivel, 1)

        lista_txt = []
        for a_id in amigos_atuais:
            m = guild.get_member(a_id)
            lista_txt.append(m.mention if m else f"<@{a_id}>")

        amigos_desc = ", ".join(lista_txt) if lista_txt else "*Nenhum amigo adicionado ainda*"

        embed_amigos = discord.Embed(
            title="👥  GESTÃO DE AMIGOS DO VIP",
            description=(
                f"Compartilhe o seu cargo personalizado com os seus amigos mais próximos!\n"
                "──────────────────────────────────────────────\n"
                f"🔹 **Seu Plano:** **{VIP_CARGOS[nivel]}**\n"
                f"🔹 **Limite de Amigos:** `{len(amigos_atuais)}/{limite}`\n"
                f"🔹 **Amigos Atuais:** {amigos_desc}\n\n"
                "Selecione um amigo no menu abaixo para adicionar, ou use o botão para liberar vaga:"
            ),
            color=Cores.PADRAO
        )
        view_amigos = ViewAmigosVIP(self.cog, self.membro.id)
        await interaction.response.send_message(embed=embed_amigos, view=view_amigos, ephemeral=True)


# ========================================================
# VIEW PAINEL DE CONTROLE DE VIPS (!painelvip - ADMIN / STAFF)
# ========================================================
class ViewPainelGestaoVIP(discord.ui.View):
    def __init__(self, cog, autor: discord.Member):
        super().__init__(timeout=180)
        self.cog = cog
        self.autor = autor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas quem abriu o painel pode interagir com estes controles.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Criar Categoria VIP", style=discord.ButtonStyle.primary, emoji="📁")
    async def botao_criar_categoria_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # Busca ou cria os 3 cargos VIP
        cargos_vips = []
        for n in ["prata", "gold", "diamante"]:
            c = await self.cog.obter_ou_criar_cargo_vip(guild, n)
            cargos_vips.append(c)

        # Permissões restritas na Categoria (apenas VIPs e Administradores)
        overwrites_cat = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_roles=True)
        }
        for c in cargos_vips:
            overwrites_cat[c] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                connect=True,
                speak=True
            )

        nome_categoria = "👑・ÁREA VIP"

        # Verifica se a categoria já existe
        cat_existente = discord.utils.get(guild.categories, name=nome_categoria)
        if cat_existente:
            embed_aviso = discord.Embed(
                title="⚠️ Categoria VIP Já Existe",
                description=f"A categoria VIP **{nome_categoria}** já foi criada no servidor!",
                color=Cores.AVISO
            )
            await interaction.followup.send(embed=embed_aviso, ephemeral=True)
            return

        try:
            # Cria APENAS a Categoria Fechada, sem criar canais automáticos
            categoria_vip = await guild.create_category(
                name=nome_categoria,
                overwrites=overwrites_cat,
                reason=f"Categoria VIP criada via !painelvip por {interaction.user.name}"
            )

            embed_sucesso = discord.Embed(
                title="✅  CATEGORIA VIP CRIADA COM SUCESSO!",
                description=(
                    f"A categoria **{nome_categoria}** foi criada no servidor!\n"
                    "──────────────────────────────────────────────\n"
                    "🔒 **Permissões:** O canal é privado e apenas membros com planos VIP e administradores conseguem vê-la.\n\n"
                    "🔊 **Calls Privadas:** Agora, quando os membros VIP usarem o botão **'Configurar Call'** no `!vip`, "
                    f"a call personalizada de cada um será criada diretamente dentro desta categoria!"
                ),
                color=Cores.SUCESSO
            )
            await interaction.followup.send(embed=embed_sucesso, ephemeral=True)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="O bot não tem permissão para criar categorias.",
                color=Cores.ERRO
            )
            await interaction.followup.send(embed=embed_erro, ephemeral=True)

    @discord.ui.button(label="Membros com VIP", style=discord.ButtonStyle.secondary, emoji="👥")
    async def botao_membros_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        vips_por_nivel = {"diamante": [], "gold": [], "prata": []}
        for membro in guild.members:
            if membro.bot:
                continue
            nivel = self.cog.obter_nivel_vip(membro)
            if nivel:
                vips_por_nivel[nivel].append(membro)

        total_vips = sum(len(l) for l in vips_por_nivel.values())

        embed_lista = discord.Embed(
            title="💎  MEMBROS VIP DO SERVIDOR",
            description=(
                f"Atualmente há **{total_vips} membro(s)** com planos VIP ativos:\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.INFO
        )

        for n, lista in vips_por_nivel.items():
            nome_plano = VIP_CARGOS[n]
            emoji_plano = "💎" if n == "diamante" else ("🥇" if n == "gold" else "🥈")
            membros_txt = "\n".join([f"• {m.mention} (`@{m.name}`)" for m in lista]) if lista else "*Nenhum membro*"
            embed_lista.add_field(
                name=f"{emoji_plano}  {nome_plano} ({len(lista)})",
                value=membros_txt,
                inline=False
            )

        embed_lista.set_footer(text=f"Total: {total_vips} membros VIP ativos")
        await interaction.followup.send(embed=embed_lista, ephemeral=True)


# ========================================================
# MODAL: DEFINIR DIAS DE DURAÇÃO DO VIP
# ========================================================
class ModalAtribuirVIPDias(discord.ui.Modal):
    def __init__(self, view_pai, nivel: str):
        self.view_pai = view_pai
        self.nivel = nivel
        nome_plano = VIP_CARGOS[nivel]
        super().__init__(title=f"⏳ Duração do {nome_plano}")

        self.dias_input = discord.ui.TextInput(
            label="Quantidade de Dias do VIP",
            placeholder="Digite o número de dias (ex: 30, 60, 365, ou 0 = Permanente)",
            default="30",
            required=True,
            max_length=5
        )
        self.add_item(self.dias_input)

    async def on_submit(self, interaction: discord.Interaction):
        valor = self.dias_input.value.strip()
        try:
            dias = int(valor)
            if dias < 0:
                dias = 0
        except ValueError:
            dias = 30

        await self.view_pai.aplicar_vip_com_dias(interaction, self.nivel, dias)


# ========================================================
# VIEW SET VIP (ADMIN MODAL / BUTTONS)
# ========================================================
class ViewSetVIP(discord.ui.View):
    def __init__(self, cog, membro: discord.Member, autor: discord.Member):
        super().__init__(timeout=60)
        self.cog = cog
        self.membro = membro
        self.autor = autor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.autor.id:
            await interaction.response.send_message(
                "❌ Apenas o moderador que usou o comando pode selecionar o VIP.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="VIP Prata", style=discord.ButtonStyle.secondary, emoji="🥈")
    async def botao_prata(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalAtribuirVIPDias(self, "prata"))

    @discord.ui.button(label="VIP Gold", style=discord.ButtonStyle.success, emoji="🥇")
    async def botao_gold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalAtribuirVIPDias(self, "gold"))

    @discord.ui.button(label="VIP Diamante", style=discord.ButtonStyle.primary, emoji="💎")
    async def botao_diamante(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalAtribuirVIPDias(self, "diamante"))

    @discord.ui.button(label="Remover VIP", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def botao_remover(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        removidos = []
        for nivel in ["prata", "gold", "diamante"]:
            nome = VIP_CARGOS[nivel]
            role = discord.utils.get(guild.roles, name=nome)
            if role and role in self.membro.roles:
                await self.membro.remove_roles(role, reason=f"VIP removido por {interaction.user.name}")
                removidos.append(nome)

        embed = discord.Embed(
            title="🗑️  VIP REMOVIDO COM SUCESSO",
            description=(
                f"Todos os cargos VIP foram retirados de {self.membro.mention}.\n"
                "──────────────────────────────────────────────"
                if removidos else f"{self.membro.mention} não possuía nenhum cargo VIP ativo."
            ),
            color=Cores.AVISO
        )
        embed.set_footer(text=f"Ação executada por {interaction.user.name} • Apaga em 2 minutos")
        for child in self.children:
            child.disabled = True
        msg = await interaction.edit_original_response(embed=embed, view=self)
        try:
            await asyncio.sleep(TEMPO_DELETE_VIP)
            await msg.delete()
        except Exception:
            pass

    async def aplicar_vip_com_dias(self, interaction: discord.Interaction, nivel: str, dias: int):
        await interaction.response.defer()
        guild = interaction.guild
        import time

        for n in ["prata", "gold", "diamante"]:
            nome_antigo = VIP_CARGOS[n]
            cargo_antigo = discord.utils.get(guild.roles, name=nome_antigo)
            if cargo_antigo and cargo_antigo in self.membro.roles:
                await self.membro.remove_roles(cargo_antigo, reason="Atualização de plano VIP")

        cargo_vip = await self.cog.obter_ou_criar_cargo_vip(guild, nivel)
        await self.membro.add_roles(cargo_vip, reason=f"VIP concedido por {interaction.user.name} ({cargo_vip.name})")

        # Salva data de expiração nos dados_vips
        guild_id_str = str(guild.id)
        user_id_str = str(self.membro.id)
        if guild_id_str not in self.cog.dados_vips:
            self.cog.dados_vips[guild_id_str] = {}
        if user_id_str not in self.cog.dados_vips[guild_id_str]:
            self.cog.dados_vips[guild_id_str][user_id_str] = {}

        if dias > 0:
            expira_em = int(time.time()) + (dias * 86400)
            self.cog.dados_vips[guild_id_str][user_id_str]["expira_em"] = expira_em
            duracao_txt = f"{dias} dias (<t:{expira_em}:R>)"
        else:
            self.cog.dados_vips[guild_id_str][user_id_str].pop("expira_em", None)
            duracao_txt = "Permanente"

        salvar_dados_vips(self.cog.dados_vips)

        cor = VIP_CORES.get(nivel, Cores.SUCESSO)
        embed_sucesso = discord.Embed(
            title="💎  VIP CONCEDIDO COM SUCESSO",
            description=(
                f"O membro {self.membro.mention} recebeu o plano **{cargo_vip.name}**!\n"
                "──────────────────────────────────────────────"
            ),
            color=cor
        )
        embed_sucesso.add_field(name="👤  Membro", value=f"{self.membro.mention}\n`@{self.membro.name}`", inline=True)
        embed_sucesso.add_field(name="🏷️  Cargo Atribuído", value=cargo_vip.mention, inline=True)
        embed_sucesso.add_field(name="⏳  Duração", value=f"`{duracao_txt}`", inline=True)
        embed_sucesso.add_field(name="🛡️  Moderador", value=f"{interaction.user.mention}\n`@{interaction.user.name}`", inline=False)
        embed_sucesso.set_footer(text="O usuário já pode utilizar !vip para abrir seu painel • Apaga em 2 minutos")

        for child in self.children:
            child.disabled = True
        msg = await interaction.edit_original_response(embed=embed_sucesso, view=self)
        try:
            await asyncio.sleep(TEMPO_DELETE_VIP)
            await msg.delete()
        except Exception:
            pass

    async def aplicar_vip(self, interaction: discord.Interaction, nivel: str):
        await self.aplicar_vip_com_dias(interaction, nivel, 30)


# ========================================================
# COG PRINCIPAL VIP
# ========================================================
class VIP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dados_vips = carregar_dados_vips()
        self.verificar_expiracao_vips.start()

    def cog_unload(self):
        self.verificar_expiracao_vips.cancel()

    @tasks.loop(minutes=5)
    async def verificar_expiracao_vips(self):
        agora = int(time.time())
        alterou = False
        for guild_id_str, users in list(self.dados_vips.items()):
            try:
                guild = self.bot.get_guild(int(guild_id_str))
            except Exception:
                continue
            if not guild:
                continue

            for user_id_str, udata in list(users.items()):
                expira_em = udata.get("expira_em")
                if expira_em and agora >= expira_em:
                    try:
                        membro = guild.get_member(int(user_id_str))
                    except Exception:
                        membro = None

                    # 1. Remover cargos base VIP
                    if membro:
                        for nivel in ["prata", "gold", "diamante"]:
                            cargo_base = discord.utils.get(guild.roles, name=VIP_CARGOS[nivel])
                            if cargo_base and cargo_base in membro.roles:
                                try:
                                    await membro.remove_roles(cargo_base, reason="VIP expirado")
                                except Exception:
                                    pass

                    # 2. Deletar cargo customizado e liberar amigos
                    cargo_id = udata.get("cargo_id")
                    if cargo_id:
                        cargo_custom = guild.get_role(cargo_id)
                        if cargo_custom:
                            try:
                                await cargo_custom.delete(reason="VIP expirado")
                            except Exception:
                                pass

                    # 3. Deletar canal de voz privado
                    canal_voz_id = udata.get("canal_voz_id")
                    if canal_voz_id:
                        canal_voz = guild.get_channel(canal_voz_id)
                        if canal_voz:
                            try:
                                await canal_voz.delete(reason="VIP expirado")
                            except Exception:
                                pass

                    # 4. Notificar membro no privado (DM)
                    if membro:
                        try:
                            emb = discord.Embed(
                                title="⌛ Seu Plano VIP Expirou",
                                description=(
                                    f"Olá {membro.name}, seu plano VIP no servidor **{guild.name}** chegou ao fim.\n\n"
                                    "Seu cargo personalizado e canal de voz foram removidos.\n"
                                    "Caso deseje renovar, entre em contato com a equipe de administração!"
                                ),
                                color=Cores.AVISO
                            )
                            await membro.send(embed=emb)
                        except Exception:
                            pass

                    # 5. Notificar log de auditoria
                    cog_logs = self.bot.get_cog("Logs")
                    if cog_logs:
                        emb_log = discord.Embed(
                            title="⌛ VIP Expirado",
                            description=f"O plano VIP de <@{user_id_str}> expirou e seus privilégios foram revogados.",
                            color=Cores.AVISO
                        )
                        await cog_logs.enviar_log(guild, emb_log)

                    # Remove o registro do usuário
                    self.dados_vips[guild_id_str].pop(user_id_str, None)
                    alterou = True

        if alterou:
            salvar_dados_vips(self.dados_vips)

    @verificar_expiracao_vips.before_loop
    async def before_verificar(self):
        await self.bot.wait_until_ready()

    def obter_nivel_vip(self, membro: discord.Member) -> str | None:
        """Retorna o nível VIP do membro ('diamante', 'gold', 'prata' ou None)."""
        nomes_cargos_membro = [c.name.lower() for c in membro.roles]
        for nivel in ["diamante", "gold", "prata"]:
            nome_esperado = VIP_CARGOS[nivel].lower()
            if nome_esperado in nomes_cargos_membro:
                return nivel
        return None

    async def obter_ou_criar_cargo_vip(self, guild: discord.Guild, nivel: str) -> discord.Role:
        """Localiza ou cria automaticamente o cargo do nível VIP com cor e destaque."""
        nome_cargo = VIP_CARGOS[nivel]
        cargo = discord.utils.get(guild.roles, name=nome_cargo)

        if not cargo:
            cargo = await guild.create_role(
                name=nome_cargo,
                color=discord.Color.default(),
                hoist=True,
                mentionable=True,
                reason=f"Criação automática do cargo {nome_cargo}"
            )
        return cargo

    # ========================================================
    # COMANDO: PAINEL DO MEMBRO VIP (!vip)
    # ========================================================
    @commands.command(name="vip", aliases=["vips", "meuvip"])
    async def vip(self, ctx):
        """Abre o Painel Interativo de Vantagens e Configuração VIP do membro."""
        await tentar_deletar_mensagem(ctx)

        nivel_atual = self.obter_nivel_vip(ctx.author)
        cor_embed = VIP_CORES.get(nivel_atual, Cores.PADRAO) if nivel_atual else Cores.PADRAO

        guild_id_str = str(ctx.guild.id)
        user_id_str = str(ctx.author.id)
        dados_user = self.dados_vips.get(guild_id_str, {}).get(user_id_str, {})
        cargo_pessoal_id = dados_user.get("cargo_id")
        cargo_pessoal = ctx.guild.get_role(cargo_pessoal_id) if cargo_pessoal_id else None
        amigos_adicionados = dados_user.get("amigos", [])

        embed = discord.Embed(
            title="👑  PAINEL DE CONTROLE VIP",
            description=(
                f"Olá {ctx.author.mention}, seja muito bem-vindo à sua central de gerenciamento VIP!\n\n"
                "Personalize seu cargo, sua sala de voz e gerencie seus privilégios diretamente "
                "utilizando os **botões interativos** abaixo.\n"
                "──────────────────────────────────────────────"
            ),
            color=cor_embed
        )

        if nivel_atual:
            nome_vip = VIP_CARGOS[nivel_atual]
            limite_amigos = VIP_LIMITES_AMIGOS.get(nivel_atual, 1)

            embed.add_field(
                name="💎  Seu Plano Ativo",
                value=f"```fix\n{nome_vip}\n```",
                inline=True
            )

            cargo_pessoal_txt = f"{cargo_pessoal.mention}\n`Cor: {str(cargo_pessoal.color)}`" if cargo_pessoal else "*Nenhum cargo criado ainda*"
            embed.add_field(
                name="🏷️  Cargo Pessoal",
                value=cargo_pessoal_txt,
                inline=True
            )

            embed.add_field(
                name="👥  Vagas de Amigos",
                value=f"**{len(amigos_adicionados)} / {limite_amigos}** amigos",
                inline=True
            )

            expira_em = dados_user.get("expira_em")
            duracao_txt = f"<t:{expira_em}:R>" if expira_em else "`Permanente`"
            embed.add_field(
                name="⏳  Validade do VIP",
                value=duracao_txt,
                inline=True
            )

            embed.add_field(
                name="⚡  Ações Rápidas Disponíveis",
                value=(
                    "• 🏷️ **Configurar Cargo:** Abre formulário para escolher nome e cor hex do seu cargo.\n"
                    "• 🎨 **Ícone do Cargo:** Escolha qualquer emoji do servidor para ser badge ao lado do nome.\n"
                    "• 🔊 **Configurar Call:** Cria ou atualiza sua call restrita apenas para quem tem seu cargo VIP.\n"
                    "• 👥 **Amigos do VIP:** Adicione ou remova amigos do seu cargo pessoal."
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="💎  Status da Assinatura",
                value="```yaml\nNenhum VIP Ativo\n```",
                inline=True
            )
            embed.add_field(
                name="🛒  Como Adquirir",
                value="Abra um ticket ou entre em contato com a equipe de administração!",
                inline=True
            )
            embed.add_field(
                name="🏆  Planos & Vantagens",
                value=(
                    f"• 🥈 **{VIP_CARGOS['prata']}**: Call privada + Cargo pessoal + {VIP_LIMITES_AMIGOS['prata']} amigo\n"
                    f"• 🥇 **{VIP_CARGOS['gold']}**: Call privada + Cargo pessoal + {VIP_LIMITES_AMIGOS['gold']} amigos\n"
                    f"• 💎 **{VIP_CARGOS['diamante']}**: Call privada + Cargo pessoal + {VIP_LIMITES_AMIGOS['diamante']} amigos"
                ),
                inline=False
            )

        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(
            text=f"Servidor: {ctx.guild.name} • Use os botões abaixo • Apaga em 2 minutos",
            icon_url=ctx.author.display_avatar.url
        )

        view = ViewPainelUsuarioVIP(self, ctx.author)
        await ctx.send(embed=embed, view=view, delete_after=120)

    # ========================================================
    # COMANDO: PAINEL DE GESTÃO DA STAFF (!painelvip)
    # ========================================================
    @commands.command(name="painelvip", aliases=["gestaovip", "staffvip", "configvip"])
    async def painelvip(self, ctx):
        """Abre o Painel Administrativo de Gestão do Sistema VIP."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "vip"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa possuir o cargo autorizado de gestão VIP para abrir este painel.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        embed = discord.Embed(
            title="⚙️  PAINEL DE ADMINISTRAÇÃO VIP",
            description=(
                f"Olá {ctx.author.mention}, use os controles abaixo para gerenciar o sistema de VIPs no servidor.\n\n"
                "• **📁 Criar Categoria VIP:** Gera automaticamente a categoria `👑・ÁREA VIP` com chat de texto "
                "e lounge de voz visíveis exclusivamente para quem possui VIP.\n"
                "• **👥 Membros com VIP:** Lista em tempo real todos os membros com VIP e seus respectivos planos.\n"
                "──────────────────────────────────────────────"
            ),
            color=Cores.PADRAO
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"Painel administrativo • {ctx.guild.name} • Apaga em 2 minutos")

        view = ViewPainelGestaoVIP(self, ctx.author)
        await ctx.send(embed=embed, view=view, delete_after=120)

    @painelvip.error
    async def painelvip_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você não possui permissão para abrir o painel de gestão VIP (`!painelvip`).",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDOS DE ADMINISTRAÇÃO: SETAR E REMOVER VIP
    # ========================================================
    @commands.command(name="setvip")
    async def setvip(self, ctx, membro: discord.Member, tipo: str = None):
        """Atribui um nível de VIP a um membro (com botões interativos ou informando o tipo)."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "vip"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de permissão ou do cargo configurado para gerenciar VIPs.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if not tipo:
            nivel_atual = self.obter_nivel_vip(membro)
            vip_texto = f"**{VIP_CARGOS[nivel_atual]}**" if nivel_atual else "*Nenhum VIP ativo*"

            embed = discord.Embed(
                title="💎  SELECIONE O VIP DO MEMBRO",
                description=(
                    f"Escolha qual nível de VIP deseja atribuir para {membro.mention}:\n"
                    "──────────────────────────────────────────────\n"
                    f"**VIP Atual:** {vip_texto}\n\n"
                    "Clique em um dos botões abaixo:"
                ),
                color=Cores.INFO
            )
            embed.set_thumbnail(url=membro.display_avatar.url)
            embed.set_footer(text="Apenas o autor do comando pode clicar • Apaga em 2 minutos")

            view = ViewSetVIP(self, membro, ctx.author)
            await ctx.send(embed=embed, view=view, delete_after=TEMPO_DELETE_VIP)
            return

        tipo_limpo = tipo.strip().lower()
        mapa_tipos = {
            "prata": "prata",
            "silver": "prata",
            "gold": "gold",
            "ouro": "gold",
            "diamante": "diamante",
            "diamond": "diamante",
        }

        if tipo_limpo not in mapa_tipos:
            embed_erro = discord.Embed(
                title="❌ Tipo de VIP Inválido",
                description=(
                    "Escolha um dos tipos de VIP válidos:\n"
                    "• `prata`\n"
                    "• `gold`\n"
                    "• `diamante`\n\n"
                    "Ou use apenas: `!setvip @Membro` para abrir o menu com botões!"
                ),
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        nivel_escolhido = mapa_tipos[tipo_limpo]

        try:
            for nivel_existente in ["prata", "gold", "diamante"]:
                nome_cargo_antigo = VIP_CARGOS[nivel_existente]
                cargo_antigo = discord.utils.get(ctx.guild.roles, name=nome_cargo_antigo)
                if cargo_antigo and cargo_antigo in membro.roles:
                    await membro.remove_roles(cargo_antigo, reason="Atualização de plano VIP")

            cargo_vip = await self.obter_ou_criar_cargo_vip(ctx.guild, nivel_escolhido)
            await membro.add_roles(cargo_vip, reason=f"VIP concedido por {ctx.author.name} ({cargo_vip.name})")

            cor = VIP_CORES.get(nivel_escolhido, Cores.SUCESSO)
            embed_sucesso = discord.Embed(
                title="💎  VIP CONCEDIDO COM SUCESSO",
                description=(
                    f"O membro {membro.mention} recebeu o plano **{cargo_vip.name}**!\n"
                    "──────────────────────────────────────────────"
                ),
                color=cor
            )
            embed_sucesso.add_field(name="👤  Membro", value=f"{membro.mention}\n`@{membro.name}`", inline=True)
            embed_sucesso.add_field(name="🏷️  Cargo", value=cargo_vip.mention, inline=True)
            embed_sucesso.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)
            embed_sucesso.set_footer(text="O usuário já pode utilizar !vip para configurar seu cargo e call.")
            await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_VIP)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="O bot não tem permissão para gerenciar ou criar este cargo VIP.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @setvip.error
    async def setvip_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Gerenciar Cargos` para conceder VIP.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa mencionar quem receberá o VIP!\n\n**Exemplo:** `!setvip @Usuario`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    @commands.command(name="removervip", aliases=["tirarvip", "delvip"])
    async def removervip(self, ctx, membro: discord.Member):
        """Remove todos os cargos de VIP do membro especificado."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "vip"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa de permissão ou do cargo configurado para remover VIPs.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        removidos = []
        try:
            for nivel in ["prata", "gold", "diamante"]:
                nome_cargo = VIP_CARGOS[nivel]
                cargo = discord.utils.get(ctx.guild.roles, name=nome_cargo)
                if cargo and cargo in membro.roles:
                    await membro.remove_roles(cargo, reason=f"VIP revogado por {ctx.author.name}")
                    removidos.append(cargo.name)

            if not removidos:
                embed_aviso = discord.Embed(
                    title="⚠️ Nenhum VIP Encontrado",
                    description=f"{membro.mention} não possui nenhum cargo de VIP ativo.",
                    color=Cores.AVISO
                )
                await ctx.send(embed=embed_aviso, delete_after=TEMPO_DELETE_ERRO)
                return

            embed_sucesso = discord.Embed(
                title="🗑️  VIP REVOGADO COM SUCESSO",
                description=(
                    f"Os seguintes cargos VIP foram removidos de {membro.mention}:\n"
                    "──────────────────────────────────────────────\n• " + "\n• ".join(removidos)
                ),
                color=Cores.SUCESSO
            )
            embed_sucesso.set_footer(text="Esta mensagem será apagada em 2 minutos.")
            await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_VIP)

        except discord.Forbidden:
            embed_erro = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Não possuo permissão para remover cargos deste membro.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @removervip.error
    async def removervip_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Gerenciar Cargos` para remover VIP.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Mencione o membro que terá o VIP revogado!\n\n**Exemplo:** `!removervip @Membro`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)


async def setup(bot):
    await bot.add_cog(VIP(bot))

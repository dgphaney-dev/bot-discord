import asyncio
import json
from pathlib import Path
import discord
from discord.ext import commands
from config import CARGO_MUTE_NOME, Cores, TEMPO_DELETE_ERRO, TEMPO_DELETE_SUCESSO
from utils.helpers import (
    converter_tempo,
    formatar_segundos,
    obter_avatar_url,
    tem_permissao_acao,
    tem_permissao_mute,
    tentar_deletar_mensagem,
)

# Caminho para o arquivo JSON de imagens personalizadas de cada moderador
ARQUIVO_MOD_IMAGENS = Path(__file__).resolve().parent.parent / "data" / "mod_imagens.json"


def carregar_mod_imagens() -> dict:
    """Carrega as imagens personalizadas dos moderadores."""
    if not ARQUIVO_MOD_IMAGENS.exists():
        return {}
    try:
        with open(ARQUIVO_MOD_IMAGENS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_mod_imagens(dados: dict):
    """Salva as imagens personalizadas no arquivo JSON."""
    ARQUIVO_MOD_IMAGENS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_MOD_IMAGENS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


class Moderacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.imagens_mods = carregar_mod_imagens()

    # ========================================================
    # MÉTODOS AUXILIARES PARA IMAGENS DE MODERAÇÃO
    # ========================================================
    def obter_imagem_mod(self, guild_id: int, user_id: int, tipo: str) -> str | None:
        """Obtém a imagem personalizada de um moderador para uma determinada ação."""
        return (
            self.imagens_mods.get(str(guild_id), {})
            .get(str(user_id), {})
            .get(tipo.lower())
        )

    def definir_imagem_mod(self, guild_id: int, user_id: int, tipo: str, url: str | None):
        """Salva ou remove a imagem personalizada de um moderador."""
        g_id = str(guild_id)
        u_id = str(user_id)
        t_tipo = tipo.lower()

        if g_id not in self.imagens_mods:
            self.imagens_mods[g_id] = {}
        if u_id not in self.imagens_mods[g_id]:
            self.imagens_mods[g_id][u_id] = {}

        if url:
            self.imagens_mods[g_id][u_id][t_tipo] = url
        else:
            self.imagens_mods[g_id][u_id].pop(t_tipo, None)

        salvar_mod_imagens(self.imagens_mods)

    # ========================================================
    # COMANDO: MUTE
    # ========================================================
    @commands.command(name="mute")
    async def mute(self, ctx, membro: discord.Member, tempo_str: str, *, motivo: str = "Não especificado"):
        """Silencia temporariamente um membro por um determinado período."""
        await tentar_deletar_mensagem(ctx)

        # 1. Verificação de permissões do autor
        if not tem_permissao_mute(ctx):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description=(
                    "Você precisa ser Administrador, ter permissão de `Gerenciar Cargos` "
                    "ou possuir o cargo autorizado para silenciar membros."
                ),
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # 2. Verificações de hierarquia e regras de negócio
        if membro == ctx.author:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode silenciar a si mesmo.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro == self.bot.user:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Eu não posso me silenciar.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode silenciar um administrador do servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # Hierarquia entre quem executa e o alvo
        if ctx.author != ctx.guild.owner and membro.top_role >= ctx.author.top_role:
            embed = discord.Embed(
                title="❌ Hierarquia Insuficiente",
                description="Você não pode silenciar um membro que possui cargo superior ou igual ao seu.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # Hierarquia do bot
        if membro.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Hierarquia do Bot",
                description="O cargo desse membro é superior ou igual ao meu cargo mais alto.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # 3. Conversão de tempo
        segundos = converter_tempo(tempo_str)
        if segundos is None or segundos <= 0:
            embed = discord.Embed(
                title="❌ Formato de Tempo Inválido",
                description=(
                    "Por favor, utilize formatos válidos como:\n"
                    "• `30s` (segundos)\n"
                    "• `15m` (minutos)\n"
                    "• `2h` (horas)\n"
                    "• `1d` (dias)"
                ),
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # 4. Localização ou criação automática do cargo de Mute
        cargo_mutado = discord.utils.get(ctx.guild.roles, name=CARGO_MUTE_NOME)
        if not cargo_mutado:
            try:
                embed_criando = discord.Embed(
                    title="⚙️ Configurando Servidor",
                    description=f"O cargo **'{CARGO_MUTE_NOME}'** não existe. Criando e configurando permissões...",
                    color=Cores.AVISO
                )
                aviso_config = await ctx.send(embed=embed_criando)

                cargo_mutado = await ctx.guild.create_role(
                    name=CARGO_MUTE_NOME,
                    reason="Criado automaticamente pelo sistema de mute."
                )

                # Ajusta permissões nos canais de texto e voz
                for canal in ctx.guild.channels:
                    try:
                        if isinstance(canal, discord.TextChannel):
                            await canal.set_permissions(
                                cargo_mutado,
                                send_messages=False,
                                add_reactions=False
                            )
                        elif isinstance(canal, discord.VoiceChannel):
                            await canal.set_permissions(
                                cargo_mutado,
                                speak=False
                            )
                    except discord.Forbidden:
                        pass

                await aviso_config.delete()
            except Exception as e:
                embed_erro = discord.Embed(
                    title="❌ Falha na Configuração",
                    description=f"Não foi possível criar o cargo '{CARGO_MUTE_NOME}':\n`{e}`",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
                return

        # 5. Aplica o cargo ao membro
        try:
            await membro.add_roles(
                cargo_mutado,
                reason=f"Mutado por {ctx.author.name}. Motivo: {motivo}"
            )
        except discord.Forbidden:
            embed_perm = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Não tenho permissões suficientes para atribuir o cargo a este usuário.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_perm, delete_after=TEMPO_DELETE_ERRO)
            return

        # 6. Embed de confirmação
        tempo_formatado = formatar_segundos(segundos)
        embed_mute = discord.Embed(
            title="🔇  MEMBRO SILENCIADO",
            description=(
                f"> O membro {membro.mention} foi punido e teve suas permissões de fala temporariamente revogadas.\n\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            ),
            color=Cores.MODERACAO
        )
        embed_mute.set_author(name=f"Moderação • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed_mute.add_field(name="👤  Membro Punido", value=f"{membro.mention}\n`@{membro.name}`", inline=True)
        embed_mute.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)
        embed_mute.add_field(name="⏱️  Duração", value=f"```fix\n{tempo_formatado}\n```", inline=True)
        embed_mute.add_field(name="📋  Motivo Registrado", value=f"```yaml\n{motivo}\n```", inline=False)

        avatar_membro = obter_avatar_url(membro)
        if avatar_membro:
            embed_mute.set_thumbnail(url=avatar_membro)

        # Imagem personalizada configurada pelo moderador para MUTE
        imagem_mod = self.obter_imagem_mod(ctx.guild.id, ctx.author.id, "mute")
        if imagem_mod:
            embed_mute.set_image(url=imagem_mod)

        embed_mute.set_footer(text=f"ID: {membro.id} • Moderação Ativa", icon_url=ctx.author.display_avatar.url)
        embed_mute.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed_mute, delete_after=TEMPO_DELETE_SUCESSO)

        # 7. Tarefa assíncrona para remover o cargo após o tempo limite
        async def desmutar_apos_tempo():
            await asyncio.sleep(segundos)
            membro_atualizado = ctx.guild.get_member(membro.id)
            if membro_atualizado and cargo_mutado in membro_atualizado.roles:
                try:
                    await membro_atualizado.remove_roles(
                        cargo_mutado,
                        reason="Tempo de silenciamento finalizado automaticamente."
                    )
                    embed_unmute = discord.Embed(
                        title="🔊 Membro Desmutado",
                        description=f"O tempo de silenciamento de {membro_atualizado.mention} expirou.",
                        color=Cores.SUCESSO
                    )
                    # Imagem personalizada configurada pelo moderador para UNMUTE
                    imagem_unmute_mod = self.obter_imagem_mod(ctx.guild.id, ctx.author.id, "unmute")
                    if imagem_unmute_mod:
                        embed_unmute.set_image(url=imagem_unmute_mod)

                    await ctx.send(embed=embed_unmute, delete_after=TEMPO_DELETE_SUCESSO)
                except Exception as erro:
                    print(f"Erro ao desmutar automaticamente {membro.name}: {erro}")

        asyncio.create_task(desmutar_apos_tempo())

    @mute.error
    async def mute_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)

        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa informar o membro e a duração!\n\n**Exemplo:** `!mute @Usuario 15m Spam no chat`",
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
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Argumento Inválido",
                description="Verifique os argumentos informados e tente novamente.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO: UNMUTE
    # ========================================================
    @commands.command(name="unmute")
    async def unmute(self, ctx, membro: discord.Member):
        """Remove o silenciamento de um membro manualmente."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_mute(ctx):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você não possui permissão para desmutar membros.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        cargo_mutado = discord.utils.get(ctx.guild.roles, name=CARGO_MUTE_NOME)
        if not cargo_mutado or cargo_mutado not in membro.roles:
            embed = discord.Embed(
                title="⚠️ Membro Não Silenciado",
                description=f"{membro.mention} não possui o cargo **'{CARGO_MUTE_NOME}'**.",
                color=Cores.AVISO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        try:
            await membro.remove_roles(
                cargo_mutado,
                reason=f"Desmutado manualmente por {ctx.author.name}"
            )
            embed_unmute = discord.Embed(
                title="🔊  MEMBRO DESMUTADO",
                description=(
                    f"> O silenciamento do membro {membro.mention} foi revogado com sucesso!\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.SUCESSO
            )
            embed_unmute.set_author(name=f"Moderação • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_unmute.add_field(name="👤  Membro", value=f"{membro.mention}\n`@{membro.name}`", inline=True)
            embed_unmute.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)
            embed_unmute.add_field(name="📋  Status", value="```diff\n+ Fala Liberada\n```", inline=True)

            avatar_membro = obter_avatar_url(membro)
            if avatar_membro:
                embed_unmute.set_thumbnail(url=avatar_membro)

            # Imagem personalizada configurada pelo moderador para UNMUTE
            imagem_mod = self.obter_imagem_mod(ctx.guild.id, ctx.author.id, "unmute")
            if imagem_mod:
                embed_unmute.set_image(url=imagem_mod)

            embed_unmute.set_footer(text=f"ID: {membro.id}", icon_url=ctx.author.display_avatar.url)
            embed_unmute.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed_unmute, delete_after=TEMPO_DELETE_SUCESSO)
        except discord.Forbidden:
            embed_perm = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Não possuo permissões na hierarquia para alterar cargos deste usuário.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_perm, delete_after=TEMPO_DELETE_ERRO)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro ao Desmutar",
                description=f"Ocorreu uma falha ao tentar desmutar:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @unmute.error
    async def unmute_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)

        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa mencionar quem deseja desmutar!\n\n**Exemplo:** `!unmute @Usuario`",
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

    @commands.command(name="ban")
    async def ban(self, ctx, membro: discord.Member, *, motivo: str = "Não especificado"):
        """Bane um membro do servidor."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "ban"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa da permissão de `Banir Membros` ou do cargo configurado para banir.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro == ctx.author:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode banir a si mesmo.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode banir um administrador do servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if ctx.author != ctx.guild.owner and membro.top_role >= ctx.author.top_role:
            embed = discord.Embed(
                title="❌ Hierarquia Insuficiente",
                description="Você não pode banir um membro com cargo superior ou igual ao seu.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Hierarquia do Bot",
                description="Este membro tem cargo igual ou superior ao cargo mais alto do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        try:
            # Imagem personalizada configurada pelo moderador para BAN
            imagem_mod = self.obter_imagem_mod(ctx.guild.id, ctx.author.id, "ban")

            # Tenta avisar o membro via mensagem privada (DM)
            try:
                embed_dm = discord.Embed(
                    title=f"🔨 Você foi banido de {ctx.guild.name}",
                    description=f"**Motivo:** {motivo}",
                    color=Cores.ERRO
                )
                if imagem_mod:
                    embed_dm.set_image(url=imagem_mod)
                await membro.send(embed=embed_dm)
            except (discord.Forbidden, discord.HTTPException):
                pass

            await membro.ban(
                reason=f"Banido por {ctx.author.name}. Motivo: {motivo}",
                delete_message_seconds=86400
            )

            embed_ban = discord.Embed(
                title="🔨  MEMBRO BANIDO DO SERVIDOR",
                description=(
                    f"> O infrator {membro.mention} foi banido permanentemente.\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.ERRO
            )
            embed_ban.set_author(name=f"Punição Aplicada • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_ban.add_field(name="👤  Membro Banido", value=f"{membro.mention}\n`@{membro.name}`", inline=True)
            embed_ban.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)
            embed_ban.add_field(name="🆔  ID do Membro", value=f"`{membro.id}`", inline=True)
            embed_ban.add_field(name="📋  Motivo do Banimento", value=f"```yaml\n{motivo}\n```", inline=False)

            avatar_membro = obter_avatar_url(membro)
            if avatar_membro:
                embed_ban.set_thumbnail(url=avatar_membro)

            if imagem_mod:
                embed_ban.set_image(url=imagem_mod)

            embed_ban.set_footer(text=f"ID: {membro.id} • Punição Permanente", icon_url=ctx.author.display_avatar.url)
            embed_ban.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed_ban, delete_after=TEMPO_DELETE_SUCESSO)

        except discord.Forbidden:
            embed_forbidden = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Não possuo privilégios suficientes para aplicar o banimento neste usuário.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_forbidden, delete_after=TEMPO_DELETE_ERRO)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro no Banimento",
                description=f"Houve uma falha inesperada ao tentar banir:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @ban.error
    async def ban_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)

        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Banir Membros` para utilizar este comando.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa mencionar quem deseja banir!\n\n**Exemplo:** `!ban @Usuario Motivo do ban`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Membro Não Encontrado",
                description="O membro informado não foi encontrado no servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    @commands.command(name="unban")
    async def unban(self, ctx, id_usuario: int, *, motivo: str = "Não especificado"):
        """Remove o banimento de um usuário pelo ID."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "ban"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa da permissão de `Banir Membros` ou do cargo configurado para desbanir.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        try:
            ban_entry = None
            async for banimento in ctx.guild.bans():
                if banimento.user.id == id_usuario:
                    ban_entry = banimento
                    break

            if not ban_entry:
                embed = discord.Embed(
                    title="❌ Banimento Não Encontrado",
                    description="O ID informado não consta na lista de banidos deste servidor.",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
                return

            usuario = ban_entry.user
            await ctx.guild.unban(
                usuario,
                reason=f"Desbanido por {ctx.author.name}. Motivo: {motivo}"
            )

            embed_unban = discord.Embed(
                title="🕊️  MEMBRO DESBANIDO",
                description=(
                    f"> O banimento do usuário {usuario.mention} foi revogado com sucesso.\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.SUCESSO
            )
            embed_unban.set_author(name=f"Moderação • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_unban.add_field(name="👤  Usuário", value=f"{usuario.mention}\n`@{usuario.name}`", inline=True)
            embed_unban.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)
            embed_unban.add_field(name="🆔  ID do Usuário", value=f"`{usuario.id}`", inline=True)
            embed_unban.add_field(name="📋  Motivo Registrado", value=f"```yaml\n{motivo}\n```", inline=False)

            avatar_usuario = obter_avatar_url(usuario)
            if avatar_usuario:
                embed_unban.set_thumbnail(url=avatar_usuario)

            # Imagem personalizada configurada pelo moderador para UNBAN
            imagem_mod = self.obter_imagem_mod(ctx.guild.id, ctx.author.id, "unban")
            if imagem_mod:
                embed_unban.set_image(url=imagem_mod)

            embed_unban.set_footer(text=f"ID: {usuario.id}", icon_url=ctx.author.display_avatar.url)
            embed_unban.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed_unban, delete_after=TEMPO_DELETE_SUCESSO)

        except discord.Forbidden:
            embed_forbidden = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Não tenho permissão para gerenciar banimentos no servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_forbidden, delete_after=TEMPO_DELETE_ERRO)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro ao Desbanir",
                description=f"Houve uma falha inesperada ao tentar desbanir:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @unban.error
    async def unban_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)

        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Banir Membros` para utilizar este comando.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa fornecer o ID numérico do usuário!\n\n**Exemplo:** `!unban 123456789012345678 Perdão`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ ID Inválido",
                description="O ID do usuário precisa ser composto apenas por números.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO: EXPULSAR / KICK
    # ========================================================
    @commands.command(name="kick", aliases=["expulsar"])
    async def kick(self, ctx, membro: discord.Member, *, motivo: str = "Não especificado"):
        """Expulsa um membro do servidor respeitando a hierarquia."""
        await tentar_deletar_mensagem(ctx)

        if not tem_permissao_acao(ctx, "kick"):
            embed = discord.Embed(
                title="❌ Sem Permissão",
                description="Você precisa da permissão de `Expulsar Membros` ou do cargo configurado para expulsar.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro == ctx.author:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode expulsar a si mesmo.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        if membro.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Ação Inválida",
                description="Você não pode expulsar um administrador do servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # Verificação rigorosa de hierarquia do autor
        if ctx.author != ctx.guild.owner and membro.top_role >= ctx.author.top_role:
            embed = discord.Embed(
                title="❌ Hierarquia Insuficiente",
                description="Você não pode expulsar um membro com cargo superior ou igual ao seu.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        # Verificação de hierarquia do bot
        if membro.top_role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                title="❌ Hierarquia do Bot",
                description="Este membro tem cargo igual ou superior ao cargo mais alto do bot.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)
            return

        try:
            # Imagem personalizada configurada pelo moderador para KICK
            imagem_mod = self.obter_imagem_mod(ctx.guild.id, ctx.author.id, "kick")

            # Tenta avisar o membro via mensagem privada (DM)
            try:
                embed_dm = discord.Embed(
                    title=f"👢 Você foi expulso de {ctx.guild.name}",
                    description=f"**Motivo:** {motivo}",
                    color=Cores.AVISO
                )
                if imagem_mod:
                    embed_dm.set_image(url=imagem_mod)
                await membro.send(embed=embed_dm)
            except (discord.Forbidden, discord.HTTPException):
                pass

            await membro.kick(reason=f"Expulso por {ctx.author.name}. Motivo: {motivo}")

            embed_kick = discord.Embed(
                title="👢  MEMBRO EXPULSO DO SERVIDOR",
                description=(
                    f"> O membro {membro.mention} foi expulso do servidor.\n\n"
                    "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                ),
                color=Cores.AVISO
            )
            embed_kick.set_author(name=f"Punição Aplicada • {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed_kick.add_field(name="👤  Membro Expulso", value=f"{membro.mention}\n`@{membro.name}`", inline=True)
            embed_kick.add_field(name="🛡️  Moderador", value=f"{ctx.author.mention}\n`@{ctx.author.name}`", inline=True)
            embed_kick.add_field(name="🆔  ID do Membro", value=f"`{membro.id}`", inline=True)
            embed_kick.add_field(name="📋  Motivo da Expulsão", value=f"```yaml\n{motivo}\n```", inline=False)

            avatar_membro = obter_avatar_url(membro)
            if avatar_membro:
                embed_kick.set_thumbnail(url=avatar_membro)

            if imagem_mod:
                embed_kick.set_image(url=imagem_mod)

            embed_kick.set_footer(text=f"ID: {membro.id}", icon_url=ctx.author.display_avatar.url)
            embed_kick.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed_kick, delete_after=TEMPO_DELETE_SUCESSO)

        except discord.Forbidden:
            embed_forbidden = discord.Embed(
                title="❌ Permissão Insuficiente",
                description="Não possuo privilégios suficientes na hierarquia de cargos para expulsar este usuário.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_forbidden, delete_after=TEMPO_DELETE_ERRO)
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro na Expulsão",
                description=f"Houve uma falha inesperada ao tentar expulsar:\n`{e}`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)

    @kick.error
    async def kick_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)

        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você precisa da permissão de `Expulsar Membros` para utilizar este comando.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Você precisa mencionar quem deseja expulsar!\n\n**Exemplo:** `!kick @Usuario Motivo da expulsão`",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="❌ Membro Não Encontrado",
                description="O membro informado não foi encontrado no servidor.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO: CONFIGURAR IMAGEM PERSONALIZADA (!setimg)
    # ========================================================
    @commands.command(name="setimg", aliases=["setimagem", "modimg", "setgif"])
    async def setimg(self, ctx, tipo: str = None, link: str = None):
        """
        Permite a cada moderador configurar sua própria imagem/GIF para ban, unban, mute ou unmute.
        Exemplo: !setimg ban https://link.com/hammer.gif (ou com anexo)
        """
        await tentar_deletar_mensagem(ctx)

        tipos_validos = {
            "ban": "ban",
            "banir": "ban",
            "kick": "kick",
            "expulsar": "kick",
            "unban": "unban",
            "desbanir": "unban",
            "mute": "mute",
            "silenciar": "mute",
            "unmute": "unmute",
            "desmutar": "unmute",
        }

        if not tipo or tipo.lower() not in tipos_validos:
            embed_ajuda = discord.Embed(
                title="🖼️ Configurar Imagem Pessoal de Punição",
                description=(
                    "Cada moderador pode definir suas próprias imagens ou GIFs para suas ações!\n\n"
                    "**Tipos disponíveis:**\n"
                    "• `ban` - Imagem que aparece quando você banir alguém.\n"
                    "• `kick` - Imagem que aparece quando você expulsar alguém.\n"
                    "• `unban` - Imagem que aparece quando você desbanir alguém.\n"
                    "• `mute` - Imagem que aparece quando você silenciar alguém.\n"
                    "• `unmute` - Imagem que aparece quando você desmutar alguém.\n\n"
                    "**Como usar:**\n"
                    "• Envie com anexo: `!setimg ban` *(anexando a imagem/GIF)*\n"
                    "• Envie com link: `!setimg ban https://link.com/gif.gif`\n"
                    "• Para remover: `!setimg ban remover`"
                ),
                color=Cores.INFO
            )
            await ctx.send(embed=embed_ajuda, delete_after=25)
            return

        tipo_acao = tipos_validos[tipo.lower()]

        # Validação de permissões para cada tipo de ação
        if tipo_acao in ["ban", "unban"]:
            if not ctx.author.guild_permissions.ban_members and not ctx.author.guild_permissions.administrator and not tem_permissao_acao(ctx, "ban"):
                embed_perm = discord.Embed(
                    title="❌ Sem Permissão",
                    description=f"Você precisa ter permissão de `Banir Membros` para configurar a imagem de `{tipo_acao}`.",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_perm, delete_after=TEMPO_DELETE_ERRO)
                return

        if tipo_acao == "kick":
            if not ctx.author.guild_permissions.kick_members and not ctx.author.guild_permissions.administrator and not tem_permissao_acao(ctx, "kick"):
                embed_perm = discord.Embed(
                    title="❌ Sem Permissão",
                    description="Você precisa ter permissão de `Expulsar Membros` para configurar a imagem de `kick`.",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_perm, delete_after=TEMPO_DELETE_ERRO)
                return

        if tipo_acao in ["mute", "unmute"]:
            if not tem_permissao_mute(ctx):
                embed_perm = discord.Embed(
                    title="❌ Sem Permissão",
                    description=f"Você precisa ter permissão para silenciar membros para configurar a imagem de `{tipo_acao}`.",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_perm, delete_after=TEMPO_DELETE_ERRO)
                return

        # Opção de remoção/reset
        if link and link.lower() in ["remover", "reset", "deletar", "limpar", "padrao"]:
            self.definir_imagem_mod(ctx.guild.id, ctx.author.id, tipo_acao, None)
            embed_removido = discord.Embed(
                title="🗑️ Imagem Removida",
                description=f"Sua imagem personalizada para **{tipo_acao.upper()}** foi removida. Voltando ao padrão.",
                color=Cores.SUCESSO
            )
            await ctx.send(embed=embed_removido, delete_after=TEMPO_DELETE_SUCESSO)
            return

        # Captura a URL do anexo ou do link
        url_imagem = None
        if ctx.message.attachments:
            url_imagem = ctx.message.attachments[0].url
        elif link:
            url_limpa = link.strip("<> ")
            if url_limpa.startswith("http://") or url_limpa.startswith("https://"):
                url_imagem = url_limpa
            else:
                embed_erro = discord.Embed(
                    title="❌ Link Inválido",
                    description="O link fornecido precisa começar com `http://` ou `https://`.",
                    color=Cores.ERRO
                )
                await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
                return
        else:
            embed_erro = discord.Embed(
                title="❌ Imagem Não Informada",
                description="Você precisa anexar uma imagem/GIF ou colar o link direto junto ao comando!",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        # Salva a imagem para o moderador específico
        self.definir_imagem_mod(ctx.guild.id, ctx.author.id, tipo_acao, url_imagem)

        embed_sucesso = discord.Embed(
            title="🖼️ Imagem Pessoal Configurada!",
            description=(
                f"Sua imagem personalizada para a ação **{tipo_acao.upper()}** foi salva com sucesso!\n"
                f"Sempre que **você** executar o comando `!{tipo_acao}`, esta imagem aparecerá no embed."
            ),
            color=Cores.SUCESSO
        )
        embed_sucesso.set_image(url=url_imagem)
        embed_sucesso.set_footer(text=f"Moderador: {ctx.author.name} | Para remover: !setimg {tipo_acao} remover")
        await ctx.send(embed=embed_sucesso, delete_after=TEMPO_DELETE_SUCESSO)

    @setimg.error
    async def setimg_error(self, ctx, error):
        await tentar_deletar_mensagem(ctx)
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permissão Negada",
                description="Você não possui permissões suficientes para configurar imagens de moderação.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed, delete_after=TEMPO_DELETE_ERRO)

    # ========================================================
    # COMANDO: VER MINHAS IMAGENS CONFIGURADAS (!minhasimagens)
    # ========================================================
    @commands.command(name="minhasimagens", aliases=["minhasimgs", "modimgs"])
    async def minhasimagens(self, ctx):
        """Exibe as imagens personalizadas configuradas pelo moderador que chamou o comando."""
        await tentar_deletar_mensagem(ctx)

        imagens = (
            self.imagens_mods.get(str(ctx.guild.id), {})
            .get(str(ctx.author.id), {})
        )

        embed = discord.Embed(
            title=f"🖼️ Imagens de Moderação de {ctx.author.name}",
            description="Aqui estão as imagens/GIFs que aparecerão nas punições executadas por você:",
            color=Cores.MODERACAO
        )

        for acao, emoji in [("ban", "🔨"), ("kick", "👢"), ("unban", "🕊️"), ("mute", "🔇"), ("unmute", "🔊")]:
            url = imagens.get(acao)
            valor = f"[Ver Imagem/GIF]({url})" if url else "*Nenhuma (Padrão)*"
            embed.add_field(name=f"{emoji} {acao.upper()}", value=valor, inline=True)

        embed.set_footer(text="Use !setimg <tipo> <link ou anexo> para personalizar qualquer uma delas.")
        await ctx.send(embed=embed, delete_after=30)


async def setup(bot):
    await bot.add_cog(Moderacao(bot))
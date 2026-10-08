import datetime
import json
from pathlib import Path
import discord
from discord.ext import commands
from config import Cores, PREFIXO, TEMPO_DELETE_ERRO
from utils.helpers import tentar_deletar_mensagem

ARQUIVO_MAPA_BADGES = Path(__file__).resolve().parent.parent / "data" / "badges_map.json"


def carregar_mapa_badges() -> dict:
    """Carrega os emojis oficiais das badges do Discord salvos no JSON."""
    if not ARQUIVO_MAPA_BADGES.exists():
        return {}
    try:
        with open(ARQUIVO_MAPA_BADGES, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# Mapeamento de Flags da API do Discord para as chaves de emojis
MAPA_FLAG_PARA_CHAVE = {
    "hypesquad_bravery": "badge_bravery",
    "hypesquad_brilliance": "badge_brilliance",
    "hypesquad_balance": "badge_balance",
    "hypesquad": "badge_hypesquad_events",
    "active_developer": "badge_activedev",
    "early_supporter": "badge_earlysupporter",
    "verified_bot_developer": "badge_botdev",
    "discord_certified_moderator": "badge_mod",
    "bug_hunter_level_1": "badge_bughunter_1",
    "bug_hunter_level_2": "badge_bughunter_2",
    "partner": "badge_partner",
    "staff": "badge_staff",
}

NOMES_BADGES = {
    "badge_bravery": "HypeSquad Bravery",
    "badge_brilliance": "HypeSquad Brilliance",
    "badge_balance": "HypeSquad Balance",
    "badge_hypesquad_events": "HypeSquad Events",
    "badge_activedev": "Desenvolvedor Ativo",
    "badge_earlysupporter": "Apoiador Inicial (Early Supporter)",
    "badge_botdev": "Desenvolvedor de Bot Verificado",
    "badge_mod": "Moderador Certificado Alumni",
    "badge_bughunter_1": "Bug Hunter Bronze",
    "badge_bughunter_2": "Bug Hunter Gold",
    "badge_partner": "Dono de Servidor Parceiro",
    "badge_staff": "Discord Staff",
    "badge_nitro": "Discord Nitro",
    "badge_legacy_username": "Nome de Usuário Original (Legado)",
    "badge_quest": "Completou uma Missão do Discord",
}

# Tabela oficial de evolução dos distintivos de Server Booster do Discord
MARCOS_BOOSTER = [
    (30, "1 Mês (Nível 1)", "badge_boost_1"),
    (60, "2 Meses (Nível 2)", "badge_boost_2"),
    (90, "3 Meses (Nível 3)", "badge_boost_3"),
    (180, "6 Meses (Nível 4)", "badge_boost_6"),
    (270, "9 Meses (Nível 5)", "badge_boost_9"),
    (365, "12 Meses / 1 Ano (Nível 6)", "badge_boost_12"),
    (455, "15 Meses (Nível 7)", "badge_boost_15"),
    (545, "18 Meses (Nível 8)", "badge_boost_18"),
    (730, "24 Meses / 2 Anos (Nível 9)", "badge_boost_24"),
]


def gerar_barra_progresso(porcentagem: float, tamanho: int = 10) -> str:
    """Gera uma barra de progresso visual em texto."""
    clamped = max(0.0, min(100.0, porcentagem))
    preenchidos = int((clamped / 100.0) * tamanho)
    vazios = tamanho - preenchidos
    return f"`[{'█' * preenchidos}{'░' * vazios}]` **{clamped:.1f}%**"


class ViewLinksPerfil(discord.ui.View):
    """Botões de atalho para abrir Avatar e Banner no navegador."""

    def __init__(self, avatar_url: str, banner_url: str | None = None):
        super().__init__(timeout=120)
        self.add_item(discord.ui.Button(label="Ver Avatar HD", url=avatar_url, emoji="🖼️"))
        if banner_url:
            self.add_item(discord.ui.Button(label="Ver Banner HD", url=banner_url, emoji="🎨"))


class Info(commands.Cog):
    """Módulo de informações avançadas de usuários e do servidor."""

    def __init__(self, bot):
        self.bot = bot
        self.mapa_badges = carregar_mapa_badges()

    async def resolver_usuario(self, ctx, entrada: str | None):
        """
        Localiza e retorna (objeto_usuario, esta_no_servidor).
        Aceita: ID puro, Menção (<@ID>), Username/Tag ou None (autor).
        """
        if not entrada:
            return ctx.author, True

        texto = entrada.strip()
        limpo = texto.replace("<@", "").replace(">", "").replace("!", "")

        # 1. Se for numérico (ID de usuário)
        if limpo.isdigit():
            user_id = int(limpo)
            # Tenta pegar no cache do servidor
            membro = ctx.guild.get_member(user_id)
            if membro:
                return membro, True
            # Tenta buscar no servidor pela API
            try:
                membro = await ctx.guild.fetch_member(user_id)
                if membro:
                    return membro, True
            except Exception:
                pass
            # Busca como usuário global no Discord
            try:
                usuario_global = await self.bot.fetch_user(user_id)
                if usuario_global:
                    return usuario_global, False
            except Exception:
                pass

        # 2. Tenta converter por menção ou nome no servidor
        try:
            membro = await commands.MemberConverter().convert(ctx, texto)
            return membro, True
        except Exception:
            pass

        # 3. Tenta converter como User global
        try:
            usuario = await commands.UserConverter().convert(ctx, texto)
            membro = ctx.guild.get_member(usuario.id)
            if membro:
                return membro, True
            return usuario, False
        except Exception:
            pass

        return None, False

    # ========================================================
    # COMANDO: USERINFO / PERFIL
    # ========================================================
    @commands.command(name="userinfo", aliases=["perfil", "ui", "user", "memberinfo", "infousuario"])
    async def userinfo(self, ctx, *, usuario: str = None):
        """Exibe o perfil completo com badges oficiais, tempo de booster e evolução (por ID, menção ou nome)."""
        await tentar_deletar_mensagem(ctx)

        alvo, no_servidor = await self.resolver_usuario(ctx, usuario)

        if not alvo:
            embed_erro = discord.Embed(
                title="❌ Usuário Não Encontrado",
                description=f"Não foi possível encontrar nenhum usuário com a identificação: `{usuario}`.\n\n"
                            "Verifique se o **ID**, **menção** ou **nome** foi digitado corretamente.",
                color=Cores.ERRO
            )
            await ctx.send(embed=embed_erro, delete_after=TEMPO_DELETE_ERRO)
            return

        # Atualiza o mapa de badges caso tenha sido gerado recentemente
        if not self.mapa_badges:
            self.mapa_badges = carregar_mapa_badges()

        # Busca dados completos da API para obter banner, accent_color e flags atualizadas
        try:
            fetched_user = await self.bot.fetch_user(alvo.id)
        except Exception:
            fetched_user = alvo

        # 1. Identificação de Booster & Nível do Distintivo
        agora = discord.utils.utcnow()
        emoji_booster_inline = None
        booster_info_texto = ""
        nivel_atual_nome = "Iniciante (< 30 dias)"
        emoji_boost_atual = self.mapa_badges.get("badge_boost_1", "🚀")

        premium_since = getattr(alvo, "premium_since", None)

        if premium_since:
            tempo_booster = agora - premium_since
            total_dias = tempo_booster.days
            horas_restantes = tempo_booster.seconds // 3600

            marco_atual_dias = 0
            proximo_marco_dias = MARCOS_BOOSTER[0][0]
            proximo_marco_nome = MARCOS_BOOSTER[0][1]
            emoji_boost_prox = self.mapa_badges.get(MARCOS_BOOSTER[0][2], "🚀")

            for dias_req, nome_m, chave_emoji in MARCOS_BOOSTER:
                if total_dias >= dias_req:
                    nivel_atual_nome = nome_m
                    emoji_boost_atual = self.mapa_badges.get(chave_emoji, "🚀")
                    marco_atual_dias = dias_req
                else:
                    proximo_marco_dias = dias_req
                    proximo_marco_nome = nome_m
                    emoji_boost_prox = self.mapa_badges.get(chave_emoji, "🚀")
                    break

            emoji_booster_inline = emoji_boost_atual

            # Se já atingiu o nível máximo (2+ Anos)
            if total_dias >= MARCOS_BOOSTER[-1][0]:
                proximo_txt = f"🏆 **Nível Máximo de Booster Atingido (2+ Anos)!**"
                barra = "`[██████████]` **100%**"
            else:
                dias_restantes = proximo_marco_dias - total_dias
                data_up = premium_since + datetime.timedelta(days=proximo_marco_dias)
                dias_no_estagio = total_dias - marco_atual_dias
                intervalo_estagio = proximo_marco_dias - marco_atual_dias
                pct = (dias_no_estagio / intervalo_estagio) * 100.0 if intervalo_estagio > 0 else 0
                barra = gerar_barra_progresso(pct)
                proximo_txt = (
                    f"• **Próximo Nível:** {emoji_boost_prox} **{proximo_marco_nome}**\n"
                    f"• **Faltam para Upar:** `{dias_restantes} dia(s)` (<t:{int(data_up.timestamp())}:R>)\n"
                    f"• **Evolução:** {barra}"
                )

            booster_info_texto = (
                f"• **Impulsionando desde:** <t:{int(premium_since.timestamp())}:F> (<t:{int(premium_since.timestamp())}:R>)\n"
                f"• **Tempo Total:** `{total_dias} dias e {horas_restantes} horas`\n"
                f"• **Distintivo Atual:** {emoji_boost_atual} **{nivel_atual_nome}**\n"
                f"{proximo_txt}"
            )
        else:
            if no_servidor:
                booster_info_texto = (
                    "❌ *Este membro não está impulsionando o servidor no momento.*\n"
                    "💡 *Ao impulsionar, ganha distintivo exclusivo com evolução contínua!*"
                )
            else:
                booster_info_texto = "❌ *Este usuário não faz parte deste servidor.*"

        # 2. Detecção de Discord Nitro
        possui_nitro = False
        if fetched_user.display_avatar.is_animated():
            possui_nitro = True
        elif getattr(fetched_user, "banner", None):
            possui_nitro = True
        elif getattr(fetched_user, "avatar_decoration", None):
            possui_nitro = True
        elif premium_since:
            possui_nitro = True

        # 3. Coleta de Todas as Badges para o Perfil (Inline e Detalhadas)
        badges_inline = []
        badges_detalhadas = []

        # Badge do Booster (se impulsiona)
        if emoji_booster_inline:
            badges_inline.append(emoji_booster_inline)
            badges_detalhadas.append(f"{emoji_booster_inline} **Server Booster ({nivel_atual_nome})**")

        # Badge do Nitro
        if possui_nitro:
            emoji_nitro = self.mapa_badges.get("badge_nitro", "🔮")
            badges_inline.append(emoji_nitro)
            badges_detalhadas.append(f"{emoji_nitro} **Discord Nitro**")

        # Badge de Nome de Usuário Legado
        if alvo.discriminator == "0" and alvo.created_at < datetime.datetime(2023, 6, 15, tzinfo=datetime.timezone.utc):
            emoji_legacy = self.mapa_badges.get("badge_legacy_username", "🏷️")
            badges_inline.append(emoji_legacy)
            badges_detalhadas.append(f"{emoji_legacy} **Nome de Usuário Original (Legado)**")

        # Badges Públicas do Discord
        flags = fetched_user.public_flags.all()
        for flag in flags:
            chave = MAPA_FLAG_PARA_CHAVE.get(flag.name)
            if chave:
                emoji_badge = self.mapa_badges.get(chave, "🎖️")
                nome_badge = NOMES_BADGES.get(chave, flag.name)
                badges_inline.append(emoji_badge)
                badges_detalhadas.append(f"{emoji_badge} **{nome_badge}**")

        # Badges especiais de Servidor
        if no_servidor and alvo.id == ctx.guild.owner_id:
            badges_inline.append("👑")
            badges_detalhadas.append("👑 **Dono do Servidor**")
        if alvo.bot:
            badges_inline.append("🤖")
            badges_detalhadas.append("🤖 **Bot Oficial**")

        if no_servidor:
            cog_vip = self.bot.get_cog("VIP")
            if cog_vip:
                nivel_vip = cog_vip.obter_nivel_vip(alvo)
                if nivel_vip:
                    badges_inline.append("💎")
                    badges_detalhadas.append(f"💎 **VIP {nivel_vip.capitalize()}**")

        # String inline com as badges juntas (exatamente como no perfil do Discord!)
        badges_inline_str = " ".join(badges_inline) if badges_inline else ""

        # 4. Status de Presença e Plataforma
        if no_servidor and hasattr(alvo, "status"):
            mapa_status = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🟡 Ausente",
                discord.Status.dnd: "🔴 Não Perturbe",
                discord.Status.offline: "⚪ Offline / Invisível",
            }
            status_txt = mapa_status.get(alvo.status, "⚪ Offline")

            dispositivos = []
            if getattr(alvo, "desktop_status", None) and alvo.desktop_status != discord.Status.offline:
                dispositivos.append("💻 PC")
            if getattr(alvo, "mobile_status", None) and alvo.mobile_status != discord.Status.offline:
                dispositivos.append("📱 Celular")
            if getattr(alvo, "web_status", None) and alvo.web_status != discord.Status.offline:
                dispositivos.append("🌐 Web")
            disp_txt = " • ".join(dispositivos) if dispositivos else "Desconhecido"

            atividades_txt = []
            for ativ in getattr(alvo, "activities", []):
                if isinstance(ativ, discord.Spotify):
                    atividades_txt.append(f"🎧 **Spotify:** {ativ.title} — *{ativ.artist}*")
                elif isinstance(ativ, discord.Game):
                    atividades_txt.append(f"🎮 **Jogando:** {ativ.name}")
                elif isinstance(ativ, discord.Streaming):
                    atividades_txt.append(f"📺 **Transmitindo:** [{ativ.name}]({ativ.url})")
                elif isinstance(ativ, discord.CustomActivity):
                    emoji_c = f"{ativ.emoji} " if ativ.emoji else ""
                    nome_c = ativ.name or ""
                    if emoji_c or nome_c:
                        atividades_txt.append(f"💭 **Status:** {emoji_c}{nome_c}")
                elif ativ.name:
                    atividades_txt.append(f"🕹️ **Atividade:** {ativ.name}")

            atividades_final = "\n".join(atividades_txt) if atividades_txt else "*Nenhuma atividade em andamento*"
            top_role_txt = alvo.top_role.mention if hasattr(alvo, "top_role") else "Nenhum"
        else:
            status_txt = "⚪ Usuário Fora do Servidor"
            disp_txt = "N/A"
            atividades_final = "*Indisponível (Usuário não está neste servidor)*"
            top_role_txt = "*Nenhum*"

        # 5. Datas e Posição de Entrada
        criado_em = int(alvo.created_at.timestamp())

        if no_servidor and getattr(alvo, "joined_at", None):
            entrou_em = int(alvo.joined_at.timestamp())
            membros_ordenados = sorted(
                [m for m in ctx.guild.members if m.joined_at],
                key=lambda m: m.joined_at
            )
            posicao_entrada = f"#{membros_ordenados.index(alvo) + 1}" if alvo in membros_ordenados else "?"
            entrada_txt = f"<t:{entrou_em}:R>"
        else:
            entrada_txt = "*Não está no servidor*"
            posicao_entrada = "N/A"

        # 6. Cargos
        if no_servidor and hasattr(alvo, "roles"):
            cargos = [c.mention for c in reversed(alvo.roles) if c != ctx.guild.default_role]
            total_cargos = len(cargos)
            cargos_exibicao = ", ".join(cargos[:15]) if cargos else "*Nenhum cargo*"
            if len(cargos) > 15:
                cargos_exibicao += f" *... e mais {len(cargos) - 15} cargos*"
        else:
            total_cargos = 0
            cargos_exibicao = "*Usuário não faz parte deste servidor*"

        # Cor do Embed
        cor_embed = getattr(alvo, "color", discord.Color.default())
        if cor_embed.value == 0:
            cor_embed = fetched_user.accent_color or Cores.INFO

        # Montagem da Descrição Estilo Perfil Oficial
        apelido_txt = f"\n> 🏷️ **Apelido no Servidor:** `{alvo.nick}`" if getattr(alvo, "nick", None) else ""
        servidor_tag = "" if no_servidor else "\n> 🌐 **Status:** Membro Global *(não está no servidor)*"

        descricao_topo = (
            f"### {alvo.display_name} {badges_inline_str}\n"
            f"> 👤 **Usuário:** `{alvo.name}`\n"
            f"> 🆔 **ID:** `{alvo.id}`{apelido_txt}{servidor_tag}\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
        )

        embed = discord.Embed(
            description=descricao_topo,
            color=cor_embed
        )
        embed.set_author(name=f"Perfil do Discord • {alvo.display_name}", icon_url=alvo.display_avatar.url)
        embed.set_thumbnail(url=alvo.display_avatar.url)

        # Banner (se tiver)
        banner_url = fetched_user.banner.url if getattr(fetched_user, "banner", None) else None
        if banner_url:
            embed.set_image(url=banner_url)

        # Campos
        embed.add_field(
            name=f"🎖️  Distintivos ({len(badges_detalhadas)})",
            value="\n".join(badges_detalhadas) if badges_detalhadas else "*Nenhum distintivo público detectado*",
            inline=False
        )

        embed.add_field(
            name="🚀  Evolução de Server Booster & Nitro",
            value=booster_info_texto,
            inline=False
        )

        embed.add_field(
            name="📡  Status & Presença",
            value=(
                f"• **Status:** {status_txt}\n"
                f"• **Dispositivos:** {disp_txt}\n"
                f"• **Cargo Principal:** {top_role_txt}"
            ),
            inline=True
        )

        embed.add_field(
            name="📅  Datas & Servidor",
            value=(
                f"• **Conta Criada:** <t:{criado_em}:R>\n"
                f"• **Entrada:** {entrada_txt}\n"
                f"• **Ordem de Entrada:** {posicao_entrada}"
            ),
            inline=True
        )

        embed.add_field(
            name="🎮  Atividades Atuais",
            value=atividades_final,
            inline=False
        )

        embed.add_field(
            name=f"🏷️  Cargos no Servidor ({total_cargos})",
            value=cargos_exibicao,
            inline=False
        )

        embed.set_footer(
            text=f"{ctx.guild.name} • Solicitado por {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()

        view = ViewLinksPerfil(alvo.display_avatar.url, banner_url)
        await ctx.send(embed=embed, view=view)

    # ========================================================
    # COMANDO: SERVERINFO
    # ========================================================
    @commands.command(name="serverinfo", aliases=["si", "server", "guildinfo", "infoservidor"])
    async def serverinfo(self, ctx):
        """Exibe todas as informações e estatísticas do servidor atual."""
        await tentar_deletar_mensagem(ctx)

        guild = ctx.guild
        criado_em = int(guild.created_at.timestamp())

        # Contagem de membros
        total_membros = guild.member_count
        humanos = sum(1 for m in guild.members if not m.bot)
        bots = sum(1 for m in guild.members if m.bot)

        # Canais
        texto = len(guild.text_channels)
        voz = len(guild.voice_channels)
        categorias = len(guild.categories)
        total_canais = len(guild.channels)

        # Cargos e Emojis
        total_cargos = len(guild.roles) - 1
        total_emojis = len(guild.emojis)
        animados = sum(1 for e in guild.emojis if e.animated)
        estaticos = total_emojis - animados

        # Boosts
        nivel_boost = guild.premium_tier
        qtd_boosts = guild.premium_subscription_count or 0
        total_boosters = len(guild.premium_subscribers)

        embed = discord.Embed(
            title=f"🏰  {guild.name.upper()}",
            description=(
                f"> Visão geral e estatísticas em tempo real de **{guild.name}**.\n\n"
                "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
            ),
            color=Cores.PADRAO
        )
        embed.set_author(name=f"Estatísticas do Servidor • {guild.name}", icon_url=guild.icon.url if guild.icon else None)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.add_field(
            name="👑  Posse & Fundação",
            value=(
                f"• **Dono:** {guild.owner.mention} (`@{guild.owner.name}`)\n"
                f"• **ID do Dono:** `{guild.owner_id}`\n"
                f"• **ID do Servidor:** `{guild.id}`\n"
                f"• **Fundado em:** <t:{criado_em}:F>\n"
                f"• **Idade:** <t:{criado_em}:R>"
            ),
            inline=True
        )

        embed.add_field(
            name="👥  Membros & População",
            value=(
                f"• **Total:** `{total_membros}` membros\n"
                f"• **👤 Usuários:** `{humanos}`\n"
                f"• **🤖 Bots:** `{bots}`"
            ),
            inline=True
        )

        embed.add_field(
            name="🚀  Impulsos (Server Boost)",
            value=(
                f"• **Nível Atual:** Nível {nivel_boost}\n"
                f"• **Total de Impulsos:** `{qtd_boosts}` boosts\n"
                f"• **Membros Boosters:** `{total_boosters}` boosters"
            ),
            inline=True
        )

        embed.add_field(
            name="📁  Canais do Servidor",
            value=(
                f"• **💬 Texto:** `{texto}`\n"
                f"• **🔊 Voz:** `{voz}`\n"
                f"• **📂 Categorias:** `{categorias}`\n"
                f"• **Total Geral:** `{total_canais}` canais"
            ),
            inline=True
        )

        embed.add_field(
            name="🎨  Customizações",
            value=(
                f"• **🏷️ Cargos:** `{total_cargos}`\n"
                f"• **😀 Emojis:** `{total_emojis}` (`{estaticos}` normais | `{animados}` GIFs)\n"
                f"• **🎭 Figurinhas:** `{len(guild.stickers)}`"
            ),
            inline=True
        )

        embed.add_field(
            name="🛡️  Segurança & Níveis",
            value=(
                f"• **Verificação:** `{str(guild.verification_level).capitalize()}`\n"
                f"• **Filtro Explícito:** `{str(guild.explicit_content_filter).capitalize()}`\n"
                f"• **2FA para Moderação:** `{'Ativado' if guild.mfa_level else 'Desativado'}`"
            ),
            inline=True
        )

        embed.set_footer(
            text=f"{guild.name} • Solicitado por {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)

    # ========================================================
    # COMANDO: AVATAR
    # ========================================================
    @commands.command(name="avatar", aliases=["pfp", "foto", "icone"])
    async def avatar(self, ctx, *, usuario: str = None):
        """Exibe o avatar do usuário em alta definição com link para download (por ID, menção ou nome)."""
        await tentar_deletar_mensagem(ctx)

        alvo, _ = await self.resolver_usuario(ctx, usuario)
        if not alvo:
            await ctx.send(f"❌ Usuário `{usuario}` não encontrado.", delete_after=TEMPO_DELETE_ERRO)
            return

        url = alvo.display_avatar.with_size(1024).url
        cor = getattr(alvo, "color", discord.Color.default())

        embed = discord.Embed(
            title=f"🖼️  Avatar de {alvo.display_name}",
            description="> Clique no botão abaixo para baixar ou visualizar em tamanho original (1024px).",
            color=cor if cor.value != 0 else Cores.PADRAO
        )
        embed.set_author(name=f"Foto de Perfil • {alvo.name}", icon_url=alvo.display_avatar.url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {alvo.id} • Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        view = ViewLinksPerfil(url)
        await ctx.send(embed=embed, view=view)

    # ========================================================
    # COMANDO: USERBANNER
    # ========================================================
    @commands.command(name="userbanner", aliases=["banneruser", "perfilbanner", "ubanner"])
    async def userbanner(self, ctx, *, usuario: str = None):
        """Exibe o banner do perfil do usuário em alta definição (por ID, menção ou nome)."""
        await tentar_deletar_mensagem(ctx)

        alvo, _ = await self.resolver_usuario(ctx, usuario)
        if not alvo:
            await ctx.send(f"❌ Usuário `{usuario}` não encontrado.", delete_after=TEMPO_DELETE_ERRO)
            return

        fetched = await self.bot.fetch_user(alvo.id)

        if not fetched.banner:
            embed_aviso = discord.Embed(
                title="⚠️ Sem Banner Customizado",
                description=f"> {alvo.mention} não possui um banner personalizado configurado no perfil.",
                color=Cores.AVISO
            )
            embed_aviso.set_footer(text=f"{ctx.guild.name}")
            embed_aviso.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed_aviso, delete_after=TEMPO_DELETE_ERRO)
            return

        url = fetched.banner.with_size(1024).url
        cor = getattr(alvo, "color", discord.Color.default())

        embed = discord.Embed(
            title=f"🎨  Banner de {alvo.display_name}",
            description="> Clique no botão abaixo para baixar ou visualizar o banner em alta definição.",
            color=cor if cor.value != 0 else Cores.PADRAO
        )
        embed.set_author(name=f"Banner de Perfil • {alvo.name}", icon_url=alvo.display_avatar.url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {alvo.id} • Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        view = ViewLinksPerfil(alvo.display_avatar.url, url)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Info(bot))

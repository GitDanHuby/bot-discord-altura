# =================================================================================
# ARQUIVO main.py COMPLETO - COM SISTEMA DE NÍVEIS
# =================================================================================

# --- Seção de Imports ---
import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from samp_client.client import SampClient
from web_server import start_web_server
from database_setup import setup_database, SessionLocal, User, Setting # Importa User
import random
import time

# --- Configuração Inicial ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.message_content = True # Habilita a intent que ativamos no portal

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Dicionário para controlar o cooldown de XP
xp_cooldowns = {}

# =================================================================================
# --- SEÇÃO DE COMANDOS DE BARRA (/) ---
# =================================================================================

# ... (Todos os seus comandos antigos: /ping, /ip, /regras, etc. continuam aqui, sem alterações) ...
@tree.command(name="ping", description="Testa se o bot está respondendo.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")

@tree.command(name="ip", description="Mostra o endereço de IP para se conectar ao servidor SAMP.")
async def ip(interaction: discord.Interaction):
    embed_ip = discord.Embed(title="🚀 Conecte-se ao Altura RolePlay City!", description="Use o IP abaixo para entrar na melhor cidade do SAMP!", color=discord.Color.blue())
    embed_ip.add_field(name="Endereço do Servidor:", value="`179.127.16.157:29015`", inline=False)
    embed_ip.set_footer(text="Clique no IP para copiar. Te vemos lá!")
    await interaction.response.send_message(embed=embed_ip)

@tree.command(name="regras", description="Mostra as regras principais do servidor.")
async def regras(interaction: discord.Interaction):
    regras_texto = """
    **1. Siga as diretrizes do Discord:** Termos | Regras.
    **2. Nicks e perfis devem ser legíveis e adequados.** Nada de "Staff", fontes estranhas ou conteúdo adulto.
    **3. Não use imagens de outros sem permissão.**
    **4. Contas fakes ou secundárias são proibidas.**
    **5. Respeite todos os membros, dentro e fora do servidor.**
    **6. Sem trolls em call:** nada de voz modificada, música ou micro estourando.
    **7. Sem trolls no chat:** ghost-ping, flood, gore, spam, etc.
    **8. Não abuse dos canais de suporte.**
    **9. Proibido divulgar outros servidores (SA-MP ou Discord).**
    **10. Links ou arquivos maliciosos serão punidos severamente.**
    **11. Nada de conteúdo que prejudique o servidor (ex: hackers, DM, etc).**
    **12. Raids = punição severa.**
    **13. Evite tentar burlar punições — isso agrava a situação.**
    **14. Sem divulgação de organizações ou comércio externo.**
    **15. Recrutamento só nos canais apropriados.**
    **16. Proibido transmitir outros servidores SA-MP em call.**
    **17. Você é responsável pela vinculação correta da sua conta.**
    
    > Ao permanecer no servidor, você aceita todas as regras.
    *📅 Atualizado em: 16/06/2025*
    """
    embed_regras = discord.Embed(title="📜 Regras do Discord - Altura RP City", description=regras_texto, color=discord.Color.orange())
    await interaction.response.send_message(embed=embed_regras)

@tree.command(name="redes_sociais", description="Mostra as redes sociais oficiais do servidor.")
async def redes_sociais(interaction: discord.Interaction):
    embed_redes = discord.Embed(title="📱 Nossas Redes Sociais", description="Siga-nos para ficar por dentro de tudo!", color=discord.Color.purple())
    embed_redes.add_field(name="YouTube", value="[Clique aqui para acessar](https://youtube.com/@snow_pr25)", inline=False)
    embed_redes.add_field(name="TikTok", value="[Clique aqui para acessar](https://www.tiktok.com/@snow_pr37?_t=8xl9kFMFyDQ&_r=1)", inline=False)
    embed_redes.add_field(name="Instagram", value="[Clique aqui para acessar](https://www.instagram.com/snow_pr25?igsh=MTNsNnA2d2xlMG9jdA==)", inline=False)
    await interaction.response.send_message(embed=embed_redes)

@tree.command(name="status", description="Verifica o status do servidor SAMP.")
async def status(interaction: discord.Interaction):
    IP_DO_SERVIDOR = "179.127.16.157"
    PORTA_DO_SERVIDOR = 29015
    try:
        with SampClient(address=IP_DO_SERVIDOR, port=PORTA_DO_SERVIDOR) as samp_client:
            info = samp_client.get_server_info()
            embed_status = discord.Embed(title=f"✅ Status do Servidor: ONLINE", color=discord.Color.green())
            embed_status.add_field(name="Nome do Servidor", value=info.hostname, inline=False)
            embed_status.add_field(name="Jogadores", value=f"{info.players}/{info.max_players}", inline=True)
            embed_status.add_field(name="Ping", value=f"{samp_client.ping()}ms", inline=True)
    except Exception as e:
        print(f"Erro ao checar status do servidor: {e}")
        embed_status = discord.Embed(title=f"❌ Status do Servidor: OFFLINE", description="Não foi possível conectar ao servidor. Tente novamente mais tarde.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed_status)

@tree.command(name="sugestao", description="Envie uma sugestão para a equipe.")
async def sugestao(interaction: discord.Interaction, texto_da_sugestao: str):
    ID_DO_CANAL_SUGESTOES = 1386752647767265541
    canal_sugestoes = client.get_channel(ID_DO_CANAL_SUGESTOES)
    if not canal_sugestoes:
        await interaction.response.send_message("Erro: Canal de sugestões não configurado.", ephemeral=True)
        return
    embed_sugestao = discord.Embed(title="💡 Nova Sugestão", description=texto_da_sugestao, color=discord.Color.yellow())
    embed_sugestao.set_author(name=f"Sugestão de: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    mensagem_enviada = await canal_sugestoes.send(embed=embed_sugestao)
    await mensagem_enviada.add_reaction("👍")
    await mensagem_enviada.add_reaction("👎")
    await interaction.response.send_message("✅ Sua sugestão foi enviada com sucesso para o canal de sugestões!", ephemeral=True)

# NOVO COMANDO /rank
@tree.command(name="rank", description="Mostra seu nível e XP no servidor.")
async def rank(interaction: discord.Interaction, membro: discord.Member = None):
    # Se o usuário não especificar um membro, ele mostra o próprio rank
    target_user = membro or interaction.user
    
    db = SessionLocal()
    try:
        user_data = db.query(User).filter(User.id == target_user.id).first()
        if not user_data:
            await interaction.response.send_message(f"{target_user.name} ainda não tem XP. Comece a conversar!", ephemeral=True)
            return

        level = user_data.level
        xp = user_data.xp
        xp_para_proximo_level = (5 * (level ** 2)) + (50 * level) + 100
        
        embed_rank = discord.Embed(title=f"🏆 Rank de {target_user.name}", color=target_user.color)
        embed_rank.set_thumbnail(url=target_user.display_avatar.url)
        embed_rank.add_field(name="Nível", value=f"**{level}**", inline=True)
        embed_rank.add_field(name="XP", value=f"**{xp} / {xp_para_proximo_level}**", inline=True)
        
        # Barra de progresso simples
        progresso = int((xp / xp_para_proximo_level) * 20)
        barra = "🟩" * progresso + "⬛" * (20 - progresso)
        embed_rank.add_field(name="Progresso", value=barra, inline=False)
        
        await interaction.response.send_message(embed=embed_rank)
    finally:
        db.close()

# =================================================================================
# --- SEÇÃO DE EVENTOS DO DISCORD ---
# =================================================================================

@client.event
async def on_ready():
    await tree.sync()
    print("Comandos de barra sincronizados.")
    activity = discord.Game(name="na cidade do Altura RP City")
    await client.change_presence(status=discord.Status.online, activity=activity)
    print(f'{client.user} conectou-se ao Discord!')
    print('Bot está online e pronto para uso.')

# NOVO EVENTO on_message PARA DAR XP
@client.event
async def on_message(message):
    # Ignora mensagens de bots e mensagens privadas
    if message.author.bot or not message.guild:
        return

    user_id = message.author.id
    current_time = time.time()

    # Cooldown de 60 segundos para ganhar XP
    if user_id in xp_cooldowns and current_time - xp_cooldowns[user_id] < 60:
        return
    
    xp_cooldowns[user_id] = current_time
    xp_ganho = random.randint(15, 25)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        # Se o usuário não existe no banco de dados, cria um novo registro
        if not user:
            user = User(id=user_id, xp=0, level=1)
            db.add(user)
        
        user.xp += xp_ganho
        
        # Verifica se o usuário subiu de nível
        xp_necessario = (5 * (user.level ** 2)) + (50 * user.level) + 100
        if user.xp >= xp_necessario:
            user.level += 1
            user.xp -= xp_necessario # Opcional: reseta o XP para o novo nível
            
            # Envia a mensagem de level up
            level_up_embed = discord.Embed(
                title="🎉 LEVEL UP! 🎉",
                description=f"Parabéns, {message.author.mention}! Você alcançou o **Nível {user.level}**!",
                color=discord.Color.magenta()
            )
            await message.channel.send(embed=level_up_embed)
            
        db.commit()
    finally:
        db.close()

# ... (on_member_join e on_member_update continuam aqui, iguais) ...
@client.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name='👏│ᴡᴇʟᴄᴏᴍᴇ')

    if welcome_channel:
        guild = member.guild
        member_count = guild.member_count
        
        db = SessionLocal()
        try:
            setting = db.query(Setting).filter(Setting.key == 'welcome_message').first()
            if setting and setting.value:
                welcome_text = setting.value
            else:
                welcome_text = f"Seja muito bem-vindo(a), {{member.mention}}, ao {{server_name}}! Configure a mensagem de boas-vindas no dashboard."
        finally:
            db.close()

        description_text = welcome_text.format(member=member, server=guild, member_mention=member.mention, member_name=member.name, server_name=guild.name, server_member_count=member_count)
        
        embed = discord.Embed(description=description_text, color=discord.Color.from_rgb(70, 130, 180))
        if client.user.avatar:
            embed.set_author(name=client.user.name, icon_url=client.user.avatar.url)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        footer_text = "© Todos os direitos reservados do Altura RP City"
        if client.user.avatar:
            embed.set_footer(text=footer_text, icon_url=client.user.avatar.url)
        else:
            embed.set_footer(text=footer_text)
        await welcome_channel.send(embed=embed)
    else:
        print(f"Aviso: Canal de boas-vindas não encontrado no servidor '{member.guild.name}'.")

@client.event
async def on_member_update(before, after):
    ID_DO_CARGO_GATILHO = 1387535159120629770
    ID_DO_CANAL_ANUNCIO = 1390048422815338596
    ID_DO_CARGO_PING    = 1380958005331230742

    cargo_gatilho = after.guild.get_role(ID_DO_CARGO_GATILHO)
    canal_anuncio = after.guild.get_channel(ID_DO_CANAL_ANUNCIO)

    if not cargo_gatilho or not canal_anuncio:
        return

    if cargo_gatilho not in before.roles and cargo_gatilho in after.roles:
        embed_parceria = discord.Embed(title="🤝 Nova Parceria Fechada!", description=f"Temos o prazer de anunciar uma nova parceria com o membro {after.mention}!", color=discord.Color.gold())
        if after.display_avatar:
            embed_parceria.set_thumbnail(url=after.display_avatar.url)
        embed_parceria.set_footer(text=f"Membro desde: {after.joined_at.strftime('%d/%m/%Y') if after.joined_at else 'Data indisponível'}")
        mensagem_ping = f"Atenção, <@&{ID_DO_CARGO_PING}>!"
        print(f"Anunciando nova parceria com {after.name} no canal {canal_anuncio.name}.")
        await canal_anuncio.send(content=mensagem_ping, embed=embed_parceria)

# =================================================================================
# --- INICIA O SITE E O BOT ---
# =================================================================================
if __name__ == "__main__":
    setup_database()
    start_web_server()
    client.run(TOKEN)

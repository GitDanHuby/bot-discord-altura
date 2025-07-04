# SEU ARQUIVO main.py COMPLETO E ATUALIZADO

import discord
from discord import app_commands
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuração das Intents
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True # Adicionamos para garantir acesso a informações do servidor

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- COMANDO DE BARRA /ping ---
@tree.command(name="ping", description="Testa se o bot está respondendo.")
async def ping(interaction: discord.Interaction):
    """Responde com Pong!"""
    await interaction.response.send_message("Pong! 🏓")

# --- COMANDO DE BARRA /ip ---
@tree.command(name="ip", description="Mostra o endereço de IP para se conectar ao servidor SAMP.")
async def ip(interaction: discord.Interaction):
    """Envia uma mensagem bonita com o IP do servidor."""
    embed_ip = discord.Embed(
        title="🚀 Conecte-se ao Altura RolePlay City!",
        description="Use o IP abaixo para entrar na melhor cidade do SAMP!",
        color=discord.Color.blue()
    )
    embed_ip.add_field(name="Endereço do Servidor:", value="`179.127.16.157:29015`", inline=False)
    embed_ip.set_footer(text="Clique no IP para copiar. Te vemos lá!")
    await interaction.response.send_message(embed=embed_ip)


# --- EVENTO DE BOT PRONTO ---
@client.event
async def on_ready():
    """Função chamada quando o bot se conecta com sucesso."""
    await tree.sync()
    print("Comandos de barra sincronizados.")
    print(f'{client.user} conectou-se ao Discord!')
    print('Bot está online e pronto para uso.')


# --- EVENTO DE ENTRADA DE MEMBRO ---
@client.event
async def on_member_join(member):
    """Função de boas-vindas com a mensagem personalizada do Altura RP."""
    welcome_channel = discord.utils.get(member.guild.text_channels, name='👏│ᴡᴇʟᴄᴏᴍᴇ')

    if welcome_channel:
        guild = member.guild
        member_count = guild.member_count
        description_text = f"""
👉 <@519353941255913487> 👋✨ Seja muito bem-vindo(a), ao Altura RolePlay City — onde a sua história começa nas alturas! 🚁🌆
🛬 Você acaba de pousar na cidade mais viva e realista do SAMP! Aqui, cada escolha conta e o roleplay é levado a sério.
👥 Agora somos **{member_count} membros** vivendo essa experiência com você! 🎉
📝 **Antes de iniciar sua jornada:**
📜 Leia atentamente as regras em <#1384229192933310585>
📢 Fique de olho nos eventos e atualizações em <#1380958104228724789>
🎮 **IP do Servidor:** `179.127.16.157:29015`
💬 Em caso de dúvidas, fale com a equipe <@&1380957723159433326>
💜 O Altura RolePlay agradece sua presença. Nos vemos nas ruas da cidade! 🚓🚶‍♂️🚕
"""
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


# --- NOVA FUNÇÃO DE PARCERIA (EVENTO DE ATUALIZAÇÃO DE MEMBRO) ---
@client.event
async def on_member_update(before, after):
    """
    Esta função é chamada sempre que um membro é atualizado (ex: recebe um cargo).
    """
    # --- CONFIGURAÇÃO --- (Lembre-se de colar seus IDs aqui!)
    ID_DO_CARGO_GATILHO = 1387535159120629770  # <<<<<<< COLOQUE O ID DO CARGO '@Anunciar Parceria'
    ID_DO_CANAL_ANUNCIO = 1390048422815338596  # <<<<<<< COLOQUE O ID DO CANAL '#parcerias'
    ID_DO_CARGO_PING    = 1380958005331230742  # <<<<<<< COLOQUE O ID DO CARGO para pingar no anúncio

    cargo_gatilho = after.guild.get_role(ID_DO_CARGO_GATILHO)
    canal_anuncio = after.guild.get_channel(ID_DO_CANAL_ANUNCIO)

    if not cargo_gatilho or not canal_anuncio:
        # Esta mensagem só aparecerá nos logs da Railway se os IDs estiverem errados
        print("ERRO: Cargo de gatilho ou Canal de anúncio não encontrado. Verifique os IDs.")
        return

    # Verifica se o membro NÃO TINHA o cargo antes E se TEM o cargo agora
    if cargo_gatilho not in before.roles and cargo_gatilho in after.roles:
        embed_parceria = discord.Embed(
            title="🤝 Nova Parceria Fechada!",
            description=f"Temos o prazer de anunciar uma nova parceria com o membro {after.mention}!",
            color=discord.Color.gold()
        )
        if after.display_avatar:
            embed_parceria.set_thumbnail(url=after.display_avatar.url)
        embed_parceria.set_footer(text=f"Membro desde: {after.joined_at.strftime('%d/%m/%Y') if after.joined_at else 'Data indisponível'}")

        mensagem_ping = f"Atenção, <@&{ID_DO_CARGO_PING}>!"

        print(f"Anunciando nova parceria com {after.name} no canal {canal_anuncio.name}.")
        await canal_anuncio.send(content=mensagem_ping, embed=embed_parceria)


# --- INICIA O BOT --- (Esta deve ser sempre a última linha)
client.run(TOKEN)

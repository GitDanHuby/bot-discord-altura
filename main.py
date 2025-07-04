import time
from keep_alive import keep_alive
import discord
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuração das Intents
intents = discord.Intents.default()
intents.members = True
intents.messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """Função chamada quando o bot se conecta com sucesso."""
    print(f'{client.user} conectou-se ao Discord!')
    print('Bot está online e pronto para uso.')

# VERSÃO FINALMENTE FINAL DA SUA FUNÇÃO on_member_join

@client.event
async def on_member_join(member):
    """
    Função de boas-vindas com menção única e personalizada.
    """
    welcome_channel = discord.utils.get(member.guild.text_channels, name='👏│ᴡᴇʟᴄᴏᴍᴇ')

    if welcome_channel:
        guild = member.guild
        member_count = guild.member_count

        # --- CORREÇÃO DA DUPLA MENÇÃO AQUI ---
        # Mantive o ping para o Staff e ajustei o "bem-vindo" para mencionar o membro apenas uma vez.
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

        embed = discord.Embed(
            description=description_text,
            color=discord.Color.from_rgb(70, 130, 180) # Um tom de azul "céu"
        )

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
keep_alive()  # Liga o servidor web
print("Servidor web ligado. Aguardando 5 segundos antes de conectar o bot...")
time.sleep(5) # Adiciona uma pausa de 5 segundos
client.run(TOKEN) # Conecta o bot ao Discord
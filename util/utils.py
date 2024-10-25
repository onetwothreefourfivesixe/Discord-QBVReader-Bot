import discord

def create_embed(title: str, description: str) -> discord.Embed:
    '''Helper function to create a Discord embed.'''
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    return embed
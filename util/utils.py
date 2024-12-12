import discord

mainColor = {'r': 56, 'g': 182, 'b': 255}
def create_embed(title: str, description: str) -> discord.Embed:
    '''Helper function to create a Discord embed.'''
    embed = discord.Embed(title=title, description=description, color=discord.Color.from_rgb(mainColor['r'], mainColor['g'], mainColor['b']))
    return embed
import discord
from discord.ext import commands

class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.mainColor = {'r': 56, 'g': 182, 'b': 255}

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Bot Help",
            description="To get started playing a game, type `!help play`. Here are the available commands:",
            color=discord.Color.from_rgb(self.mainColor['r'], self.mainColor['g'], self.mainColor['b'])
        )
        for cog, commands_list in mapping.items():
            if cog:
                cog_name = cog.qualified_name
            else:
                cog_name = "Commands"
            command_names = [command.name for command in commands_list]
            if command_names:
                embed.add_field(
                    name=f"`{cog_name}`",
                    value="\n".join(command_names),
                    inline=False
                )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=f"{cog.qualified_name} Commands",
            description=cog.description,
            color=discord.Color.from_rgb(self.mainColor['r'], self.mainColor['g'], self.mainColor['b'])
        )
        for command in cog.get_commands():
            embed.add_field(
                name=command.name,
                value=command.help or "No description",
                inline=False
            )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(
            title=f"{group.name} Subcommands",
            description=group.help or "No description",
            color=discord.Color.from_rgb(self.mainColor['r'], self.mainColor['g'], self.mainColor['b'])
        )
        for command in group.commands:
            embed.add_field(
                name=command.name,
                value=command.help or "No description",
                inline=False
            )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=command.name,
            description=command.help or "No description",
            color=discord.Color.from_rgb(self.mainColor['r'], self.mainColor['g'], self.mainColor['b'])
        )
        channel = self.get_destination()
        await channel.send(embed=embed)
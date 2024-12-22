import discord
from discord.ext import commands
from util.utils import mainColor

class HelpCommand(commands.HelpCommand):
    """
    Custom HelpCommand class for a Discord bot using discord.py.

    This class extends the default HelpCommand to provide a customized help
    experience for users. It overrides methods to send help messages for the
    entire bot, specific cogs, command groups, and individual commands. The
    help messages are sent as embedded messages with a consistent color theme.

    Attributes:
        mainColor (dict): RGB values for the embed color theme.

    Methods:
        send_bot_help(mapping): Sends an embed with a list of all commands
            categorized by cogs.
        send_cog_help(cog): Sends an embed with a list of commands for a
            specific cog.
        send_group_help(group): Sends an embed with a list of subcommands
            for a command group.
        send_command_help(command): Sends an embed with details for a
            specific command.
    """
    def __init__(self):
        super().__init__()
        # mainColor = {'r': 56, 'g': 182, 'b': 255}

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Bot Help",
            description="To get started playing a game, type `!help play`. Here are the available commands:",
            color=discord.Color.from_rgb(mainColor['r'], mainColor['g'], mainColor['b'])
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
            color=discord.Color.from_rgb(mainColor['r'], mainColor['g'], mainColor['b'])
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
            color=discord.Color.from_rgb(mainColor['r'], mainColor['g'], mainColor['b'])
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
            color=discord.Color.from_rgb(mainColor['r'], mainColor['g'], mainColor['b'])
        )
        channel = self.get_destination()
        await channel.send(embed=embed)
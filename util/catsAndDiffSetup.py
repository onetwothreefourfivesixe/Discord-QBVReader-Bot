import discord
from discord.ext import commands
from discord.ui import Select
from discord.ui.view import View
from util.text import TEXT

from util.utils import create_embed, mainColor

class GameSetupView(View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=90.0)
        self.ctx = ctx
        self.categories = []
        self.difficulties = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Check if the interaction user is the same as the command invoker
        return interaction.user == self.ctx.author

    async def on_timeout(self) -> None:
        # Send a timeout message when the view times out
        await self.ctx.send(embed=create_embed('Timeout', "Game setup timed out. Please try again."))

    @discord.ui.select(
        placeholder="Select categories (multi-select)",
        options=[
            discord.SelectOption(label=cats, value=TEXT["cats"][cats]) for cats in TEXT["cats"].keys()
        ],
        min_values=0,
        max_values=len(TEXT["cats"]),
        custom_id="categories_select"
    )
    async def categories_callback(self, interaction: discord.Interaction, select: Select):
        # Extract selected values from interaction data
        self.categories = interaction.data.get("values", [])
        await interaction.response.defer()

    @discord.ui.select(
        placeholder="Select difficulties (multi-select)",
        options=[
            discord.SelectOption(label=diff, value=diff) for diff in TEXT["diff"]
        ],
        min_values=0,
        max_values=len(TEXT["diff"]),
        custom_id="difficulty_select"
    )
    async def difficulty_callback(self, interaction: discord.Interaction, select: Select):
        # Extract selected values from interaction data
        self.difficulties = interaction.data.get("values", [])
        await interaction.response.defer()

    @discord.ui.button(
            label="Done",
            style=discord.ButtonStyle.green,
            custom_id="finished_button"
        )
    async def done_callback(self, button: discord.Button, interaction: discord.Interaction):
        self.done = True
        self.stop()
        self.categories = ','.join(self.categories)
        self.difficulties = ','.join(self.difficulties)
        self.stop()  # Stops the view from listening for further interactions
        await interaction.response.send_message(embed=create_embed("Game Status", "Game setup completed!"), ephemeral=True)
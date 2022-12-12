import subprocess
from nextcord.ext import commands
from nextcord.ext.commands import Bot

# Runs commands on the OS and spits out results
class OSCommands(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    # Runs the fortune command
    @commands.command(brief='Generates a random fortune!', description='Generates a random fortune using the linux command "fortune" and posts it for all to see.')
    async def fortune(self, ctx):
        proc = subprocess.Popen(["/usr/games/fortune"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        await ctx.send("```" + out.decode('utf-8') + "```")


import nextcord
from nextcord import ui
from nextcord.ext import commands
from nextcord import Interaction
from nextcord.ext.commands import Bot
import math

### Subclass for a modal this will use ###
class modalField(ui.Modal):
    def __init__(self):
        super().__init__(
            "Character Description",
            timeout=5*60, # 5 minutes
        )

        self.statOrder=['str','dex','res','cha','clv','luk']

        self.name = ui.TextInput(
            label="Name",
            required = True,
            min_length = 1,
            max_length = 50
        )
        self.add_item(self.name)

        self.stats = nextcord.ui.TextInput(
            label="Enter statvals:\nstr, dex, res, cha, clv, luk",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="Insert as numbers separated by a new line. E.G. 0\n0\n0\n0\n0\n0\n",
            required=True,
            max_length=1800,
        )
        self.add_item(self.stats)

    # On error or close, make sure to close the modal.
    async def error(self, error, interaction) -> None:
        self.stop()

    async def on_timeout(self) -> None:
        self.stop()

    # On submission, calculate relevant stats.
    async def callback(self, interaction: nextcord.Interaction) -> None:
        # Validate input and load in dictionary
        splitStr = self.stats.value.split("\n")
        if (len(splitStr) < 6 ):
            response = "Error: Enter values for each stat."
            await interaction.send(response)
            return
        statDict = None
        try:
            statDict = dict(zip(self.statOrder, [eval(i) for i in splitStr]))        
        except:
            response = "Failed to parse stat list, make sure only to insert numbers"
            await interaction.send(response)
            return

        # Compute relevant stats:
        armor_class = 12 + statDict['dex'] + math.floor(statDict['luk']/2)
        health_pool = 20 + statDict['str'] + 2 * statDict['res']
        init = statDict['dex'] + math.floor(statDict['luk']/2)

        unarmed_stat = statDict['dex'] if statDict['dex'] > statDict['str'] else statDict['str']

        unarmed=f"{unarmed_stat} + proficiency"
        unarmed_dmg=f"{unarmed_stat} + proficiency/2"
        dex_weapon=f"Weapon Bonus + {statDict['dex']} + proficiency"
        dex_weapon_dmg=f"Damage = d* + {statDict['dex']} + proficiency" 
        str_weapon=f"Weapon Bonus + {statDict['str']} + proficiency"
        str_weapon_dmg=f"Damage = d* + {statDict['str']} + proficiency" 

        resp_list_left = [ 
            f"STR: {statDict['str']}",
            f"DEX: {statDict['dex']}",
            f"RES: {statDict['res']}",
            f"CHA: {statDict['cha']}",
            f"CLV: {statDict['clv']}",
            f"LUK: {statDict['luk']}",
        ]
        resp_list_right = [
            f"AC: {armor_class}",
            f"HP: {health_pool}",
            f"INIT: {init}"
        ]
        resp_list_bottom = [
            f"Unarmed Hit: {unarmed}",
            f"Unarmed DMG: {unarmed_dmg}",
            f"DEX WEP HIT: {dex_weapon}",
            f"DEX WEP DMG: {dex_weapon_dmg}",
            f"STR WEP HIT: {str_weapon}",
            f"STR WEP DMG: {str_weapon_dmg}",
            "",
            f"REMINDER: Skill Checks >= 13 lead to a proficiency point."
        ]
        

        embed = nextcord.Embed(
            title=self.name.value,
            color=0xFF5733
        )
        embed.add_field(name="Base Stats:",             value="\n".join(resp_list_left))
        embed.add_field(name="Secondary Stats:",        value="\n".join(resp_list_right))
        embed.add_field(name="Combat Stats:",           value="\n".join(resp_list_bottom), inline=False)
        await interaction.send(embed=embed)
        self.stop()

##########################################

# A small class to generate stats quickly for my ttrpg, Dungeons and Dorks.
class DungeonsAndDorks(commands.Cog):
    guild_ids = None
    def __init__(self, bot, guild_ids):
        super().__init__()
        self.bot = bot
        self.guild_ids = guild_ids

    @nextcord.slash_command(
        name="charsheet",
        description="Make a Dungeons and Dorks character sheet",
        guild_ids = guild_ids
    )
    async def charsheet(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(modalField())


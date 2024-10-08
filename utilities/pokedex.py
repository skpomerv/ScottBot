import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import Bot
import random
import string

# Runs some trivial simple commands and spits out results
class Pokedex(commands.Cog):
    def __init__(self, bot, data_dir):
        super().__init__()
        self.bot = bot
        self.types = []
        self.nouns = []
        self.adjectives = []

        self.types = list(filter(None,open(data_dir + '/pokemon-types.txt').read().split("\n")))
        self.nouns = list(filter(None,open(data_dir + '/english-nouns.txt').read().split("\n")))
        self.adjectives = list(filter(None,open(data_dir + '/english-adjectives.txt').read().split("\n")))


    @commands.command(brief='Makes a randomly generated pokemon (there is no "crazytypes" flag)', description='Makes a stupid pokemon, provides a type or two, and gives it a dex description.', aliases=['pokemon'])
    async def pokedex(self, ctx, *args):
        entrynum = random.randint(1250,9999)

        if len(args) > 0 and "crazytypes" in [x.lower() for x in args]:
            typecount = random.randint(1,2)
            types = random.sample(self.nouns, typecount)
        else:
            typecount = random.randint(1,2)
            types = random.sample(self.types, typecount)
        

        if len(types) == 1:
            typestring = types[0]
        else:
            typestring = f"{types[0]}\n{types[1]}"

        myNoun = random.choice(self.nouns)
        myAdj = random.choice(self.adjectives)

        # make a list of the first 1-3 characters of the noun, adj, and user for the name of the mon
        nameGen = [ ctx.author.name[:random.randint(1,3)], myNoun[:random.randint(1,3)], myAdj[:random.randint(1,3)]]
        random.shuffle(nameGen)

        name = f"{nameGen[0]}{nameGen[1]}{nameGen[2]}mon"
        embed = nextcord.Embed( title=f"Pokedex Entry #{entrynum}: {name}",
                                description=f"The {myAdj} {myNoun} pokemon",
                                color=nextcord.Color.red())
        embed.add_field(name="types:",
                        value=typestring,
                        inline=True)

        footertext=f"Generated by {ctx.author.name}"
        embed.set_footer(text=footertext, icon_url=ctx.author.avatar.url)
       
        # The random string is there to prevent discord from cacheing the same image
        cacherefresh = ''.join(random.choices(string.ascii_lowercase+string.digits, k=6))
        embed.set_image(url="https://picsum.photos/300/200?{}".format(cacherefresh))


        message=ctx.message
        await ctx.send(embed=embed)
        await message.delete()

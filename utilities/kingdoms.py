from discord.ext import commands
from discord.ext.commands import Bot
import json
import random

# Gives players a hidden role for the game Kingdoms
class Kingdoms(commands.Cog):
    data_dir = None
    vList = [ "default" ]
    signupMessage = None
    playerList = []
    variant = "default"
    kingdomsChannel = None

    def __init__(self, bot, ddir):
        super().__init__()
        self.bot = bot
        self.data_dir = ddir

    # Assign Role Logic
    # Returns a dict with keys being players and their role+description as a string being the value
    def assign_roles(self):
        min_players = 0
        max_players = 0
 
        loaded_dict = None
        with open (f"{self.data_dir}/{self.variant}.json") as json_file:
            loaded_dict=json.load(json_file)

        player_dict = dict()

        if loaded_dict == None:
            return f"Error: Dict did not load for game variant {self.variant}"

        # First, determine the loaded dict's "mandatory" and optional roles 
        mandatory_roles = []
        optional_roles = []
        role_dict = loaded_dict['roles']
        for key in role_dict:
            if ('optional' in role_dict[key].keys() ) and role_dict[key]['optional']:
                if 'count' in role_dict[key].keys():
                    for i in range(0,int(role_dict[key]['count'])):
                        optional_roles.append(key)
                    max_players = max_players + int(role_dict[key]['count'])
                else:
                    max_players = max_players + 1;
                    optional_roles.append(key)
            else:
                if 'count' in role_dict[key].keys():
                    min_players = min_players + int(role_dict[key]['count'])
                    max_players = max_players + int(role_dict[key]['count'])
                    for i in range(0,int(role_dict[key]['count'])):
                        mandatory_roles.append(key)
                else:
                    min_players = min_players + 1
                    max_players = max_players + 1;
                    mandatory_roles.append(key)

        player_count = len(self.playerList)
        if (player_count < min_players) or (player_count > max_players):
            return f"Error: Player count is currently {player_count}. We need between {min_players} and {max_players} players."
            
        # We're gonna shuffle the player list and optional roles.
        # I shuffle both the player list and the optional roles so we don't know the optional roles that are assigned and the
        # player list so we don't know who gets mandatory roles.
        playerListCopy = self.playerList.copy()
        random.shuffle(playerListCopy)
        random.shuffle(optional_roles)

        #Next step, assign mandatory roles first
        for i in range(0, len(mandatory_roles)):
            cur = playerListCopy.pop(0)

            rolename = mandatory_roles.pop(0) 
            #get the chosen rule from the dict
            randkey = random.choice(list(role_dict[rolename]['rules'].keys()))
            player_dict[cur] = f"Your role is: {rolename}\n{role_dict[rolename]['rules'][randkey]}"

            del role_dict[rolename]['rules'][randkey]

        for i in range(0, len(playerListCopy)): 
            cur = playerListCopy.pop(0)
            rolename = optional_roles.pop(0) 
            randkey = random.choice(list(role_dict[rolename]['rules'].keys()))
            player_dict[cur] = f"Your role is: {rolename}\n{role_dict[rolename]['rules'][randkey]}"

        return player_dict

    # Stuff For Signup and Start Game

    async def signup(self, ctx, *args):
        if (self.signupMessage != None):
            await ctx.send("Signup for a game has already started. React to that post with any emote to sign up.")
            return
        self.signupMessage = await ctx.send("React to this post to give yourself a Kingdoms Role. For a default game, up to 6 players may join at the moment and at least 5 players must be in the game to start. The signup will cancel if `!kingdoms start` has been run or `!kingdoms abandon` has been run.\nNote: Removing an emote does not remove you from the queue, so it is advised to reset the game if that is the case.")
        return

    async def startGame(self, ctx, *args):
        if self.signupMessage == None:
            await ctx.send("No signup has been detected! Please use `!kingdoms` to start!\n")
            return

        role_list = self.assign_roles()
        #If it is a string and not a dict, that means we have an error
        if isinstance(role_list, str):
            await ctx.send(role_list)
            await ctx.send("The game signup has not been reset, so if you need to clear the settings, do so manually.")
            return

        # Send out messages with the roles.
        for uid in self.playerList:
            user = await self.bot.fetch_user(uid)
            await user.send(role_list[uid]) 

        # Prep for a new game
        self.signupMessage = None
        self.playerList = []
        self.variant = "default"


    ### Listeners ##
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = await self.bot.fetch_user(payload.user_id)
        if message == self.signupMessage:
            if not (payload.user_id in self.playerList):
                self.playerList.append(payload.user_id)
                await user.send("You have been queued for the next game!")
        return 


    ### Commands ###
    @commands.command(hidden=True, brief='Sets a channel to be for Kingdoms Games', description='Begins a game of Kingdoms')
    async def setKingdomsChannel(self, ctx, *args):
        if ctx.author.guild_permissions.administrator == False:
            return
        self.kingdomsChannel = ctx.channel.id
        await channel.send(f"Kingdoms channel has been set to {ctx.channel}")


    @commands.command(hidden=True, brief='Sets a channel to be for Kingdoms Games', description='Begins a game of Kingdoms')
    async def resetKingdomsChannel(self, ctx, *args):
        if ctx.author.guild_permissions.administrator == False:
            return

        self.kingdomsChannel = None
        await channel.send(f"Kingdoms channel has been reset")

    @commands.command(brief='Preps and starts a game of kingdoms', description='Begins a game of Kingdoms')
    async def kingdoms(self, ctx, *args):
        if not (self.kingdomsChannel == None or self.kingdomsChannel == ctx.channel.id):
            return

        if len(args) == 0:
            await self.signup(ctx, args)
            return
        elif args[0].lower() == "help":
            await ctx.send("`!kingdoms` starts a game. `!kingdoms start` begins it. `!kingdoms reset` resets the queue in case a previous signup needs to be abandoned.")
        #elif args[0].lower() == "variant":
        #    if len(args) == 1:
        #        await ctx.send(f"Variant needs an argument? Currently the legal options are {self.vList}") 
        elif (args[0].lower() == "abandon") or (args[0].lower() == "reset"):
            self.signupMessage = None
            for uid in self.playerList:
                user = await self.bot.fetch_user(uid)
                await user.send("Game has been cancelled. Re-join the next game if you would like to play!") 
            self.playerList = []
            self.variant = "default"
            await ctx.send("Signup has been reset.\n")
        elif args[0].lower() == "start":
            await self.startGame(ctx, args)

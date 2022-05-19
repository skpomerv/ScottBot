import json
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from random import sample
from random import randint


class EDHMaker(commands.Cog):

    def __init__(self, bot, data_dir):
        # Discord specific stuff
        super().__init__()
        self.bot = bot

        # EDH Deck maker stuff
        self.original_json =    data_dir + '/AtomicCards.json' 
        self.legal_json =       data_dir + '/LegalCMDR.json'
        self.cmdr_json =        data_dir + '/CandidateCMDR.json'
        self.partner_json =     data_dir + '/PartnerCMDR.json'
        self.land_json =        data_dir + '/Lands.json'

        # Make some of the JSONs a bit easier to work with
        self.generateLegalJSON()
        self.generateLandJSON()
        self.generateCandidateCommanderJSON()
        self.generatePartnersJSON()

        
    ### Tools for Loading Dictionaries ###

    def getDict(self):
        cardDict = None
        with open(self.original_json) as json_file:
            cardDict = json.load(json_file)["data"]
        return cardDict

    def getLegalDict(self):
        cardDict = None
        with open(self.legal_json) as json_file:
            cardDict = json.load(json_file)
        return cardDict         

    def getCommanderDict(self): 
        cardDict = None
        with open(self.cmdr_json) as json_file:
            cardDict = json.load(json_file)
        return cardDict
    
    def getPartnerDict(self):
        cardDict = None
        with open(self.partner_json) as json_file:
            cardDict = json.load(json_file)
        return cardDict

    def getLandDict(self): 
        cardDict = None
        with open(self.land_json) as json_file:
            cardDict = json.load(json_file)
        return cardDict

    ### JSON Generators ###

    # Makes a json of all known legal nonland cards.
    def generateLegalJSON(self):
        myDict = {}
        cardDict = self.getDict()

        for key, val in cardDict.items():
            if (('legalities' in val[0]) and ('types' in val[0])):
                if (('commander' in val[0]["legalities"]) & ('Land' not in val[0]['types'])) :
                    if (val[0]["legalities"]["commander"] != "Banned"):
                        myDict[key] = val

        f = open(self.legal_json, "w")
        json.dump(myDict, f)
        f.close()


    # Makes a json of all legal lands
    def generateLandJSON(self):
        myDict = {}
        cardDict = self.getDict()

        for key, val in cardDict.items():
            if (('legalities' in val[0]) and ('types' in val[0])):
                if (('commander' in val[0]["legalities"]) & ('Land' in val[0]['types'])) :
                    if (val[0]["legalities"]["commander"] != "Banned"):
                        myDict[key] = val

        f = open(self.land_json, "w")
        json.dump(myDict, f)
        f.close()

    # Makes a json of all known legal commanders
    def generateCandidateCommanderJSON(self): 
        myDict = {}
        #Let's save some time and get the legal dictionary instead of the illegal one.
        cardDict = self.getLegalDict()

        #if a card is a legendary creature, it can be a commander
        for key, val in cardDict.items():
            notAdded = True

            # If it's a legendary creature, it can be a commander
            if (('supertypes' in val[0]) & ('types' in val[0])): # I don't trust python short circuiting
                if (('Legendary' in val[0]['supertypes']) & ('Creature' in val[0]['types'])):
                    #print("Adding: {}".format(key))
                    myDict[key] = val 
                    notAdded = False
            # If the card is not a legendary creature, it may still be a commander if the rules text says so
            if notAdded:
                if ('text' in val[0]):
                    if("can be your commander" in val[0]['text']):
                        myDict[key] = val 

        f = open(self.cmdr_json, "w")
        json.dump(myDict, f)
        f.close()


    # Makes a json of all known partner commanders
    def generatePartnersJSON(self): 
        myDict = {}
        #Let's save some time and get the legal dictionary instead of the illegal one.
        cardDict = self.getCommanderDict()

        #if a card is a legendary creature, it can be a commander
        for key, val in cardDict.items():
            # If the card is not a legendary creature, it may still be a commander if the rules text says so
            if ('text' in val[0]):
                if (("Partner" in val[0]['text']) | ( "Friends Forever" in val[0]['text'] ) ):
                    myDict[key] = val 

        f = open(self.partner_json, "w")
        json.dump(myDict, f)
        f.close()


    ### Deck Generators ###

    # Gets all color identity colors that aren't in this list of provided cards.
    # Returns two lists, first list is the legal one, the illegal one is the second list
    def getColors(self, cardList):
        # Though I anticipate I'll only use this for commanders I'm being conservative
        # and loading all cards...
        cardData = self.getDict() 
        
        current_legal_colors = ['W', 'U', 'B', 'R', 'G']
       
        # This loop looks slow but card colors and the number of cards provided to getColors is
        # always small
        for card in cardList:
            for color in cardData[card][0]['colorIdentity']:
                if color in current_legal_colors:
                    current_legal_colors.remove(color)
 
        return [x for x in ['W', 'U', 'B', 'R', 'G'] if x not in current_legal_colors ], current_legal_colors

    # Returns true if a card is a partner card, false otherwise
    def isPartner(self, card):
        cardDict = self.getPartnerDict()
        return card in cardDict
    
    # Gets a dictionary and selects a random card from it.
    # Color restrictions is an array of characters 'w' 'u' 'b' 'r' and 'g'. These are the "illegal colors"
    # cardCount is an integer of how many cards to return
    # card_restrictions are cards not allowed to be selected by the algorithm, perhaps because a
    #           previous step already added it to the deck (the commander cant also be in the 99)
    # role should either be 'land', 'commander', 'partner' or 'nonland' to determine the working data set.
    def getXRandomCardsFromDict(self, color_restrictions, card_restrictions, cardCount, role):
        cardList = []
        cardDict = None
        if role == 'commander':
            cardDict = self.getCommanderDict()
        elif role == 'partner':
            cardDict = self.getPartnerDict()
        elif role == 'nonland':
            cardDict = self.getLegalDict()
        elif role == 'land':
            cardDict = self.getLandDict()
        else:
            return None;
        # Filter cards that contain our filter colors.
        # I could statically compute these but that performance gain probably isn't worth it. 
        for key, val in cardDict.items():
            if key not in card_restrictions:
                addCard = True

                for c in color_restrictions:
                    if (c in val[0]['colorIdentity']):
                        addCard = False
                        break

                if addCard:
                    cardList.append(key)

        if cardCount > len(cardList):
            return None

        # Grab n cards from the list
        # Unlike random.choices, sample grabs without relacement so there arent duplicate choices.
        return sample(cardList, cardCount)
        

        # Generates a (probably) terrible EDH deck
        # At the moment there are no color restriction options
        # Returns a map that maps keys (cardnames) to a small dict of ['isCMDR', and 'count']
    def makeDeck(self):
        #initial vars
        colorToLand = { "W":"Plains", "B":"Swamp", "U":"Island", "G":"Forest", "R":"Mountain" }
        cmdrList = []
        deckList = []

        landCount = randint(33,42)
        basicLandCount = int(landCount * .66)
        nonlandCount = 100-landCount

        # get commander
        cmdrList = self.getXRandomCardsFromDict([], [], 1, 'commander')
        if self.isPartner(cmdrList[0]):
            cmdrList.append(newDeck.getXRandomCardsFromDict([], [], 1, 'partner')[0])

        # Find out the colors I am using and the colors I'm not.
        legalColors, illegalColors = self.getColors(cmdrList)

        # I know it's backwards, but we're starting with the basic lands.

        # The below code block is equivalent to
        # if len(legalColors) <= 1 then basicMul = basicLandCount
        # else basicMul = basicLandCount / len(legalColors)
        # It is done this way to make sure the variable exists in the
        # scope, and as a bonus the branch prediction should make this
        # run like 0.00...001% faster! 
        basicMul = basicLandCount
        basicTypes = 1
        if len(legalColors) > 1:
            basicMul = int( basicLandCount / len(legalColors) ) 
            basicTypes = len(legalColors)

        # Re-computing the nonbasic land count as basicMul * basics probably has a remainder.
        nonBasicLandCount = landCount - (basicMul * basicTypes) 

        # omit illegal colors, ban previously added cards from being readded, add nonlandcount cards (minus number of commanders)
        deckList = deckList + self.getXRandomCardsFromDict(illegalColors, cmdrList, nonlandCount-len(cmdrList), 'nonland')
        deckList = deckList + self.getXRandomCardsFromDict(illegalColors, cmdrList+deckList, int(nonBasicLandCount), 'land')

        # For the sake of ease I'm going to actually make this a dict with an inner dict of "isCMDR" and "count"
        # for the value. I should have make the lists a dict from the get-go but I forgot I could have
        # multiple basic lands when I first planned this method rip lmao.
        # The reason I use an inner dict as opposed to a list is for understandability, not speed.
        finalDict = {}
        for c in cmdrList:
            innerMap = { "isCMDR":True, "count":1 }
            finalDict[c] = innerMap

        for c in deckList:
            innerMap = {"isCMDR":False, "count":1 }
            finalDict[c] = innerMap

        # Mapping basic lands is only mostly trivial
        if len(legalColors) == 0:
            finalDict["Wastes"] = { "isCMDR":False, "count":basicMul }
        for color in legalColors:
            finalDict[colorToLand[color]] = { "isCMDR":False, "count":basicMul }

        return finalDict



    # Converts the deck arg into a string that looks pretty to humans
    def dictToString(self, deck):
        myString = ""
        for key in deck:
            myString = myString + "{}x {}".format(deck[key]['count'], key)
            if deck[key]['isCMDR']:
                myString = myString + " *CMDR*"
            myString = myString + "\n"
        return myString


    @commands.command(brief='Generates an EDH deck', description='Makes a random EDH deck that is probably not good. Note double faced cards (which use "//" may need to be hand modified to be supported by whatever you shove this into.')
    async def edh(self, ctx, *args):
        myString = self.dictToString(self.makeDeck())
        await ctx.send("Here's your deck!\n```" + myString + "```")


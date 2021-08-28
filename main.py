import discord
import json
import random
import math
import time
from discord.ext import commands
from discord.utils import get
import asyncio

intents = discord.Intents.default()
intents.members = True
client = discord.Client()
bot = commands.Bot(command_prefix="$", intents=intents)
bot.remove_command('help')


def fetch_database():
    with open('C:/Users/Joey/PycharmProjects/discordBot/database.json') as x:
        data = json.load(x)
        x.close()
    return data


class Duel:
    words = ['slashes', 'swings', 'lunges', 'stabs', 'hacks', 'carves', 'cleaves']

    def __init__(self):
        self.activeDuelers = []
        self.pool = 0
        self.active = False
        self.timeout = 0
        self.winner = ''

    def setup_duel(self, d1, d2, p):
        self.activeDuelers.append(d1)
        self.activeDuelers.append(d2)
        self.pool = p
        self.active = True
        self.timeout = time.time()

    def clear_duel(self):
        self.activeDuelers.clear()
        self.timeout = 0
        self.winner = ''
        self.pool = 0
        self.active = False

    def do_duel(self):
        database[self.activeDuelers[0]] -= self.pool
        database[self.activeDuelers[1]] -= self.pool

        if random.random() < 0.5:
            database[self.activeDuelers[0]] += self.pool * 2
            self.winner = self.activeDuelers[0]
        else:
            database[self.activeDuelers[0]] += self.pool * 2
            self.winner = self.activeDuelers[1]
        save_database()


class Prediction:
    aBetters = {}
    bBetters = {}

    def __init__(self, event, a, b):
        self.event = event
        self.a = a
        self.b = b
        self.active = False
        self.locked = True

    def get_total(self):
        total = 0
        for z in self.aBetters.values():
            total += z
        for z in self.bBetters.values():
            total += z
        return total

    def add_to_pool(self, x, y, btr):
        if x == 'a' or x == 'A':
            if btr not in self.bBetters.keys():
                if btr not in self.aBetters.keys():
                    self.aBetters[btr] = y
                else:
                    self.aBetters[btr] += y
                database[btr] -= y
        elif x == 'b' or x == 'B':
            if btr not in self.aBetters.keys():
                if btr not in self.bBetters.keys():
                    self.bBetters[btr] = y
                else:
                    self.bBetters[btr] += y
                database[btr] -= y

    def get_returns(self, btr, x):
        total = self.get_total()
        bProb = len(self.aBetters) / (len(self.aBetters) + len(self.bBetters))
        aProb = len(self.bBetters) / (len(self.aBetters) + len(self.bBetters))
        aPool = total / len(self.aBetters)
        bPool = total / len(self.bBetters)

        if x in ["a", "A"]:
            return self.return_helper(self.aBetters[btr], aProb, aPool)
        elif x in ["b", "B"]:
            return self.return_helper(self.bBetters[btr], bProb, bPool)

    def get_probability(self):
        return [len(self.bBetters) / (len(self.aBetters) + len(self.bBetters)),
                len(self.aBetters) / (len(self.aBetters) + len(self.bBetters))]

    @staticmethod
    def return_helper(bet, prob, pool):
        if 0 <= bet <= 10000:
            return int((bet * (2 + prob)) + bet + pool)
        if 10000 < bet <= 100000:
            return int(((bet * (2.5 + prob)) - 5000) + bet + pool)
        if 100000 < bet <= 500000:
            return int(((bet * (4 + prob)) - 155000) + bet + pool)
        if 500000 < bet:
            return int(((bet * (7 + prob)) - 1655000) + bet + pool)

    def set_prediction(self, e, a, b):
        self.event = e
        self.a = a
        self.b = b
        self.active = True
        self.locked = False

    def clear_prediction(self):
        self.set_prediction('', '', '')
        self.aBetters.clear()
        self.bBetters.clear()
        self.active = False

    def print_betters(self):
        print('[%s]' % ', '.join(map(str, self.aBetters)))
        print('[%s]' % ', '.join(map(str, self.bBetters)))


t = 120
pred = Prediction('', '', '')
duel = Duel()
database = fetch_database()


def award_betters(x):
    results = '**```'
    if x == 'a' or x == 'A':
        for better in pred.aBetters:
            winnings = pred.get_returns(better, x)
            results += f" - {better} has won {winnings} points!\n"
            database[better] += winnings
        results = results[:-1]
        results += "```**"
        return results
    elif x == 'b' or x == 'B':
        for better in pred.bBetters:
            winnings = pred.get_returns(better, x)
            results += f"{better} has won {winnings} points!\n"
            database[better] += winnings
        results = results[:-1]
        results += "```**"
        return results


def save_database():
    with open('C:/Users/Joey/PycharmProjects/discordBot/database.json', 'w') as x:
        json.dump(database, x)
    reload_database()


def reload_database():
    global database
    database = fetch_database()


@bot.event
async def on_ready():
    print('Logged into server.')


#
#   Predictions:
#


@bot.command(name='predict')
async def _predict(ctx, *args):
    pred.clear_prediction()
    if len(args) == 0:
        await ctx.channel.send('**```Commands: \n'
                               ' - $predict "event" "outcome 1" "outcome 2"\n')
    elif len(args) == 3:
        if not pred.active:
            pred.set_prediction(args[0], args[1], args[2])
            await ctx.channel.send(
                f"**```Prediction started:\n {pred.event}:\n  - A: {pred.a}\n  - B: {pred.b}\nYou have {t} seconds to place your bets.```**")
            await lock(ctx, t)
        else:
            await ctx.channel.send("```There is already a bet in place.```")

    else:
        await ctx.channel.send(' `Error: Unknown command. try: $help`')


@bot.command(name='cancel')
async def _cancel(ctx, *args):
    if str(ctx.author) == "JoayeLmao#4662":
        if pred.active:
            for better in pred.aBetters:
                database[better] += pred.aBetters[better]
                await ctx.channel.send(f"`returned {pred.aBetters[better]} to {better}`")
            for better in pred.bBetters:
                database[better] += pred.bBetters[better]
                await ctx.channel.send(f"`returned {pred.bBetters[better]} to {better}`")
            await ctx.channel.send(' `The bet was manually canceled.`')
            pred.active = False
        else:
            await ctx.channel.send("There is not an active bet.")
    else:
        await ctx.channel.send("You are not Joey.")


@bot.command(name='bet')
async def _bet(ctx, *args):
    user = str(ctx.author)
    if pred.active:
        if not pred.locked:
            if len(args) == 2:
                if (args[0] == 'A' or args[0] == 'a') or (args[0] == 'B' or args[0] == 'b'):
                    if args[1].isnumeric():
                        if user in database.keys():
                            if database[user] >= int(args[1]):
                                pred.add_to_pool(args[0], int(args[1]), user)
                                await ctx.channel.send(f' placed {args[1]} point bet for {str(ctx.author.mention)}')
                            else:
                                await ctx.channel.send(
                                    f'Error: {ctx.author.mention} you do not have enough points to place that bet. You have {database[user]}')
                        else:
                            await ctx.channel.send('`Initializing user in database. Enter command again to place bet.`')
                    elif args[1] == 'max':
                        if user in database.keys():
                            bet = int(database[user])
                            pred.add_to_pool(args[0], bet, user)
                            await ctx.channel.send(f' placed {bet} point bet for {str(ctx.author.mention)}')
                        else:
                            await ctx.channel.send('`Initializing user in database. Enter command again to place bet.`')
                    else:
                        await ctx.channel.send("`Error: Betting amount must be a number.`")
                else:
                    await ctx.channel.send("`Error: You can only bet on either 'A' or 'B'`")
            else:
                await ctx.channel.send(' `Error: Unknown command. try: $help`')
        else:
            await ctx.channel.send(' `Error: This prediction is locked. Wait for the results!`')
    else:
        await ctx.channel.send(' `Error: There is not an active prediction. Try starting one!`')


@bot.command(name='s')
async def _simulate(ctx):
    await ctx.channel.send("simulating bets")
    pred.clear_prediction()
    pred.set_prediction("Will Braulio win this game?", "Yes", "No")
    pred.add_to_pool('a', 1, "Mallwhore#9154")
    pred.add_to_pool('a', 1, "Wise Peanut Brain#8452")
    pred.add_to_pool('a', 1, "Prediction Bot#2319")
    pred.add_to_pool('b', 1, "JoayeLmao#4662")
    await lock(ctx, 1)


@bot.command(name='sd')
async def _simduel(ctx):
    await ctx.channel.send("simulating duel")
    duel.clear_duel()
    duel.setup_duel("JoayeLmao#4662", "JOI BOT#3774", 20)
    duel.do_duel()
    await ctx.channel.send(f'`{duel.activeDuelers[0][:-5]} vs {duel.activeDuelers[1][:-5]}`')
    await asyncio.sleep(2)
    await ctx.channel.send(
        f'`{duel.activeDuelers[0][:-5]} {random.choice(duel.words)} at {duel.activeDuelers[1][:-5]}`')
    await asyncio.sleep(2)
    await ctx.channel.send(
        f'`{duel.activeDuelers[1][:-5]} {random.choice(duel.words)} at {duel.activeDuelers[0][:-5]}`')
    await asyncio.sleep(2)
    await ctx.channel.send(
        f'`{duel.activeDuelers[0][:-5]} {random.choice(duel.words)} at {duel.activeDuelers[1][:-5]}`')
    await asyncio.sleep(2)
    await ctx.channel.send(f'`The winner is {duel.winner[:-5]}! They have won {duel.pool * 2} points!`')


async def lock(ctx, timer):
    await asyncio.sleep(timer)
    if len(pred.bBetters) == 0 or len(pred.aBetters) == 0:
        await ctx.channel.send(' `Canceling bet. There must be one person betting for either side.`')
        for better in pred.aBetters:
            database[better] += pred.aBetters[better]
        for better in pred.bBetters:
            database[better] += pred.bBetters[better]
    else:
        if pred.active:
            pred.locked = True
            await ctx.channel.send(
                f' `The bets are locked in! The total pot is: {pred.get_total()}, at {int(float(pred.get_probability()[0]) * 100)}%:{int(float(pred.get_probability()[1]) * 100)}% odds`')


@bot.command(name='calc')
async def _calc(ctx, *args):
    # $calc {bet} {pool} {odd1} {odd2} {a or b}
    if len(args) == 5:
        bet = int(args[0])
        pool = int(args[1])
        odd1 = int(args[2])
        odd2 = int(args[3])
        x = args[4]

        bProb = odd1 / (odd1 + odd2)
        aProb = odd2 / (odd1 + odd2)
        aPool = pool / odd1
        bPool = pool / odd2

        returns = 0

        if x in ["a", "A"]:
            if 0 <= bet <= 10000:
                returns = int((bet * (2 + aProb)) + bet + aPool)
            if 10000 < bet <= 100000:
                returns = int(((bet * (2.5 + aProb)) - 5000) + bet + aPool)
            if 100000 < bet <= 500000:
                returns = int(((bet * (4 + aProb)) - 155000) + bet + aPool)
            if 500000 < bet:
                returns = int(((bet * (7 + aProb)) - 1655000) + bet + aPool)
        elif x in ["b", "B"]:
            if 0 <= bet <= 10000:
                returns = int((bet * (2 + bProb)) + bet + bPool)
            if 10000 < bet <= 100000:
                returns = int(((bet * (2.5 + bProb)) - 5000) + bet + bPool)
            if 100000 < bet <= 500000:
                returns = int(((bet * (4 + bProb)) - 155000) + bet + bPool)
            if 500000 < bet:
                returns = int(((bet * (7 + bProb)) - 1655000) + bet + bPool)

        await ctx.channel.send(returns)


@bot.command(name='close')
async def _close(ctx, *args):
    user = str(ctx.author)
    if len(args) == 1:
        if str(ctx.author) == "JoayeLmao#4662":
            if (args[0] == 'A' or args[0] == 'a') or (args[0] == 'B' or args[0] == 'b'):
                await ctx.channel.send(
                    f"```Prediction ended. The winner for '{pred.event}' is {'A' if (args[0] == 'A' or args[0] == 'a') else 'B'}: '{pred.a if (args[0] == 'A' or args[0] == 'a') else pred.b}'```")
                res = award_betters(args[0])
                await ctx.channel.send(res)
                save_database()
            else:
                await ctx.channel.send(' `Error: Unknown command. try: $help`')
        else:
            await ctx.channel.send(' `Error: You are not Joey. You cannot close the bet. Thank Abraham for this.`')
    else:
        await ctx.channel.send(' `Error: Unknown command. try: $help`')


#
#   Misc. Betting Methods:
#

@bot.command(name='duel')
async def _duel(ctx, *args):
    if not duel.active:
        if len(args) == 2:
            await duelcall(ctx, args)
        else:
            await ctx.channel.send('`Error: Unknown command. try: $help`')
    else:
        if time.time() - duel.timeout < 30:
            if len(args) == 2:
                duel.clear_duel()
                await duelcall(ctx, args)
            else:
                await ctx.channel.send('`Error: Unknown command. try: $help`')
        else:
            await ctx.channel.send('`Error: There is already an active duel, please wait!`')


async def duelcall(ctx, args):
    user = args[0]
    user = user[3:-1]
    user = bot.get_user(int(user))
    auth = str(ctx.author)
    if user is not None:
        if database[str(user.name) + "#" + str(user.discriminator)] >= int(args[1]):
            if database[auth] >= int(args[1]):
                await ctx.channel.send(
                    f'{args[0]}: {str(ctx.author.mention)} has challenged you to a duel for {args[1]} points. You have 30 seconds to accept using $duelacc!')
                duel.setup_duel(str(ctx.author), str(user.name) + "#" + str(user.discriminator), int(args[1]))
            else:
                await ctx.channel.send(f'`Error: {auth} does not have enough points to initiate this duel.`')
        else:
            await ctx.channel.send(
                f'`Error: {str(user.name) + "#" + str(user.discriminator)} does not have enough points to initiate this duel.`')
    else:
        await ctx.channel.send('`Error: That user could not be found.`')


@bot.command(name='duelacc')
async def _duelacc(ctx):
    user = str(ctx.author)
    if duel.active:
        if time.time() - duel.timeout < 30:
            if user == duel.activeDuelers[1]:
                duel.do_duel()
                await ctx.channel.send(f'`{duel.activeDuelers[0][:-5]} vs {duel.activeDuelers[1][:-5]}`')
                await asyncio.sleep(2)
                await ctx.channel.send(
                    f'`{duel.activeDuelers[0][:-5]} {random.choice(duel.words)} at {duel.activeDuelers[1][:-5]}`')
                await asyncio.sleep(2)
                await ctx.channel.send(
                    f'`{duel.activeDuelers[1][:-5]} {random.choice(duel.words)} at {duel.activeDuelers[0][:-5]}`')
                await asyncio.sleep(2)
                await ctx.channel.send(
                    f'`{duel.activeDuelers[0][:-5]} {random.choice(duel.words)} at {duel.activeDuelers[1][:-5]}`')
                await asyncio.sleep(2)
                await ctx.channel.send(f'`The winner is {duel.winner[:-5]}! They have won {duel.pool * 2} points!`')
                duel.clear_duel()
                save_database()
            else:
                await ctx.channel.send(f'`Error: {user} you were not challenged to a duel.`')
        else:
            await ctx.channel.send(f'`Error: Your duel timed out.`')
            duel.clear_duel()
    else:
        await ctx.channel.send('`Error: There is not an active duel.`')


@bot.command(name='coinflip')
async def _coinflip(ctx, *args):
    user = str(ctx.author)
    ans = None
    headtail = False
    if len(args) == 2:
        if args[0] in ["Heads", "heads", "HEADS", "head", "h"]:
            ans = True
        elif args[0] in ["Tails", "tails", "TAILS", "tail", "t"]:
            ans = False
        if args[1].isnumeric() and ans is not None:
            val = int(args[1])
            if val <= 200:
                await ctx.channel.send(f'`Doing a coinflip for {args[1]} points`')
                await asyncio.sleep(1)
                await ctx.channel.send(f'`The coin flies into the air!...`')
                await asyncio.sleep(1)
                if random.random() < 0.5:
                    await ctx.channel.send(f'`...and lands on heads!`')
                    await asyncio.sleep(1)
                    headtail = True
                else:
                    await ctx.channel.send(f'`...and lands on tails!`')
                    await asyncio.sleep(1)
                    headtail = False
                if headtail == ans:
                    await ctx.channel.send(f'`You won {math.ceil(val + val * .5)}!`')
                    database[user] += math.ceil(val + val * .5)
                    save_database()
                else:
                    await ctx.channel.send(f'`You lost, try again!`')
                    database[user] -= val
                    save_database()
            else:
                await ctx.channel.send(f'`Error: You went over the max bet limit of 200!`')
    else:
        await ctx.channel.send('`Error: Unknown command. try: $help`')


#
# General Point Commands:
#


@bot.command(name='upgrade')
async def _upgraderank(ctx, *args):
    rIds = [800225768469823498, 800226751485050890, 800226792831975455, 800226813925261343, 800226834046386176]
    if len(args) == 0:
        user = str(ctx.author)
        if len(ctx.author.roles) == 2:
            if database[user] >= 1000:
                database[user] -= 1000
                role = get(ctx.guild.roles, id=rIds[1])
                await ctx.author.add_roles(role)
                await ctx.channel.send(f'{ctx.author.mention} has increased their rank to Knight!')
                save_database()
            else:
                await ctx.channel.send(
                    f'Error: {ctx.author.mention} you do not have enough points to purchase that role. You have {database[user]}')
        elif len(ctx.author.roles) == 3:
            if database[user] >= 10000:
                database[user] -= 10000
                role = get(ctx.guild.roles, id=rIds[2])
                await ctx.author.add_roles(role)
                await ctx.channel.send(f'{ctx.author.mention} has increased their rank to Lord!')
                save_database()
            else:
                await ctx.channel.send(
                    f'Error: {ctx.author.mention} you do not have enough points to purchase that role. You have {database[user]}')
        elif len(ctx.author.roles) == 4:
            if database[user] >= 500000:
                database[user] -= 500000
                role = get(ctx.guild.roles, id=rIds[3])
                await ctx.author.add_roles(role)
                await ctx.channel.send(f'{ctx.author.mention} has increased their rank to King!')
                save_database()
            else:
                await ctx.channel.send(
                    f'Error: {ctx.author.mention} you do not have enough points to purchase that role. You have {database[user]}')
        elif len(ctx.author.roles) == 5:
            if database[user] >= 10000000:
                database[user] -= 10000000
                role = get(ctx.guild.roles, id=rIds[4])
                await ctx.author.add_roles(role)
                await ctx.channel.send(f'{ctx.author.mention} has increased their rank to GOD!')
                save_database()
            else:
                await ctx.channel.send(
                    f'Error: {ctx.author.mention} you do not have enough points to purchase that role. You have {database[user]}')
        elif len(ctx.author.roles) == 6:
            await ctx.channel.send(f'Error: {ctx.author.mention} you are the maximum rank on the server!')
    else:
        if args[0] == "help" or args[0] == "?":
            await ctx.channel.send(
                '```Upgrade your rank with points: \n - Knight: 1000 points \n - Lord: 10000 points \n - King: 500000 points \n - GOD: 10000000 points```')
        else:
            await ctx.channel.send('Error: Unknown command')


@bot.command(name='help')
async def _help(ctx):
    await ctx.channel.send('**```Commands: \n'
                           ' - $predict {"event"} {"outcome 1"} {"outcome 2"}\n'
                           ' - $bet {A or B} {$ amount}\n'
                           ' - $duel {@user} {$ amount}\n'
                           ' - $coinflip {heads or tails} {$ amount}\n'
                           ' - $leaderboard\n'
                           ' - $bal\n'
                           ' - $bailout```**\n')


@bot.command(name='leaderboard')
async def _leaderboard(ctx):
    d = sorted(database.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    await ctx.channel.send(f'```Leaderboard: \n'
                           f'  1. {d[0][0]}: {d[0][1]}\n'
                           f'  2. {d[1][0]}: {d[1][1]}\n'
                           f'  3. {d[2][0]}: {d[2][1]}\n'
                           f'  4. {d[3][0]}: {d[3][1]}\n'
                           f'  5. {d[4][0]}: {d[4][1]}```')


@bot.command(name='bal')
async def _bal(ctx):
    user = str(ctx.author)
    if user in database.keys():
        await ctx.channel.send(f' {str(ctx.author.mention)}, your balance is {database[user]}')


@bot.command(name='add')
async def _add(ctx, *args):
    user = args[0]
    if len(args) == 2:
        if user in database.keys() and str(ctx.author) == "JoayeLmao#4662":
            database[args[0]] += int(args[1])
            save_database()
            await ctx.channel.send(f'`{args[1]} has been given to {user}`')
        else:
            print("error")
    else:
        await ctx.channel.send(' `Error: Unknown command. try: $help`')


@bot.command(name='bailout')
async def _bailout(ctx):
    user = str(ctx.author)

    if database[user] == 0:
        database[user] += 20
        save_database()
        await ctx.channel.send(f'{ctx.author.mention}\'s broke ass has been given a 20 point bailout.')
    else:
        await ctx.channel.send('`Error: you cannot redeem a bailout unless you have zero points.`')


bot.run('MTY5NTYzNDIzMTkxOTkwMjcz.Vw1sPg.gcskCX61sDrKQV_08PAPQnCKiTo')

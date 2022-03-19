#!/usr/bin/env python

import discord
import json
import chess.svg
import re
from cairosvg import svg2png
from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions

intents = discord.Intents.all()
client = commands.Bot(command_prefix="c! ", intents=intents)
client.remove_command('help')

with open("/Users/benjamin/Documents/Developer/Python/ChessBot/.token.txt") as file:
    content = file.readlines()

TOKEN = content[0]

chess_unicode = {
    "k": "♔",
    "q": "♕",
    "r": "♖",
    "b": "♗",
    "n": "♘",
    "p": "♙",
    "K": "♚",
    "Q": "♛",
    "R": "♜",
    "B": "♝",
    "N": "♞",
    "P": "♟︎"
}


def save_file(settings, name):
    with open('/Users/benjamin/Documents/Developer/Python/ChessBot/{}.json'.format(name), 'w') as file:
        json.dump(settings, file, indent=4)


def get_file(name):
    with open('/Users/benjamin/Documents/Developer/Python/ChessBot/{}.json'.format(name), 'r') as file:
        return json.load(file)


def in_game(ctx):
    data = get_file('data')
    guild = str(ctx.guild.id)
    player = ctx.author.id
    playing = False
    for i in range(0, 3):
        if player == data[guild][str(i)]["p1"] or player == data[guild][str(i)]["p2"]:
            playing = True
            break
    return playing


def get_turn(ctx, game_num):
    data = get_file('data')
    guild = str(ctx.guild.id)
    return data[guild][str(game_num)]['turn']


async def send_board(ctx, game_num, this_board):
    data = get_file('data')
    guild = str(ctx.guild.id)
    fen = this_board.fen()
    board = chess.Board(fen)
    boardsvg = chess.svg.board(board=board)
    svg2png(bytestring=boardsvg, write_to='board.png')
    with open('board.png', "rb") as fh:
        f = discord.File(fh, filename='board.png')
    if this_board.turn:
        colour = "White"
    else:
        colour = "Black"
    await ctx.send("**{}'s Turn** - *{}*".format(
        ctx.guild.get_member(data[guild][str(game_num)][get_turn(ctx, game_num)]).display_name, colour), file=f)
    pieces_string = ""
    send = False
    if data[guild][str(game_num)]['scorew'] != "":
        pieces_string += "\n`White: {}`".format(data[guild][str(game_num)]['scorew'])
        send = True
    if data[guild][str(game_num)]['scoreb'] != "":
        pieces_string += "\n`Black: {}`".format(data[guild][str(game_num)]['scoreb'])
        send = True
    if send:
        await ctx.send(pieces_string)


@client.event
async def on_ready():
    data = get_file('data')
    for guild in client.guilds:
        if not str(guild.id) in data:
            temp = data
            temp_data = {
                guild.id: {
                    "channel": None,
                    "0": {"active": "0", "p1": None, "p2": None, "scoreb": "", "scorew": "", "turn": "p1", "fen": None},
                    "1": {"active": "0", "p1": None, "p2": None, "scoreb": "", "scorew": "", "turn": "p1", "fen": None},
                    "2": {"active": "0", "p1": None, "p2": None, "scoreb": "", "scorew": "", "turn": "p1", "fen": None}
                }
            }
            temp.update(temp_data)
            save_file(data, 'data')
    await client.change_presence(activity=discord.Game(name="c! help"))
    print("online")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.guild is None:
        embed = discord.Embed(title="Server Error", description="Please use me in a server")
        await message.channel.send(embed=embed)
        return
    data = get_file('data')
    if data[str(message.guild.id)]["channel"] == message.channel.id or data[str(message.guild.id)]["channel"] is None:
        await client.process_commands(message)


@client.command()
async def start(ctx):
    data = get_file('data')
    guild = str(ctx.guild.id)
    player = ctx.author.id
    if in_game(ctx):
        embed = discord.Embed(title="Start Error",
                              description="You are already in a game\nUse `c! end` to end your current game")
        await ctx.send(embed=embed)
        return
    max_games = True
    started_games = False
    game_number = 0
    for i in range(0, 3):
        if data[guild][str(i)]["active"] == "2":
            continue
        elif data[guild][str(i)]["active"] == "1":
            started_games = True
            continue
        else:
            max_games = False
            game_number = i
            data[guild][str(i)]["active"] = "1"
            data[guild][str(i)]["p1"] = player
            save_file(data, 'data')
            break
    if max_games and not started_games:
        embed = discord.Embed(title="Start Error", description="Maxinum number of games in play")
        embed.add_field(name="Active Games", value="<@!{}>` vs `<@!{}>\n<@!{}>` vs `<@!{}>\n<@!{}>` vs `<@!{}>".format(
            data[guild]["0"]["p1"], data[guild]["0"]["p2"],
            data[guild]["1"]["p1"], data[guild]["1"]["p2"],
            data[guild]["2"]["p1"], data[guild]["2"]["p2"]
        ))
        await ctx.channel.send(embed=embed)
        return
    elif max_games and started_games:
        embed = discord.Embed(title="Start Error", description="Maxinum number of games started")
        in_play = [
            "<@!{}>` vs `<@!{}>\n".format(data[guild]["0"]["p1"], data[guild]["0"]["p2"]),
            "<@!{}>` vs `<@!{}>\n".format(data[guild]["1"]["p1"], data[guild]["1"]["p2"]),
            "<@!{}>` vs `<@!{}>\n".format(data[guild]["2"]["p1"], data[guild]["2"]["p2"])
        ]
        for i in range(0, 3):
            if data[guild][str(i)]["active"] == "1":
                in_play[i] = ("<@!{}> would like to play chess, join them with `c! join `<@!{}>\n".format(
                    data[guild][str(i)]["p1"], data[guild][str(i)]["p1"]))
        embed.add_field(name="Started Games", value="".join(in_play))
        await ctx.send(embed=embed)
    embed = discord.Embed(title="Start", description="Game Started")
    embed.add_field(name="Join", value="<@!{}> would like to play chess, join them with `c! join `<@!{}>\n".format(
        data[guild][str(game_number)]["p1"], data[guild][str(game_number)]["p1"]))
    await ctx.send(embed=embed)


@client.command()
async def active(ctx):
    data = get_file('data')
    guild = str(ctx.guild.id)
    in_play = [
        "<@!{}>` vs `<@!{}>\n".format(data[guild]["0"]["p1"], data[guild]["0"]["p2"]),
        "<@!{}>` vs `<@!{}>\n".format(data[guild]["1"]["p1"], data[guild]["1"]["p2"]),
        "<@!{}>` vs `<@!{}>\n".format(data[guild]["2"]["p1"], data[guild]["2"]["p2"])
    ]
    for i in range(0, 3):
        if data[guild][str(i)]["active"] == "0":
            in_play[i] = "`Empty Game Slot`\n"
        elif data[guild][str(i)]["active"] == "1":
            in_play[i] = (
                "<@!{}> would like to play chess, join them with `c! join `<@!{}>\n".format(data[guild][str(i)]["p1"],
                                                                                            data[guild][str(i)]["p1"]))
    embed = discord.Embed(title="Started Games", description="".join(in_play))
    await ctx.send(embed=embed)


@client.command()
async def join(ctx, args):
    data = get_file('data')
    target = int(args[args.index("!") + 1: args.index(">", args.index("!"))])
    guild = str(ctx.guild.id)
    if in_game(ctx):
        embed = discord.Embed(title="Join Error",
                              description="You are already in a game\nUse `c! end` to end your current game")
        await ctx.send(embed=embed)
        return
    playing = False
    busy = -1
    game_num = -1
    this_board = chess.Board()
    for i in range(0, 3):
        if data[guild][str(i)]["p1"] == target:
            playing = True
            if data[guild][str(i)]["p2"] is not None:
                busy = i
                break
            game_num = i
            data[guild][str(game_num)]["active"] = "2"
            data[guild][str(game_num)]["p2"] = ctx.author.id
            data[guild][str(game_num)]['fen'] = this_board.fen()
            save_file(data, 'data')
            break
    if not playing:
        embed = discord.Embed(title="Join Error",
                              description="That person is not in a game\nStart a game with `c! start` or Use `c! active` to view active games")
        await ctx.send(embed=embed)
        return
    elif playing and busy != -1:
        embed = discord.Embed(title="Join Error",
                              description="That person is playing <@!{}>\nStart a game with `c! start` or Use `c! active` to view active games".format(
                                  data[guild][busy]["p2"]))
        await ctx.send(embed=embed)
        return
    embed = discord.Embed(title="Join", description="You successfully joined a game")
    await ctx.send(embed=embed)
    await send_board(ctx, game_num, this_board)


@client.command()
async def end(ctx):
    data = get_file('data')
    guild = str(ctx.guild.id)
    player = ctx.author.id
    for i in range(0, 3):
        if player == data[guild][str(i)]["p1"] or player == data[guild][str(i)]["p2"]:
            embed = discord.Embed(title="End", description="Your game was ended".format(data[guild][str(i)]["p2"]))
            data[guild][str(i)]["p1"] = None
            data[guild][str(i)]["p2"] = None
            data[guild][str(i)]["active"] = "0"
            data[guild][str(i)]["scorew"] = ""
            data[guild][str(i)]["scoreb"] = ""
            data[guild][str(i)]["turn"] = "p1"
            data[guild][str(i)]["fen"] = None
            await ctx.send(embed=embed)
            save_file(data, 'data')
            return
    embed = discord.Embed(title="End Error",
                          description="You are not in a game\nJoin or Start a game with `c! join [mention]` or `c! start`\nUse `c! active` to view active games")
    await ctx.send(embed=embed)


@client.command()
async def move(ctx, *args):
    data = get_file('data')
    guild = str(ctx.guild.id)
    player = ctx.author.id
    game_num = -1
    for i in range(0, 3):
        if player == data[guild][str(i)]["p1"] or player == data[guild][str(i)]["p2"]:
            game_num = i
    if game_num == -1:
        embed = discord.Embed(title="Move Error",
                              description="You are not in a game\nJoin or Start a game with `c! join [mention]` or `c! start`\nUse `c! active` to view active games")
        await ctx.send(embed=embed)
        return
    if data[guild][str(game_num)][get_turn(ctx, game_num)] != player:
        embed = discord.Embed(title="Move Error", description="It is not your turn")
        await ctx.send(embed=embed)
        return
    this_board = chess.Board(data[guild][str(game_num)]['fen'])
    move_string = "".join(args).replace(" ", "").lower()
    move_pattern = re.compile("^[a-h][1-8][a-h][1-8]")
    if move_pattern.match(move_string) is None:
        embed = discord.Embed(title="Move Error", description="Invalid Move\nMove must consist of [a-h][1-8][a-h][1-8]")
        await ctx.send(embed=embed)
        return
    move = chess.Move.from_uci(move_string)
    if not move in this_board.legal_moves:
        embed = discord.Embed(title="Move Error", description="Illegal Move")
        await ctx.send(embed=embed)
        return
    target_piece = str(this_board.piece_at(move.to_square))
    if target_piece != 'None':
        if target_piece.islower():
            data[guild][str(game_num)]['scorew'] += chess_unicode[target_piece]
        else:
            data[guild][str(game_num)]['scoreb'] += chess_unicode[target_piece]
    this_board.push(move)
    if this_board.is_checkmate():
        embed = discord.Embed(title="Game Over",
                              description="<@!{}> Wins".format(data[guild][str(game_num)][get_turn(ctx, game_num)]))
        await ctx.send(embed=embed)
        await end(ctx)
        return
    elif this_board.is_stalemate():
        embed = discord.Embed(title="Game Over", description="Stalemate - Draw")
        await ctx.send(embed=embed)
        await end(ctx)
        return
    elif this_board.is_insufficient_material():
        embed = discord.Embed(title="Game Over", description="Insufficient Material - Draw")
        await ctx.send(embed=embed)
        await end(ctx)
        return
    elif this_board.is_check():
        embed = discord.Embed(title="Check!")
        await ctx.send(embed=embed)
    if get_turn(ctx, game_num) == "p1":
        data[guild][str(game_num)]['turn'] = "p2"
    elif get_turn(ctx, game_num) == "p2":
        data[guild][str(game_num)]['turn'] = "p1"
    data[guild][str(game_num)]['fen'] = this_board.fen()
    save_file(data, 'data')
    await send_board(ctx, game_num, this_board)


@client.command()
async def board(ctx):
    data = get_file('data')
    guild = str(ctx.guild.id)
    player = ctx.author.id
    if not in_game(ctx):
        embed = discord.Embed(title="Board Error",
                              description="You are not in a game\nJoin or Start a game with `c! join [mention]` or `c! start`\nUse `c! active` to view active games")
        await ctx.send(embed=embed)
        return
    game_num = -1
    for i in range(0, 3):
        if player == data[guild][str(i)]["p1"] or player == data[guild][str(i)]["p2"]:
            game_num = i
    this_board = chess.Board(data[guild][str(game_num)]['fen'])
    await send_board(ctx, game_num, this_board)


@client.command()
async def pieces(ctx):
    data = get_file('data')
    guild = str(ctx.guild.id)
    player = ctx.author.id
    if not in_game(ctx):
        embed = discord.Embed(title="Pieces Error",
                              description="You are not in a game\nJoin or Start a game with `c! join [mention]` or `c! start`\nUse `c! active` to view active games")
        await ctx.send(embed=embed)
        return
    game_num = -1
    for i in range(0, 3):
        if player == data[guild][str(i)]["p1"] or player == data[guild][str(i)]["p2"]:
            game_num = i
    embed = discord.Embed(title="Pieces")
    send = False
    if data[guild][str(game_num)]['scorew'] != "":
        embed.add_field(name="White has taken", value="`{}`".format(data[guild][str(game_num)]['scorew']), inline=True)
        send = True
    if data[guild][str(game_num)]['scoreb'] != "":
        embed.add_field(name="Black has taken", value="`{}`".format(data[guild][str(game_num)]['scoreb']), inline=True)
        send = True
    if send:
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Pieces", description="No pieces have been taken yet")
        await ctx.send(embed=embed)


@client.command()
@commands.has_permissions(manage_guild=True)
async def channel(ctx, args):
    data = get_file('data')
    guild = str(ctx.guild.id)
    target = int(args[args.index("#") + 1: args.index(">", args.index("#"))])
    data[guild]["channel"] = target
    save_file(data, 'data')
    embed = discord.Embed(title="Set Channel",
                          description="Chess channel has now been set to <#{}>\nI can only be used in this channel, to change this type `c! channel [channel_mention]`".format(
                              target))
    await ctx.send(embed=embed)


@client.command()
async def help(ctx):
    embed = discord.Embed(title="Help", description="List of commands for ChessBot")
    embed.add_field(name="channel", value="Set the chess channel", inline=False)
    embed.add_field(name="start", value="Start a game", inline=False)
    embed.add_field(name="active", value="Shows a list of all active games", inline=False)
    embed.add_field(name="join [mention]", value="Join an active game", inline=False)
    embed.add_field(name="move [piece_location] [location]", value="Move piece at a location to another location",
                    inline=False)
    embed.add_field(name="board", value="Display the board", inline=False)
    embed.add_field(name="pieces", value="Display the pieces taken", inline=False)
    embed.add_field(name="end", value="End the game you're currently in", inline=False)
    embed.add_field(name="debug", value="Display all internal game data", inline=False)
    embed.set_footer(text="Bot coded by Ben Norton")
    await ctx.send(embed=embed)


@client.command()
async def debug(ctx):
    data = get_file('data')
    guild = str(ctx.guild.id)
    player = ctx.author.id
    game_num = -1
    for i in range(0, 3):
        if player == data[guild][str(i)]["p1"] or player == data[guild][str(i)]["p2"]:
            game_num = i
    this_board = chess.Board(data[guild][str(game_num)]["fen"])
    await ctx.send("`{}\n{}`".format(data[guild][str(game_num)], this_board))


@channel.error
async def channel_error(ctx, error):
    if isinstance(error, MissingPermissions):
        embed = discord.Embed(title="Channel Error",
                              description="You do not have permission to set the chess channel\nYou must have the `Manage Server` permission")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Channel Error", description="Incorrect Usage")
        embed.add_field(name="Usage", value="`c! channel [channel_mention]`")
        await ctx.send(embed=embed)


@join.error
async def join_error(ctx, error):
    embed = discord.Embed(title="Join Error", description="Incorrect Usage")
    embed.add_field(name="Usage", value="`c! join [mention]`\nFind active games with `c! active`")
    await ctx.send(embed=embed)
    print(error)


client.run(TOKEN)

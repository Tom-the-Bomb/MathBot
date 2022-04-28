from typing import Optional

import Discord_Games as games
from Discord_Games import button_games

import discord
from discord.ext import commands

from ..context import MathContext
from ..bot import MathBot

class Games(commands.Cog):

    def __init__(self, bot: MathBot) -> None:
        self.bot = bot
        self.twenty_48_emojis: dict[str, str] = {
            "0":    "<:grey:821404552783855658>", 
            "2":    "<:twoo:821396924619161650>", 
            "4":    "<:fourr:821396936870723602>", 
            "8":    "<:eightt:821396947029983302>", 
            "16":   "<:sixteen:821396959616958534>", 
            "32":   "<:thirtytwo:821396969632169994>", 
            "64":   "<:sixtyfour:821396982869524563>", 
            "128":  "<:onetwentyeight:821396997776998472>",
            "256":  "<:256:821397009394827306>",
            "512":  "<:512:821397040247865384>",
            "1024": "<:1024:821397097453846538>",
            "2048": "<:2048:821397123160342558>",
            "4096": "<:4096:821397135043067915>",
            "8192": "<:8192:821397156127965274>",
        }

    @commands.command(name="connect4", aliases=["c4"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def connect4(self, ctx: MathContext, member: discord.Member):
        game = games.ConnectFour(
            red  = ctx.author,         
            blue = member,             
        )
        await game.start(ctx)
    
    @commands.command(name="tictactoe", aliases=["ttt"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def tictactoe(self, ctx: MathContext, member: discord.Member):
        game = button_games.BetaTictactoe(
            cross  = ctx.author, 
            circle = member
        )
        await game.start(ctx)

    @commands.command(name="hangman")
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def hangman(self, ctx: MathContext):
        game = button_games.BetaHangman()
        await game.start(ctx)

    @commands.command(name="chess")
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def chess(self, ctx: MathContext, member: discord.Member):
        game = games.Chess(
            white = ctx.author, 
            black = member
        )
        await game.start(ctx, timeout=60, add_reaction_after_move=True)

    @commands.command(name="twenty48", aliases=["2048"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def twenty48(self, ctx: MathContext):
        game = button_games.BetaTwenty48(self.twenty_48_emojis)
        await game.start(ctx, delete_button=True)

    @commands.command(name="guess", aliases=["aki", "guesscharacter", "characterguess", "akinator"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def guess(self, ctx: MathContext):
        async with ctx.typing():
            game = button_games.BetaAkinator()
            await game.start(ctx, timeout=120, delete_button=True)

    @commands.command(name="typerace", aliases=["tr"])
    @commands.max_concurrency(2, commands.BucketType.channel)
    async def typerace(self, ctx: MathContext):

        game = games.TypeRacer()
        await game.start(
            ctx, 
            embed_color=ctx.bot.color,
            timeout=30,
        )

    @commands.command(name="battleship", aliases=["bs"])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def _battleship(self, ctx: MathContext, member: discord.Member):
        game = games.BattleShip(ctx.author, member)
        await game.start(ctx)

    @commands.command(name="wordle", aliases=["wd"])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def _worldle(self, ctx: MathContext):
        game = button_games.BetaWordle(color=ctx.bot.color)
        await game.start(ctx)

    @commands.command(name="memory-game", aliases=["mem"])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def _memory_game(self, ctx: MathContext):
        game = button_games.MemoryGame()
        await game.start(ctx)

    @commands.command(name="rockpaperscissors", aliases=["rps"])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def _rps(self, ctx: MathContext, member: Optional[discord.Member] = None):
        game = button_games.BetaRockPaperScissors(member)
        await game.start(ctx)

    @commands.command(name="reaction", aliases=["react"])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def reaction(self, ctx: MathContext):
        game = button_games.BetaReactionGame()
        await game.start(ctx)

async def setup(bot: MathBot) -> None:
    await bot.add_cog(Games(bot))
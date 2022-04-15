from typing import Any

import discord
from discord.ext import commands

class MathContext(commands.Context):

    async def reply(self, content: Any = None, **kwargs) -> discord.Message:
        mention_author = kwargs.pop('mention_author', False)
        return await super().reply(content, mention_author=mention_author, **kwargs)
from __future__ import annotations

from typing import Any, TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from .bot import MathBot

class MathContext(commands.Context['MathBot']):

    async def reply(self, content: Any = None, **kwargs) -> discord.Message:
        mention_author = kwargs.pop('mention_author', False)
        return await super().reply(content, mention_author=mention_author, **kwargs)
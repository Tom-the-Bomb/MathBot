from typing import Awaitable, Optional, Callable, TypeVar, ParamSpec, TypeAlias
import functools
import asyncio

import discord

__all__: tuple[str, ...] = (
    'Number',
    'NUM_PAT',
    'num',
    'to_thread',
    'truncate',
    'AuthorOnlyView',
)

P = ParamSpec('P')
T = TypeVar('T')

Number: TypeAlias = int | float
NUM_PAT = r'[-+]?\d+\.?\d*'

def num(n: str) -> Number:
    n = float(n)
    if n.is_integer():
        n = int(n)
    return n

def to_thread(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Awaitable[T]:
        return asyncio.to_thread(func, *args, **kwargs)

    return wrapper

def truncate(content: str, limit: int = 2000) -> str:
    if len(content) > limit:
        return content[:1997] + '...'
    else:
        return content

class AuthorOnlyView(discord.ui.View):

    def __init__(self, author: discord.User, *, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(f'This interaction can only be used by {self.author.mention}', ephemeral=True)
            return False
        else:
            return True
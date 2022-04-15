from typing import Any, Optional, ClassVar
import os
import json

import logging

import discord
from discord.ext import commands

from aiohttp import ClientSession, MultipartWriter

from .context import MathContext

class MathBot(commands.Bot):
    color: ClassVar[int] = 0x2F3136

    def __init__(self, **kwargs):

        self.load_config()
        self._default_prefixes: list[str] = self.config['DEFAULT_PREFIXES']
        
        super().__init__(
            command_prefix=commands.when_mentioned_or(*self._default_prefixes), 
            description='A basic bot for aquarists',
            intents=discord.Intents.all(),
            case_insensitive=True, 
            status=discord.Status.idle,
            activity=discord.Game('beep boop'),
            **kwargs
        )

        self.session: Optional[ClientSession] = None

        self._token:  str = self.config['TOKEN']

        logger = logging.getLogger('discord')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()

        handler.setFormatter(
            logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        )

        logger.addHandler(handler)
        self._logger: logging.Logger = logger

        self._logger.info('--- INITIALIZED ---')

        return

    def load_config(self) -> None:
        with open('config.json') as config:
            self.config: dict[str, Any] = json.load(config)

    def run(self, *args, **kwargs) -> None:
        token: str = kwargs.pop('token', self._token)
        return super().run(token, *args, **kwargs)
    
    async def load_all_cogs(self, *, jishaku: bool = True) -> None:

        if jishaku:
            await self.load_extension('jishaku')

        for ext in os.listdir('./bot/ext'):
            if not ext.endswith(".py"):
                continue

            await self.load_extension('bot.ext.' + ext[:-3])
        return None

    async def on_connect(self) -> None:
        self._logger.info('bot is connected')

    async def on_ready(self) -> None:
        self._logger.info('bot is ready')

    async def start(self, *args, **kwargs) -> None:
        self.session = ClientSession()
        
        await self.load_all_cogs()
        return await super().start(*args, **kwargs)

    async def close(self) -> None:
        await self.session.close()
        return await super().close()

    async def get_context(self, message: discord.Message, *, cls: type = MathContext):
        return await super().get_context(message, cls=cls)

    async def post_mystbin(self, code: str, *, language: Optional[str] = None) -> str:
        MYSTBIN_URL = 'https://mystb.in/api/pastes'

        payload = MultipartWriter()
        content = payload.append(code)
        content.set_content_disposition('form-data', name='data')

        meta = {'index': 0}

        if language:
            meta['syntax'] = language

        content = payload.append_json(
            {'meta': [meta]}
        )

        content.set_content_disposition("form-data", name='meta')

        async with self.session.post(MYSTBIN_URL, data=payload) as r:
            if r.ok:
                data = await r.json()
                paste = 'https://mystb.in/' + data['pastes'][0]['id']
                return paste

    async def on_command_error(self, ctx: MathContext, error: Exception) -> None:

        if isinstance(error, commands.CommandNotFound):
            return
        
        await ctx.send(error)
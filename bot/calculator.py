from __future__ import annotations

from typing import ClassVar
import re

import discord

from .utils import *
from .context import MathContext

NUM_PAT = r'\d+\.?\d*'

class Calculator:
    operators: ClassVar[tuple[str, ...]] = ("/", "*", "-", "+")    
       
    def __init__(self, expression: str) -> None:
        self.expression = expression

    def __str__(self) -> str:
        def recur(op) -> None:
            self.sub_regex(op)
            if re.search(fr"(-?{NUM_PAT}\{op}-?{NUM_PAT})", self.expression):
                recur(op)

        for op in self.operators:
            if re.search(fr"(-?{NUM_PAT}\{op}-?{NUM_PAT})", self.expression):
                recur(op)
        return self.expression

    def sub_regex(self, operator: str) -> None:
        def sub_fn(v) -> str:
            x, y = v.group().split(operator)
            x, y = num(x), num(y)
            conv = {
                "/": lambda x, y: x/y,
                "*": lambda x, y: x*y,
                "-": lambda x, y: x-y,
                "+": lambda x, y: x+y,
            }   
            return str(conv.get(operator)(x, y))
        try:
            self.expression = re.sub(
                fr"(-?{NUM_PAT}\{operator}-?{NUM_PAT})", sub_fn, self.expression
            )
        except TypeError:
            pass

class CalcButton(discord.ui.Button):

    view: CalculatorView
    SYMBOL_CONV = {
        '×': '*',
        '÷': '/',
    }
    
    def __init__(self, label: str, *, style: discord.ButtonStyle = discord.ButtonStyle.grey, row: int, custom_id: str = None):
        super().__init__(style=style, label=str(label), row=row, custom_id=custom_id)

    async def edit(self, interaction: discord.Interaction, *, error: bool = False) -> discord.Message:
        content = 'ERROR' if error else self.view.expression
        content = content or '\u200b'
        content += ' ' * (40 - len(content))
        embed = discord.Embed(description=f'```ansi\n\u001b[0;32m{content}\n```', color=self.view.ctx.bot.color)
        return await interaction.response.edit_message(embed=embed)

    async def callback(self, interaction: discord.Interaction):

        if self.label == '=':
            try:
                result = str(Calculator(self.view.expression))
                self.view.expression = result
                return await self.edit(interaction)
            except Exception:
                return await self.edit(interaction, error=True)

        elif self.label == 'ⓘ':
            embed = discord.Embed(title='Simple Calculator', color=self.view.ctx.bot.color)
            embed.description = (
                '• A simple calculator, for performing simple arithmetic operations\n'
                '• such operations include: `+` `-` `×` `÷`\n'
                '• Press the buttons to enter numbers and operators\n'
                '• Hit `=` to evaluate the entered expression\n'
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        elif self.label == 'C':
            self.view.expression = ''
            return await self.edit(interaction)

        elif self.label == '⌫':
            self.view.expression = self.view.expression[:-1]
            return await self.edit(interaction)

        elif self.label == 'Close':
            return await interaction.message.delete()

        else:
            term = self.SYMBOL_CONV.get(self.label, self.label)
            self.view.expression += term
            return await self.edit(interaction)

class CalculatorView(AuthorOnlyView):

    BUTTONS: ClassVar[tuple[tuple[int | str, ...], ...]] = (
        (1, 2, 3, '+', '⌫'),
        (4, 5, 6, '-', 'C'),
        (7, 8, 9, '×', 'Close'),
        ('.', '0', '=', '÷', 'ⓘ'),
    )

    def __init__(
        self, 
        ctx: MathContext, 
        author: discord.User, *, 
        timeout: float = None
    ) -> None:

        super().__init__(author, timeout=timeout)

        self.ctx = ctx
        self.expression: str = ''

        for i, row in enumerate(self.BUTTONS):
            for button in row:
                style = (
                    discord.ButtonStyle.green if button == '=' else
                    discord.ButtonStyle.blurple if button in ('+', '-', '×', '÷') else
                    discord.ButtonStyle.red if button in ('⌫', 'C', 'Close', 'ⓘ') else
                    discord.ButtonStyle.gray
                )
                
                item = CalcButton(button, style=style, row=i)
                if button == '\u200b':
                    item.disabled = True

                self.add_item(item)
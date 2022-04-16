from __future__ import annotations

from typing import Optional, ClassVar

from io import BytesIO
from enum import Enum
import re

import discord
from discord.ext import commands

import aiohttp
import numpy as np

import matplotlib
matplotlib.use('agg')
from matplotlib import pyplot as plt

from ..utils import *
from ..bot import MathBot
from ..context import MathContext

LATEX_URL = 'https://latex.codecogs.com/png.latex?%5Cdpi%7B300%7D%20%5Chuge%20'

INSTRUCTIONS_2STEP = (
    '• Solves a **2** step linear equation\n'
    '• with the format: `y = mx + b`'
)

INSTRUCTIONS_3STEP = (
    '• Solves a **3** step linear equation\n'
    '• with the format: `y = x(a + b) / (c + d)`'
)

class Etype(Enum):
    linear2 = '2 Step Linear'
    linear3 = '3 Step Linear'
    quadratic = 'Quadratic'

def eq_from_etype(etype: Etype) -> str:
    return 'y=mx+b' if etype == Etype.linear2 else r'y=\frac{x(a+b)}{c+d}'

def em_from_etype(etype: Etype, color: int | discord.Color = None) -> discord.Embed:
    inst = INSTRUCTIONS_2STEP if etype == Etype.linear2 else INSTRUCTIONS_3STEP
    embed = discord.Embed(title=f'{etype.value} Equation Solver', description=inst, color=color)
    return embed

async def render_latex(session: aiohttp.ClientSession, latex: str) -> discord.File:
    url = LATEX_URL + r'{\color{white}' + latex + r'}'
    try:
        async with session.get(url) as r:
            buffer = BytesIO(await r.read())
            return discord.File(buffer, 'equation.png')
    except RecursionError as e:
        raise e
    except Exception:
        return await render_latex(session, latex)

@to_thread
def linear_graph(m: Number, b: Number, x: Number, y: Number) -> BytesIO:

    plt.style.use(["fast", "fivethirtyeight", "ggplot"])
    plt.style.use("bmh")
    buffer = BytesIO()
    
    lim = abs(x) * 3
    x_ = np.linspace(-lim, lim, 100)
    y_  = [(m * i + b) for i in x_]

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.spines['left'].set_position('center')
    ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    plt.plot(x,y, 'r')
    plt.plot(x_, y_)
    plt.plot(x, y, marker='o')
    plt.savefig(buffer)
    plt.close()

    buffer.seek(0)
    return buffer

class EquationSolver:

    def __init__(self, equation: str = None, *, etype: Etype, **variables: dict[str, Number]) -> None:
        self.equation = equation
        self.etype = etype

        VALID_VARS = ('m', 'a', 'b', 'c', 'd', 'y')
        if any(var not in VALID_VARS for var in variables.keys()):
            raise TypeError('Inapproporite keyword argument names')

        self.variables = variables
        
        assert self.equation or self.variables
        
    def evaluate(self) -> Optional[tuple[Number, Number, Number, Number, str]]:
        
        if self.etype == Etype.linear2:

            if not (
                (m := num(self.variables.get('m', 0))) and 
                (b := num(self.variables.get('b', 0))) and 
                (y := num(self.variables.get('y', 0)))
            ):
                if terms := re.match(fr'({NUM_PAT})(=)({NUM_PAT})\*?(x)(\+|-)({NUM_PAT})', self.equation):
                    y = num(terms.group(1))
                    m = num(terms.group(3))
                    op = terms.group(5)
                    b = num(terms.group(6))
                    b = -b if op == '-' else b
                else:
                    raise InvalidEquation()
            
            mx = y - b
            x = mx / m

            steps = (
                f'{self.equation or f"{y} = {m}𝑥 + {b}"}\n'+
                (
                    f'{m}𝑥 = {y} - {b}\n' if b > 0 else 
                    f'{m}𝑥 = {y} + {abs(b)}\n' if b < 0 else 
                    f'{m}𝑥 = {y}\n'
                ) +
                f'𝑥 = {mx} / {m}\n'+
                f'𝑥 = {x}'
            )
            return m, b, x, y, steps
            
        elif self.etype == Etype.linear3:

            if not (
                (a := num(self.variables.get('a', 0))) and 
                (b := num(self.variables.get('b', 0))) and 
                (c := num(self.variables.get('c', 0))) and
                (d := num(self.variables.get('d', 0))) and 
                (y := num(self.variables.get('y', 0)))
            ):
                if terms := re.match(fr'({NUM_PAT})=x\*?\(({NUM_PAT})(\+|-)({NUM_PAT})\)/\(({NUM_PAT})(\+|-)({NUM_PAT})', self.equation):

                    y = num(terms.group(1))

                    a = num(terms.group(2))
                    op1 = terms.group(3)
                    b = num(terms.group(4))
                    b = -b if op1 == '-' else b

                    c = num(terms.group(5))
                    op2 = terms.group(6)
                    d = num(terms.group(7))
                    d = -d if op2 == '-' else d
                else:
                    raise InvalidEquation()
            
            ab =  a + b
            cd = c + d
            xab = y * cd
            x = xab / ab
            
            steps = (
               f'{self.equation or f"{y} = 𝑥({a} + {b}) / ({c} + {d})"}\n'+
               f'{y} = {ab}𝑥 / ({cd})\n'+
               f'{ab}𝑥 = {y} * {cd}\n'+
               f'{ab}𝑥 = {xab}\n'+
               f'𝑥 = {xab} / {ab}\n'+
               f'𝑥 = {x}\n'
            )
            return ab, 0, x, xab, steps # m, b, x, y, steps

class ManualButton(discord.ui.Button):

    view: ManualModeView
    SYMBOL_CONV = {'𝑥': 'x'}
    
    def __init__(self, label: str, *, style: discord.ButtonStyle = discord.ButtonStyle.grey, row: int):
        super().__init__(style=style, label=str(label), row=row)

    async def edit(self, interaction: discord.Interaction, *, error: bool = False) -> discord.Message:
        content = 'Invalid Equation' if error else self.view.equation
        content = content or '\u200b'
        content += ' ' * (40 - len(content))
        embed = discord.Embed(description=f'```ansi\n\u001b[0;32m{content}\n```', color=self.view.ctx.bot.color)
        return await interaction.response.edit_message(embed=embed)

    async def callback(self, interaction: discord.Interaction):

        if self.label == 'Enter':
            try:
                results = EquationSolver(self.view.equation, etype=self.view.etype).evaluate()
                steps = results[-1]
                graph = await linear_graph(*results[:-1])
                graph = discord.File(graph, 'graph.png')

                embed = discord.Embed(
                    title='Solution:',
                    description=f'```py\n{steps}\n```',
                    color=self.view.ctx.bot.color
                )
                embed.set_image(url='attachment://graph.png')

                return await interaction.response.edit_message(embed=embed, attachments=[graph], view=None)
            except InvalidEquation:
                return await self.edit(interaction, error=True)
            except Exception as e:
                return await interaction.response.send_message(
                    content=f'Oops! An error occured: `{e}`'
                )

        elif self.label == 'ⓘ':
            eq_format = 'y = mx + b' if self.view.etype == Etype.linear2 else 'y = x(a + b) / (c + d)'
            embed = discord.Embed(title='Equation Solver - Manual Mode', color=self.view.ctx.bot.color)
            embed.description = (
                '• Equation Solver\n'
                f'• Solves a {self.view.etype.value} Equation\n'
                '• Press the buttons to enter numbers and operators\n'
                f'• Enter the equation in the format of `{eq_format}`\n'
                '• Hit `Enter` to evaluate the entered expression\n'
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        elif self.label == 'C':
            self.view.equation = ''
            return await self.edit(interaction)

        elif self.label == '⌫':
            self.view.equation = self.view.expression[:-1]
            return await self.edit(interaction)

        elif self.label == 'Close':
            return await interaction.message.delete()

        else:
            term = self.SYMBOL_CONV.get(self.label, self.label)
            self.view.equation += term
            return await self.edit(interaction)

class ManualModeView(AuthorOnlyView):

    BUTTONS: ClassVar[tuple[tuple[int | str, ...], ...]] = (
        (1, 2, 3, '+', '⌫'),
        (4, 5, 6, '-', 'C'),
        (7, 8, 9, '𝑥', 'Close'),
        ('.', '0', '=', 'Enter', 'ⓘ'),
    )

    def __init__(
        self, 
        ctx: MathContext, 
        author: discord.User, *,
        etype: Etype,
        timeout: float = None
    ) -> None:

        super().__init__(author, timeout=timeout)

        self.ctx = ctx
        self.etype = etype
        self.equation: str = ''

        for i, row in enumerate(self.BUTTONS):
            for button in row:
                style = (
                    discord.ButtonStyle.green if button == 'Enter' else
                    discord.ButtonStyle.blurple if button in ('+', '-', '𝑥') else
                    discord.ButtonStyle.red if button in ('⌫', 'C', 'Close', 'ⓘ') else
                    discord.ButtonStyle.gray
                )
                
                item = ManualButton(button, style=style, row=i)
                self.add_item(item)

class VarInput(discord.ui.Modal, title='Variable Input'):
    
    def __init__(self, variable: str, button: VarButton) -> None:
        super().__init__()
        
        self.variable = variable
        self.button = button
        
        self.value = discord.ui.TextInput(
            label=f'What do you want the value of {self.variable} to be?', 
            style=discord.TextStyle.short,
            required=True,
        )
        self.add_item(self.value)
        
    async def on_submit(self, interaction: discord.Interaction) -> None:
        value = self.value.value
        try:
            float(value)
        except ValueError:
            return await interaction.response.send_message('Value must be a number!, try again', ephemeral=True)
        else:
            self.button.value = num(value)
            self.button.view.equation_vars[self.button.label] = value
            
            etype = self.button.view.etype
            
            embed = em_from_etype(etype, color=self.button.view.ctx.bot.color)
        
            remove_latex = self.button.view.latex_eq.replace(r'\frac', '\u0000')
            remove_latex = remove_latex.replace(self.variable, value)
            self.button.view.latex_eq = remove_latex.replace('\u0000', r'\frac')

            img = await render_latex(self.button.view.ctx.bot.session, self.button.view.latex_eq)
            embed.set_image(url='attachment://equation.png')

            self.button.disabled = True

            if all(child.disabled for child in self.button.view.children[:5]):
                self.button.view.children[-1].disabled = False

            return await interaction.response.edit_message(embed=embed, attachments=[img], view=self.button.view)
            
class VarButton(discord.ui.Button):

    view: EquationView
    value: Number

    def __init__(self, label: str, *, style: discord.ButtonStyle = discord.ButtonStyle.blurple, row: int = None):
        super().__init__(style=style, label=str(label))

    async def callback(self, interaction: discord.Interaction):

        if self.label == 'Enter':
            results = EquationSolver(etype=self.view.etype, **self.view.equation_vars).evaluate()
            steps = results[-1]
            graph = await linear_graph(*results[:-1])
            graph = discord.File(graph, 'graph.png')

            embed = discord.Embed(
                title='Solution:',
                description=f'```py\n{steps}\n```',
                color=self.view.ctx.bot.color
            )
            embed.set_image(url='attachment://graph.png')

            return await interaction.response.edit_message(embed=embed, attachments=[graph], view=None)
        elif self.label == 'manual mode':
            ctx = self.view.ctx
            spaces = ' ' * 40
            embed = discord.Embed(description=f'```py\n\u200b{spaces}\u200b\n```', color=self.view.ctx.bot.color)
            return await interaction.response.edit_message(
                embed=embed, 
                attachments=[],
                view=ManualModeView(ctx, ctx.author, etype=self.view.etype, timeout=300)
            )
        else:
            return await interaction.response.send_modal(VarInput(self.label, self))

class EquationView(AuthorOnlyView):

    def __init__(
        self, 
        ctx: MathContext, 
        author: discord.User, *, 
        etype: Etype,
        timeout: float = None
    ) -> None:

        super().__init__(author, timeout=timeout)

        self.ctx = ctx
        self.etype = etype

        self.equation_vars: dict[str, Number] = {}
        self.latex_eq = eq_from_etype(etype)

        inputs = ('y', 'm', 'b') if self.etype == Etype.linear2 else ('y', 'a', 'b', 'c', 'd')

        for var in inputs:
            self.add_item(VarButton(var))

        if (amt := len(self.children)) < 5:
            for _ in range(5 - amt):
                blank = VarButton('\u200b', style=discord.ButtonStyle.gray)
                blank.disabled = True
                self.add_item(blank)

        self.add_item(VarButton('manual mode', style=discord.ButtonStyle.red, row=1))

        enter = VarButton('Enter', style=discord.ButtonStyle.green, row=1)
        enter.disabled = True
        self.add_item(enter)

class EquationSelect(discord.ui.Select):

    view: SelectView

    def __init__(self, bot: MathBot) -> None:

        options = [
            discord.SelectOption(value=Etype.linear2.name, label='2 step linear equation'),
            discord.SelectOption(value=Etype.linear3.name, label='3 step linear equation'), 
        ]

        super().__init__(
            placeholder='Select a type of equation to solve',
            min_values=1,
            max_values=1,
            options=options,
        )

        self.bot = bot

    async def callback(self, interaction: discord.Interaction) -> None:
        
        etype = Etype[self.values[0]]

        equation = eq_from_etype(etype)
        embed = em_from_etype(etype, self.view.ctx.bot.color)
        img = await render_latex(self.bot.session, equation)
        embed.set_image(url='attachment://equation.png')

        view = EquationView(self.view.ctx, self.view.author, etype=etype, timeout=300)
        return await interaction.response.edit_message(embed=embed, attachments=[img], view=view)

class SelectView(AuthorOnlyView):

    def __init__(
        self, 
        ctx: MathContext, 
        author: discord.User, *,
        timeout: float = None
    ) -> None:

        super().__init__(author, timeout=timeout)

        self.ctx = ctx
        self.add_item(EquationSelect(self.ctx.bot))

class EquationsCog(commands.Cog):
    
    def __init__(self, bot: MathBot) -> None:
        self.bot = bot

    @commands.command(name='equation', aliases=['eq'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def solve_equation(self, ctx: MathContext) -> discord.Message:
        embed = discord.Embed(
            title='Equation Solver',
            color=self.bot.color
        )
        return await ctx.send(embed=embed, view=SelectView(ctx, ctx.author, timeout=300))

async def setup(bot: MathBot) -> None:
    await bot.add_cog(EquationsCog(bot))
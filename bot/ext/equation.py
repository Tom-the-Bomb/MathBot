from __future__ import annotations

from typing import Optional, ClassVar

from io import BytesIO
from enum import Enum
import re
import math
import cmath

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
    '• with the format: `y = mx + b`\n'
)

INSTRUCTIONS_3STEP = (
    '• Solves a **3** step linear equation\n'
    '• with the format: `e = x(a + b) / (c + d)`\n'
)

INSTRUCTIONS_ABCD = (
    '• Solves the formula `(a + b * c) / d`\n'
    '• with the provided values for a, b, c and d\n'
)

INSTRUCTIONS_QUAD = (
    '• Solves a quadratic equation\n'
    '• with the format: `ax^2 + bx + c`\n'
)

END = '• Press each blue button to input the desired values for each variable in the equation\n'

class Etype(Enum):
    linear2 = {
        'name': '2 Step Linear',
        'latex': 'y=mx+b',
        'instructions': INSTRUCTIONS_2STEP + END,
        'equation': 'y = mx + b',
        'vars': ('y', 'm', 'b'),
        'buttons': (
            (1, 2, 3, '+', '⌫'),
            (4, 5, 6, '-', 'C'),
            (7, 8, 9, '𝑥', 'Close'),
            ('.', '0', '=', 'Enter', 'ⓘ'),
        )
    }
    linear3 = {
        'name': '3 Step Linear',
        'latex': r'y=\frac{x(a+b)}{c+d}',
        'instructions': INSTRUCTIONS_3STEP + END,
        'equation': 'y = mx + b',
        'vars': ('y', 'a', 'b', 'c', 'd'),
        'buttons': (
            (1, 2, 3, '+', '𝑥'),
            (4, 5, 6, '-', '('),
            (7, 8, 9, '÷', ')'),
            ('.', '0', '=', '\u200b', '\u200b'),
            ('Enter', '⌫', 'C', 'Close', 'ⓘ'),
        )
    }
    abcdformula = {
        'name': '`(a + b * c) / d`',
        'latex': r'\frac{a+b\times%20c}{d}',
        'instructions': INSTRUCTIONS_ABCD + END,
        'equation': 'y = mx + b',
        'vars': ('a', 'b', 'c', 'd'),
        'buttons': (
            (1, 2, 3, '+', '𝑥'),
            (4, 5, 6, '-', '('),
            (7, 8, 9, '×', ')'),
            ('.', '0', '=', '÷', '\u200b'),
            ('Enter', '⌫', 'C', 'Close', 'ⓘ'),
        )
    }
    quadratic = {
        'name': 'Quadratic',
        'latex': 'y=ax^2+bx+c',
        'instructions': INSTRUCTIONS_QUAD + END,
        'equation': 'y = mx + b',
        'vars': ('y', 'a', 'b', 'c'),
        'buttons': (
            (1, 2, 3, '+', '⌫'),
            (4, 5, 6, '-', 'C'),
            (7, 8, 9, '𝑥', 'Close'),
            ('.', '0', '=', '☐²', 'Enter'),
            ('ⓘ', '\u200b', '\u200b', '\u200b', '\u200b')
        )
    }

def em_from_etype(etype: Etype, color: int | discord.Color = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"{etype.value['name']} Equation Solver", 
        description=etype.value['instructions'],
        color=color
    )
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
def plot_graph(*, etype: Etype, **variables: dict[str, Number]) -> BytesIO:

    plt.style.use(["fast", "fivethirtyeight", "ggplot"])
    plt.style.use("bmh")
    buffer = BytesIO()

    x = variables.get('x')
    y = variables.get('y')
    
    if isinstance(x, tuple):
        lim = abs(x[-1]) * 3
    else:
        lim = abs(x) * 3

    x_ = np.linspace(-lim, lim, 100)

    if etype in (Etype.linear2, Etype.linear3):
        m = variables.get('m')
        b = variables.get('b')
        y_  = [(m * i + b) for i in x_]
    elif etype == Etype.quadratic:
        a = variables.get('a')
        b = variables.get('b')
        c = variables.get('c')
        y_  = [(a * i ** 2 + b * i + c) for i in x_]

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.spines['left'].set_position('center')
    ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    plt.plot(x_, y_)
    
    if isinstance(x, tuple):
        for root in x:
            plt.plot(root, y, marker='o')
    else:
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
        
    def evaluate(self) -> Optional[dict[str, Number | str] | str]:
        
        if self.etype == Etype.linear2:

            if (
                (m := self.variables.get('m')) is not None and 
                (b := self.variables.get('b')) is not None and 
                (y := self.variables.get('y')) is not None
            ):
                m, b, y = num(m), num(b), num(y)
            else:
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
            return {
                'm': m, 
                'b': b,
                'x': x,
                'y': y,
                'steps': steps
            }
            
        elif self.etype == Etype.linear3:

            if (
                (a := self.variables.get('a')) is not None and 
                (b := self.variables.get('b')) is not None and 
                (c := self.variables.get('c')) is not None and
                (d := self.variables.get('d')) is not None and 
                (y := self.variables.get('y')) is not None
            ):
                a, b, c, d, y = num(a), num(b), num(c), num(d), num(y)
            else:
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
            return {
                'm': ab, 
                'b': 0,
                'x': x,
                'y': xab,
                'steps': steps
            }

        elif self.etype == Etype.quadratic:

            if (
                (a := self.variables.get('a')) is not None and 
                (b := self.variables.get('b')) is not None and 
                (c := self.variables.get('c')) is not None and
                (y := self.variables.get('y')) is not None
            ):  
                a, b, c, y = num(a), num(b), num(c), num(y)
            else:
                if terms := re.match(fr'({NUM_PAT})=({NUM_PAT})x\^2(\+|-)({NUM_PAT})x(\+|-)({NUM_PAT})', self.equation):
                    y = num(terms.group(1))

                    a = num(terms.group(2))
                    op1 = terms.group(3)
                    b = num(terms.group(4))
                    b = -b if op1 == '-' else b

                    op2 = terms.group(5)
                    c = num(terms.group(6))
                    c = -c if op2 == '-' else c
                else:
                    raise InvalidEquation()
                
            cy = c - y
            a2 = 2 * a
            b24ac = b ** 2 - 4 * a * cy

            try:
                sqrtv = math.sqrt(b24ac)
            except ValueError:
                sqrtv = cmath.sqrt(b24ac)

            if b24ac == 0:
                roots = (-b / a2,)
            else:
                bplus = -b + sqrtv
                roots1 = bplus / a2

                bminus = -b - sqrtv
                roots2 = bminus / a2
                roots = (roots1, roots2)

            steps = (
                f'{self.equation or f"{y} = {a}𝑥² + {b}𝑥 + {c}"}\n'
                f'0 = {a}𝑥² + {b}𝑥 + {cy}\n'
                f'𝑥 = ({-b} ± √({b}² - 4 * {a} * {c})) / (2 * {a})\n'
                f'𝑥 = ({-b} ± √{b24ac}) / {a2}\n'
            )

            if b24ac == 0:
                steps += (
                    f'𝑥 = {-b} / {a2}'
                    f'𝑥 = {roots[0]}'
                )
            else:
                steps += (
                    f'𝑥 = ({-b} ± {sqrtv}) / {a2}\n'
                    'Positive root:\n'
                    f'𝑥 = ({-b} + {sqrtv}) / {a2}\n'
                    f'𝑥 = {bplus} / {a2}\n'
                    f'𝑥 = {roots1}\n'
                    'Negative root:\n'
                    f'𝑥 = ({-b} - {sqrtv}) / {a2}\n'
                    f'𝑥 = {bminus} / {a2}\n'
                    f'𝑥 = {roots2}\n'
                )
            return {
                'a': a,
                'b': b,
                'c': c,
                'x': roots,
                'y': y,
                'steps': steps,
            }
            
        elif self.etype == Etype.abcdformula:

            if (
                (a := self.variables.get('a')) is not None and 
                (b := self.variables.get('b')) is not None and 
                (c := self.variables.get('c')) is not None and
                (d := self.variables.get('d')) is not None
            ):
                a, b, c, d = num(a), num(b), num(c), num(d)
            else:
                if terms := re.match(fr'\(({NUM_PAT})(\+|-)({NUM_PAT})\*({NUM_PAT})\)/({NUM_PAT})', self.equation):
                    a = num(terms.group(1))

                    op = terms.group(2)
                    b = num(terms.group(3))
                    b = -b if op == '-' else b

                    c = num(terms.group(4))
                    d = num(terms.group(5))
                else:
                    raise InvalidEquation()

            bc = b * c
            abc = a + bc
            abcd = abc / d

            steps = (
                f'= {self.equation or f"({a} + {b} × {c}) / {d}"}\n'
                f'= {a} + {bc}\n'
                f'= {abc} / {d}\n'
                f'= {abcd}\n'
            )
            return steps

class ManualButton(discord.ui.Button):

    view: ManualModeView
    SYMBOL_CONV = {
        '𝑥': 'x',
        '×': '*',
        '÷': '/',
        '☐²': '^2'
    }
    
    def __init__(self, label: str, *, style: discord.ButtonStyle = discord.ButtonStyle.grey, row: int):
        super().__init__(style=style, label=str(label), row=row)

    async def edit(self, interaction: discord.Interaction, *, error: bool = False) -> discord.Message:
        content = 'Invalid Equation' if error else self.view.equation
        content = content or '\u200b'
        content += ' ' * (40 - len(content))
        embed = discord.Embed(description=f'```ansi\n\u001b[0;32m{content}\n```', color=self.view.ctx.bot.color)
        return await interaction.response.edit_message(embed=embed)

    async def callback(self, interaction: discord.Interaction) -> discord.Message:

        if self.label == 'Enter':
            try:
                if self.view.etype == Etype.abcdformula:
                    steps = EquationSolver(self.view.equation, etype=self.view.etype).evaluate()
                    assert isinstance(steps, str)
                    
                    embed = discord.Embed(
                        title='Solution:',
                        description=f'```py\n{steps}\n```',
                        color=self.view.ctx.bot.color
                    )

                    return await interaction.response.edit_message(embed=embed, attachments=[], view=None)
                else:
                    results = EquationSolver(self.view.equation, etype=self.view.etype).evaluate()
                    steps = results.pop('steps')
                    graph = await plot_graph(**results, etype=self.view.etype)
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
            embed = discord.Embed(title='Equation Solver - Manual Mode', color=self.view.ctx.bot.color)
            embed.description = (
                '• Equation Solver\n'
                f"• Solves a {self.view.etype.value['name']} Equation\n"
                '• Press the buttons to enter numbers and operators\n'
                f"• Enter the equation in the format of `{self.view.etype.value['equation']}`\n"
                '• Hit `Enter` to evaluate the entered expression\n'
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        elif self.label == 'C':
            self.view.equation = ''
            return await self.edit(interaction)

        elif self.label == '⌫':
            self.view.equation = self.view.equation[:-1]
            return await self.edit(interaction)

        elif self.label == 'Close':
            return await interaction.message.delete()

        else:
            term = self.SYMBOL_CONV.get(self.label, self.label)
            self.view.equation += term
            return await self.edit(interaction)

class ManualModeView(AuthorOnlyView):
    buttons: tuple[tuple[int | str, ...], ...]

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
        self.buttons = etype.value['buttons']

        for i, row in enumerate(self.buttons):
            for button in row:
                style = (
                    discord.ButtonStyle.green if button == 'Enter' else
                    discord.ButtonStyle.blurple if button in ('+', '-', '÷', '×', '𝑥', '☐²', '(', ')') else
                    discord.ButtonStyle.red if button in ('⌫', 'C', 'Close', 'ⓘ') else
                    discord.ButtonStyle.gray
                )
                
                item = ManualButton(button, style=style, row=i)

                if button == '\u200b':
                    item.disabled = True
                    
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
            remove_latex = remove_latex.replace(r'\times', '\u0001')

            remove_latex = remove_latex.replace(self.variable, value)

            replace_latex = remove_latex.replace('\u0000', r'\frac')
            self.button.view.latex_eq = replace_latex.replace('\u0001', r'\times')

            img = await render_latex(self.button.view.ctx.bot.session, self.button.view.latex_eq)
            embed.set_image(url='attachment://equation.png')

            self.button.disabled = True

            first_row = (button for button in self.button.view.children if button.row in (0, None))
            if all(child.disabled for child in first_row):
                self.button.view.children[-1].disabled = False

            return await interaction.response.edit_message(embed=embed, attachments=[img], view=self.button.view)
            
class VarButton(discord.ui.Button):

    view: EquationView
    value: Number

    def __init__(self, label: str, *, style: discord.ButtonStyle = discord.ButtonStyle.blurple, row: int = None):
        super().__init__(style=style, label=str(label), row=row)

    async def callback(self, interaction: discord.Interaction):

        if self.label == 'Cancel':
            return await interaction.message.delete()
        elif self.label == 'Enter':
            try:
                if self.view.etype == Etype.abcdformula:
                    steps = EquationSolver(etype=self.view.etype, **self.view.equation_vars).evaluate()
                    assert isinstance(steps, str)
                    
                    embed = discord.Embed(
                        title='Solution:',
                        description=f'```py\n{steps}\n```',
                        color=self.view.ctx.bot.color
                    )

                    return await interaction.response.edit_message(embed=embed, attachments=[], view=None)

                else:
                    results = EquationSolver(etype=self.view.etype, **self.view.equation_vars).evaluate()
                    steps = results.pop('steps')
                    graph = await plot_graph(**results, etype=self.view.etype)
                    graph = discord.File(graph, 'graph.png')

                    embed = discord.Embed(
                        title='Solution:',
                        description=f'```py\n{steps}\n```',
                        color=self.view.ctx.bot.color
                    )
                    embed.set_image(url='attachment://graph.png')

                    return await interaction.response.edit_message(embed=embed, attachments=[graph], view=None)
            except ZeroDivisionError:
                return await interaction.response.send_message('Division by 0 is not allowed. try again', ephemeral=True)
            except Exception as e:
                return await interaction.response.send_message(
                    content=f'Oops! An error occured: `{e}`'
                )

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
        self.latex_eq: str = etype.value['latex']

        for var in self.etype.value['vars']:
            self.add_item(VarButton(var))

        self.add_item(VarButton('Cancel', style=discord.ButtonStyle.red, row=1))
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
            discord.SelectOption(value=Etype.quadratic.name, label='Quadratic equation'),
            discord.SelectOption(value=Etype.abcdformula.name, label='Solve: (a + b * c) / d'),
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

        equation = etype.value['latex']
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
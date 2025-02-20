import discord
from discord.ext import commands
import random
import asyncio

class BaseballGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="야구게임")
    async def start_baseball_game(self, ctx):
        """
        #야구게임: 컴퓨터가 랜덤으로 만든 4자리 숫자를 맞추는 야구 게임을 시작합니다.
        """
        # 0~9까지 숫자 중 랜덤으로 4자리 숫자 생성 (중복 가능, 앞자리가 0이어도 상관없음)
        secret_number = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        attempts = 0

        await ctx.send("숫자 야구 게임을 시작합니다! 4자리 숫자를 맞춰보세요. (중간에 종료하려면 `#야구게임그만` 입력)")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        while True:
            try:
                message = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send(f"시간 초과! 게임을 종료합니다. 정답은 `{secret_number}`였습니다.")
                break

            guess = message.content.strip()
            if guess == "#야구게임그만":
                await ctx.send(f"게임을 종료합니다. 정답은 `{secret_number}`였습니다.")
                break

            if not guess.isdigit() or len(guess) != 4:
                await ctx.send("4자리 숫자를 입력해주세요.")
                continue

            attempts += 1

            # 스트라이크와 볼 계산
            strikes = 0
            balls = 0
            for i in range(4):
                if guess[i] == secret_number[i]:
                    strikes += 1
                elif guess[i] in secret_number:
                    balls += 1

            if strikes == 4:
                await ctx.send(f"홈런! {attempts}번만에 맞추셨습니다!")
                break
            else:
                # 맞는 숫자가 하나도 없으면 "아웃"
                if strikes == 0 and balls == 0:
                    await ctx.send("아웃")
                else:
                    result = []
                    if strikes:
                        result.append(f"스트라이크 {strikes}")
                    if balls:
                        result.append(f"볼 {balls}")
                    await ctx.send(', '.join(result))

async def setup(bot):
    await bot.add_cog(BaseballGame(bot))

import discord
from discord.ext import commands
import random
import asyncio

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="주사위")
    async def roll_dice(self, ctx, *args):
        try:
            if len(args) == 0:
                n, m = 6, 1  # 기본값: 1~6 사이에서 1개
            elif len(args) == 1:
                n, m = int(args[0]), 1  # 1~n 사이에서 1개
            elif len(args) == 2:
                n, m = int(args[0]), int(args[1])  # 1~n 사이에서 m개
            else:
                await ctx.send("❌ 올바르지 않은 형식입니다! 예시: `#주사위`, `#주사위 10`, `#주사위 10 3`")
                return
            
            if n < 1 or m < 1 or m > 10:
                await ctx.send("❌ 범위를 벗어났습니다! N은 1 이상의 값이어야 하며, M은 1~10 사이여야 합니다.")
                return
            
            loading_message = await ctx.send("🎲 주사위를 굴리고 있습니다... 잠시만 기다려 주세요!")
            await asyncio.sleep(2)  # 2초 후 결과 출력
            await loading_message.delete()
            
            results = [random.randint(1, n) for _ in range(m)]
            await ctx.send(f"🎲 주사위 결과: {', '.join(map(str, results))}")
        
        except ValueError:
            await ctx.send("❌ 올바른 숫자를 입력해주세요! 예시: `#주사위 6 2`")

async def setup(bot):
    await bot.add_cog(Dice(bot))

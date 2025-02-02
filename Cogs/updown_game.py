import discord
from discord.ext import commands
import random
import asyncio

class UpDownGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.command(name="업다운")
    async def updown(self, ctx, max_number: str):
        if not max_number.isdigit():
            await ctx.send("🚨 숫자를 입력해야 합니다! 예: #업다운 100")
            return

        max_number = int(max_number)
        if max_number < 3 or max_number > 10000:
            await ctx.send("🚨 3에서 10000 사이의 숫자만 입력할 수 있습니다!")
            return

        secret_number = random.randint(1, max_number)
        self.games[ctx.author.id] = {"number": secret_number, "attempts": 0}
        await ctx.send(f"🎮 {ctx.author.mention}, 1부터 {max_number} 사이의 숫자를 맞혀보세요! (게임을 종료하려면 #업다운그만 입력)")

    @commands.command(name="업다운그만")
    async def stop_updown(self, ctx):
        if ctx.author.id not in self.games:
            await ctx.send("🚨 당신은 현재 업다운 게임을 진행 중이 아닙니다!")
            return
        
        secret_number = self.games[ctx.author.id]["number"]
        del self.games[ctx.author.id]
        await ctx.send(f"⛔ 게임이 종료되었습니다. 하틴봇이 선정한 숫자는 **{secret_number}**였습니다!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if message.author.id in self.games:
            game = self.games[message.author.id]
            
            if message.content.isdigit():
                guess = int(message.content)
                game["attempts"] += 1
                
                if guess < game["number"]:
                    await message.channel.send(f"🔺 **업!**\n하틴봇의 숫자가 더 크네요!")
                elif guess > game["number"]:
                    await message.channel.send(f"🔻 **다운!**\n하틴봇의 숫자가 더 작네요!")
                else:
                    await message.channel.send(f"🎉 **정답입니다!**\n답은 **{game['number']}**입니다!\n총 시도 횟수: {game['attempts']}번")
                    del self.games[message.author.id]

async def setup(bot):
    await bot.add_cog(UpDownGame(bot))

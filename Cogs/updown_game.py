import discord
from discord.ext import commands
import random
import asyncio

class UpDownGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.command(name="업다운")
    async def updown(self, ctx, max_number: str = None):
        if max_number is None:
            await ctx.send("🚨 숫자를 입력해야 합니다! 예: #업다운 100")
            return

        if not max_number.isdigit():
            await ctx.send("🚨 숫자를 입력해야 합니다! 예: #업다운 100")
            return

        max_number = int(max_number)
        if max_number < 3 or max_number > 10000:
            await ctx.send("🚨 3에서 10000 사이의 숫자만 입력할 수 있습니다!")
            return

        secret_number = random.randint(1, max_number)
        self.games[ctx.author.id] = {"number": secret_number, "attempts": 0, "guesses": [], "last_activity": asyncio.get_event_loop().time()}
        await ctx.send(f"🎮 {ctx.author.mention}님,\n1부터 {max_number} 사이의 숫자를 맞혀보세요!\n(게임을 종료하려면 #업다운그만 입력)\n(내가 입력한 숫자와 결과를 한눈에 볼려면 #업다운종합 입력)")
        
        asyncio.create_task(self.auto_end_game(ctx.author.id, ctx))

    async def auto_end_game(self, player_id, ctx):
        while player_id in self.games:
            await asyncio.sleep(100)
            game = self.games.get(player_id)
            if game and asyncio.get_event_loop().time() - game["last_activity"] >= 100:
                del self.games[player_id]
                await ctx.send(f"⏳ {ctx.author.mention}님, 100초 동안 응답이 없어 게임이 자동 종료되었습니다. 하틴봇이 선정한 숫자는 **{game['number']}**였습니다!")

    @commands.command(name="업다운그만")
    async def stop_updown(self, ctx):
        if ctx.author.id not in self.games:
            await ctx.send("🚨 당신은 현재 업다운 게임을 진행 중이 아닙니다!")
            return
        
        secret_number = self.games[ctx.author.id]["number"]
        del self.games[ctx.author.id]
        await ctx.send(f"⛔ 게임이 종료되었습니다. 하틴봇이 선정한 숫자는 **{secret_number}**였습니다!")

    @commands.command(name="업다운종합")
    async def updown_summary(self, ctx):
        if ctx.author.id not in self.games:
            await ctx.send("🚨 당신은 현재 업다운 게임을 진행 중이 아닙니다!")
            return
        
        game = self.games[ctx.author.id]
        results = "\n".join([f"{i+1}번째 입력한 숫자: {guess} | 결과: {'업🔺' if guess < game['number'] else '다운🔻'}" for i, guess in enumerate(game["guesses"])])
        results = results if results else "없음"
        await ctx.send(f"📊 **업다운 게임 종합 정보**\n{results}\n🎯 총 시도 횟수: {game['attempts']}번")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if message.author.id in self.games:
            game = self.games[message.author.id]
            game["last_activity"] = asyncio.get_event_loop().time()
            
            if message.content.isdigit():
                guess = int(message.content)
                game["attempts"] += 1
                game["guesses"].append(guess)
                
                if guess < game["number"]:
                    await message.channel.send(f"🔺 **업!**\n하틴봇의 숫자가 {guess}보다 더 크네요!")
                elif guess > game["number"]:
                    await message.channel.send(f"🔻 **다운!**\n하틴봇의 숫자가 {guess}보다 더 작네요!")
                else:
                    await message.channel.send(f"🎉 **정답입니다!**\n답은 **{game['number']}**입니다!\n총 시도 횟수: {game['attempts']}번")
                    del self.games[message.author.id]

async def setup(bot):
    await bot.add_cog(UpDownGame(bot))

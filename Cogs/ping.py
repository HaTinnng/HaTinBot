import discord
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="핑")
    async def ping(self, ctx):
        """
        #핑 : 봇의 현재 핑 상태를 확인
        """
        latency = round(self.bot.latency * 1000)  # 단위를 ms(밀리초)로 변환
        await ctx.send(f"🏓 퐁! (현재 핑: {latency}ms)")

async def setup(bot):
    await bot.add_cog(Ping(bot))

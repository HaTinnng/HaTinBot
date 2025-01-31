import discord
from discord.ext import commands
import random

class RandomEmoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="랜덤이모지", help="서버 내의 이모지 중 하나를 랜덤으로 보여줍니다.")
    async def random_emoji(self, ctx):
        # 서버 내의 모든 이모지를 가져옵니다.
        emojis = ctx.guild.emojis

        # 서버에 이모지가 없다면 메시지를 보냅니다.
        if not emojis:
            await ctx.send("❌ 서버에 이모지가 없습니다.")
            return

        # 랜덤으로 이모지를 선택합니다.
        emoji = random.choice(emojis)

        # 랜덤으로 선택된 이모지를 메시지로 보냅니다.
        await ctx.send(f"{emoji}")

async def setup(bot):
    await bot.add_cog(RandomEmoji(bot))

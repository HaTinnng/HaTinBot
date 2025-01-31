import discord
from discord.ext import commands

class Furry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="퍼리충311")
    async def furry_image(self, ctx):
        """지정한 이미지 출력"""
        image_url = "https://cdn.discordapp.com/attachments/896805898478039060/1334911175695138969/logo.png?ex=679e4069&is=679ceee9&hm=99a7aee8a5f70b0221a730a6d64500f88855c2cbfb0de627ab15ca193e8cd525&"  # ✅ 여기에 원하는 이미지 URL 추가

        embed = discord.Embed(title="퍼리충 311", description="이건 퍼리충이야! 🐺", color=0x3498db)
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Furry(bot))

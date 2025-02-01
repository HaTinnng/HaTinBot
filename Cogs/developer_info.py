import discord
from discord.ext import commands

class DeveloperInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="개발자")
    async def developer_info(self, ctx):
        """개발자의 정보를 출력하는 명령어"""
        embed = discord.Embed(
            title="👨‍💻 개발자 정보",
            description="이 봇의 개발자 정보입니다!",
            color=discord.Color.blue()
        )
        embed.add_field(name="개발자", value="🚀 **HaTin@6874**", inline=False)
        embed.add_field(name="GitHub", value="[GitHub 링크](https://github.com/HaTinnng)", inline=False)
        embed.add_field(name="연락처", value="✉️ ---------", inline=False)
        embed.set_footer(text="문의가 필요하면 언제든지 연락하세요!")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DeveloperInfo(bot))

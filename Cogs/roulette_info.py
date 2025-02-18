import discord
from discord.ext import commands

class RouletteInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="룰렛정보", aliases=["슬롯정보", "배당정보"])
    async def roulette_info(self, ctx):
        """
        룰렛 게임의 각 조합별 배당금(배율) 정보를 보여줍니다.
        """
        embed = discord.Embed(
            title="🎰 777 룰렛 배당금 정보",
            description="각 조합이 당첨되었을 때, 배팅금에 곱해지는 배율입니다.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="세 개가 일치",
            value=(
                "• **777**: 77배\n"
                "• **★★★**: 52배\n"
                "• **☆☆☆**: 38배\n"
                "• **💎💎💎**: 25배\n"
                "• **🍒🍒🍒**: 18배\n"
                "• **🍀🍀🍀**: 12배\n"
                "• **🔔🔔🔔**: 5배"
            ),
            inline=False
        )
        embed.add_field(
            name="두 개가 일치",
            value=(
                "• **77**: 27배\n"
                "• **★★**: 18배\n"
                "• **☆☆**: 12배\n"
                "• **💎💎**: 8배\n"
                "• **🍒🍒**: 4배\n"
                "• **🍀🍀**: 2배\n"
                "• **🔔🔔**: 1배"
            ),
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RouletteInfo(bot))

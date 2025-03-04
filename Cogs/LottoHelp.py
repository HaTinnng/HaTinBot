import discord
from discord.ext import commands

class LottoHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="복권")
    async def lotto_help(self, ctx):
        """
        #복권 : 복권 시스템에 대한 도움말 출력
        """
        embed = discord.Embed(
            title="🎟 복권 시스템 안내",
            description="대한민국 로또 방식과 동일한 복권 시스템입니다!",
            color=discord.Color.green()
        )

        embed.add_field(name="🛒 복권 구매", value="`#복권구매 n` - 복권을 n장 구매 (1장 = 5,000원, 최대 30장)\n `#복권구매 다/전부/올인` - 구매가능한 만큼 최대한 복권을 구매", inline=False)
        embed.add_field(name="🎯 당첨 결과 확인", value="`#복권결과` - 이번 주 당첨 번호 확인", inline=False)
        embed.add_field(name="🎟 내 복권 조회", value="`#복권확인` - 내가 구매한 복권과 당첨 여부 확인", inline=False)
        embed.add_field(name="⏳ 복권 추첨", value="매주 **일요일 21:00 (KST)** 자동 추첨", inline=False)

        embed.add_field(
            name="💰 당첨금 안내",
            value=(
                "**1등:** 100,000,000원 (6개 일치)\n"
                "**2등:** 5,000,000원 (5개 일치)\n"
                "**3등:** 500,000원 (4개 일치)\n"
                "**4등:** 5,000원 (3개 일치)\n"
                "**꽝:** 0원"
            ),
            inline=False
        )

        embed.set_footer(text="🎰 행운을 빕니다! | 개발자: 하틴(HaTin)")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LottoHelp(bot))

import discord
from discord.ext import commands

class StockHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="주식도움말", aliases=["주식도움", "주식하는법", "주식방법"])
    async def stock_help(self, ctx):
        """
        #주식도움말: 주식 게임 관련 모든 명령어 및 사용법을 안내합니다.
        """
        embed = discord.Embed(
            title="📌 주식 게임 도움말",
            description="주식 게임에서 사용할 수 있는 명령어 목록입니다.",
            color=discord.Color.blue()
        )

        embed.add_field(name="💰 **기본 명령어**", value=(
            "`#주식(참가, 참여, 시작) [닉네임]` - 주식 게임에 참가합니다.\n"
            "`#주식이름변경 [새 닉네임]` - 자신의 닉네임을 변경합니다.\n"
            "`#주식(도움말, 도움, 방법, 하는법)` - 주식 게임 관련 도움말을 확인합니다.\n"
            "`#주식/#현재가` - 현재 주식 목록과 가격을 확인합니다.\n"
            "`#다음변동` - 다음 주식 변동 시각을 확인합니다.\n"
        ), inline=False)

        embed.add_field(name="📈 **주식 거래 명령어**", value=(
            "`#주식구매 [종목명] [수량]` - 해당 주식을 지정 수량만큼 구매합니다.\n"
            "`#주식구매 [종목명] all/전부/올인/다/풀매수` - 전 재산으로 최대 수량을 구매합니다.\n"
            "`#주식판매 [종목명] [수량]` - 해당 주식을 지정 수량만큼 판매합니다.\n"
            "`#주식판매 [종목명] all/전부/올인/다/풀매도` - 보유한 모든 주식을 판매합니다.\n"
            "`#변동내역 [종목명]` - 해당 주식의 최근 5회 변동 내역을 확인합니다.\n"
        ), inline=False)

        embed.add_field(name="📊 **기타 정보 명령어**", value=(
            "`#프로필/#자산/#자본` - 내 보유 현금과 주식, 자산 정보를 확인합니다.\n"
            "`#랭킹` - 전체 유저 중 보유 자산 상위 10명을 확인합니다.\n"
            "`#시즌` - 현재 시즌 정보 및 종료 시각을 확인합니다.\n"
        ), inline=False)

        embed.set_footer(text="📢 최신 업데이트: 주식 가격 변동폭 조정 (50원 이하 시 ±100%)")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StockHelp(bot))

import discord
from discord.ext import commands
from datetime import datetime, timedelta

class 날짜계산(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="날짜계산", help="오늘 날짜에 입력한 숫자를 더한 날짜를 계산합니다.")
    async def date_calc(self, ctx, days: str = None):
        """
        오늘 날짜에 입력한 숫자를 더한 날짜를 계산합니다.
        사용법: #날짜계산 [숫자]
        예시: #날짜계산 10 => 오늘 날짜에서 10일을 더한 날짜가 출력됩니다.
        """

        # 입력값이 없는 경우
        if days is None:
            await ctx.send("⚠️ 오류: 숫자를 입력해주세요! (예: `#날짜계산 10`)")
            return

        # 입력값이 숫자가 아닌 경우
        if not days.isdigit():
            await ctx.send("⚠️ 오류: 숫자만 입력해주세요! (예: `#날짜계산 10`)")
            return

        days = int(days)  # 입력값을 정수로 변환
        
        # 오늘 날짜
        today = datetime.today()
        
        # 날짜 계산 (현재 날짜 + 입력한 일수)
        new_date = today + timedelta(days=days)
        
        # 새로운 날짜 포맷팅 (YYYY-MM-DD)
        new_date_str = new_date.strftime("%Y-%m-%d")
        
        # 결과 메시지
        await ctx.send(f"📅 오늘 날짜: {today.strftime('%Y-%m-%d')}\n"
                       f"⏳ {days}일 후의 날짜: **{new_date_str}**")

async def setup(bot):
    """봇에 Cog 추가 (파일명이 '날짜계산'으로 설정됨)"""
    await bot.add_cog(날짜계산(bot))

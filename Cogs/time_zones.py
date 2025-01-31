import discord
from discord.ext import commands
import pytz
from datetime import datetime

class TimeZone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="시간")
    async def get_time(self, ctx, country: str = None):
        """세계 여러 나라의 시간을 알려주는 명령어"""
        
        # 국가별 시간대 맵핑 (예시)
        time_zones = {
            "한국": "Asia/Seoul",
            "미국": "America/New_York",
            "영국": "Europe/London",
            "프랑스": "Europe/Paris",
            "독일": "Europe/Berlin",
            "일본": "Asia/Tokyo",
            "호주": "Australia/Sydney",
            "인도": "Asia/Kolkata",
            "캐나다": "America/Toronto",
            "브라질": "America/Sao_Paulo"
        }
        
        if country is None or country not in time_zones:
            await ctx.send("⚠️ 나라를 입력해주세요. 예시: `#시간 한국`, `#시간 미국`")
            return
        
        # 지정된 나라의 시간대 정보 가져오기
        tz = pytz.timezone(time_zones[country])
        
        # 현재 시간을 해당 시간대에 맞게 가져오기
        current_time = datetime.now(tz)
        
        # 시간 포맷 설정 (예시: 2025-01-29 14:30:00)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 응답 메시지 보내기
        await ctx.send(f"{country}의 현재 시간은 {formatted_time}입니다.")

async def setup(bot):
    await bot.add_cog(TimeZone(bot))

import discord
from discord.ext import commands
import random

class Fortune(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="오늘의운세", aliases=["운세", "오운"], help="오늘의 운세를 알려드립니다.")
    async def todays_fortune(self, ctx):
        fortunes = [
            "오늘은 기회가 찾아오는 날! 과감히 도전해보세요.",
            "오늘은 좀 더 차분한 마음으로 하루를 시작하는 것이 좋습니다.",
            "행운이 따르는 하루입니다! 작은 일이라도 행운을 느낄 수 있을 거예요.",
            "오늘은 계획을 세우고 차근차근 실천하는 것이 중요합니다.",
            "오늘은 자신감을 가지고 도전하는 것이 좋은 날입니다. 실패를 두려워하지 마세요!",
            "오늘은 주변 사람들과 소통하는 것이 중요한 날입니다. 대화를 통해 좋은 결과를 얻을 수 있습니다.",
            "오늘은 작은 성취가 큰 보람으로 돌아오는 날입니다. 꾸준한 노력이 중요합니다.",
            "오늘은 감정적으로 조금 흔들릴 수 있는 날입니다. 침착하게 상황을 바라보세요.",
            "오늘은 귀찮은 일이 생길 수 있지만, 끝까지 처리하고 나면 마음이 가벼워질 거예요.",
            "운이 좋지 않다고 느껴질 수 있지만, 침착함을 유지하세요. 곧 좋은 일이 생길 것입니다."
        ]

        # 랜덤으로 운세 문구를 선택합니다.
        fortune = random.choice(fortunes)

        # 선택된 운세를 출력합니다.
        await ctx.send(f"오늘의 운세: {fortune}")

async def setup(bot):
    await bot.add_cog(Fortune(bot))

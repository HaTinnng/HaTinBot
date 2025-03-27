import discord
from discord.ext import commands

# 다음 업데이트 내역 (개발자가 직접 수정)
NEXT_UPDATE_LOGS = [
    {
        "date": "2025-03-31",
        "details": [
            "**시즌 종료**",
            "🔹 2025 시즌2이 종료가 됩니다.",
            "🔹 25.04.01 00:10에 새로운 시즌이 시작됩니다.(2025 시즌3)",
            "🔹 시즌종료와 동시에 모든 자금 및 주식은 초기화 됩니다.",
            "🔹 보유자금 TOP3에게 칭호가 부여됩니다.(⚠️유저데이터 삭제를 하면 칭호도 같이 삭제가 됩니다. 주의해주세요!)",
            "\u200b",
            "**주식변동내역**",
            "🔹 주식 변동율 변경(+21.58% ~ -18.32% --> 18.98% ~ -17.12%)",
            "🔹 주식 시작가 변경(주식가가 너무 높아서 구매 가능한 주식이 줄어드는 문제 해결)",
            "🔹 시즌 시간 변경(안정화된 주식의 기간을 증가 / 25일 --> 27일)",
            "🔹 프로필/랭킹 UI 변경(좀 더 보기 쉬운 UI를 이용)",
            "🔹 복권 로직 변경(복권 구매 가격 10,000원 --> 20,000원)",
            "🔹 복권 로직 변경(복권 최대 구매 개수 50개 --> 100개)",
            "🔹 주식쿠폰 수정(기존의 쿠폰은 삭제, 새로운 쿠폰이 새롭게 추가)",
            "🔹 주식 칭호 수정(TOP3에게 지급되는 칭호 앞에 메달을 추가)",
            "🔹 대출 로직 변경(최대 5,000,000원까지 대출이 되며 대출받으면 바로 이자 5% 가산)",
            "🔹 주식 소각 추가(돈을 받지 않고 바로 주식을 소각을 진행 가능/돈을 받지 않음)",
            "🔹 주식도움말 변경 및 내용 추가",
            "\u200b",
            "**예정 업데이트**",
            "✅ **사용자 인터페이스 개선**: 도움말 및 명령어 사용법 업데이트.",
            "✅ **버그 수정 및 최적화**: 기존 기능의 안정성을 향상시킵니다.",
        ]
    },
]

class NextUpdateLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="다음업데이트", aliases=["예정업데이트", "패치예정", "업데이트예정"])
    async def next_update_log(self, ctx):
        """
        #다음업데이트: 다음 업데이트 예정 내역을 확인합니다.
        """
        for log in NEXT_UPDATE_LOGS:
            details_list = log["details"]
            update_date = log["date"]

            embed = discord.Embed(
                title=f"📢 다음 업데이트 예정 - {update_date}",
                description="다음 업데이트에 포함될 기능들을 미리 확인하세요!",
                color=discord.Color.blue()
            )

            # Discord 임베드의 필드 길이 제한(1024자)을 고려하여 나누어 추가
            details_chunk = ""
            for detail in details_list:
                if len(details_chunk) + len(detail) > 1000:
                    embed.add_field(name="🔹 예정 업데이트 내용", value=details_chunk, inline=False)
                    details_chunk = ""
                details_chunk += f"{detail}\n"

            if details_chunk:
                embed.add_field(name="🔹 예정 업데이트 내용", value=details_chunk, inline=False)

            embed.set_footer(text="🚀 새로운 업데이트가 곧 찾아옵니다!")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NextUpdateLog(bot))

import discord
from discord.ext import commands

# 다음 업데이트 내역 (개발자가 직접 수정)
NEXT_UPDATE_LOGS = [
    {
        "date": "2025-02-31",
        "details": [
            "**시즌 종료**",
            "2025 시즌1이 종료가 됩니다.",
            "25.03.03 00:10에 새로운 시즌이 시작됩니다.(2025 시즌2)",
            "**주식변동내역**",
            "시즌 중에 추가된 주식은 자동삭제가 됩니다. 하지만 일부는 유지됩니다.(멸망병원, 르끌경호 삭제)",
            "주식 변동율 변경(±23.78% --> +19.58% ~ -16.32%)",
            "주식 시작가 변경(주식가가 낮아서 빨리 상장폐지가 되는 문제 해결)",
            "기본금 변경(지원금 도입으로 인하여 돈 수급이 원활해 기본금 감소(800,000 --> 750,000)",
            "지원금 변경(하루 12시에 초기화 되어 한번에 30,000 수급이 가능하게 변경하여 하루에 60,000으로 변경)",
            "주식명 변경(시작가가 변경됨으로써 시작가가 이름인 주식명 변경(오십만전자 --> ????)",
            "시즌결과 추가(유저데이터가 지우기 쉬워 칭호가 유지되기 어려워 TOP3의 결과를 데이터에 저장)",
            "**예정 업데이트**",
            "⛏️ **광산 시스템 도입**: 방치형 게임을 도입.(주식과 별개로 운영)",
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

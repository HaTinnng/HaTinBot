import discord
from discord.ext import commands

# 업데이트 내역 저장 (개발자가 직접 수정)
UPDATE_LOGS = [
    {
        "date": "2025-03-03",
        "details": [
            "**명령어 변동사항**",
            "**추가사항**",
            "✅ `#포커` 추가: (자금 가지고 할 수 있던게 적었던 부분을 보완)",
            "✅ `#레이스` 추가: (자금 가지고 할 수 있던게 적었던 부분을 보완)",
            "✅ `#복권` 뒤에 다/전부/올인 기능 추가: (자신이 구매할 수 있는 최대 수량으로 구매)",
            "✅ `#베팅` 뒤에 다/전부/올인 기능 추가",
            "✅ `#경마` 명령어 추가(경마시스템에 대한 도움말을 출력)",
            "\u200b",
            "**수정사항**",
            "✅ 복권 구매 수량 증가: (10개 --> 30개)",
            "✅ `#복권` UI/UX 수정: (구매수량이 증가하면서 버튼시스템 도입으로 보기 편하게 수정)",
            "✅ `#복권` 당첨금 증가: (전체적인 돈이 증가하면서 상대적으로 미미해보이던 당첨금을 수정)",
            "\u200b",
            "**주식 변동사항**",
            "✅ `#대출` 한도 상향 (500,000 --> 5,000,000)",
            "✅ `#주식`시 변동가격에 천단위 구별 추가",
            "✅ 주식에서 평균 구매가를 제외한 모든 숫자에서 소수점이하는 표시가 안되도록 수정"
            "✅ `#매수 다/전부/올인/전체`입력 시 랜덤한 수량으로 랜덤한 주식을 매수",
            "✅ `#매도 다/전부/올인/전체`입력 시 가지고 있는 모든 주식을 매도",
            "✅ 주식에서 필요한 모든 부분에서 천단위 구분 추가",
            "✅ 주식 변동율 변경 (-18.32% ~ 21.52% --> -19.82% ~ 20.52%)",
            "\u200b",
            "**기타**",
            "각종 버그 수정 및 최적화",
            "\u200b",
            "**현재 개발 사항 (예정)**",
            "📌 블랙잭 멀티 기능 추가",
            "✨ 과자 먹는 중..."
        ]
    },
]

class UpdateLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="업데이트", aliases=["업데이트내역", "패치노트"])
    async def update_log(self, ctx):
        """
        #업데이트: 최근 업데이트 내역을 확인합니다.
        """

        for log in UPDATE_LOGS[:3]:  # 최근 3개의 업데이트만 표시
            details_list = log["details"]
            update_date = log["date"]

            embed = discord.Embed(
                title=f"📢 업데이트 내역 - {update_date}",
                description="최근 업데이트된 내용을 확인하세요!",
                color=discord.Color.green()
            )

            # Discord 임베드의 필드 길이 제한(1024자)을 고려하여 나누어 추가
            details_chunk = ""
            for detail in details_list:
                if len(details_chunk) + len(detail) > 1000:
                    embed.add_field(name="🔹 업데이트 내용", value=details_chunk, inline=False)
                    details_chunk = ""
                details_chunk += f"{detail}\n"

            if details_chunk:
                embed.add_field(name="🔹 업데이트 내용", value=details_chunk, inline=False)

            embed.set_footer(text="🔄 최신 업데이트 정보를 확인하세요!")

            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UpdateLog(bot))

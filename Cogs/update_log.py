import discord
from discord.ext import commands

# 업데이트 내역 저장 (개발자가 직접 수정)
UPDATE_LOGS = [
    {
        "date": "2025-02-17",
        "details": [
            "**명령어 변동사항**",
            "**추가사항**",
            "✅ `#룰렛` 추가: (자금 가지고 할 수 있던게 적었던 부분을 보완)",
            "✅ `#복권` 추가: (자금 가지고 할 수 있던게 적었던 부분을 보완)",
            "✅ `#뽑기확률` 추가: (뽑기확률을 공개하여 투명한 게임을 추구)",
            "✅ `#룰렛` 뒤에 다/전부/올인 기능 추가: (가지고 있는 돈 전부를 이용해 룰렛을 배팅합니다. 경고문이 나오며 일정시간이 지나면 자동으로 취소)",
            "\u200b",
            "**수정사항**",
            "✅ `#도움말` 업데이트: (봇이 발달하면서 도움말이 미흡했던 부분을 수정)",
            "✅ 룰렛 확률 수정 및 보상 증가: (확률이 너무 낮아 돌리면 손해만 보는 상황을 수정)",
            "✅ #룰렛과 동일한 명령어 #슬롯 추가",
            "\u200b",
            "**주식 변동사항**",
            "**주식종목**",
            "`멸망병원`(시작가: 350000), `르끌경호`(시작가: 650000) 추가: (많은 주식이 상장폐지 하면서 살게 없어지는 주식시장 개선)",
            "`지원금` 추가: (매일 #지원금 입력시 지원금 지급, 매일 00:00에 초기화)",
            "\u200b",
            "**주식 로직 변경**",
            "주식이 50원 이하일 경우 변동폭 제한 해제에서 모든 부분에서 변동폭을 동일하게 유지하며 13원미만이 되면 주식이 자동으로 상장폐지가 되게 변경",
            "MongoDB 연동으로 데이터 유지",
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

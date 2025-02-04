import discord
from discord.ext import commands

# 업데이트 내역 저장 (개발자가 직접 수정)
UPDATE_LOGS = [
    {
        "date": "2025-02-04",
        "details": [
            "**명령어 변동사항**",
            "**추가사항**",
            "✅ `#종목소개` 추가: (주식의 시작가격범위, 주식주에 대한 설명 추가)",
            "✅ `#주식도움말` 추가: (주식에 필요한 설명과 명령어를 정리한 문서 제공)",
            "✅ `#업데이트` 명령어 추가: (업데이트 날짜와 내역 확인 가능)",

            "**수정사항**",
            "✅ `#도움말` 업데이트: (봇이 발달하면서 도움말이 미흡했던 부분을 수정)",

            "**주식 변동사항**",
            "**주식종목**",
            "`311유통`을 제외한 나머지 시작가격 조정 (더 세분화하여 지루한 상황 해결)",

            "**명령어**",
            "`주식구매`, `주식판매` 시 `all/전부/올인/다` 입력 시 전체 매수/매도 가능",
            "`프로필` 명령어에 `자산`, `자본` 추가",
            "`변동내역` 명령어로 최근 5개 주가 변동 내역 확인 가능",
            "`매수`, `매도` 명령어 추가 (구매/판매와 동일)",

            "**주식 로직 변경**",
            "기초자본 증가: 50만 → 80만",
            "주식 변동폭 증가: ±12.3% ~ ±23.78%",
            "주식 거래 시간 변경: 매월 1일 00:10 종료 → 3일 00:10 시작",
            "주식이 50원 이하일 경우 변동폭 제한 해제 (±100%)",
            "MongoDB 연동으로 데이터 유지",

            "**기타**",
            "각종 버그 수정 및 최적화",

            "**현재 개발 사항 (예정)**",
            "📌 블랙잭 멀티 기능 추가",
            "📌 초능력 목록 추가",
            "📌 뽑기 확률 명령어 추가",
            "📌 뽑기 1등, 2등 기록 저장 추가",
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

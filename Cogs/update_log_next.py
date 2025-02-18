import discord
from discord.ext import commands

# 다음 업데이트 내역 (개발자가 직접 수정)
NEXT_UPDATE_LOGS = [
    {
        "date": "2025-02-24",
        "details": [
            "**예정 업데이트**",
            "📌 **블랙잭 멀티 기능 추가**: 멀티 플레이어와 함께 블랙잭을 즐길 수 있습니다.",
            "✨ **새로운 과자 아이템 추가**: 게임 내 과자 아이템 사용 시 일시적인 능력치 상승 효과 제공.",
            "✅ **사용자 인터페이스 개선**: 도움말 및 명령어 사용법 업데이트.",
            "✅ **버그 수정 및 최적화**: 기존 기능의 안정성을 향상시킵니다.",
        ]
    },
]

class NextUpdateLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="다음업데이트", aliases=["예정업데이트", "패치예정"])
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

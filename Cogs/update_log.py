import discord
from discord.ext import commands

# 업데이트 내역 저장 (개발자가 직접 수정)
UPDATE_LOGS = [
    {
        "date": "2025-02-04",
        "details": [
            "**추가사항**",
            "**명령어 변동사항**",
            "✅ `#주식이름변경` 명령어 추가 (닉네임 변경 가능)",
            "✅ `#주식도움말` 추가 (모든 명령어 설명 제공)",
            "✅ `#업데이트` 명령어 추가 (업데이트 내역 확인 가능)",
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
        embed = discord.Embed(
            title="📢 최신 업데이트 내역",
            description="최근 업데이트된 내용을 확인하세요!",
            color=discord.Color.green()
        )

        for log in UPDATE_LOGS[:3]:  # 최근 3개의 업데이트만 표시
            details = "\n".join(log["details"])
            embed.add_field(name=f"📅 {log['date']}", value=details, inline=False)

        embed.set_footer(text="🔄 최신 업데이트 정보를 확인하세요!")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UpdateLog(bot))

import discord
from discord.ext import commands

class HatinBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="하틴봇", help="하틴봇에 대한 정보를 제공합니다!")
    async def hatinbot_info(self, ctx):
        """하틴봇에 대한 정보를 출력하는 명령어"""

        embed = discord.Embed(
            title="🤖 하틴봇 정보",
            description="하틴봇은 다양한 기능을 제공하는 다목적 디스코드 봇입니다!\n"
                        "채팅, 게임, 유틸리티, 관리 기능까지 모두 포함되어 있습니다.",
            color=0x5865F2  # Discord 블루 컬러
        )

        embed.set_thumbnail(url="https://your-image-url.com/logo.png")  # 하틴봇 이미지 (수정 가능)
        embed.add_field(name="✨ 주요 기능", value="""
        - 🎮 **미니 게임** (가위바위보, 랜덤 추천 등)
        - 🛠️ **유틸리티 명령어** (운세, 음식 추천 등)
        - 🔧 **서버 관리 기능** (관리자 전용 명령어 지원)
        - 🤖 **자동 응답 기능** (특정 키워드 반응)
        """, inline=False)

        embed.add_field(name="📜 주요 명령어", value="""
        - `#가위바위보` → 하틴봇과 가위바위보를 할 수 있습니다.
        - `#오늘의음식` → 랜덤으로 음식 추천을 받습니다.
        - `#하틴봇` → 하틴봇에 대한 정보를 확인할 수 있습니다.
        """, inline=False)

        embed.set_footer(text="하틴봇과 함께 즐거운 디스코드 생활을!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HatinBot(bot))

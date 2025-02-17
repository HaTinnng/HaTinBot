import discord
from discord.ext import commands

class DrawOdds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # (아이템 이름, 확률(%) ) 형태로 아이템 목록을 정의합니다.
        # 아래 확률의 합은 100%입니다.
        self.items = [
            ("전설적인 용의 검", 0.01),
            ("황금 재규어", 0.168),
            ("미래의 타임머신", 0.344),
            ("슈퍼 파워 포션", 0.519),
            ("무적의 방패", 0.694),
            ("영원한 왕국의 지도", 0.905),
            ("하늘의 별", 1.115),
            ("초능력의 가방", 1.325),
            ("불사의 꽃", 1.536),
            ("빛나는 다이아몬드", 1.746),
            ("세계 최고의 책", 1.956),
            ("마법의 반지", 2.167),
            ("검은색 호랑이", 2.377),
            ("회복의 물약", 2.588),
            ("천상의 오브", 2.798),
            ("고대의 룬", 3.008),
            ("불사의 영혼", 3.219),
            ("천사의 깃털", 3.429),
            ("순수한 진주", 3.639),
            ("황금 조각", 3.849),
            ("마법의 돌", 4.060),
            ("고블린의 금", 4.271),
            ("슬라임의 젤리", 4.481),
            ("빛나는 나무", 4.691),
            ("동전", 4.902),
            ("버려진 신발", 5.112),
            ("스크래치 카드", 5.322),
            ("쓸모없는 돌", 5.533),
            ("헛된 나뭇가지", 5.743),
            ("고장난 시계", 5.954),
            ("찢어진 신문", 6.164),
            ("빈 병", 6.375)
        ]
    
    @commands.command(name="뽑기확률")
    async def show_draw_odds(self, ctx):
        """
        뽑기 확률을 보여주는 명령어입니다.
        각 아이템이 뽑힐 확률을 확인할 수 있습니다.
        """
        description_lines = []
        for item, probability in self.items:
            # 각 아이템과 확률을 포맷하여 문자열로 생성합니다.
            description_lines.append(f"**{item}**: `{probability}%`")
        description = "\n".join(description_lines)
        
        embed = discord.Embed(
            title="뽑기 확률 안내",
            description=description,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DrawOdds(bot))

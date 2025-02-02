import discord
from discord.ext import commands
import random
import asyncio

class Draw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items = [
            ("전설적인 용의 검", 0.01),
            ("황금 재규어", 0.24),
            ("미래의 타임머신", 0.49),
            ("슈퍼 파워 포션", 0.74),
            ("무적의 방패", 0.99),
            ("영원한 왕국의 지도", 1.29),
            ("하늘의 별", 1.59),
            ("초능력의 가방", 1.89),
            ("불사의 꽃", 2.19),
            ("빛나는 다이아몬드", 2.49),
            ("세계 최고의 책", 2.79),
            ("마법의 반지", 3.09),
            ("검은색 호랑이", 3.39),
            ("회복의 물약", 3.69),
            ("천상의 오브", 3.99),
            ("고대의 룬", 4.29),
            ("불사의 영혼", 4.59),
            ("천사의 깃털", 4.89),
            ("순수한 진주", 5.19),
            ("황금 조각", 5.49),
            ("마법의 돌", 5.79),
            ("고블린의 금", 6.09),
            ("슬라임의 젤리", 6.39),
            ("빛나는 나무", 6.69),
            ("동전", 6.99),
            ("버려진 신발", 7.29),
            ("스크래치 카드", 7.59),
            ("쓸모없는 돌", 7.89),
            ("헛된 나뭇가지", 8.19),
            ("고장난 시계", 8.49),
            ("찢어진 신문", 8.79),
            ("빈 병", 9.09)
        ]

        # 확률 정규화 (총합 100% 보장)
        total_probability = sum(prob for _, prob in self.items)
        self.items = [(item, prob / total_probability * 100) for item, prob in self.items]

        # 아이템을 희귀도에 따라 그룹화
        self.item_groups = {
            "전설": self.items[:1],
            "최고급": self.items[1:4],
            "고급": self.items[4:8],
            "중급": self.items[8:12],
            "일반": self.items[12:16],
            "하급": self.items[16:20],
            "최하급": self.items[20:24],
            "쓰레기": self.items[24:]
        }

        # 각 그룹별 메시지
        self.group_messages = {
            "전설": "🌟 **엄청난 행운! 전설적인 아이템을 획득했습니다!**",
            "최고급": "🎉 **굉장한 아이템을 뽑았어요! 정말 운이 좋군요!**",
            "고급": "😃 **훌륭한 선택이에요! 기대해도 좋습니다!**",
            "중급": "🙂 **괜찮은 아이템이네요! 실망할 필요 없어요!**",
            "일반": "😐 **나쁘지 않아요. 무난한 선택입니다.**",
            "하급": "😅 **조금 아쉽지만 사용할 만한 아이템이군요.**",
            "최하급": "🙄 **이걸로 뭘 할 수 있을까요? 그다지 유용하진 않네요.**",
            "쓰레기": "😢 **...이걸 왜 뽑았을까요? 그냥 버려도 될 것 같은데요.**"
        }

    @commands.command(name="뽑기", aliases=["가챠"])
    async def draw(self, ctx, num: str = None):
        if num:
            await ctx.send("❌ #뽑기/가챠만 적어도 작동합니다! 연속뽑기나 마이너스뽑기는 존재하지 않습니다.")
            return

        loading_message = await ctx.send("🎰 **물건을 뽑는 중입니다... 잠시만 기다려 주세요!**")
        await asyncio.sleep(3.5)
        await loading_message.delete()

        rand_value = random.uniform(0, 100)  # 0~100 범위의 랜덤 값
        cumulative_probability = 0

        selected_item = "빈 병"  # 기본값 설정 (마지막 아이템 보장)
        for item, probability in self.items:
            cumulative_probability += probability
            if rand_value <= cumulative_probability:
                selected_item = item
                break

        # 해당 아이템이 속한 그룹 찾기
        selected_group = next((group for group, items in self.item_groups.items() if selected_item in dict(items)), "쓰레기")
        result_message = self.group_messages[selected_group]

        embed = discord.Embed(
            title="**상품을 뽑았습니다!**",
            description="**결과는!**",
            color=discord.Color.green()
        )

        embed.add_field(
            name=f"결과: {selected_item}",
            value=f"{result_message}",
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Draw(bot))

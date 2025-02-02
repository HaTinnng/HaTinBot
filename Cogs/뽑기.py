import discord
from discord.ext import commands
import random
import asyncio

class Draw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items = [
            ("전설적인 용의 검", 0.01),
            ("황금 재규어", 0.05),
            ("미래의 타임머신", 0.1),
            ("슈퍼 파워 포션", 0.2),
            ("무적의 방패", 0.5),
            ("영원한 왕국의 지도", 1),
            ("하늘의 별", 2),
            ("초능력의 가방", 3),
            ("불사의 꽃", 4),
            ("빛나는 다이아몬드", 5),
            ("세계 최고의 책", 6),
            ("마법의 반지", 7),
            ("검은색 호랑이", 8),
            ("회복의 물약", 9),
            ("천상의 오브", 10),
            ("고대의 룬", 12),
            ("불사의 영혼", 15),
            ("천사의 깃털", 20),
            ("순수한 진주", 25),
            ("황금 조각", 30),
            ("마법의 돌", 35),
            ("고블린의 금", 40),
            ("슬라임의 젤리", 45),
            ("빛나는 나무", 50),
            ("동전", 60),
            ("버려진 신발", 70),
            ("스크래치 카드", 80),
            ("쓸모없는 돌", 90),
            ("헛된 나뭇가지", 95),
            ("고장난 시계", 98),
            ("찢어진 신문", 99),
            ("빈 병", 100)
        ]

        # 확률을 0~1 사이로 정규화
        total_probability = sum(prob for _, prob in self.items)
        self.items = [(item, prob / total_probability) for item, prob in self.items]

    @commands.command(name="뽑기", aliases=["가챠"])
    async def draw(self, ctx, num: str = None):
        if num:
            await ctx.send("❌ #뽑기/가챠만 적어도 작동합니다! 연속뽑기나 마이너스뽑기는 존재하지 않습니다.")
            return

        loading_message = await ctx.send("🎰 **물건을 뽑는 중입니다... 잠시만 기다려 주세요!**")
        await asyncio.sleep(3.5)
        await loading_message.delete()

        rand_value = random.random()
        cumulative_probability = 0

        for item, probability in self.items:
            cumulative_probability += probability
            if rand_value <= cumulative_probability:
                selected_item = item
                break
        else:
            selected_item = "빈 병"

        embed = discord.Embed(
            title="**상품을 뽑았습니다!**", 
            description="**결과는!**",
            color=discord.Color.green()
        )

        embed.add_field(
            name=f"결과: {selected_item}",
            value=f"🎉 {self.get_message_for_item(selected_item)}",
            inline=False
        )

        await ctx.send(embed=embed)

    def get_message_for_item(self, item):
        """아이템에 따라 다른 메시지 출력"""
        if item == "전설적인 용의 검":
            return "🎉 **우와! 최고의 행운이에요! 정말 대단한 선택입니다!** 🏆"
        elif item == "빈 병":
            return "😅 **그냥 갖다버리는게 더 낫겠네요....**"
        else:
            low_prob_items = ["황금 재규어", "미래의 타임머신", "슈퍼 파워 포션"]
            mid_prob_items = ["무적의 방패", "영원한 왕국의 지도", "하늘의 별", "초능력의 가방"]
            high_prob_items = ["불사의 꽃", "빛나는 다이아몬드", "세계 최고의 책", "마법의 반지"]
            very_high_prob_items = ["검은색 호랑이", "회복의 물약", "천상의 오브", "고대의 룬"]
            very_high_prob_items_2 = ["불사의 영혼", "천사의 깃털", "순수한 진주", "황금 조각"]
            high_prob_items_2 = ["마법의 돌", "고블린의 금", "슬라임의 젤리", "빛나는 나무", "동전"]
            max_prob_items = ["쓸모없는 돌", "헛된 나뭇가지", "고장난 시계", "찢어진 신문"]

            if item in low_prob_items:
                return f"🎉 **축하합니다!** {item}이(가) 나왔어요! 정말 행운이네요!"
            elif item in mid_prob_items:
                return f"😄 **잘 뽑았어요!** {item}이(가) 나왔어요!"
            elif item in high_prob_items:
                return f"🤔 **괜찮네요!** {item}이(가) 나왔어요!"
            elif item in very_high_prob_items:
                return f"😅 **그럭저럭 나쁘지 않아요!** {item}이(가) 나왔어요."
            elif item in very_high_prob_items_2:
                return f"😶 **그냥 그런가 봐요.** {item}이(가) 나왔어요."
            elif item in high_prob_items_2:
                return f"😌 **그래도 괜찮아요.** {item}이(가) 나왔어요."
            elif item in max_prob_items:
                return f"😅 **이걸 왜 뽑았을까요?** {item}이(가) 나왔어요."
            else:
                return f"😅 **그냥 갖다버리는게 더 낫겠네요....**"

async def setup(bot):
    await bot.add_cog(Draw(bot))

import discord
from discord.ext import commands
import random
import asyncio

class Draw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items = [
            ("전설적인 용의 검", 0.01),  # 0.01% 확률로 나오는 최고의 아이템
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
            ("쓸모없는 돌", 90),  # 거의 확실하게 나오는 물건
            ("헛된 나뭇가지", 95),
            ("고장난 시계", 98),
            ("찢어진 신문", 99),
            ("빈 병", 100)
        ]
        self.items = [(item, probability / 100) for item, probability in self.items]  # 확률을 0과 1 사이로 변환

    @commands.command(name="뽑기")
    async def draw(self, ctx, num: str = None):
        """
        #뽑기 명령어로 한 번만 상품을 뽑을 수 있습니다.
        확률에 따라 가치가 높은 아이템부터 낮은 아이템까지 나옵니다.
        """
        # #뽑기 뒤에 숫자나 문자가 있으면 경고 메시지 출력
        if num:
            await ctx.send("❌ #뽑기만 적어도 작동합니다! 연속뽑기나 마이너스뽑기는 존재하지 않습니다.")
            return

        # 뽑는 중 메시지 출력
        await ctx.send("🎰 **물건을 뽑는 중입니다... 잠시만 기다려 주세요!**")

        # 5초 딜레이
        await asyncio.sleep(5)

        # 기존 메세지 자동 삭제
        await loading_message.delete()

        rand_value = random.random()  # 0과 1 사이의 랜덤 값

        selected_item = "빈 병"  # 기본값은 빈 병
        total_probability = 0

        # 확률을 기반으로 상품을 선택
        for item, probability in self.items:
            total_probability += probability
            if rand_value <= total_probability:
                selected_item = item
                break

        # 결과 메시지 설정
        embed = discord.Embed(
            title="**상품을 뽑았습니다!**", 
            description="**결과는!**",
            color=discord.Color.green()
        )

        # 결과 출력
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
            # 확률에 따라 다른 메시지
            low_prob_items = [
                "황금 재규어", "미래의 타임머신", "슈퍼 파워 포션",
            ]
            mid_prob_items = [
                "무적의 방패", "영원한 왕국의 지도", "하늘의 별", "초능력의 가방"
            ]
            high_prob_items = [
                "불사의 꽃", "빛나는 다이아몬드", "세계 최고의 책", "마법의 반지"
            ]
            very_high_prob_items = [
                "검은색 호랑이", "회복의 물약", "천상의 오브", "고대의 룬"
            ]
            very_high_prob_items_2 = [
                "불사의 영혼", "천사의 깃털", "순수한 진주", "황금 조각"
            ]
            high_prob_items_2 = [
                "마법의 돌", "고블린의 금", "슬라임의 젤리", "빛나는 나무", "동전"
            ]
            max_prob_items = [
                "쓸모없는 돌", "헛된 나뭇가지", "고장난 시계", "찢어진 신문"
            ]

            # 확률을 기반으로 멘트 다르게 출력
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
                return f"😅 **그냥 갖다버리는게 더 낫겠네요...."

async def setup(bot):
    await bot.add_cog(Draw(bot))

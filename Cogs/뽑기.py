import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))  # 한국 표준시 (KST)

class Draw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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
        self.first_place_file = "first_place_records.txt"  # 1등 기록 저장 파일
        self.second_place_file = "second_place_records.txt"  # 2등 기록 저장 파일
        self.load_first_place_records()  # 서버 시작 시 기록 불러오기
        self.load_second_place_records()

    def load_first_place_records(self):
        try:
            with open(self.first_place_file, "r", encoding="utf-8") as f:
                self.first_place_records = f.read().splitlines()
        except FileNotFoundError:
            self.first_place_records = []
    
    def load_second_place_records(self):
        try:
            with open(self.second_place_file, "r", encoding="utf-8") as f:
                self.second_place_records = f.read().splitlines()
        except FileNotFoundError:
            self.second_place_records = []

    def save_first_place_record(self, record):
        with open(self.first_place_file, "a", encoding="utf-8") as f:
            f.write(record + "\n")
    
    def save_second_place_record(self, record):
        with open(self.second_place_file, "a", encoding="utf-8") as f:
            f.write(record + "\n")

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

        now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        if selected_item == "전설적인 용의 검":
            record = f"{now} - {ctx.author.name}님이 전설적인 용의 검을 뽑았습니다!"
            self.first_place_records.append(record)
            self.save_first_place_record(record)
        elif selected_item == "황금 재규어":
            record = f"{now} - {ctx.author.name}님이 황금 재규어를 뽑았습니다!"
            self.second_place_records.append(record)
            self.save_second_place_record(record)

        rarity_groups = {
            "전설": ["전설적인 용의 검"],
            "최고급": ["황금 재규어", "미래의 타임머신", "슈퍼 파워 포션"],
            "고급": ["무적의 방패", "영원한 왕국의 지도", "하늘의 별", "초능력의 가방"],
            "중급": ["불사의 꽃", "빛나는 다이아몬드","세계 최고의 책", "마법의 반지"],
            "일반": ["검은색 호랑이","회복의 물약", "천상의 오브","고대의 룬"],
            "하급": ["불사의 영혼", "천사의 깃털","순수한 진주", "황금 조각"],
            "최하급": ["마법의 돌","고블린의 금", "슬라임의 젤리", "빛나는 나무"],
            "쓰레기1": ["동전", "버려진 신발", "스크래치 카드", "쓸모없는 돌"],
            "쓰레기2": ["헛된 나뭇가지", "고장난 시계", "찢어진 신문", "빈 병"]
        }
        item_rarity = next((rarity for rarity, items in rarity_groups.items() if selected_item in items), "기타")
        rarity_messages = {
            "전설": "🌟 엄청난 행운! 전설적인 아이템을 획득했습니다!",
            "최고급": "🎉 굉장한 아이템을 뽑았어요! 정말 운이 좋군요!",
            "고급": "😃 훌륭한 선택이에요! 기대해도 좋습니다!",
            "중급": "🙂 괜찮은 아이템이네요! 실망할 필요 없어요!",
            "일반": "😐 나쁘지 않아요. 무난한 선택입니다.",
            "하급": "😅 조금 아쉽지만 사용할 만한 아이템이군요.",
            "최하급": "😓 아쉽네요... 그래도 다음 기회를 노려보세요!",
            "쓰레기1": "😢 이건 진짜 쓰레기네요... 다음번에는 더 나은 걸 뽑기를!",
            "쓰레기2": "🗑️ 완전한 쓰레기... 그냥 버리는 게 나을지도?"
        }

        embed = discord.Embed(
            title="**상품을 뽑았습니다!**",
            description=f"🎉 {selected_item}을(를) 획득하셨습니다!\n{rarity_messages.get(item_rarity, '🎁 예상치 못한 아이템이 나왔습니다!')}\n",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Draw(bot))

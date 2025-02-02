import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime

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

        if selected_item == "전설적인 용의 검":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record = f"{now} - {ctx.author.name}님이 전설적인 용의 검을 뽑았습니다!"
            self.first_place_records.append(record)
            self.save_first_place_record(record)  # 파일에 저장
        elif selected_item == "황금 재규어":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record = f"{now} - {ctx.author.name}님이 황금 재규어를 뽑았습니다!"
            self.second_place_records.append(record)
            self.save_second_place_record(record)  # 파일에 저장

        embed = discord.Embed(
            title="**상품을 뽑았습니다!**",
            description="**결과는!**",
            color=discord.Color.green()
        )
        embed.add_field(
            name=f"결과: {selected_item}",
            value=f"🎉 축하합니다! {selected_item}을(를) 획득하셨습니다!",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(name="뽑기1등")
    async def first_place(self, ctx):
        if not self.first_place_records:
            await ctx.send("❌ 아직 1등 기록이 없습니다!")
        else:
            records = "\n".join(self.first_place_records[-10:])  # 최근 10개까지만 표시
            await ctx.send(f"🏆 **최근 1등 기록:**\n{records}")
    
    @commands.command(name="뽑기2등")
    async def second_place(self, ctx):
        if not self.second_place_records:
            await ctx.send("❌ 아직 2등 기록이 없습니다!")
        else:
            records = "\n".join(self.second_place_records[-10:])  # 최근 10개까지만 표시
            await ctx.send(f"🥈 **최근 2등 기록:**\n{records}")

async def setup(bot):
    await bot.add_cog(Draw(bot))

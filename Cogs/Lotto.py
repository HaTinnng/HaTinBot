import discord
import random
from discord.ext import commands, tasks
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import pytz

# MongoDB 설정
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

class Lotto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]
        self.lotto_draw_task = None

        # 매주 일요일 21:00 (KST) 자동 추첨
        self.lotto_draw_task.start()

    def cog_unload(self):
        self.lotto_draw_task.cancel()

    def get_seoul_time(self):
        return datetime.now(pytz.timezone("Asia/Seoul"))

    @commands.Cog.listener()
    async def on_ready(self):
        """봇이 준비되면 태스크 시작"""
        if not self.lotto_draw_task:
            self.lotto_draw_task = self.lotto_draw_task_func()
            self.lotto_draw_task.start()

    @commands.command(name="복권구매")
    async def buy_lotto(self, ctx, ticket_count: int):
        """
        #복권구매 [n] : 1장당 1,000원, 최대 10장까지 구매 가능
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})

        if not user:
            await ctx.send("❌ 주식 게임에 참가하지 않았습니다. `#주식참가`를 먼저 입력하세요!")
            return

        if ticket_count <= 0:
            await ctx.send("❌ 최소 1장 이상 구매해야 합니다!")
            return

        if ticket_count > 10:
            await ctx.send("❌ 한 주에 최대 10장까지만 구매할 수 있습니다!")
            return

        cost = ticket_count * 5000

        if user["money"] < cost:
            await ctx.send(f"❌ 잔액이 부족합니다! (필요 금액: {cost:,}원)")
            return

        # 유저가 이번 주에 산 복권 확인
        current_week = self.get_seoul_time().strftime("%Y-%W")
        user_lotto = self.db.lotto.find_one({"_id": user_id})

        if user_lotto and user_lotto.get("week") == current_week:
            if len(user_lotto["tickets"]) + ticket_count > 10:
                await ctx.send("❌ 한 주에 최대 10장까지만 구매할 수 있습니다!")
                return
        else:
            self.db.lotto.delete_one({"_id": user_id})  # 새로운 주가 시작되면 초기화

        # 복권 구매 (1~45 중 6개 랜덤)
        tickets = [[random.randint(1, 45) for _ in range(6)] for _ in range(ticket_count)]
        self.db.users.update_one({"_id": user_id}, {"$inc": {"money": -cost}})
        self.db.lotto.update_one(
            {"_id": user_id},
            {"$set": {"week": current_week}, "$push": {"tickets": {"$each": tickets}}},
            upsert=True
        )

        await ctx.send(f"🎟 {ctx.author.mention}, {ticket_count}장 복권을 구매했습니다! (총 {cost:,}원)")

    @commands.command(name="복권결과")
    async def lotto_result(self, ctx):
        """
        #복권결과 : 이번 주 당첨 번호 확인
        """
        current_week = self.get_seoul_time().strftime("%Y-%W")
        lotto_data = self.db.lotto_result.find_one({"week": current_week})

        if not lotto_data:
            await ctx.send("📢 이번 주 복권 당첨 번호가 아직 추첨되지 않았습니다!")
            return

        numbers = lotto_data["numbers"]
        await ctx.send(f"📢 이번 주 당첨 번호: `{' '.join(map(str, numbers))}`")

    @commands.command(name="복권확인")
    async def check_lotto(self, ctx):
        """
        #복권확인 : 본인의 복권 번호 확인 + 당첨 여부 확인 (추첨 전에도 복권 확인 가능)
        """
        user_id = str(ctx.author.id)
        current_week = self.get_seoul_time().strftime("%Y-%W")
        user_lotto = self.db.lotto.find_one({"_id": user_id})

        if not user_lotto or user_lotto.get("week") != current_week:
            await ctx.send("🎟 이번 주에 구매한 복권이 없습니다!")
            return

        # 사용자가 구매한 복권 번호 표시
        tickets = user_lotto["tickets"]
        ticket_messages = [f"🎟 `{i+1}번`: `{sorted(ticket)}`" for i, ticket in enumerate(tickets)]

        # 이번 주 추첨 결과 확인
        lotto_data = self.db.lotto_result.find_one({"week": current_week})
        if not lotto_data:
            await ctx.send("📢 이번 주 복권 추첨이 아직 진행되지 않았습니다!\n\n" + "\n".join(ticket_messages))
            return

        winning_numbers = set(lotto_data["numbers"])
        total_prize = 0
        result_messages = []

        for idx, ticket in enumerate(tickets, start=1):
            matched = len(set(ticket) & winning_numbers)
            prize = 0

            if matched == 6:
                prize = 100000000  # 1등 (1억 원)
                result_messages.append(f"🏆 `{idx}번`: `{sorted(ticket)}` → **1등 (100,000,000원)** 🎉")
            elif matched == 5:
                prize = 5000000  # 2등 (500만 원)
                result_messages.append(f"🥈 `{idx}번`: `{sorted(ticket)}` → **2등 (5,000,000원)** 🎊")
            elif matched == 4:
                prize = 500000  # 3등 (50만 원)
                result_messages.append(f"🥉 `{idx}번`: `{sorted(ticket)}` → **3등 (500,000원)** 🎉")
            elif matched == 3:
                prize = 5000  # 4등 (5천 원)
                result_messages.append(f"💰 `{idx}번`: `{sorted(ticket)}` → **4등 (5,000원)** 🎊")
            else:
                result_messages.append(f"❌ `{idx}번`: `{sorted(ticket)}` → **꽝**")

            total_prize += prize

        if total_prize > 0:
            self.db.users.update_one({"_id": user_id}, {"$inc": {"money": total_prize}})

        await ctx.send("📜 **이번 주 복권 번호 목록**\n" + "\n".join(ticket_messages) +
                       "\n\n🎯 **당첨 결과:**\n" + "\n".join(result_messages) +
                       f"\n\n💰 **총 당첨 금액:** {total_prize:,}원")

async def setup(bot):
    await bot.add_cog(Lotto(bot))

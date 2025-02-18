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

###############################################
# 1. 전역 체크 함수 (주식 시즌 체크)
###############################################
def global_stock_season_check(ctx):
    """
    주식 명령어는 매월 1일 0시 10분부터 26일 0시 10분까지 사용 가능합니다.
    복권 관련 명령어(Lotto Cog)는 언제든 사용 가능하도록 예외 처리합니다.
    """
    # Lotto Cog에 속한 명령어는 언제든 허용
    if ctx.command and ctx.command.cog and ctx.command.cog.qualified_name == "Lotto":
        return True

    now = datetime.now(pytz.timezone("Asia/Seoul"))
    try:
        # 현재 달의 1일 0시10분 (새 시즌 시작)
        season_start = now.replace(day=1, hour=0, minute=10, second=0, microsecond=0)
        # 현재 달의 26일 0시10분 (시즌 종료)
        season_end = now.replace(day=26, hour=0, minute=10, second=0, microsecond=0)
    except ValueError:
        # (예외 상황 발생 시 기본적으로 허용)
        return True

    if season_start <= now < season_end:
        return True
    else:
        raise commands.CheckFailure(
            "현재는 주식 시즌이 아닙니다. 주식 명령어는 매월 1일 0시 10분부터 26일 0시 10분까지 사용 가능합니다!"
        )

# 메인 봇 파일에서 아래와 같이 전역 체크를 추가하세요.
# 예시:
#   bot = commands.Bot(command_prefix="#")
#   bot.add_check(global_stock_season_check)

###############################################
# 2. Lotto Cog (복권 관련 명령어)
###############################################
class Lotto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]
        self.last_reset_month = None

        # 봇 실행 시 복권 추첨 태스크와 초기화 태스크 시작
        self.lotto_draw_task.start()
        self.lotto_reset_task.start()

    def cog_unload(self):
        """Cog이 언로드될 때 태스크 종료"""
        self.lotto_draw_task.cancel()
        self.lotto_reset_task.cancel()

    def get_seoul_time(self):
        """현재 한국 시간 반환"""
        return datetime.now(pytz.timezone("Asia/Seoul"))

    def get_next_lotto_draw_time(self):
        """
        현재 시각을 기준으로 다음 로또 추첨일(매주 일요일 21:00)을 계산합니다.
        """
        now = self.get_seoul_time()
        # 오늘 요일에 따라 일요일까지 남은 일수 계산 (일요일: weekday()==6)
        days_until_sunday = (6 - now.weekday()) % 7
        candidate = now.replace(hour=21, minute=0, second=0, microsecond=0) + timedelta(days=days_until_sunday)
        # 만약 오늘이 일요일이고 이미 21시가 지났다면 다음 일요일로 설정
        if now.weekday() == 6 and now >= now.replace(hour=21, minute=0, second=0, microsecond=0):
            candidate += timedelta(days=7)
        return candidate

    @commands.command(name="복권구매")
    async def buy_lotto(self, ctx, ticket_count: int):
        """
        #복권구매 [n] : 1장당 5,000원, 최대 10장까지 구매 가능
        ※ 복권은 주식 돈을 사용하지만, 복권 명령어는 언제든 사용할 수 있습니다.
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        now = self.get_seoul_time()
        # 현재 주식 시즌의 시작과 종료 시각 계산
        season_start = now.replace(day=1, hour=0, minute=10, second=0, microsecond=0)
        season_end = now.replace(day=26, hour=0, minute=10, second=0, microsecond=0)
        # 다음 로또 추첨일 계산
        next_draw = self.get_next_lotto_draw_time()
        if not (season_start <= next_draw < season_end):
            await ctx.send("❌ 다음 로또 추첨일이 현재 주식 시즌에 포함되지 않으므로 복권 구매가 불가능합니다!")
            return

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
            self.db.lotto.delete_one({"_id": user_id})  # 새 주가 시작되면 초기화

        # 1~45 중 6개 랜덤 선택으로 복권 티켓 생성
        tickets = [sorted(random.sample(range(1, 46), 6)) for _ in range(ticket_count)]
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
        #복권확인 : 본인의 복권 번호 및 당첨 여부 확인 (추첨 전에도 확인 가능)
        """
        user_id = str(ctx.author.id)
        current_week = self.get_seoul_time().strftime("%Y-%W")
        user_lotto = self.db.lotto.find_one({"_id": user_id})

        if not user_lotto or user_lotto.get("week") != current_week:
            await ctx.send("🎟 이번 주에 구매한 복권이 없습니다!")
            return

        # 사용자가 구매한 복권 번호 나열
        tickets = user_lotto["tickets"]
        ticket_messages = [f"🎟 `{i+1}번`: `{ticket}`" for i, ticket in enumerate(tickets)]

        # 이번 주 복권 추첨 결과 확인
        lotto_data = self.db.lotto_result.find_one({"week": current_week})
        if not lotto_data:
            await ctx.send("📢 이번 주 복권 추첨이 아직 진행되지 않았습니다!\n\n" + "\n".join(ticket_messages))
            return

        winning_numbers = set(lotto_data["numbers"])
        total_prize = 0
        result_messages = []

        for idx, ticket in enumerate(tickets, start=1):
            matched = len(set(ticket) & winning_numbers)
            prize = {6: 100000000, 5: 5000000, 4: 500000, 3: 5000}.get(matched, 0)
            total_prize += prize
            result_messages.append(
                f"🎟 `{idx}번`: `{ticket}` → `{matched}개 일치` {'🎉 당첨!' if prize > 0 else '❌ 꽝'}"
            )

        if total_prize > 0:
            self.db.users.update_one({"_id": user_id}, {"$inc": {"money": total_prize}})

        await ctx.send(
            "📜 **이번 주 복권 번호 목록**\n" + "\n".join(ticket_messages) +
            "\n\n🎯 **당첨 결과:**\n" + "\n".join(result_messages) +
            f"\n\n💰 **총 당첨 금액:** {total_prize:,}원"
        )

    @tasks.loop(hours=1)  # 매 시간마다 실행하여 일요일 21시 감지
    async def lotto_draw_task(self):
        """매주 일요일 21:00 자동 복권 추첨"""
        now = self.get_seoul_time()
        if now.weekday() == 6 and now.hour == 21:
            current_week = now.strftime("%Y-%W")
            winning_numbers = sorted(random.sample(range(1, 46), 6))

            self.db.lotto_result.update_one(
                {"week": current_week},
                {"$set": {"numbers": winning_numbers}},
                upsert=True
            )

            channel = self.bot.get_channel(YOUR_CHANNEL_ID)  # 결과 발표 채널 ID 설정
            if channel:
                await channel.send(f"🎉 이번 주 복권 당첨 번호: `{' '.join(map(str, winning_numbers))}`")

    @lotto_draw_task.before_loop
    async def before_lotto_draw(self):
        """봇이 준비될 때까지 대기"""
        await self.bot.wait_until_ready()
    
    @tasks.loop(minutes=1)
    async def lotto_reset_task(self):
        """매월 26일 0시 10분에 복권 데이터 초기화"""
        now = self.get_seoul_time()
        if now.day == 26 and now.hour == 0 and now.minute == 10:
            # 같은 달에 이미 초기화하지 않았다면
            if self.last_reset_month != now.month:
                # 복권 구매 내역과 추첨 결과 모두 초기화
                self.db.lotto.delete_many({})
                self.db.lotto_result.delete_many({})
                self.last_reset_month = now.month
                channel = self.bot.get_channel(YOUR_CHANNEL_ID)  # 결과 발표 채널 ID 설정
                if channel:
                    await channel.send("📢 복권 데이터가 초기화되었습니다. 새로운 시즌을 시작합니다!")

async def setup(bot):
    await bot.add_cog(Lotto(bot))

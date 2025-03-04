import os
import discord
from discord.ext import commands
import random
import asyncio
from pymongo import MongoClient

# ===== 상수 설정 =====
RACE_TRACK_LENGTH = 20      # 레이스 트랙 길이 (칸 수)
RACE_DELAY = 1              # 각 업데이트 간 대기 시간 (초)
PAYOUT_MULTIPLIER = 2       # 승리 시 베팅금액의 배수 지급 (예: 2배 지급)

# MongoDB 설정 (기존 StockMarket 코드와 동일)
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

class RaceGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]

    def cog_unload(self):
        self.mongo_client.close()

    @commands.command(name="레이스베팅")
    async def race_bet(self, ctx, choice: str, bet: str):
        """
        #레이스베팅 [레인선택] [베팅금]:
        현금만을 이용하여 레이스 게임에 참여합니다.
        
        예시: `#레이스베팅 1 50000`
         - 1번 레인을 선택하고 50,000원을 베팅하여 경주에 참여합니다.
        
        게임 규칙:
        - 1번, 2번, 3번 총 3개의 레인이 있습니다.
        - 각 레인은 랜덤한 속도로 전진하며, 먼저 결승선(트랙 길이 도달)을 통과한 레인이 승리합니다.
        - 베팅 금액은 즉시 현금(예금이 아님)에서 차감되며,
          선택한 레인이 승리할 경우 베팅 금액의 **{PAYOUT_MULTIPLIER}배**를 상금으로 획득합니다.
        """
        # 레인 선택 검증: 1, 2, 3 중 하나여야 함
        if choice not in ["1", "2", "3"]:
            await ctx.send("레인 선택은 1, 2 또는 3 중 하나여야 합니다.")
            return
        chosen_lane = int(choice)

        # 베팅 금액 처리 (콤마 제거 후 정수 변환)
        try:
            bet_amount = int(bet.replace(",", ""))
            if bet_amount <= 0:
                await ctx.send("베팅 금액은 1원 이상이어야 합니다.")
                return
        except Exception:
            await ctx.send("베팅 금액을 올바르게 입력해주세요.")
            return

        # 사용자 조회 (주식 게임 참가 여부 확인)
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. 먼저 `#주식참가`를 사용해주세요.")
            return

        # 현금(= money)만 사용하여 베팅 가능 여부 확인
        cash = user.get("money", 0)
        if cash < bet_amount:
            await ctx.send("현금 잔액이 부족합니다.")
            return

        # 베팅 금액 차감
        new_cash = cash - bet_amount
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_cash}})

        # 레이스 초기화: 3개 레인의 시작 위치는 0
        lanes = {1: 0, 2: 0, 3: 0}
        race_message = await ctx.send(
            f"레이스 시작! 베팅 금액: {bet_amount:,}원, 선택한 레인: {chosen_lane}"
        )

        finished = False
        winner = None

        # 레이스 시뮬레이션 (각 업데이트마다 각 레인이 랜덤하게 전진)
        while not finished:
            for lane in lanes:
                lanes[lane] += random.randint(1, 3)
                if lanes[lane] >= RACE_TRACK_LENGTH:
                    finished = True
                    winner = lane
                    lanes[lane] = RACE_TRACK_LENGTH
                    break

            # 각 레인의 진행 상황 출력
            display = ""
            for lane in range(1, 4):
                progress = "─" * lanes[lane]
                remaining = " " * (RACE_TRACK_LENGTH - lanes[lane])
                finish_flag = "🏁" if lanes[lane] >= RACE_TRACK_LENGTH else ""
                display += f"레인 {lane}: |{progress}{finish_flag}{remaining}|\n"
            await race_message.edit(content=display)
            await asyncio.sleep(RACE_DELAY)

        # 레이스 종료 및 결과 처리
        result_msg = f"레이스 종료! 승리한 레인: {winner}\n"
        if winner == chosen_lane:
            win_amount = bet_amount * PAYOUT_MULTIPLIER
            updated_cash = new_cash + win_amount
            self.db.users.update_one({"_id": user_id}, {"$set": {"money": updated_cash}})
            result_msg += (
                f"축하합니다! 베팅에 성공하여 {win_amount:,}원을 획득했습니다.\n"
                f"현재 현금 잔액: {updated_cash:,}원"
            )
        else:
            result_msg += f"아쉽게도 베팅에 실패하였습니다. 현재 현금 잔액: {new_cash:,}원"

        await ctx.send(result_msg)

async def setup(bot):
    await bot.add_cog(RaceGame(bot))

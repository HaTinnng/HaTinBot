import os
import discord
from discord.ext import commands
import random
import asyncio
from pymongo import MongoClient

# ===== 상수 설정 =====
RACE_TRACK_LENGTH = 20      # S와 🏁 사이의 칸 수
RACE_DELAY = 1              # 레이스 진행 시 업데이트 간격 (초)
AUTO_START_DELAY = 120      # 방 생성 후 자동 시작까지 대기 시간 (2분)

# MongoDB 설정 (주식 게임과 동일 DB 사용)
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

# 사용 가능한 동물 이모지 목록
ANIMAL_EMOJIS = ["🐢", "🐇", "🦊", "🐼", "🐒", "🐰", "🦄", "🐻"]

class MultiRaceGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]
        self.current_race = None  # 현재 진행 중인 레이스 방 정보

    def cog_unload(self):
        self.mongo_client.close()

    async def auto_start_race(self):
        """자동 시작 타이머: 방 생성 후 AUTO_START_DELAY(2분) 후 레이스 시작"""
        await asyncio.sleep(AUTO_START_DELAY)
        if self.current_race and not self.current_race.get("started", False):
            channel = self.current_race["channel"]
            await channel.send("자동 시작 시간이 도래했습니다. 레이스를 시작합니다!")
            await self.start_race()

    @commands.command(name="레이스참가")
    async def join_race(self, ctx, bet: str):
        """
        #레이스참가 [금액]:
        멀티 레이스 방에 참가합니다.
        - 입력한 금액만큼 현금을 베팅하고, 방이 없으면 새 방을 생성합니다.
        - 방이 생성되면 2분 후 자동으로 레이스가 시작됩니다.
        """
        # 베팅 금액 파싱 (콤마 제거 후 정수 변환)
        try:
            bet_amount = int(bet.replace(",", ""))
            if bet_amount <= 0:
                await ctx.send("베팅 금액은 1원 이상이어야 합니다.")
                return
        except Exception:
            await ctx.send("베팅 금액을 올바르게 입력해주세요.")
            return

        user_id = str(ctx.author.id)
        # DB에서 사용자 조회 (주식 게임 참가 여부 확인)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. 먼저 `#주식참가`를 사용해주세요.")
            return

        cash = user.get("money", 0)
        if cash < bet_amount:
            await ctx.send("현금 잔액이 부족합니다.")
            return

        # 베팅 금액 차감
        new_cash = cash - bet_amount
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_cash}})

        # 현재 진행 중인 레이스 방이 없거나 이미 시작된 경우 새 방 생성
        if self.current_race is None or self.current_race.get("started", False):
            self.current_race = {
                "participants": [],
                "total_bet": 0,
                "channel": ctx.channel,
                "race_message": None,
                "auto_start_task": None,
                "started": False
            }
            # 자동 시작 타이머 시작
            self.current_race["auto_start_task"] = asyncio.create_task(self.auto_start_race())

        # 이미 참가한 사용자면 중복 참가 방지
        for participant in self.current_race["participants"]:
            if participant["user_id"] == user_id:
                await ctx.send(f"{ctx.author.mention}, 이미 레이스에 참가하셨습니다.")
                return

        # 참가자 추가 (랜덤 동물 이모지 할당)
        participant = {
            "user_id": user_id,
            "username": ctx.author.display_name,
            "bet": bet_amount,
            "position": 0,
            "emoji": random.choice(ANIMAL_EMOJIS)
        }
        self.current_race["participants"].append(participant)
        self.current_race["total_bet"] += bet_amount

        await ctx.send(f"{ctx.author.mention}님이 {bet_amount:,}원을 베팅하고 레이스에 참가하셨습니다! (현재 참가자 수: {len(self.current_race['participants'])})")

    @commands.command(name="레이스시작")
    async def manual_start_race(self, ctx):
        """
        #레이스시작:
        현재 방의 레이스를 수동으로 시작합니다.
        """
        if self.current_race is None:
            await ctx.send("현재 진행 중인 레이스 방이 없습니다.")
            return
        if self.current_race.get("started", False):
            await ctx.send("이미 레이스가 시작되었습니다.")
            return
        # 자동 시작 타이머 취소 (수동 시작 시)
        if self.current_race.get("auto_start_task"):
            self.current_race["auto_start_task"].cancel()
            self.current_race["auto_start_task"] = None

        await ctx.send("수동 명령으로 레이스를 시작합니다!")
        await self.start_race()

    async def start_race(self):
        """실제 레이스 시뮬레이션을 진행하고, 우승자에게 베팅 풀 금액을 지급합니다."""
        if self.current_race is None or len(self.current_race["participants"]) == 0:
            return

        self.current_race["started"] = True
        channel = self.current_race["channel"]
        participants = self.current_race["participants"]

        # 모든 참가자의 위치 초기화
        for participant in participants:
            participant["position"] = 0

        # 초기 레이스 진행 메시지 생성
        race_msg = await channel.send("레이스 준비중...")
        self.current_race["race_message"] = race_msg

        finished = False
        winner = None

        # 레이스 진행 루프
        while not finished:
            for participant in participants:
                # 각 참가자가 1~3칸씩 전진
                participant["position"] += random.randint(1, 3)
                if participant["position"] >= RACE_TRACK_LENGTH:
                    participant["position"] = RACE_TRACK_LENGTH
                    finished = True
                    winner = participant
                    break

            # 레이스 진행 상황 표시 (각 참가자별로 고정된 시작점과 도착점 사이에서 동물 이모지가 이동)
            display = "🐾 **멀티 레이스 진행 상황** 🏁\n\n"
            for idx, participant in enumerate(participants, start=1):
                pos = participant["position"]
                # 고정된 시작점(S)과 도착점(🏁) 사이에 pos 칸만큼 '-' 표시 후 동물 이모지 삽입
                track = "S" + "-" * pos + participant["emoji"] + "-" * (RACE_TRACK_LENGTH - pos) + "🏁"
                display += f"레인 {idx} ({participant['username']}): {track}\n"
            await race_msg.edit(content=display)
            await asyncio.sleep(RACE_DELAY)

        # 레이스 종료 후 결과 처리
        total_pool = self.current_race["total_bet"]
        winner_id = winner["user_id"]
        winner_name = winner["username"]
        result_msg = f"레이스 종료! 우승자: {winner_name} (레인 {participants.index(winner)+1})\n"
        result_msg += f"총 베팅금액 {total_pool:,}원을 우승자에게 지급합니다."

        # 우승자에게 베팅 풀 금액 지급 (DB 업데이트)
        winner_record = self.db.users.find_one({"_id": winner_id})
        if winner_record:
            updated_cash = winner_record.get("money", 0) + total_pool
            self.db.users.update_one({"_id": winner_id}, {"$set": {"money": updated_cash}})
            result_msg += f"\n{winner_name}님의 새로운 현금 잔액: {updated_cash:,}원"

        await channel.send(result_msg)
        # 레이스 방 초기화
        self.current_race = None

async def setup(bot):
    await bot.add_cog(MultiRaceGame(bot))

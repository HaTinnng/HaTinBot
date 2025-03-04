import os
import discord
from discord.ext import commands
import random
import asyncio
from pymongo import MongoClient

# ===== 상수 설정 =====
RACE_TRACK_LENGTH = 40      # 시작점(|)과 도착점(🏁) 사이의 칸 수 (40칸)
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
            await channel.send("⏰ 자동 시작 시간이 도래했습니다. 레이스를 시작합니다!")
            await self.start_race()

    @commands.command(name="레이스")
    async def race_help(self, ctx):
        """
        #레이스:
        솔로 레이스 게임 도움말과 멀티플레이 레이스 추가 정보를 함께 출력합니다.
        """
        help_text = (
            "```css\n"
            "[ 솔로 레이스 게임 도움말 ]\n"
            "#레이스베팅 [레인선택] [베팅금] : 선택한 레인에 베팅금액을 걸고 솔로 레이스에 참여합니다.\n"
            "    예) #레이스베팅 1 50000\n"
            "\n"
            "게임 규칙:\n"
            " - 총 3개의 레인이 있으며, 각 레인은 랜덤한 속도로 전진합니다.\n"
            " - 먼저 결승선(트랙 길이 도달)에 도착한 레인이 승리합니다.\n"
            " - 승리 시 베팅 금액의 2배를 상금으로 획득합니다.\n"
            " - 베팅 금액은 즉시 차감됩니다.\n"
            "```\n"
            "```diff\n"
            "[ 멀티 레이스 게임 도움말 ]\n"
            "#레이스참가 [금액] : 방이 없을시 레이스 방을 생성합니다. (방 생성 시 베팅 금액 입력)\n"
            "#레이스참가 [0, .] : 무료로 레이스 방을 생성합니다. (베팅금 X)\n"
            "#레이스참가 : 방이 있을경우 베팅금을 입력할 필요없이 #레이스참가를 입력하면 방장이 베팅한 금액을 자동으로 베팅합니다.\n"
            "#레이스시작 : 현재 생성된 레이스 방의 레이스를 수동으로 시작합니다.\n"
            "#레이스방 : 현재 생성된 레이스 방 정보를 확인합니다.(베팅금, 방장, 참가수, 참가인원)\n"
            "\n"
            "게임 규칙:\n"
            " - 레이스방이 없으면 #레이스참가 베팅액 또는 무료로 방을 만들 수 있습니다.\n"
            " - 방을 만들고 2분뒤에 자동으로 시작합니다.\n"
            " - 승리 시 베팅한 금액을 상금으로 획득합니다.\n"
            " - 베팅 금액은 즉시 차감됩니다.\n"
            "```"
        )
        await ctx.send(help_text)

    @commands.command(name="레이스참가")
    async def join_race(self, ctx, bet: str = None):
        """
        #레이스참가 [금액]:
        멀티 레이스 방에 참가합니다.
        - 새 방을 생성하는 경우, 베팅 금액을 입력해야 합니다.
          (베팅 금액으로 '0' 또는 '.'를 입력하면 무료로 진행됩니다.)
        - 이미 방이 존재하는 경우, 입력 없이 참가하면 방장이 설정한 금액과 동일하게 적용됩니다.
        """
        user_id = str(ctx.author.id)
        # DB에서 사용자 조회 (주식 게임 참가 여부 확인)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. 먼저 `#주식참가`를 사용해주세요.")
            return

        # 새 방 생성 시 (현재 방이 없거나 이미 시작된 경우)
        if self.current_race is None or self.current_race.get("started", False):
            if bet is None:
                await ctx.send("새 방을 생성하려면 베팅 금액을 입력해야 합니다. 예: `#레이스참가 50000` 또는 무료로 진행하려면 `#레이스참가 0` 혹은 `#레이스참가 .`")
                return
            if bet in ["0", "."]:
                bet_amount = 0
            else:
                try:
                    bet_amount = int(bet.replace(",", ""))
                    if bet_amount < 0:
                        await ctx.send("베팅 금액은 0원 이상이어야 합니다.")
                        return
                except Exception:
                    await ctx.send("베팅 금액을 올바르게 입력해주세요.")
                    return
            room_bet = bet_amount
            self.current_race = {
                "participants": [],
                "total_bet": 0,
                "room_bet": room_bet,
                "channel": ctx.channel,
                "race_message": None,
                "auto_start_task": None,
                "started": False
            }
            self.current_race["auto_start_task"] = asyncio.create_task(self.auto_start_race())
        else:
            # 이미 생성된 방이 있는 경우, 베팅 금액은 방장이 설정한 금액으로 자동 적용
            room_bet = self.current_race["room_bet"]
            if bet is not None:
                await ctx.send("이미 생성된 방이 있으므로, 베팅 금액은 방장이 설정한 금액과 동일하게 적용됩니다.")

        # 사용자가 베팅할 금액에 대해 현금 잔액 확인 (무료 게임은 금액 확인 없이 진행)
        cash = user.get("money", 0)
        if room_bet > 0 and cash < room_bet:
            await ctx.send("현금 잔액이 부족합니다.")
            return

        # 베팅 금액 차감 (무료 게임인 경우 차감하지 않음)
        if room_bet > 0:
            new_cash = cash - room_bet
            self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_cash}})
        else:
            new_cash = cash

        # 중복 참가 체크
        for participant in self.current_race["participants"]:
            if participant["user_id"] == user_id:
                await ctx.send(f"{ctx.author.mention}, 이미 레이스에 참가하셨습니다.")
                return

        # 참가자 추가 (랜덤 동물 이모지 할당)
        participant = {
            "user_id": user_id,
            "username": ctx.author.display_name,
            "bet": room_bet,
            "position": 0,
            "emoji": random.choice(ANIMAL_EMOJIS)
        }
        self.current_race["participants"].append(participant)
        self.current_race["total_bet"] += room_bet

        # 꾸며진 메시지 출력
        decoration = "✨🌟✨"
        bet_text = f"{room_bet:,}원" if room_bet > 0 else "무료"
        await ctx.send(f"{decoration} {ctx.author.mention}님이 {bet_text}을(를) 베팅하고 레이스에 참가하셨습니다! 🎉 (현재 참가자 수: {len(self.current_race['participants'])}) {decoration}")

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
        if self.current_race.get("auto_start_task"):
            self.current_race["auto_start_task"].cancel()
            self.current_race["auto_start_task"] = None

        await ctx.send("수동 명령으로 레이스를 시작합니다!")
        await self.start_race()

    @commands.command(name="레이스방")
    async def race_room(self, ctx):
        """
        #레이스방:
        - 방장(첫 참가자)
        - 베팅액
        - 참가자 수 및 참가자 목록
        """
        if self.current_race is None:
            await ctx.send("현재 생성된 레이스 방이 없습니다.")
            return

        participants = self.current_race.get("participants", [])
        room_bet = self.current_race.get("room_bet", 0)
        leader = participants[0]["username"] if participants else "없음"
        num_participants = len(participants)
        participant_names = ", ".join([p["username"] for p in participants]) if participants else "없음"

        info = (
            "════════════════════════════════════════\n"
            "            **🏁 현재 레이스 방 정보 🏁**\n"
            "════════════════════════════════════════\n"
            f"**방장**      : {leader}\n"
            f"**베팅액**    : {room_bet:,}원{' (무료)' if room_bet == 0 else ''}\n"
            f"**참가자 수** : {num_participants}\n"
            f"**참가자**    : {participant_names}\n"
            "════════════════════════════════════════"
        )
        await ctx.send(info)

    async def start_race(self):
        """실제 레이스 시뮬레이션을 진행하고, 우승자에게 베팅 풀 금액을 지급합니다."""
        if self.current_race is None or len(self.current_race["participants"]) == 0:
            return

        self.current_race["started"] = True
        channel = self.current_race["channel"]
        participants = self.current_race["participants"]

        for participant in participants:
            participant["position"] = 0

        race_msg = await channel.send("레이스 준비중...")
        self.current_race["race_message"] = race_msg

        finished = False
        winner = None

        while not finished:
            for participant in participants:
                # 각 참가자가 1~4칸씩 전진
                participant["position"] += random.randint(1, 4)
                if participant["position"] >= RACE_TRACK_LENGTH:
                    participant["position"] = RACE_TRACK_LENGTH
                    finished = True
                    winner = participant
                    break

            # 고정된 시작점(|)과 도착점(🏁) 사이에서 동물 이모지가 이동하는 트랙 표시
            display = "🐾 **멀티 레이스 진행 상황** 🏁\n\n"
            for idx, participant in enumerate(participants, start=1):
                pos = participant["position"]
                track = "|" + "-" * pos + participant["emoji"] + "-" * (RACE_TRACK_LENGTH - pos) + "🏁"
                display += f"레인 {idx} ({participant['username']}): {track}\n"
            await race_msg.edit(content=display)
            await asyncio.sleep(RACE_DELAY)

        total_pool = self.current_race["total_bet"]
        winner_id = winner["user_id"]
        winner_name = winner["username"]
        result_msg = f"🏆 레이스 종료! 우승자: {winner_name} (레인 {participants.index(winner)+1})\n"
        result_msg += f"총 베팅금액 {total_pool:,}원을 우승자에게 지급합니다."

        winner_record = self.db.users.find_one({"_id": winner_id})
        if winner_record:
            updated_cash = winner_record.get("money", 0) + total_pool
            self.db.users.update_one({"_id": winner_id}, {"$set": {"money": updated_cash}})
            result_msg += f"\n🎉 {winner_name}님의 새로운 현금 잔액: {updated_cash:,}원"

        await channel.send(result_msg)
        self.current_race = None

async def setup(bot):
    await bot.add_cog(MultiRaceGame(bot))

import os
import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient

class RaceBetting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 주식 게임과 동일한 DB("stock_game")의 users 컬렉션을 사용합니다.
        self.mongo_client = MongoClient(os.environ.get("MONGODB_URI"))
        self.db = self.mongo_client["stock_game"]
        
        # 경마 ID를 증가시키기 위한 변수
        self.race_counter = 1
        # 현재 시즌 식별자 저장 (예: "2025-02")
        self.current_season = self.get_season_identifier()
        
        # 현재 진행 중인 경마 경기 정보를 초기화합니다.
        self.current_race = self.init_race()
        # 자동 경마 시작 중복 실행 방지를 위한 변수
        self.last_auto_race_min = None
        self.auto_race_loop.start()

    def cog_unload(self):
        self.auto_race_loop.cancel()
        self.mongo_client.close()

    def get_season_identifier(self):
        """
        현재 시즌을 "연도-월" 형식으로 반환합니다.
        만약 현재 날짜가 26일 이상이면 다음 달의 시즌으로 간주합니다.
        """
        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)
        if now.day < 26:
            return f"{now.year}-{now.month:02d}"
        else:
            if now.month == 12:
                return f"{now.year+1}-01"
            else:
                return f"{now.year}-{now.month+1:02d}"

    def check_season_reset(self):
        """
        만약 현재 시즌 식별자와 저장된 시즌 식별자가 다르다면(즉, 새 시즌이 시작되었다면),
        경마 ID를 1로 재설정하고, 현재 경마 및 DB의 경마 결과를 초기화합니다.
        """
        new_season = self.get_season_identifier()
        if self.current_season != new_season:
            self.race_counter = 1
            self.current_race = self.init_race()
            self.db.race_results.delete_many({})
            self.current_season = new_season

    def init_race(self):
        """
        새로운 경마 경기 정보를 초기화합니다.
        - 5마리의 말: 각 말은 번호(id), 이름(name), 배당률(odds)을 가집니다.
        - 경기 정보에는 고유 race_id, 시작 시간, 베팅 내역(bets)을 포함합니다.
        """
        horses = [
            {"id": "1", "name": "썬더번개", "odds": 2.0},
            {"id": "2", "name": "번개돌풍", "odds": 3.5},
            {"id": "3", "name": "자이언트", "odds": 4.0},
            {"id": "4", "name": "바람의전사", "odds": 5.0},
            {"id": "5", "name": "불꽃질주", "odds": 6.0},
        ]
        race = {
            "race_id": self.race_counter,  # 고유 race_id 할당
            "start_time": datetime.now(pytz.timezone("Asia/Seoul")),
            "horses": horses,
            "bets": {}  # 사용자 ID를 key로 한 경기당 한 번의 베팅 내역
        }
        self.race_counter += 1  # 다음 경기를 위해 race_id 증가
        return race

    def is_race_available(self):
        """
        경마 베팅은 주식 게임의 시즌(매월 1일 0시 10분 ~ 26일 0시 10분) 동안에만 이용 가능합니다.
        """
        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)
        season_start = tz.localize(datetime(now.year, now.month, 1, 0, 10, 0))
        season_end = tz.localize(datetime(now.year, now.month, 26, 0, 10, 0))
        return season_start <= now < season_end

    def ensure_race_participation(self, user):
        """
        주식 게임에 등록된 사용자에게 경마용 닉네임(race_nickname)이 설정되어 있지 않다면,
        자동으로 주식 게임의 username을 경마용 닉네임으로 설정합니다.
        """
        if not user.get("race_nickname"):
            nickname = user.get("username", "Unknown")
            self.db.users.update_one({"_id": user["_id"]}, {"$set": {"race_nickname": nickname}})
            user["race_nickname"] = nickname
        return user

    @tasks.loop(minutes=1)
    async def auto_race_loop(self):
        """
        매 분마다 실행하여 한국시간으로 오후 6시(18:00)가 되면 자동으로 경마를 진행합니다.
        단, 시즌 기간 중에만 작동하며, 한 번만 실행되도록 중복을 방지합니다.
        경마 결과는 환경변수 RACE_CHANNEL_ID에 지정된 채널로 전송됩니다.
        """
        self.check_season_reset()
        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)
        if not self.is_race_available():
            return
        if now.hour == 18 and now.minute == 0:
            if self.last_auto_race_min != now.minute:
                self.last_auto_race_min = now.minute
                race_channel_id = os.environ.get("RACE_CHANNEL_ID")
                if race_channel_id:
                    channel = self.bot.get_channel(int(race_channel_id))
                    if channel:
                        await self.run_race(channel)
        else:
            self.last_auto_race_min = None

    async def run_race(self, channel):
        """
        경마를 진행하여 결과를 처리합니다.
        - 베팅이 없으면 경기 진행 없이 종료 메시지를 전송합니다.
        - 베팅이 있는 경우, 각 말의 배당률에 따른 가중치로 우승 말을 결정하고
          베팅 결과를 처리한 후, 결과를 DB의 race_results 컬렉션에 기록하고 채널에 전송합니다.
        """
        self.check_season_reset()
        race = self.current_race
        tz = pytz.timezone("Asia/Seoul")
        current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        if not race["bets"]:
            msg = f"🏇 **경마 결과** 🏇\n현재 경기에서 베팅한 사용자가 없어 경마가 진행되지 않았습니다. ({current_time})"
            self.db.race_results.insert_one({
                "race_id": race["race_id"],
                "timestamp": current_time,
                "winner": None,
                "details": msg
            })
            self.current_race = self.init_race()
            await channel.send(msg)
            return

        horses = race["horses"]
        weights = [1 / horse["odds"] for horse in horses]
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        winner = random.choices(horses, weights=probabilities, k=1)[0]

        msg_lines = [
            f"🏇 **경마 결과** 🏇",
            f"우승 말: **{winner['name']}** (배당률: {winner['odds']:.2f}배) ({current_time})"
        ]
        for user_id, bet in race["bets"].items():
            bet_amount = bet["amount"]
            if bet["horse_id"] == winner["id"]:
                payout = int(bet_amount * winner["odds"])
                msg_lines.append(f"<@{user_id}>님이 베팅에 성공하여 {payout:,}원을 획득하였습니다! (베팅금: {bet_amount:,}원)")
                self.db.users.update_one({"_id": user_id}, {"$inc": {"money": payout}})
                won = True
            else:
                msg_lines.append(f"<@{user_id}>님은 베팅에 실패하였습니다. (베팅금: {bet_amount:,}원)")
                payout = 0
                won = False
            self.db.users.update_one(
                {"_id": user_id},
                {"$push": {"bet_history": {
                    "race_id": race["race_id"],
                    "bet": bet,
                    "won": won,
                    "payout": payout,
                    "timestamp": current_time
                }}}
            )
        full_msg = "\n".join(msg_lines)
        self.db.race_results.insert_one({
            "race_id": race["race_id"],
            "timestamp": current_time,
            "winner": winner["name"],
            "details": full_msg
        })
        self.current_race = self.init_race()
        await channel.send(full_msg)

    @commands.command(name="경마정보")
    async def race_info(self, ctx):
        """
        #경마정보:
        현재 진행 중인 경마 경기의 시작 시간, 참가 가능한 말 목록(번호, 이름, 배당률)과
        자동 경마 시작 예정 시간(한국시간 기준)을 보여줍니다.
        (경마 베팅은 시즌 기간에만 이용 가능합니다.)
        """
        self.check_season_reset()
        if not self.is_race_available():
            await ctx.send("경마 베팅은 현재 시즌 기간에만 이용 가능합니다.")
            return

        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)
        # 자동 경마는 매일 18:00에 시작되므로, 다음 경마 시작 예정 시간을 계산합니다.
        if now.hour < 18:
            next_race_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
        else:
            next_race_time = (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)

        race = self.current_race
        msg_lines = [
            f"**현재 경마 경기 (Race ID: {race['race_id']})**",
            f"경기 시작 시간: {race['start_time'].strftime('%Y-%m-%d %H:%M:%S')}",
            f"자동 경마 시작 예정 시간: {next_race_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "참가 말 목록:"
        ]
        for horse in race["horses"]:
            msg_lines.append(f"번호: {horse['id']} - {horse['name']} (배당률: {horse['odds']:.2f}배)")
        await ctx.send("\n".join(msg_lines))

    @commands.command(name="베팅")
    async def place_bet(self, ctx, horse_identifier: str, amount: str):
        """
        #베팅 [말 번호 또는 이름] [금액 또는 all/전부/올인]:
        현재 경마 경기에서 선택한 말에 금액을 베팅합니다.
        주식 게임의 잔액에서 차감되며, 말 번호 또는 이름 모두 인식됩니다.
        (경마 베팅은 시즌 기간에만 이용 가능합니다.)
        """
        self.check_season_reset()
        if not self.is_race_available():
            await ctx.send("경마 베팅은 현재 시즌 기간에만 이용 가능합니다.")
            return
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가 [이름]`을 사용하여 먼저 참가해주세요.")
            return
        user = self.ensure_race_participation(user)
        selected_horse = None
        for horse in self.current_race["horses"]:
            if horse_identifier == horse["id"] or horse_identifier.lower() == horse["name"].lower():
                selected_horse = horse
                break
        if not selected_horse:
            await ctx.send("존재하지 않는 말입니다. `#경마정보` 명령어로 말 목록을 확인해주세요.")
            return
        special_bet = ["all", "전부", "올인", "다"]
        user_money = user.get("money", 0)
        try:
            if amount.lower() in special_bet:
                bet_amount = user_money
            else:
                bet_amount = int(amount)
                if bet_amount <= 0:
                    await ctx.send("베팅 금액은 1원 이상이어야 합니다.")
                    return
        except Exception:
            await ctx.send("베팅 금액을 올바르게 입력해주세요.")
            return
        if bet_amount > user_money:
            await ctx.send("잔액이 부족합니다.")
            return
        self.current_race["bets"][user_id] = {
            "horse_id": selected_horse["id"],
            "amount": bet_amount
        }
        self.db.users.update_one({"_id": user_id}, {"$inc": {"money": -bet_amount}})
        await ctx.send(f"{ctx.author.mention}님이 {selected_horse['name']}에 {bet_amount:,}원을 베팅하였습니다. (남은 잔액: {user_money - bet_amount:,}원)")

    @commands.command(name="내베팅")
    async def my_bet(self, ctx):
        """
        #내베팅:
        현재 경마 경기에서 본인이 베팅한 내역을 확인합니다.
        (경마 베팅은 시즌 기간에만 이용 가능합니다.)
        """
        self.check_season_reset()
        if not self.is_race_available():
            await ctx.send("경마 베팅은 현재 시즌 기간에만 이용 가능합니다.")
            return
        user_id = str(ctx.author.id)
        bet = self.current_race["bets"].get(user_id)
        if not bet:
            await ctx.send("현재 경기에서 베팅 내역이 없습니다.")
            return
        horse = next((h for h in self.current_race["horses"] if h["id"] == bet["horse_id"]), None)
        horse_name = horse["name"] if horse else "알 수 없음"
        await ctx.send(f"당신은 현재 **{horse_name}**에 {bet['amount']:,}원을 베팅하셨습니다.")

    @commands.command(name="경마시작")
    @commands.has_permissions(administrator=True)
    async def start_race(self, ctx):
        """
        #경마시작:
        관리자가 수동으로 경기 결과를 결정하여 경마를 진행할 수 있습니다.
        (자동 경마는 매일 오후 6시에 진행됩니다.)
        """
        self.check_season_reset()
        if not self.is_race_available():
            await ctx.send("경마 베팅은 현재 시즌 기간에만 이용 가능합니다.")
            return
        await self.run_race(ctx.channel)

    @commands.command(name="경마결과")
    async def race_results(self, ctx):
        """
        #경마결과:
        최근 5회의 경마 경기 결과를 보여줍니다.
        만약 명령어를 입력한 사용자가 해당 경기에서 베팅했다면,
        베팅 성공 여부와 획득 금액(또는 베팅금)을 함께 표시합니다.
        참가하지 않은 경기의 경우 "참가하지 않음"으로 표시합니다.
        """
        self.check_season_reset()
        results_cursor = self.db.race_results.find({}).sort("timestamp", -1).limit(5)
        results = list(results_cursor)
        if not results:
            await ctx.send("아직 경마 결과가 없습니다.")
            return
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        bet_history = user.get("bet_history", []) if user else []
        # 경기 당 한 번의 베팅만 있다고 가정하고, race_id별로 사용자의 베팅 기록을 딕셔너리로 만듭니다.
        user_bets = {record["race_id"]: record for record in bet_history}
        msg_lines = ["**최근 경마 결과:**"]
        for res in results:
            race_id = res.get("race_id", "N/A")
            timestamp = res.get("timestamp", "N/A")
            winner = res.get("winner", "없음")
            line = f"Race ID {race_id} - {timestamp} - 우승: {winner}"
            if race_id in user_bets:
                bet = user_bets[race_id]
                if bet["won"]:
                    line += f" | 당신의 베팅: 성공, 획득: {bet['payout']:,}원"
                else:
                    bet_amount = bet["bet"]["amount"] if "bet" in bet and "amount" in bet["bet"] else 0
                    line += f" | 당신의 베팅: 실패, 베팅금: {bet_amount:,}원"
            else:
                line += " | 참가하지 않음"
            msg_lines.append(line)
        await ctx.send("\n".join(msg_lines))

async def setup(bot):
    await bot.add_cog(RaceBetting(bot))

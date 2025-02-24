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
        
        # 현재 진행 중인 경마 경기 정보를 초기화합니다.
        self.current_race = self.init_race()

    def cog_unload(self):
        self.mongo_client.close()

    def init_race(self):
        """
        새로운 경마 경기 정보를 초기화합니다.
        경기에는 5마리의 말이 있으며, 각 말은 고유 번호, 이름, 배당률을 가집니다.
        베팅 내역은 빈 딕셔너리로 초기화합니다.
        """
        horses = [
            {"id": "1", "name": "썬더번개", "odds": 2.0},
            {"id": "2", "name": "번개돌풍", "odds": 3.5},
            {"id": "3", "name": "자이언트", "odds": 4.0},
            {"id": "4", "name": "바람의전사", "odds": 5.0},
            {"id": "5", "name": "불꽃질주", "odds": 6.0},
        ]
        race = {
            "race_id": 1,  # 경기 ID (필요에 따라 증가시킬 수 있음)
            "start_time": datetime.now(pytz.timezone("Asia/Seoul")),
            "horses": horses,
            "bets": {}  # 사용자 ID를 key로 하여 베팅 내역 저장 (한 경기당 한 번만 베팅 가능)
        }
        return race

    def ensure_race_participation(self, user):
        """
        주식 게임에 등록된 사용자에게 경마 참여용 닉네임(race_nickname)이 설정되어 있지 않다면,
        자동으로 주식 게임의 username을 race_nickname으로 설정합니다.
        """
        if not user.get("race_nickname"):
            nickname = user.get("username", "Unknown")
            self.db.users.update_one({"_id": user["_id"]}, {"$set": {"race_nickname": nickname}})
            user["race_nickname"] = nickname
        return user

    @commands.command(name="경마정보")
    async def race_info(self, ctx):
        """
        #경마정보:
        현재 진행 중인 경마 경기의 시작 시간과 참가 가능한 말 목록(번호, 이름, 배당률)을 보여줍니다.
        """
        race = self.current_race
        msg_lines = [
            f"**현재 경마 경기 (Race ID: {race['race_id']})**",
            f"경기 시작 시간: {race['start_time'].strftime('%Y-%m-%d %H:%M:%S')}",
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
        주식 게임의 잔액에서 차감됩니다.
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가 [이름]`을 사용하여 먼저 참가해주세요.")
            return

        # 자동으로 경마 참여를 보장 (race_nickname 설정)
        user = self.ensure_race_participation(user)

        # 사용자가 입력한 말 식별 (번호 또는 이름)
        selected_horse = None
        for horse in self.current_race["horses"]:
            if horse_identifier == horse["id"] or horse_identifier.lower() == horse["name"].lower():
                selected_horse = horse
                break
        if not selected_horse:
            await ctx.send("존재하지 않는 말입니다. `#경마정보` 명령어로 말 목록을 확인해주세요.")
            return

        # 베팅 금액 결정 (특정 문자열 입력 시 전액 베팅)
        special_bet = ["all", "전부", "올인"]
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

        # 현재 경기의 베팅 내역에 사용자 베팅 기록 추가 (한 경기당 한 번만 베팅 가능)
        self.current_race["bets"][user_id] = {
            "horse_id": selected_horse["id"],
            "amount": bet_amount
        }

        # 주식 게임의 잔액에서 베팅 금액 차감
        self.db.users.update_one({"_id": user_id}, {"$inc": {"money": -bet_amount}})
        await ctx.send(f"{ctx.author.mention}님이 {selected_horse['name']}에 {bet_amount:,}원을 베팅하였습니다. (남은 잔액: {user_money - bet_amount:,}원)")

    @commands.command(name="내베팅")
    async def my_bet(self, ctx):
        """
        #내베팅:
        현재 경마 경기에서 본인이 베팅한 내역을 확인합니다.
        """
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
        관리자가 경기 결과를 결정하여 경마 경기를 진행합니다.
        각 말의 배당률에 따른 가중치로 우승 말을 결정하고,
        베팅한 사용자에게 배당금(베팅금 x 배당률)을 지급하며, 베팅 내역을 기록합니다.
        """
        race = self.current_race
        if not race["bets"]:
            await ctx.send("아직 베팅한 사용자가 없습니다.")
            return

        # 각 말의 당첨 확률 계산 (배당률이 낮을수록 당첨 확률이 높음)
        horses = race["horses"]
        weights = [1 / horse["odds"] for horse in horses]
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        winner = random.choices(horses, weights=probabilities, k=1)[0]

        msg_lines = [
            f"🏇 **경마 결과** 🏇",
            f"우승 말: **{winner['name']}** (배당률: {winner['odds']:.2f}배)"
        ]
        current_time = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
        # 베팅 결과 처리 및 사용자 bet_history 기록
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
        # 경기 종료 후 새로운 경기 초기화
        self.current_race = self.init_race()
        await ctx.send("\n".join(msg_lines))

async def setup(bot):
    await bot.add_cog(RaceBetting(bot))

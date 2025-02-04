import os
import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient

# ===== 상수 설정 =====
JOIN_BONUS = 800000         # 참가 시 지급 자금 (800,000원)
DEFAULT_MONEY = 800000      # 시즌 초기화 후 유저 기본 잔액 (800,000원)
# MongoDB URI는 클라우드에서 비밀변수 MONGODB_URI를 통해 불러옵니다.
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

# ===== DB에 저장할 주식 초기화 함수 =====
def init_stocks():
    """
    17개의 주식을 아래와 같이 초기화합니다.
      - "311유통": 100
      - "썬더타이어": 500 ~ 1000
      - "룡치수산": 3000 ~ 5000
      - "맥턴맥주": 7000 ~ 8000
      - "섹보경아트": 9000 ~ 12000
      - "전차자동차": 18000 ~ 25000
      - "이리여행사": 33000 ~ 42000
      - "디코커피": 50000 ~ 60000
      - "와이제이엔터": 75000 ~ 90000
      - "파피게임사": 120000 ~ 150000
      - "하틴봇전자": 170000 ~ 210000
      - "하틴출판사": 240000 ~ 270000
      - "창훈버거": 300000 ~ 330000
      - "끼룩제약": 375000 (약간의 오차 허용)
      - "날틀식품": 420000 ~ 450000
      - "오십만통신": 500000

    각 종목은 추가적으로 아래 필드를 가집니다.
      - last_change, percent_change: 최근 가격 변동 내역
      - listed: 상장 여부 (이제 가격 변동폭에 따라 조정되므로 별도 상장폐지 처리는 하지 않습니다)
      - history: 최근 5회 가격 기록 (최초값 포함)
    """
    stocks = {}
    stocks["1"] = {
        "_id": "1",
        "name": "311유통",
        "price": random.randint(99, 100),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["2"] = {
        "_id": "2",
        "name": "썬더타이어",
        "price": random.randint(500, 1000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["3"] = {
        "_id": "3",
        "name": "룡치수산",
        "price": random.randint(3000, 5000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["4"] = {
        "_id": "4",
        "name": "맥턴맥주",
        "price": random.randint(7000, 8000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["5"] = {
        "_id": "5",
        "name": "섹보경아트",
        "price": random.randint(9000, 12000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["6"] = {
        "_id": "6",
        "name": "전차자동차",
        "price": random.randint(18000, 25000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["7"] = {
        "_id": "7",
        "name": "이리여행사",
        "price": random.randint(33000, 42000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["8"] = {
        "_id": "8",
        "name": "디코커피",
        "price": random.randint(50000, 60000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["9"] = {
        "_id": "9",
        "name": "와이제이엔터",
        "price": random.randint(75000, 90000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["10"] = {
        "_id": "10",
        "name": "파피게임사",
        "price": random.randint(120000, 150000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["11"] = {
        "_id": "11",
        "name": "하틴봇전자",
        "price": random.randint(170000, 210000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }    
    stocks["12"] = {
        "_id": "12",
        "name": "하틴출판사",
        "price": random.randint(240000, 270000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["13"] = {
        "_id": "13",
        "name": "창훈버거",
        "price": random.randint(300000, 330000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["14"] = {
        "_id": "14",
        "name": "끼룩제약",
        "price": random.randint(374999, 375000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["15"] = {
        "_id": "15",
        "name": "날틀식품",
        "price": random.randint(420000, 450000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    } 
    stocks["16"] = {
        "_id": "16",
        "name": "오십만통신",
        "price": random.randint(499999, 500000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }    
    # 각 종목의 history에 최초 가격 추가
    for s in stocks.values():
        s["history"].append(s["price"])
    return stocks

# ===== Discord Cog: StockMarket =====
class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # MongoDB 연결 (환경변수 MONGODB_URI 사용)
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]

        # season 컬렉션 (단일 문서 _id="season") 초기화
        if self.db.season.find_one({"_id": "season"}) is None:
            season_doc = {
                "_id": "season",
                "year": self.get_seoul_time().year,
                "season_no": 1,
                "last_reset": None
            }
            self.db.season.insert_one(season_doc)

        # stocks 컬렉션 초기화 (문서가 없으면)
        if self.db.stocks.count_documents({}) == 0:
            stocks = init_stocks()
            for stock in stocks.values():
                self.db.stocks.insert_one(stock)

        # users 컬렉션은 사용자가 가입할 때 생성됨

        # ※ 주식 목록 순위 비교를 위한 이전 순서를 저장할 딕셔너리 (주식 _id -> 인덱스)
        self.prev_stock_order = {}

        self.last_update_min = None  # 업데이트한 분 기억
        self.last_reset_month = None  # (year, month) 기준으로 시즌 리셋 여부 체크
        self._last_trading_status = self.is_trading_open()

        # 주기적 작업 시작
        self.stock_update_loop.start()
        self.season_reset_loop.start()
        self.trading_resume_loop.start()

    def cog_unload(self):
        self.stock_update_loop.cancel()
        self.season_reset_loop.cancel()
        self.trading_resume_loop.cancel()
        self.mongo_client.close()

    def get_seoul_time(self):
        return datetime.now(pytz.timezone("Asia/Seoul"))

    def is_trading_open(self):
        """
        거래 가능 여부를 결정합니다.
        매월 1일 00:10부터 3일 00:10 전까지는 거래 중단.
        그 외에는 거래 가능.
        """
        now = self.get_seoul_time()
        if now.day == 1:
            if now.hour == 0 and now.minute < 10:
                return True
            else:
                return False
        elif now.day == 2:
            return False
        elif now.day == 3:
            if now.hour == 0 and now.minute < 10:
                return False
            else:
                return True
        else:
            return True

    def get_next_update_info(self):
        """다음 주식 변동 시각과 남은 시간을 계산하여 반환합니다."""
        now = self.get_seoul_time()
        candidate_times = []
        for m in [0, 20, 40]:
            candidate = now.replace(minute=m, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(hours=1)
            candidate_times.append(candidate)
        next_time = min(candidate_times, key=lambda t: t)
        delta = next_time - now
        return next_time, delta

    def update_stocks(self):
        """
        거래 가능 시간에 주식 가격을 현재 가격의 변동폭 제한 내에서 변동합니다.
          - 기본 변동폭 제한: ±23.78%
          - 단, 주식가가 50원 미만이면 변동폭 제한을 ±100%로 확대합니다.
        단, 이미 상장폐지( listed==False )된 종목은 업데이트하지 않습니다.
        또한 각 종목의 history 필드에 최근 5회 가격을 기록합니다.
        """
        if not self.is_trading_open():
            return

        cursor = self.db.stocks.find({})
        for stock in cursor:
            if not stock.get("listed", True):
                continue  # 상장폐지된 종목은 업데이트하지 않음 (현재는 listed 필드 변경 없이 그대로 유지)

            old_price = stock["price"]
            if old_price < 50:
                limit = 100.0
            else:
                limit = 23.78

            percent_change = random.uniform(-limit, limit)
            new_price = int(old_price * (1 + percent_change / 100))
            new_price = max(new_price, 1)

            update_fields = {
                "last_change": new_price - old_price,
                "percent_change": round(percent_change, 2),
                "price": new_price,
            }
            history = stock.get("history", [])
            history.append(new_price)
            history = history[-5:]
            update_fields["history"] = history

            self.db.stocks.update_one({"_id": stock["_id"]}, {"$set": update_fields})

    @tasks.loop(seconds=10)
    async def stock_update_loop(self):
        """
        매 10초마다 현재 시간이 분이 0, 20, 40분일 때 주식 가격을 업데이트합니다.
        단, 같은 분 내 중복 업데이트는 방지합니다.
        거래가 중단된 시간에는 업데이트하지 않습니다.
        """
        now = self.get_seoul_time()
        if not self.is_trading_open():
            return
        if now.minute in [0, 20, 40]:
            if self.last_update_min != now.minute:
                self.update_stocks()
                self.last_update_min = now.minute

    @tasks.loop(minutes=1)
    async def season_reset_loop(self):
        """
        매 분마다 현재 시간을 확인하여, 매월 1일 00:10에 시즌 종료 및 초기화 처리를 진행합니다.
        시즌 종료 시 모든 유저의 자산을 산출하여 상위 3명에게 칭호를 부여한 후,
        모든 유저의 잔액과 포트폴리오를 초기화(기본금은 800,000원)하고 주식 데이터를 새로 초기화합니다.
        """
        now = self.get_seoul_time()
        if now.day == 1 and now.hour == 0 and now.minute == 10:
            if self.last_reset_month != (now.year, now.month):
                await self.process_season_end(now)
                self.last_reset_month = (now.year, now.month)

    @tasks.loop(minutes=1)
    async def trading_resume_loop(self):
        """
        매 분마다 거래 가능 여부를 확인하여, 매월 3일 00:10에 거래 재개(업데이트 minute 초기화 등)를 처리합니다.
        """
        current_status = self.is_trading_open()
        if current_status and not self._last_trading_status:
            self.last_update_min = None
        self._last_trading_status = current_status

    async def process_season_end(self, now):
        """
        시즌 종료 시 모든 유저의 자산(현금 + 보유 주식 평가액)을 산출하여 상위 3명에게
        칭호("YYYY 시즌N TOP{순위}")를 부여하고, 모든 유저의 잔액과 포트폴리오(구매가 정보 포함)를 초기화합니다.
        주식 데이터는 새로 초기화됩니다.
        """
        ranking = []
        for user in self.db.users.find({}):
            total = user.get("money", DEFAULT_MONEY)
            portfolio = user.get("portfolio", {})
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if stock:
                    total += stock["price"] * holding.get("amount", 0)
            ranking.append((user["_id"], total))
        ranking.sort(key=lambda x: x[1], reverse=True)
        season = self.db.season.find_one({"_id": "season"})
        for idx, (user_id, _) in enumerate(ranking[:3], start=1):
            title = f"{season['year']} 시즌{season['season_no']} TOP{idx}"
            user = self.db.users.find_one({"_id": user_id})
            if user:
                titles = user.get("titles", [])
                if title not in titles:
                    titles.append(title)
                    self.db.users.update_one({"_id": user_id}, {"$set": {"titles": titles}})
        self.db.users.update_many({}, {"$set": {"money": DEFAULT_MONEY, "portfolio": {}}})
        self.db.stocks.delete_many({})
        stocks = init_stocks()
        for stock in stocks.values():
            self.db.stocks.insert_one(stock)
        self.db.season.update_one(
            {"_id": "season"},
            {"$inc": {"season_no": 1}, "$set": {"last_reset": now.strftime("%Y-%m-%d %H:%M:%S")}}
        )

    # ===== 명령어들 =====

    @commands.command(name="주식참가", aliases=["주식참여", "주식시작"])
    async def join_stock(self, ctx, *, username: str = None):
        """
        #주식참가 [이름]:
        최초 참가 시 반드시 이름을 입력해야 하며, 입력한 이름은 이후 #프로필, #랭킹 등에 표시됩니다.
        이름이 입력되지 않으면 경고 메시지를 출력합니다.
        """
        if not username:
            await ctx.send("경고: 주식 게임에 참가하려면 반드시 이름을 입력해야 합니다. 예: `#주식참가 홍길동`")
            return
        user_id = str(ctx.author.id)
        if self.db.users.find_one({"_id": user_id}):
            await ctx.send("이미 주식 게임에 참가하셨습니다.")
            return
        user_doc = {
            "_id": user_id,
            "username": username,
            "money": JOIN_BONUS,
            "portfolio": {},
            "titles": []
        }
        self.db.users.insert_one(user_doc)
        await ctx.send(f"{ctx.author.mention}님, '{username}'이라는 이름으로 주식 게임에 참가하셨습니다! 초기 자금 {JOIN_BONUS}원을 지급받았습니다.")

    @commands.command(name="주식이름변경")
    async def change_username(self, ctx, *, new_name: str = None):
        """
        #주식이름변경 [새이름]:
        사용자가 언제든지 자신의 게임 내 이름을 변경할 수 있습니다.
        """
        if not new_name:
            await ctx.send("새 이름을 입력해주세요. 예: `#주식이름변경 홍길동2`")
            return
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. 먼저 `#주식참가 [이름]`으로 참가해주세요.")
            return
        self.db.users.update_one({"_id": user_id}, {"$set": {"username": new_name}})
        await ctx.send(f"{ctx.author.mention}님의 이름이 '{new_name}'(으)로 변경되었습니다.")

    @commands.command(name="주식초기화")
    @commands.is_owner()
    async def reset_game(self, ctx):
        """
        #주식초기화 (봇 소유자 전용):
        칭호를 제외하고 모든 유저의 잔액과 포트폴리오를 초기화하고, 주식 데이터를 새로 생성합니다.
        """
        self.db.users.update_many({}, {"$set": {"money": DEFAULT_MONEY, "portfolio": {}}})
        self.db.stocks.delete_many({})
        stocks = init_stocks()
        for stock in stocks.values():
            self.db.stocks.insert_one(stock)
        await ctx.send("주식 게임이 초기화되었습니다. (칭호는 유지됩니다.)")

    @commands.command(name="주식", aliases=["주식목록", "현재가"])
    async def show_stocks(self, ctx):
        """
        #주식:
        전체 주식 목록을 **가격 오름차순(낮은 가격 → 높은 가격)** 으로 정렬하여 출력합니다.
        만약 이전 목록에 비해 순위가 변경되었다면 주식 이름 왼쪽에 🔺(상승) 또는 🔻(하락) 아이콘을 표시합니다.
        """
        stocks_list = list(self.db.stocks.find({}).sort("price", 1))
        new_order = {}
        msg_lines = []
        for idx, stock in enumerate(stocks_list):
            new_order[stock["_id"]] = idx
            arrow_change = ""
            if self.prev_stock_order and stock["_id"] in self.prev_stock_order:
                old_index = self.prev_stock_order[stock["_id"]]
                if idx < old_index:
                    arrow_change = "🔺"
                elif idx > old_index:
                    arrow_change = "🔻"
            if stock.get("last_change", 0) > 0:
                arrow = f"🔺{abs(stock['last_change'])}"
            elif stock.get("last_change", 0) < 0:
                arrow = f"🔻{abs(stock['last_change'])}"
            else:
                arrow = "⏺0"
            line = f"{arrow_change}{stock['name']}: {stock['price']}원 ({arrow}) (변동율: {stock['percent_change']}%)"
            msg_lines.append(line)
        self.prev_stock_order = new_order
        await ctx.send("\n".join(msg_lines))

    @commands.command(name="다음변동", aliases=["변동", "변동시간","갱신","다음갱신"])
    async def next_update(self, ctx):
        """#다음변동: 다음 주식 변동 시각과 남은 시간을 안내합니다."""
        next_time, delta = self.get_next_update_info()
        await ctx.send(f"다음 변동 시각: {next_time.strftime('%H:%M:%S')} (남은 시간: {str(delta).split('.')[0]})")

    @commands.command(name="주식구매")
    async def buy_stock(self, ctx, stock_name: str, amount: str):
        """
        #주식구매 [종목명] [수량 또는 all/전부/올인/다/풀매수]:
        해당 주식 종목을 지정 수량 또는 전액으로 구매합니다.
        """
        if not self.is_trading_open():
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return

        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return

        stock = self.db.stocks.find_one({"name": stock_name})
        if not stock:
            await ctx.send("존재하지 않는 주식 종목입니다.")
            return
        if not stock.get("listed", True):
            await ctx.send("해당 주식은 거래할 수 없습니다.")
            return

        special_buy = ["all", "전부", "올인", "다", "풀매수"]
        price = stock["price"]
        try:
            if amount.lower() in special_buy:
                max_shares = user["money"] // price
                if max_shares <= 0:
                    await ctx.send("잔액이 부족하여 구매할 수 없습니다.")
                    return
                buy_amount = max_shares
            else:
                buy_amount = int(amount)
                if buy_amount <= 0:
                    await ctx.send("구매 수량은 1 이상이어야 합니다.")
                    return
        except Exception:
            await ctx.send("구매 수량을 올바르게 입력해주세요.")
            return

        total_cost = price * buy_amount
        if user["money"] < total_cost:
            await ctx.send("잔액이 부족합니다.")
            return

        new_money = user["money"] - total_cost
        portfolio = user.get("portfolio", {})
        if stock["_id"] in portfolio:
            holding = portfolio[stock["_id"]]
            new_amount = holding.get("amount", 0) + buy_amount
            new_total_cost = holding.get("total_cost", 0) + total_cost
            portfolio[stock["_id"]] = {"amount": new_amount, "total_cost": new_total_cost}
        else:
            portfolio[stock["_id"]] = {"amount": buy_amount, "total_cost": total_cost}

        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "portfolio": portfolio}})
        await ctx.send(f"{ctx.author.mention}님이 {stock['name']} 주식을 {buy_amount}주 구매하였습니다. (총 {total_cost}원)")

    @commands.command(name="주식판매")
    async def sell_stock(self, ctx, stock_name: str, amount: str):
        """
        #주식판매 [종목명] [수량 또는 all/전부/올인/다/풀매도]:
        해당 주식 종목을 지정 수량 또는 전량 판매합니다.
        """
        if not self.is_trading_open():
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return

        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return

        stock = self.db.stocks.find_one({"name": stock_name})
        if not stock:
            await ctx.send("존재하지 않는 주식 종목입니다.")
            return
        if not stock.get("listed", True):
            await ctx.send("해당 주식은 거래할 수 없습니다.")
            return

        portfolio = user.get("portfolio", {})
        if stock["_id"] not in portfolio:
            await ctx.send("해당 주식을 보유하고 있지 않습니다.")
            return

        holding = portfolio[stock["_id"]]
        current_amount = holding.get("amount", 0)
        if current_amount <= 0:
            await ctx.send("판매할 주식 보유 수량이 부족합니다.")
            return

        special_sell = ["all", "전부", "올인", "다", "풀매도"]
        try:
            if amount.lower() in special_sell:
                sell_amount = current_amount
            else:
                sell_amount = int(amount)
                if sell_amount <= 0:
                    await ctx.send("판매 수량은 1 이상이어야 합니다.")
                    return
        except Exception:
            await ctx.send("판매 수량을 올바르게 입력해주세요.")
            return

        if sell_amount > current_amount:
            await ctx.send("판매할 주식 보유 수량이 부족합니다.")
            return

        revenue = stock["price"] * sell_amount
        new_money = user["money"] + revenue

        remaining = current_amount - sell_amount
        if remaining > 0:
            avg_price = holding["total_cost"] / current_amount
            new_total_cost = int(avg_price * remaining)
            portfolio[stock["_id"]] = {"amount": remaining, "total_cost": new_total_cost}
        else:
            portfolio.pop(stock["_id"])

        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "portfolio": portfolio}})
        await ctx.send(f"{ctx.author.mention}님이 {stock['name']} 주식을 {sell_amount}주 판매하여 {revenue}원을 획득하였습니다.")

    @commands.command(name="프로필", aliases=["보관함"])
    async def profile(self, ctx):
        """
        #프로필:
        자신의 현금, 각 종목별 보유 주식 수량, 해당 종목의 현재 평가액 및 평균 구매가(구매가 정보)를 포함한 전체 자산을 보여줍니다.
        게임 참가 시 입력한 이름이 표시됩니다.
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return

        portfolio = user.get("portfolio", {})
        total_stock_value = 0
        portfolio_lines = []
        for sid, holding in portfolio.items():
            stock = self.db.stocks.find_one({"_id": sid})
            if not stock:
                continue
            amount = holding.get("amount", 0)
            current_price = stock.get("price", 0)
            stock_value = current_price * amount
            total_stock_value += stock_value
            avg_buy = round(holding.get("total_cost", 0) / amount, 2) if amount > 0 else 0
            portfolio_lines.append(
                f"{stock.get('name', 'Unknown')}: {amount}주 (현재가: {current_price}원, 총액: {stock_value}원, 평균구매가: {avg_buy}원)"
            )
        portfolio_str = "\n".join(portfolio_lines) if portfolio_lines else "보유 주식 없음"
        total_assets = user.get("money", DEFAULT_MONEY) + total_stock_value
        titles_str = ", ".join(user.get("titles", [])) if user.get("titles", []) else "없음"
        username = user.get("username", ctx.author.display_name)
        msg = (
            f"**{username}님의 프로필**\n"
            f"현금 잔액: {user['money']}원\n"
            f"보유 주식 총액: {total_stock_value}원\n"
            f"전체 자산 (현금 + 주식): {total_assets}원\n\n"
            f"보유 주식:\n{portfolio_str}\n"
            f"칭호: {titles_str}"
        )
        await ctx.send(msg)

    @commands.command(name="랭킹")
    async def ranking(self, ctx):
        """
        #랭킹:
        전체 유저의 자산(현금+보유 주식 평가액)을 기준으로 상위 10명을 (유저 id와 게임 내 이름 포함) 출력합니다.
        """
        ranking_list = []
        for user in self.db.users.find({}):
            total = user.get("money", DEFAULT_MONEY)
            portfolio = user.get("portfolio", {})
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if stock:
                    total += stock["price"] * holding.get("amount", 0)
            ranking_list.append((user["_id"], total, user.get("username", "알 수 없음")))
        ranking_list.sort(key=lambda x: x[1], reverse=True)
        msg_lines = ["**랭킹 TOP 10**"]
        for idx, (uid, total, uname) in enumerate(ranking_list[:10], start=1):
            msg_lines.append(f"{idx}. {uname} (ID: {uid}) - {total}원")
        await ctx.send("\n".join(msg_lines))

    @commands.command(name="시즌")
    async def season_info(self, ctx):
        """
        #시즌:
        현재 시즌명과 시즌 종료 시각(다음 달 1일 00:10:00, 한국시간 기준), 남은 시간을 보여줍니다.
        """
        season = self.db.season.find_one({"_id": "season"})
        season_name = f"{season['year']} 시즌{season['season_no']}"
        now = self.get_seoul_time()
        tz = pytz.timezone("Asia/Seoul")
        if now.month == 12:
            next_year = now.year + 1
            next_month = 1
        else:
            next_year = now.year
            next_month = now.month + 1
        season_end = tz.localize(datetime(year=next_year, month=next_month, day=1, hour=0, minute=10, second=0))
        remaining = season_end - now
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        remaining_str = f"{days}일 {hours}시간 {minutes}분 {seconds}초"
    
        await ctx.send(
            f"현재 시즌: **{season_name}**\n"
            f"시즌 종료 시각: {season_end.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"남은 시간: {remaining_str}"
        )

    @commands.command(name="변동내역")
    async def price_history(self, ctx, stock_name: str):
        """
        #변동내역 [주식명]:
        해당 주식의 최근 5회 가격 기록과 각 기록이 바로 이전 대비 상승(🔺),
        하락(🔻), 동일(⏺)했는지를 표시하여 출력합니다.
        """
        stock = self.db.stocks.find_one({"name": stock_name})
        if not stock:
            await ctx.send("존재하지 않는 주식 종목입니다.")
            return
        history = stock.get("history", [])
        if not history:
            await ctx.send("해당 주식의 변동 내역이 없습니다.")
            return
        lines = [f"**{stock_name} 최근 변동 내역**"]
        for i, price in enumerate(history):
            if i == 0:
                arrow = "⏺"
            else:
                prev = history[i-1]
                if price > prev:
                    arrow = "🔺"
                elif price < prev:
                    arrow = "🔻"
                else:
                    arrow = "⏺"
            lines.append(f"{price}원 {arrow}")
        await ctx.send("\n".join(lines))

    @commands.command(name="주식완전초기화")
    @commands.is_owner()
    async def reset_full_game(self, ctx):
        """
        #주식완전초기화 (봇 소유자 전용):
        - **모든 유저 데이터 삭제 (users 컬렉션 완전 삭제)**
        - **모든 주식 데이터 초기화**
        - **시즌 정보는 유지됨**
        - **기존 참가 유저들은 모두 사라지므로 다시 #주식참가를 해야 함**
        """
        confirmation_message = await ctx.send("⚠️ **경고: 주식 게임을 완전히 초기화합니다.** ⚠️\n"
                                              "모든 유저 데이터가 삭제됩니다. 이 작업은 되돌릴 수 없습니다.\n"
                                              "이 작업을 진행하려면 `확인`이라고 입력하세요.")

        def check(m):
            return m.author == ctx.author and m.content == "확인"

        try:
            await self.bot.wait_for("message", check=check, timeout=20)
        except TimeoutError:
            await ctx.send("⏳ 초기화가 취소되었습니다.")
            return

        # 모든 유저 데이터 삭제
        self.db.users.delete_many({})
        
        # 모든 주식 데이터 초기화
        self.db.stocks.delete_many({})
        stocks = init_stocks()
        for stock in stocks.values():
            self.db.stocks.insert_one(stock)

        await ctx.send("✅ **주식 게임이 완전히 초기화되었습니다.**\n"
                       "모든 유저 데이터가 삭제되었으며, 참가하려면 `#주식참가`를 다시 입력해야 합니다.")


async def setup(bot):
    await bot.add_cog(StockMarket(bot))

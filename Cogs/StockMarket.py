import os
import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient
import io
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.font_manager as fm

# ===== 상수 설정 =====
JOIN_BONUS = 750000         # 참가 시 지급 자금 (750,000원)
DEFAULT_MONEY = 750000      # 시즌 초기화 후 유저 기본 잔액 (750,000원)
SUPPORT_AMOUNT = 30000  # 지원금 3만원
# MongoDB URI는 클라우드에서 비밀변수 MONGODB_URI를 통해 불러옵니다.
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

plt.rcParams["axes.unicode_minus"] = False

# ===== DB에 저장할 주식 초기화 함수 =====
def init_stocks():
    """
    17개의 주식을 아래와 같이 초기화합니다.
      - "311유통": 1500
      - "썬더타이어": 3500 ~ 5000
      - "룡치수산": 17000 ~ 19500
      - "맥턴맥주": 32000 ~ 40000
      - "섹보경아트": 64000 ~ 70000
      - "전차자동차": 100000
      - "이리여행사": 155000
      - "디코커피": 280000 ~ 290000
      - "와이제이엔터": 460000 ~ 500000
      - "파피게임사": 650000 ~ 680000
      - "하틴봇전자": 790000 ~ 820000
      - "하틴출판사": 1225000 ~ 1300000
      - "창훈버거": 1755555
      - "끼룩제약": 2250000 ~ 2400000
      - "날틀식품": 3000000
      - "백만통신": 1000000
      - "베스트보험": 10000
      - "후니마트": 4500000

    각 종목은 추가적으로 아래 필드를 가집니다.
      - last_change, percent_change: 최근 가격 변동 내역
      - listed: 상장 여부 (이제 가격 변동폭에 따라 조정되므로 별도 상장폐지 처리는 하지 않습니다)
      - history: 최근 5회 가격 기록 (최초값 포함)
    """
    stocks = {}
    stocks["1"] = {
        "_id": "1",
        "name": "311유통",
        "price": random.randint(1500, 1501),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["2"] = {
        "_id": "2",
        "name": "썬더타이어",
        "price": random.randint(3500, 5000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["3"] = {
        "_id": "3",
        "name": "룡치수산",
        "price": random.randint(17000, 19500),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["4"] = {
        "_id": "4",
        "name": "맥턴맥주",
        "price": random.randint(32000, 40000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["5"] = {
        "_id": "5",
        "name": "섹보경아트",
        "price": random.randint(64000, 70000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["6"] = {
        "_id": "6",
        "name": "전차자동차",
        "price": random.randint(100000, 100001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["7"] = {
        "_id": "7",
        "name": "이리여행사",
        "price": random.randint(155000, 155001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["8"] = {
        "_id": "8",
        "name": "디코커피",
        "price": random.randint(280000, 290000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["9"] = {
        "_id": "9",
        "name": "와이제이엔터",
        "price": random.randint(460000, 500000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["10"] = {
        "_id": "10",
        "name": "파피게임사",
        "price": random.randint(650000, 680000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["11"] = {
        "_id": "11",
        "name": "하틴봇전자",
        "price": random.randint(790000, 820000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }    
    stocks["12"] = {
        "_id": "12",
        "name": "하틴출판사",
        "price": random.randint(1255000, 1300000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["13"] = {
        "_id": "13",
        "name": "창훈버거",
        "price": random.randint(1755555, 1755556),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["14"] = {
        "_id": "14",
        "name": "끼룩제약",
        "price": random.randint(2250000, 2300000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["15"] = {
        "_id": "15",
        "name": "날틀식품",
        "price": random.randint(3000000, 3000001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["16"] = {
        "_id": "16",
        "name": "백만통신",
        "price": random.randint(1000000, 1000001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["17"] = {
        "_id": "17",
        "name": "베스트보험",
        "price": random.randint(10000, 10001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": []
    }
    stocks["18"] = {
        "_id": "18",
        "name": "후니마트",
        "price": random.randint(4500000, 4500001),
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
        self.last_interest_day = None  # 마지막으로 이자가 적용된 날짜 (YYYY-MM-DD)
        self.bank_interest_loop.start()

        # 기존 사용자 문서에 새 필드 추가 (없을 경우에만)
        self.db.users.update_many(
            {"bank": {"$exists": False}},
            {"$set": {"bank": 0}}
        )
        self.db.users.update_many(
            {"loan": {"$exists": False}},
            {"$set": {"loan": {"amount": 0, "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")}}}
        )

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
        self.bank_interest_loop.cancel()

    def get_seoul_time(self):
        return datetime.now(pytz.timezone("Asia/Seoul"))

    def is_trading_open(self):
        """
        거래 가능 여부를 결정합니다.
        거래는 매월 1일 0시 10분부터 26일 0시 10분까지 진행됩니다.
        그 외의 시간에는 거래가 중단됩니다.
        """
        
        now = self.get_seoul_time()
        tz = pytz.timezone("Asia/Seoul")
        # 현재 달의 시즌 시작 및 종료 시각 (0시 10분 기준)
        season_start = tz.localize(datetime(year=now.year, month=now.month, day=1, hour=0, minute=10, second=0))
        season_end = tz.localize(datetime(year=now.year, month=now.month, day=26, hour=0, minute=10, second=0))
        # 현재 시각이 시즌 기간 내에 있으면 거래 가능
        return season_start <= now < season_end


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
        모든 주식의 가격을 20.58% ~ -19.82% 변동폭 내에서 변동합니다.
        가격이 13원 미만이 되면 상장폐지되며, 가격이 0원이 되고 변동이 중단됩니다.
        """
        if not self.is_trading_open():
            return
        
        cursor = self.db.stocks.find({})
        for stock in cursor:
            if not stock.get("listed", True):
                # 상장폐지된 주식은 가격이 0원이 되며, 이후 변동되지 않음
                self.db.stocks.update_one({"_id": stock["_id"]}, {"$set": {"price": 0}})
                continue  # 변동을 적용하지 않음
            
            old_price = stock["price"]
            percent_change = random.uniform(-19.82, 20.58)  # 모든 주식 동일 변동폭 적용
            new_price = int(old_price * (1 + percent_change / 100))
            new_price = max(new_price, 1)
            
            # 가격이 13원 미만이면 상장폐지 처리 (가격 0원으로 설정)
            if new_price < 13:
                self.db.stocks.update_one(
                    {"_id": stock["_id"]},
                    {"$set": {"listed": False, "price": 0}}
                )
                continue

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

    def update_loan_interest(self, user):
        # 사용자 문서에 loan 필드가 없으면 기본값 사용
        loan_info = user.get("loan", {"amount": 0, "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")})
        last_update_str = loan_info.get("last_update")
        try:
            # 파싱 후 서울 타임존을 추가하여 aware datetime 객체로 변환
            tz = pytz.timezone("Asia/Seoul")
            last_update = tz.localize(datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S"))
        except Exception:
            last_update = self.get_seoul_time()
        now = self.get_seoul_time()  # 이 값은 이미 aware datetime
        days_passed = (now - last_update).days
        if days_passed > 0 and loan_info.get("amount", 0) > 0:
            new_amount = int(loan_info["amount"] * (1.03 ** days_passed))
            loan_info["amount"] = new_amount
            loan_info["last_update"] = now.strftime("%Y-%m-%d %H:%M:%S")
            self.db.users.update_one({"_id": user["_id"]}, {"$set": {"loan": loan_info}})
        return loan_info.get("amount", 0)

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
        매 분마다 현재 시간을 확인하여, 매월 26일 0시 10분에 시즌 종료 및 초기화 처리를 진행합니다.
        시즌 종료 시 모든 유저의 자산을 산출하여 상위 3명에게 칭호를 부여한 후,
        모든 유저의 잔액과 포트폴리오를 초기화(기본금은 750,000원)하고 주식 데이터를 새로 초기화합니다.
        """
        now = self.get_seoul_time()
        if now.day == 26 and now.hour == 0 and now.minute == 10:
            if self.last_reset_month != (now.year, now.month):
                await self.process_season_end(now)
                self.last_reset_month = (now.year, now.month)


    @tasks.loop(minutes=1)
    async def trading_resume_loop(self):
        """
        매 분마다 거래 가능 여부를 확인하여, 매월 1일 00:10에 거래 재개(업데이트 minute 초기화 등)를 처리합니다.
        """
        current_status = self.is_trading_open()
        if current_status and not self._last_trading_status:
            self.last_update_min = None
        self._last_trading_status = current_status

    @tasks.loop(minutes=1)
    async def bank_interest_loop(self):
        """
        매 분마다 현재 시간이 0시 0분인 경우 모든 유저의 은행 예금에 0.5% 이자를 추가합니다.
        하루에 한 번만 적용되도록 last_interest_day를 확인합니다.
        """
        now = self.get_seoul_time()
        current_day = now.date()
        if now.hour == 0 and now.minute == 0:
            if self.last_interest_day != current_day:
                # 모든 유저의 bank 필드에 0.5% 이자 적용 (예금 잔액 * 1.005)
                result = self.db.users.update_many(
                    {},
                    [{
                        "$set": {"bank": {"$floor": {"$multiply": ["$bank", 1.005]}}}
                    }]
                )
                print(f"은행 예금 이자 적용: {result.modified_count}명의 유저에게 0.5% 이자 지급됨.")
                self.last_interest_day = current_day

    async def process_season_end(self, now):
        """
        시즌 종료 시 모든 유저의 자산(현금 + 예금 + 보유 주식 평가액 - 대출금)을 산출하여 상위 3명에게
        칭호("YYYY 시즌N TOP{순위}")를 부여한 후, 유저 자산과 주식 데이터를 초기화합니다.
        또한, 시즌 종료 시 TOP3 기록과 함께 시즌 진행 기간을 season_results 컬렉션에 저장합니다.
        """
        ranking = []
        for user in self.db.users.find({}):
            # 현금과 예금 포함
            total = user.get("money", DEFAULT_MONEY) + user.get("bank", 0)
            portfolio = user.get("portfolio", {})
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if stock:
                    total += stock["price"] * holding.get("amount", 0)
            # 대출금 차감 (있다면)
            loan_info = user.get("loan")
            if loan_info and isinstance(loan_info, dict):
                total -= loan_info.get("amount", 0)
            ranking.append((user["_id"], total))
        ranking.sort(key=lambda x: x[1], reverse=True)
        season = self.db.season.find_one({"_id": "season"})
        season_name = f"{season['year']} 시즌{season['season_no']}"

        # 시즌 진행 기간: 이번 달 1일 0시 10분 ~ 26일 0시 10분 (한국 시간 기준)
        tz = pytz.timezone("Asia/Seoul")
        season_start = tz.localize(datetime(year=now.year, month=now.month, day=1, hour=0, minute=10, second=0))
        season_end = tz.localize(datetime(year=now.year, month=now.month, day=26, hour=0, minute=10, second=0))

        # 시즌 결과 기록 문서에 진행 기간 추가
        season_result_doc = {
            "season_name": season_name,
            "start_time": season_start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": season_end.strftime("%Y-%m-%d %H:%M:%S"),
            "results": []
        }
        for idx, (user_id, total_assets) in enumerate(ranking[:3], start=1):
            user = self.db.users.find_one({"_id": user_id})
            if user:
                season_result_doc["results"].append({
                    "rank": idx,
                    "user_id": user_id,
                    "username": user.get("username", "알 수 없음"),
                    "total_assets": total_assets
                })
        self.db.season_results.insert_one(season_result_doc)

        # 칭호 부여 (TOP3) - 메달 이모지 추가
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for idx, (user_id, _) in enumerate(ranking[:3], start=1):
            medal = medals.get(idx, "")
            title = f"{medal} {season['year']} 시즌{season['season_no']} TOP{idx}"
            user = self.db.users.find_one({"_id": user_id})
            if user:
                titles = user.get("titles", [])
                if title not in titles:
                    titles.append(title)
                    self.db.users.update_one({"_id": user_id}, {"$set": {"titles": titles}})

        # 유저 자산과 포트폴리오 초기화, 주식 데이터 초기화
        self.db.users.update_many(
            {},
            {"$set": {
                "money": DEFAULT_MONEY,
                "bank": 0,
                "portfolio": {},
                "loan": {
                    "amount": 0,
                    "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")
                }
            }}
        )
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

        # 앞뒤 공백 제거 후 빈 문자열 체크
        username = username.strip()
        if not username:
            await ctx.send("경고: 올바른 닉네임을 입력해주세요. (공백만 입력할 수 없습니다.)")
            return

        # 중복 닉네임 체크 (이미 사용 중인 닉네임이면 참가 불가)
        if self.db.users.find_one({"username": username}):
            await ctx.send("경고: 이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해주세요.")
            return

        # 닉네임의 최대 글자수 제한 (15글자)
        if len(username) > 15:
            await ctx.send("경고: 닉네임은 최대 15글자까지 입력할 수 있습니다.")
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
            "titles": [],
            "bank": 0,  # 은행 예금 잔액
            "loan": {"amount": 0, "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")}  # 대출 정보
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

    @commands.command(name="주식", aliases=["주식목록", "현재가", "가격","주가"])
    async def show_stocks(self, ctx):
        """
        #주식:
        # 전체 주식 목록을 **가격 오름차순(낮은 가격 → 높은 가격)** 으로 정렬하여 출력합니다.
        # 상장폐지된 주식은 전체 정보가 취소선(~취소선~)으로 표시됩니다.
        """
        stocks_list = list(self.db.stocks.find({}).sort("price", 1))
        new_order = {}
        msg_lines = []
        
        for idx, stock in enumerate(stocks_list):
            new_order[stock["_id"]] = idx
            arrow_change = ""
            
            # 주식 순위 변동 아이콘 (🔺, 🔻)
            if self.prev_stock_order and stock["_id"] in self.prev_stock_order:
                old_index = self.prev_stock_order[stock["_id"]]
                if idx < old_index:
                    arrow_change = "🔺"
                elif idx > old_index:
                    arrow_change = "🔻"

            # 가격 변동 아이콘
            if stock.get("last_change", 0) > 0:
                arrow = f"🔺{abs(stock['last_change']):,}"
            elif stock.get("last_change", 0) < 0:
                arrow = f"🔻{abs(stock['last_change']):,}"
            else:
                arrow = "⏺0"
            
            # 주식 정보 문자열 생성
            stock_info = f"{arrow_change}**{stock['name']}**: `{stock['price']:,}원` ({arrow}) (변동율: `{stock['percent_change']}%`)"
            
            # 상장폐지된 주식은 전체를 취소선 처리
            if not stock.get("listed", True):
                stock_info = f"~~{stock_info}~~"

            # 한 번만 추가 (중복 방지)
            msg_lines.append(stock_info)    
            
        
        self.prev_stock_order = new_order
        
        # 메시지가 너무 길어질 경우 Discord 메시지 길이 제한(2000자)에 맞게 분할 전송
        if not msg_lines:
            await ctx.send("📉 현재 등록된 주식이 없습니다.")
            return
        
        # Discord는 2000자 이상의 메시지를 허용하지 않으므로, 1900자 기준으로 나눠서 전송
        output = "\n".join(msg_lines)
        if len(output) > 1900:
            chunks = [output[i:i + 1900] for i in range(0, len(output), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(output)

    @commands.command(name="다음변동", aliases=["변동", "변동시간","갱신","다음갱신"])
    async def next_update(self, ctx):
        """#다음변동: 다음 주식 변동 시각과 남은 시간을 안내합니다."""
        next_time, delta = self.get_next_update_info()
        await ctx.send(f"다음 변동 시각: {next_time.strftime('%H:%M:%S')} (남은 시간: {str(delta).split('.')[0]})")

    @commands.command(name="주식구매", aliases=["매수"])
    async def buy_stock(self, ctx, stock_name: str = None, amount: str = None):
        """
        #주식구매 [종목명] [수량 또는 all/전부/올인/다/풀매수]:
        - 지정 종목 구매는 기존 로직을 따릅니다.
        - 만약 첫 번째 인자로 "다" (또는 동의어)만 입력하면,
        남은 자금 내에서 매 구매마다 랜덤하게 한 종목을 선택하고,
        해당 종목을 랜덤한 수량(1주 이상, 구매 가능한 최대 수량 내)만큼 구매합니다.
        """
        special_tokens = ["all", "전부", "올인", "다", "풀매수"]
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return

        # 랜덤 구매 분기: 첫 번째 인자가 special token이면 두 번째 인자는 무시
        if stock_name is not None and stock_name.lower() in special_tokens:
            current_money = user.get("money", 0)
            # 거래 가능한 모든 상장 주식 조회
            stocks_list = list(self.db.stocks.find({"listed": True}))
            if not stocks_list:
                await ctx.send("구매 가능한 주식이 없습니다.")
                return

            # 최소 주가 확인
            min_price = min(stock["price"] for stock in stocks_list)
            if current_money < min_price:
                await ctx.send("잔액이 부족하여 어떤 주식도 구매할 수 없습니다.")
                return

            purchases = {}  # {stock_id: 총 구매 주식 수}
            # 잔액으로 최소 1주라도 살 수 있는 경우 계속 진행
            while True:
                affordable_stocks = [s for s in stocks_list if s["price"] <= current_money]
                if not affordable_stocks:
                    break
                # 랜덤하게 주식 선택
                chosen_stock = random.choice(affordable_stocks)
                price = chosen_stock["price"]
                max_possible = current_money // price
                if max_possible < 1:
                    break
                # 구매할 수량을 1주 이상 max_possible 주 사이에서 랜덤 결정
                random_quantity = random.randint(1, max_possible)
                cost = price * random_quantity
                current_money -= cost
                sid = chosen_stock["_id"]
                purchases[sid] = purchases.get(sid, 0) + random_quantity

            # 유저 포트폴리오 업데이트
            portfolio = user.get("portfolio", {})
            for sid, shares in purchases.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if not stock:
                    continue
                cost = stock["price"] * shares
                if sid in portfolio:
                    portfolio[sid]["amount"] += shares
                    portfolio[sid]["total_cost"] += cost
                else:
                    portfolio[sid] = {"amount": shares, "total_cost": cost}
            self.db.users.update_one({"_id": user_id}, {"$set": {"money": current_money, "portfolio": portfolio}})

            # 결과 메시지 작성: 각 주식의 구매 내역과 최종 잔액 표시
            msg_lines = []
            for sid, shares in purchases.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if stock:
                    total_cost = stock["price"] * shares
                    msg_lines.append(f"- {stock['name']} 주식 {shares:,.0f}주 구매 (총 {total_cost:,.0f}원)")
            response = (
                f"{ctx.author.mention}님, 랜덤 매수 명령으로 아래와 같이 구매가 완료되었습니다.\n"
                + "\n".join(msg_lines)
                + f"\n남은 잔액: {current_money:,.0f}원"
            )
            await ctx.send(response)
            return

        # 지정 종목 구매 처리
        if stock_name is None or amount is None:
            await ctx.send("구매할 종목명과 수량을 입력해주세요. 예: `#주식구매 썬더타이어 10`")
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
        await ctx.send(f"{ctx.author.mention}님이 {stock['name']} 주식을 {buy_amount:,.0f}주 구매하였습니다. (총 {total_cost:,.0f}원)")

    @commands.command(name="매도", aliases=["주식판매"])
    async def sell_stock(self, ctx, stock_name: str, amount: str = None):
        """
        #매도 [종목명 또는 다] [수량 또는 다]:
        - 특정 종목의 주식을 지정 수량 또는 전량 판매합니다.
        - 만약 종목명에 "다" (또는 "전부", "전체")를 입력하면, 사용자가 보유한 모든 주식을 매도합니다.
        """
        # 거래 가능 여부 확인
        if not self.is_trading_open():
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return

        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return

        # 만약 stock_name에 "다" (또는 동의어)를 입력하면, 전체 포트폴리오의 주식을 매도합니다.
        if stock_name.lower() in ["다", "전부", "전체", "풀매도", "올인", "all"]:
            portfolio = user.get("portfolio", {})
            if not portfolio:
                await ctx.send("판매할 주식이 없습니다.")
                return
        
            total_revenue = 0
            messages = []
            # 모든 종목에 대해 매도 처리
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if not stock:
                    continue
                current_amount = holding.get("amount", 0)
                if current_amount <= 0:
                    continue
                revenue = stock["price"] * current_amount
                total_revenue += revenue
                messages.append(f"- {stock['name']} 주식 {current_amount:,.0f}주 매도하여 {revenue:,}원 획득")
            new_money = user["money"] + total_revenue
        
            # 포트폴리오 전체 삭제 후 현금 업데이트
            self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "portfolio": {}}})
            await ctx.send(
                f"{ctx.author.mention}님, 보유한 모든 주식을 매도하였습니다.\n"
                f"총 {total_revenue:,.0f}원을 획득하였습니다. (현재 잔액: {new_money:,.0f}원)\n" +
                "\n".join(messages)
            )
            return

        # 특정 종목 매도 처리 (두 번째 인자 amount가 필요)
        if amount is None:
            await ctx.send("판매할 주식 수량을 입력해주세요. (예: `#매도 종목명 10` 또는 `#매도 종목명 다`)")
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
        await ctx.send(
            f"{ctx.author.mention}님이 {stock['name']} 주식을 {sell_amount:,.0f}주 판매하여 {revenue:,}원을 획득하였습니다. (현재 잔액: {new_money:,}원)"
        )

    @commands.command(name="프로필", aliases=["보관함", "자산", "자본"])
    async def profile(self, ctx):
        """
        #프로필:
        자신의 현금, 은행 예금, 각 종목별 보유 주식 수량, 해당 종목의 현재 평가액 및 평균 구매가(구매가 정보)를 포함한 전체 자산과
        대출 금액을 보여줍니다.
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
                f"{stock.get('name', 'Unknown')}: {amount}주 (현재가: {current_price:,}원, 총액: {stock_value:,}원, 평균구매가: {avg_buy:,}원)"
            )
        portfolio_str = "\n".join(portfolio_lines) if portfolio_lines else "보유 주식 없음"
    
        # 현금, 은행 예금, 대출 금액 가져오기
        cash = user.get("money", DEFAULT_MONEY)
        bank = user.get("bank", 0)
        loan_amount = user.get("loan", {}).get("amount", 0)
    
        # 전체 자산은 현금, 예금, 보유 주식의 합에서 대출 금액을 차감합니다.
        total_assets = cash + bank + total_stock_value - loan_amount
        titles_str = ", ".join(user.get("titles", [])) if user.get("titles", []) else "없음"
        username = user.get("username", ctx.author.display_name)
    
        msg = (
            f"**{username}님의 프로필**\n"
            f"현금 잔액: {cash:,.0f}원\n"
            f"은행 예금: {bank:,.0f}원\n"
            f"대출 금액: {loan_amount:,.0f}원\n"
            f"보유 주식 총액: {total_stock_value:,}원\n"
            f"전체 자산 (현금 + 예금 + 주식 - 대출): {total_assets:,.0f}원\n\n"
            f"보유 주식:\n{portfolio_str}\n"
            f"칭호: {titles_str}"
        )
        await ctx.send(msg)

    @commands.command(name="랭킹", aliases=["순위"])
    async def ranking(self, ctx):   
        """
        #랭킹:
        전체 유저의 자산(현금+보유 주식 평가액)을 기준으로 상위 10명을 (유저 id와 게임 내 이름 포함) 출력합니다.
        """
        ranking_list = []
        for user in self.db.users.find({}):
            total = user.get("money", DEFAULT_MONEY) + user.get("bank", 0)
            portfolio = user.get("portfolio", {})
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if stock:
                    total += stock["price"] * holding.get("amount", 0)
            # 대출금(빚)이 있으면 총 자산에서 차감 (대출 정보가 없거나 None이면 0으로 처리)
            loan_info = user.get("loan")
            if loan_info and isinstance(loan_info, dict):
                total -= loan_info.get("amount", 0)
            ranking_list.append((user["_id"], total, user.get("username", "알 수 없음")))
    
        ranking_list.sort(key=lambda x: x[1], reverse=True)
        msg_lines = ["**랭킹 TOP 10**"]
        for idx, (uid, total, uname) in enumerate(ranking_list[:10], start=1):
            msg_lines.append(f"{idx}. {uname} (ID: {uid}) - {total:,.0f}원")
        await ctx.send("\n".join(msg_lines))

    @commands.command(name="시즌")
    async def season_info(self, ctx):
        """
        #시즌:
        현재 시즌명과 시즌 진행 기간(시작: 매월 1일 0시 10분, 종료: 매월 26일 0시 10분),
        남은 시간(현재 시즌 종료까지 또는 다음 시즌 시작까지)을 보여줍니다.
        """
        season = self.db.season.find_one({"_id": "season"})
        season_name = f"{season['year']} 시즌{season['season_no']}"
        now = self.get_seoul_time()
        tz = pytz.timezone("Asia/Seoul")
        
        if now.day < 26:
            # 현재 시즌 진행 중: 이번 달 1일 ~ 26일
            season_start = tz.localize(datetime(year=now.year, month=now.month, day=1, hour=0, minute=10, second=0))
            season_end = tz.localize(datetime(year=now.year, month=now.month, day=26, hour=0, minute=10, second=0))
            remaining = season_end - now
        else:
            # 시즌 종료 후: 다음 시즌 시작 정보를 표시
            if now.month == 12:
                next_year = now.year + 1
                next_month = 1
            else:
                next_year = now.year
                next_month = now.month + 1
            season_start = tz.localize(datetime(year=next_year, month=next_month, day=1, hour=0, minute=10, second=0))
            season_end = tz.localize(datetime(year=next_year, month=next_month, day=26, hour=0, minute=10, second=0))
            remaining = season_start - now

        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        remaining_str = f"{days}일 {hours}시간 {minutes}분 {seconds}초"
    
        await ctx.send(
            f"현재 시즌: **{season_name}**\n"
            f"시즌 기간: {season_start.strftime('%Y-%m-%d %H:%M:%S')} ~ {season_end.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"남은 시간: {remaining_str}"
        )

    @commands.command(name="변동내역")
    async def price_history(self, ctx, stock_name: str):
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
        """
        #변동내역 [주식명]:
        해당 주식의 최근 5회 가격 기록을 Windows 11의 Malgun Gothic 폰트를 사용해
        선 그래프로 출력합니다.
        """
        # 데이터베이스에서 주식 데이터 가져오기
        stock = self.db.stocks.find_one({"name": stock_name})
        if not stock:
            await ctx.send("존재하지 않는 주식 종목입니다.")
            return
        history = stock.get("history", [])
        if not history:
            await ctx.send("해당 주식의 변동 내역이 없습니다.")
            return

        # 1. 커스텀 폰트 파일의 절대 경로 계산 (프로젝트 루트의 fonts 폴더 내 "MyCustomFont.ttf")
        # __file__은 현재 이 Cog 파일의 경로이므로, 프로젝트 루트까지의 경로를 직접 조정합니다.
        # 예를 들어, 현재 폴더(Cogs)에서 상위 폴더로 올라가서 fonts 폴더로 접근하는 경우:
        font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "온글잎 나나양.ttf")
        if not os.path.exists(font_path):
            await ctx.send("커스텀 폰트 파일을 찾을 수 없습니다.")
            return

        # 2. 폰트를 fontManager에 추가하고 FontProperties 생성
        try:
            fm.fontManager.addfont(font_path)
            font_prop = fm.FontProperties(fname=font_path)
            custom_font = font_prop.get_name()
        except Exception as e:
            print("커스텀 폰트 로드 오류:", e)
            custom_font = "sans-serif"
        plt.rcParams["font.family"] = custom_font
        plt.rcParams["axes.unicode_minus"] = False

        # 그래프 그리기
        plt.figure(figsize=(6, 4))
        plt.plot(history, marker='o', linestyle='-', color='blue')
        plt.title(f"{stock_name} 변동 내역", fontsize=16, fontweight="bold")
        plt.xlabel("측정 횟수", fontsize=14)
        plt.ylabel("주가 (원)", fontsize=14)
        plt.grid(True)

        # 각 데이터 포인트 위에 가격 표시 (천 단위 구분 포함)
        for i, price in enumerate(history):
            plt.annotate(
                f"{price:,}",
                xy=(i, price),
                xytext=(-10, 0),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize=10
            )
        # x축 눈금을 -4부터 0까지로 설정 (최근 5회 측정 기준)
        # history의 길이가 5인 경우, 왼쪽부터 -4, -3, -2, -1, 0 으로 표시합니다.
        if len(history) == 5:
            plt.xticks(range(len(history)), [-4, -3, -2, -1, 0])
        else:
            # history의 길이가 다를 경우 동적으로 계산
            plt.xticks(range(len(history)), range(-len(history)+1, 1))

        # 그래프를 이미지로 저장 후 Discord에 전송
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close()

        file = discord.File(fp=buffer, filename="price_history.png")
        await ctx.send(file=file)

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


    @commands.command(name="주식지원금", aliases=["지원금"])
    async def stock_support(self, ctx):
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
        """
        #주식지원금: 하루에 0시와 12시마다 지원금(30,000원)을 받을 수 있습니다.
        마지막 지원 시각이 현재 기간(0시~11시59분 또는 12시~23시59분)보다 이전이면 지원금을 지급합니다.
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가` 명령어로 참가해주세요.")
            return

        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)

        # 현재 시간이 어느 기간에 속하는지 판별합니다.
        # 0시부터 11시59분이면 period_reset은 오늘 0시, 12시부터 23시59분이면 오늘 12시로 지정합니다.
        if now.hour < 12:
            period_reset = tz.localize(datetime(now.year, now.month, now.day, 0, 0, 0))
        else:
            period_reset = tz.localize(datetime(now.year, now.month, now.day, 12, 0, 0))

        # 마지막 지원 시각을 확인합니다.
        last_support_str = user.get("last_support_time", None)
        last_support = None
        if last_support_str:
            try:
                # DB에 저장된 문자열은 "YYYY-MM-DD HH:MM:SS" 형식입니다.
                last_support = tz.localize(datetime.strptime(last_support_str, "%Y-%m-%d %H:%M:%S"))
            except Exception:
                last_support = None

        # 만약 이번 기간(0시 또는 12시 이후)에 이미 지원금을 받았다면 지급하지 않습니다.
        if last_support is not None and last_support >= period_reset:
            await ctx.send(f"{ctx.author.mention}님, 이번 기간에는 이미 지원금을 받으셨습니다!")
            return

        # 지원금 지급: 잔액 업데이트 후 현재 시각을 기록합니다.
        new_money = user.get("money", 0) + SUPPORT_AMOUNT
        self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"money": new_money, "last_support_time": now.strftime("%Y-%m-%d %H:%M:%S")}}
        )

        await ctx.send(
            f"{ctx.author.mention}님, {SUPPORT_AMOUNT:,}원의 지원금을 받았습니다! 현재 잔액: {new_money:,}원\n"
            f"지원금은 매일 0시, 12시에 초기화됩니다."
        )

    @commands.command(name="유저데이터삭제", aliases=["유저삭제"])
    @commands.is_owner()
    async def delete_user_data(self, ctx, user_id: str):
        """
        #유저데이터 [유저ID]: 해당 유저의 모든 데이터를 삭제합니다.
        이후 #주식참가를 해야 다시 참가할 수 있습니다. (관리자 전용)
        """
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("해당 유저 데이터를 찾을 수 없습니다.")
            return

        self.db.users.delete_one({"_id": user_id})
        await ctx.send(f"유저 ID `{user_id}`의 모든 데이터가 삭제되었습니다. 다시 참가하려면 `#주식참가`를 사용해야 합니다.")

    @commands.command(name="주식추가")
    @commands.is_owner()
    async def add_stock(self, ctx, stock_name: str, min_price: int, max_price: int):
        """
        #주식추가 [이름] [최소 가격] [최대 가격]:
        새로운 주식을 추가합니다. (관리자 전용)
        """
        if self.db.stocks.find_one({"name": stock_name}):
            await ctx.send("이미 존재하는 주식입니다.")
            return

        new_stock = {
            "_id": str(self.db.stocks.count_documents({}) + 1),
            "name": stock_name,
            "price": random.randint(min_price, max_price),
            "last_change": 0,
            "percent_change": 0,
            "listed": True,
            "history": []
        }
        new_stock["history"].append(new_stock["price"])  # 최초 가격 기록 추가
        self.db.stocks.insert_one(new_stock)
        await ctx.send(f"✅ 새로운 주식 `{stock_name}`이 추가되었습니다! 초기 가격: {new_stock['price']:,}원")

    @commands.command(name="주식쿠폰입력")
    async def redeem_stock_coupon(self, ctx, coupon_code: str):
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
        """
        #주식쿠폰입력 [쿠폰코드]:
        올바른 쿠폰 코드를 입력하면 해당 쿠폰의 지급 금액을 추가 지급합니다.
        각 유저는 각 쿠폰을 최대 설정한 횟수만큼 사용할 수 있습니다.
        """
        # 여러 쿠폰을 딕셔너리로 관리합니다.
        # 각 쿠폰 코드는 지급 금액과 최대 사용 횟수를 포함합니다.
        valid_coupons = {
            "2025Season2": {"reward": 300000, "max_usage": 1},
            # "": {"reward": 200000, "max_usage": 2} 다음 원하는 거 추가
        }

        if coupon_code not in valid_coupons:
            await ctx.send("❌ 유효하지 않은 쿠폰 코드입니다. 다시 확인해주세요.")
            return

        coupon_data = valid_coupons[coupon_code]
        reward_amount = coupon_data["reward"]
        max_coupon_usage = coupon_data["max_usage"]

        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가` 명령어로 참가해주세요.")
            return

        # 유저별 쿠폰 사용 기록을 "coupon_redemptions" 필드로 관리합니다.
        coupon_usage = user.get("coupon_redemptions", {})
        current_usage = coupon_usage.get(coupon_code, 0)

        if current_usage >= max_coupon_usage:
            await ctx.send("❌ 이미 최대 사용 횟수만큼 쿠폰을 사용하셨습니다.")
            return

        new_money = user.get("money", 0) + reward_amount
        coupon_usage[coupon_code] = current_usage + 1

        self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"money": new_money, "coupon_redemptions": coupon_usage}}
        )

        await ctx.send(
            f"🎉 {ctx.author.mention}님, 쿠폰이 적용되었습니다! `{reward_amount:,}원`을 지급받았습니다.\n"
            f"현재 잔액: `{new_money}원`\n"
            f"이 쿠폰은 총 {max_coupon_usage}회 사용 가능하며, 현재 사용 횟수: {coupon_usage[coupon_code]}회 사용했습니다."
        )


    @commands.command(name="유저정보", aliases=["유저조회"])
    @commands.has_permissions(administrator=True)  # 관리자 권한 필요
    async def get_user_info(self, ctx, user: discord.Member = None):
        """
        #유저정보 [@멘션 또는 ID] :
        # 관리자 전용 명령어로 특정 유저 또는 전체 유저의 자산 정보를 조회합니다.
        """
        if user:
            user_id = str(user.id)
            user_data = self.db.users.find_one({"_id": user_id})
            
            if not user_data:
                await ctx.send(f"❌ `{user.display_name}`님은 주식 시스템에 등록되지 않았습니다.")
                return
                
            # 유저의 총 자산 계산 (현금 + 보유 주식 평가액)
            total_assets = user_data.get("money", 0)
            portfolio = user_data.get("portfolio", {})
            
            for stock_id, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": stock_id})
                if stock:
                    total_assets += stock["price"] * holding.get("amount", 0)
            
            embed = discord.Embed(title="📜 유저 정보", color=discord.Color.blue())
            embed.add_field(name="닉네임", value=user_data.get("username", user.display_name), inline=False)
            embed.add_field(name="디스코드 ID", value=user.id, inline=False)
            embed.add_field(name="총 자산", value=f"{total_assets:,}원", inline=False)
            
            await ctx.send(embed=embed)
            
        else:
            # 전체 유저 조회 (최대 10명까지만 표시)
            users = self.db.users.find({})
            user_list = []
            
            for user_data in users:
                user_id = user_data["_id"]
                discord_user = ctx.guild.get_member(int(user_id))
                nickname = user_data.get("username", "알 수 없음")
                total_assets = user_data.get("money", 0)
                
                portfolio = user_data.get("portfolio", {})
                for stock_id, holding in portfolio.items():
                    stock = self.db.stocks.find_one({"_id": stock_id})
                    if stock:
                        total_assets += stock["price"] * holding.get("amount", 0)
                display_name = discord_user.display_name if discord_user else "탈퇴한 유저"
                user_list.append(f"👤 `{display_name}` (ID: `{user_id}`) - **{total_assets:,}원**")
            
            if not user_list:
                await ctx.send("❌ 등록된 유저가 없습니다.")
                return
            
            # 최대 10명까지 표시
            user_list = user_list[:10]
            
            embed = discord.Embed(title="📜 전체 유저 정보 (상위 10명)", color=discord.Color.green())
            embed.description = "\n".join(user_list)
            await ctx.send(embed=embed)

    @get_user_info.error
    async def get_user_info_error(ctx, error):
        """관리자가 아닌 사용자가 명령어를 사용할 경우 오류 메시지 출력"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 이 명령어는 관리자만 사용할 수 있습니다.")
    
    @commands.command(name="주식종목초기화")
    @commands.is_owner()
    async def reset_stock_items(self, ctx):
        """
        #주식종목초기화 (봇 소유자 전용):
        모든 유저의 보유 주식을 제거하고, 모든 주식 종목을 초기 시작 주가로 복구합니다.
        (유저 데이터는 유지하며, 보유 주식과 주가만 초기화됩니다.)
        """
        # 내부에서 사용할 View 정의 (30초 타임아웃)
        class ConfirmResetView(discord.ui.View):
            def __init__(self, timeout=30):
                super().__init__(timeout=timeout)
                self.value = None  # 사용자가 어떤 버튼을 눌렀는지 저장 (True: 계속, False: 취소)

            @discord.ui.button(label="계속하기", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                # 명령어를 실행한 사용자만 상호작용 가능하도록 체크
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("이 명령어를 실행한 사용자가 아닙니다.", ephemeral=True)
                    return
                self.value = True
                self.stop()
                await interaction.response.send_message("초기화를 진행합니다...", ephemeral=True)

            @discord.ui.button(label="그만두기", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("이 명령어를 실행한 사용자가 아닙니다.", ephemeral=True)
                    return
                self.value = False
                self.stop()
                await interaction.response.send_message("초기화가 취소되었습니다.", ephemeral=True)

        warning_message = (
            "⚠️ **경고: 주식종목초기화를 진행하면 모든 유저의 보유 주식이 제거되고, "
            "모든 주식 종목이 초기 시작 주가로 복구됩니다. 이 작업은 되돌릴 수 없습니다.**\n"
            "계속하시겠습니까?"
        )

        view = ConfirmResetView(timeout=30)
        await ctx.send(warning_message, view=view)

        # 버튼 응답을 30초 동안 대기
        await view.wait()

        if view.value is None:
            await ctx.send("시간 초과로 초기화가 취소되었습니다.")
            return

        if not view.value:
            await ctx.send("초기화가 취소되었습니다.")
            return

        # 초기화 진행: 유저의 보유 주식(포트폴리) 제거
        self.db.users.update_many({}, {"$set": {"portfolio": {}}})

        # 주식 데이터 초기화 (상장폐지된 종목 포함 모두 초기 상태로 복구)
        self.db.stocks.delete_many({})
        stocks = init_stocks()
        for stock in stocks.values():
            self.db.stocks.insert_one(stock)

        await ctx.send("✅ 모든 주식 종목이 초기화되었습니다. 모든 유저의 보유 주식이 제거되었습니다.")
    
    @commands.command(name="칭호지급")
    @commands.is_owner()
    async def award_title(self, ctx, target: str, *, title: str):
        """
        #칭호지급 [유저ID 또는 다] [칭호명]:
        봇 소유자 전용 명령어입니다.
        - 특정 유저의 ID를 입력하면 해당 유저에게 칭호를 부여합니다.
        - "다"를 입력하면 현재 주식 게임에 참가한 모든 유저에게 칭호를 부여합니다.
        단, 해당 유저가 이미 동일한 칭호를 보유 중이면 지급되지 않습니다.
        """
        if target == "다":
            # 전체 유저 중 아직 해당 칭호가 없는 유저들만 업데이트
            result = self.db.users.update_many(
                {"titles": {"$ne": title}},
                {"$addToSet": {"titles": title}}
            )
            if result.modified_count > 0:
                await ctx.send(f"총 {result.modified_count}명의 유저에게 '{title}' 칭호가 부여되었습니다.")
            else:
                await ctx.send("모든 유저가 이미 해당 칭호를 보유하고 있습니다.")
        else:
            user = self.db.users.find_one({"_id": target})
            if not user:
                await ctx.send("해당 유저는 주식 게임에 등록되어 있지 않습니다.")
                return
            if title in user.get("titles", []):
                await ctx.send("해당 유저는 이미 이 칭호를 보유하고 있습니다.")
                return
            self.db.users.update_one(
                {"_id": target},
                {"$addToSet": {"titles": title}}
            )
            await ctx.send(f"유저 `{target}`에게 '{title}' 칭호가 부여되었습니다.")
    
    @commands.command(name="시즌결과")
    async def season_results(self, ctx, *, season_name: str = None):
        """
        #시즌결과:
        - 인자 없이 실행하면 기록된 모든 시즌명을 나열하며, 각 시즌의 시작 날짜와 종료 날짜를 보여줍니다.
          (기록된 시즌이 10개 이상일 경우 페이지네이션을 지원합니다.)
        - 시즌명을 함께 입력하면 해당 시즌의 TOP3 (닉네임, 최종 보유 자금) 결과와
          시즌 진행 기간(시작 날짜 ~ 종료 날짜)을 보여줍니다.
        """
        if season_name is not None:
            # 특정 시즌의 결과 조회
            season_doc = self.db.season_results.find_one({"season_name": season_name})
            if not season_doc:
                await ctx.send(f"'{season_name}' 시즌 결과를 찾을 수 없습니다.")
                return
            results = season_doc.get("results", [])
            if not results:
                await ctx.send(f"'{season_name}' 시즌 결과가 없습니다.")
                return
            # 시즌 진행 기간도 함께 표시
            lines = [
                f"**{season_name} 시즌 TOP3 결과**",
                f"기간: {season_doc.get('start_time', 'N/A')} ~ {season_doc.get('end_time', 'N/A')}"
            ]
            for entry in results:
                lines.append(f"{entry['rank']}위: {entry['username']} - {entry['total_assets']:,}원")
            await ctx.send("\n".join(lines))
        else:
            # 저장된 시즌 목록 조회
            seasons = list(self.db.season_results.find({}))
            if not seasons:
                await ctx.send("아직 기록된 시즌 결과가 없습니다.")
                return

            # 시즌 기록 정렬 (예: "2023 시즌1", "2023 시즌2" 등)
            seasons.sort(key=lambda doc: doc["season_name"])

            # 만약 시즌 기록이 10개 미만이면 단순 목록으로 표시
            if len(seasons) < 10:
                lines = [
                    f"{doc['season_name']}: {doc.get('start_time', 'N/A')} ~ {doc.get('end_time', 'N/A')}"
                    for doc in seasons
                ]
                await ctx.send("기록된 시즌 결과 목록:\n" + "\n".join(lines))
            else:
                # 페이지당 10개씩 표시하도록 함
                items_per_page = 10
                total_pages = (len(seasons) + items_per_page - 1) // items_per_page

                # View 및 버튼 클래스 정의
                class SeasonResultsView(discord.ui.View):
                    def __init__(self, seasons, items_per_page, current_page=0):
                        super().__init__(timeout=60)
                        self.seasons = seasons
                        self.items_per_page = items_per_page
                        self.current_page = current_page
                        self.total_pages = (len(seasons) + items_per_page - 1) // items_per_page
                        self.update_buttons()

                    def update_buttons(self):
                        self.clear_items()
                        self.add_item(PrevButton(self))
                        # 가운데 버튼은 현재 페이지 표시 (클릭 불가)
                        self.add_item(discord.ui.Button(label=f"{self.current_page+1}/{self.total_pages}", style=discord.ButtonStyle.secondary, disabled=True))
                        self.add_item(NextButton(self))

                    def get_page_content(self):
                        start = self.current_page * self.items_per_page
                        end = start + self.items_per_page
                        page_seasons = self.seasons[start:end]
                        lines = [
                            f"{idx+1}. {doc['season_name']}: {doc.get('start_time', 'N/A')} ~ {doc.get('end_time', 'N/A')}"
                            for idx, doc in enumerate(page_seasons, start=start)
                        ]
                        return "\n".join(lines)

                class PrevButton(discord.ui.Button):
                    def __init__(self, view_obj):
                        super().__init__(label="이전", style=discord.ButtonStyle.primary)
                        self.view_obj = view_obj

                    async def callback(self, interaction: discord.Interaction):
                        if self.view_obj.current_page <= 0:
                            await interaction.response.send_message("첫번째 페이지입니다.", ephemeral=True)
                        else:
                            self.view_obj.current_page -= 1
                            self.view_obj.update_buttons()
                            content = self.view_obj.get_page_content()
                            await interaction.response.edit_message(content=content, view=self.view_obj)

                class NextButton(discord.ui.Button):
                    def __init__(self, view_obj):
                        super().__init__(label="다음", style=discord.ButtonStyle.primary)
                        self.view_obj = view_obj

                    async def callback(self, interaction: discord.Interaction):
                        if self.view_obj.current_page >= self.view_obj.total_pages - 1:
                            await interaction.response.send_message("마지막 페이지입니다.", ephemeral=True)
                        else:
                            self.view_obj.current_page += 1
                            self.view_obj.update_buttons()
                            content = self.view_obj.get_page_content()
                            await interaction.response.edit_message(content=content, view=self.view_obj)

                view = SeasonResultsView(seasons, items_per_page)
                content = view.get_page_content()
                await ctx.send(content, view=view)

    @commands.command(name="예금")
    async def deposit(self, ctx, amount: str):
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가`로 참가해주세요.")
            return
        try:
            if amount.lower() in ["all", "전부", "올인", "다", "풀예금"]:
                if user["money"] == 0:
                    await ctx.send("현금 잔액이 0원입니다.")
                    return
                deposit_amount = user["money"]
            else:
                deposit_amount = int(amount)
                if deposit_amount <= 0:
                    await ctx.send("예금액은 1원 이상이어야 합니다.")
                    return
        except Exception:
            await ctx.send("예금액을 올바르게 입력해주세요.")
            return
        if user["money"] < deposit_amount:
            await ctx.send("현금 잔액이 부족합니다.")
            return
        new_money = int(user["money"] - deposit_amount)
        new_bank = int(user.get("bank", 0) + deposit_amount)
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "bank": new_bank}})
        await ctx.send(f"{ctx.author.mention}님, {deposit_amount:,}원이 예금되었습니다. (은행 잔액: {new_bank:,}원, 현금: {new_money:,}원)")

    @commands.command(name="출금")
    async def withdraw(self, ctx, amount: str):
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가`로 참가해주세요.")
            return
        try:
            if amount.lower() in ["all", "전부", "올인", "다", "풀출금"]:
                if user.get("bank", 0) == 0:
                    await ctx.send("예금액이 0원입니다.")
                    return
                withdraw_amount = user.get("bank", 0)
            else:
                withdraw_amount = int(amount)
                if withdraw_amount <= 0:
                    await ctx.send("출금액은 1원 이상이어야 합니다.")
                    return
        except Exception:
            await ctx.send("출금액을 올바르게 입력해주세요.")
            return
        bank_balance = user.get("bank", 0)
        if bank_balance < withdraw_amount:
            await ctx.send("은행 잔액이 부족합니다.")
            return
        new_bank = bank_balance - withdraw_amount
        new_money = user["money"] + withdraw_amount
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "bank": new_bank}})
        await ctx.send(f"{ctx.author.mention}님, {withdraw_amount:,}원이 출금되었습니다. (은행 잔액: {new_bank:,}원, 현금: {new_money:,}원)")

    @commands.command(name="대출")
    async def take_loan(self, ctx, amount: str):
        if '.' in amount:
            await ctx.send("소수점 이하의 금액은 입력할 수 없습니다. 정수 금액만 입력해주세요.")
            return
        
        # 1. 시즌(거래 가능 시간) 체크
        try:
            if not self.is_trading_open():
                await ctx.send("대출 기능은 거래 가능 시간(시즌)에서만 사용할 수 있습니다.")
                return
        except Exception as e:
            await ctx.send(f"시즌 체크 오류: {e}")
            return

        # 2. 사용자 조회
        try:
            user_id = str(ctx.author.id)
            user = self.db.users.find_one({"_id": user_id})
            if not user:
                await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가`로 참가해주세요.")
                return
        except Exception as e:
            await ctx.send(f"사용자 조회 오류: {e}")
            return

        # 3. 대출 이자 업데이트
        try:
            current_loan = self.update_loan_interest(user)
        except Exception as e:
            await ctx.send(f"대출 이자 업데이트 오류: {e}")
            return

        max_loan = 3000000  # 최대 대출 한도

        # 4. 입력값 처리
        try:
            if amount.lower() in ["다", "all", "전부", "풀대출", "올인인"]:
                loan_amount = max_loan - current_loan
                if loan_amount <= 0:
                    await ctx.send("이미 최대 대출 한도에 도달했습니다.")
                    return
            else:
                loan_amount = int(amount)
                if loan_amount <= 0:
                    await ctx.send("대출 금액은 1원 이상이어야 합니다.")
                    return
        except Exception as e:
            await ctx.send(f"대출 금액 처리 오류: {e}")
            return

        if current_loan + loan_amount > max_loan:
            available = max_loan - current_loan
            await ctx.send(f"대출 한도는 총 {max_loan:,}원입니다. 현재 대출 잔액: {current_loan:,}원. 추가로 {available:,}원만 대출 가능합니다.")
            return

        # 5. 사용자 대출 및 현금 정보 업데이트
        try:
            new_loan = current_loan + loan_amount
            new_money = user.get("money", 0) + loan_amount
            loan_update = {
                "amount": new_loan,
                "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "loan": loan_update}})
        except Exception as e:
            await ctx.send(f"대출 정보 업데이트 오류: {e}")
            return

        # 6. 성공 메시지 전송
        try:
            await ctx.send(f"{ctx.author.mention}님, {loan_amount:,}원의 대출을 받았습니다. (현재 대출 잔액: {new_loan:,}원, 현금: {new_money:,}원)")
        except Exception as e:
            await ctx.send(f"메시지 전송 오류: {e}")

    @commands.command(name="대출상환", aliases=["상환"])
    async def repay_loan(self, ctx, amount: str):
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가`로 참가해주세요.")
            return
        current_loan = self.update_loan_interest(user)
        if current_loan == 0:
            await ctx.send("대출금이 0원입니다.")
            return
        try:
            if amount.lower() in ["all", "전부", "올인", "다", "풀상환"]:
                repay_amount = current_loan
            else:
                repay_amount = int(amount)
                if repay_amount <= 0:
                    await ctx.send("상환 금액은 1원 이상이어야 합니다.")
                    return
        except Exception:
            await ctx.send("상환 금액을 올바르게 입력해주세요.")
            return
        if user["money"] < repay_amount:
            await ctx.send("현금 잔액이 부족하여 대출 상환이 불가능합니다.")
            return
        if repay_amount > current_loan:
            repay_amount = current_loan  # 초과 상환 방지
        new_money = user["money"] - repay_amount
        new_loan = current_loan - repay_amount
        loan_update = {
            "amount": new_loan,
            "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "loan": loan_update}})
        await ctx.send(f"{ctx.author.mention}님, {repay_amount:,}원을 대출 상환하였습니다. (남은 대출 잔액: {new_loan:,}원, 현금: {new_money:,}원)")

    @commands.command(name="다음시즌")
    async def next_season(self, ctx):
        """
        #다음시즌:
        현재 진행 중인 시즌이 아닌, 다음에 진행될 시즌에 대한 정보를 출력합니다.
        (시즌 기간은 매월 1일 0시 10분부터 26일 0시 10분까지로 설정)
        """
        now = self.get_seoul_time()
        tz = pytz.timezone("Asia/Seoul")
        
        # 다음 시즌은 항상 현재 달의 시즌이 끝난 후, 즉 다음 달 1일 0시 10분에 시작합니다.
        if now.month == 12:
            next_year = now.year + 1
            next_month = 1
        else:
            next_year = now.year
            next_month = now.month + 1
        
        next_season_start = tz.localize(datetime(next_year, next_month, 1, 0, 10, 0))
        next_season_end = tz.localize(datetime(next_year, next_month, 26, 0, 10, 0))
        
        # 남은 시간을 계산합니다.
        remaining = next_season_start - now
        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        remaining_str = f"{days}일 {hours}시간 {minutes}분 {seconds}초"
        
        await ctx.send(
            f"**다음 시즌 정보**\n"
            f"시즌 기간: {next_season_start.strftime('%Y-%m-%d %H:%M:%S')} ~ {next_season_end.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"시작까지 남은 시간: {remaining_str}"
        )

async def setup(bot):
    await bot.add_cog(StockMarket(bot))

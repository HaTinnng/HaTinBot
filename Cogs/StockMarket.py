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
from urllib.parse import urlparse

# ===== 상수 설정 =====
JOIN_BONUS = 750000         # 참가 시 지급 자금 (750,000원)
DEFAULT_MONEY = 750000      # 시즌 초기화 후 유저 기본 잔액 (750,000원)
SUPPORT_AMOUNT = 30000      # 지원금 3만원
# MongoDB URI는 클라우드에서 비밀변수 MONGODB_URI를 통해 불러옵니다.
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

plt.rcParams["axes.unicode_minus"] = False

# ===== 전역 약어 맵 (정식 '이름'을 키로 사용) =====
ALIAS_MAP = {
    "311유통":    ["311", "유통"],
    "썬더타이어": ["썬더", "타이어"],
    "룡치수산":   ["룡치", "수산"],
    "맥턴맥주":   ["맥턴", "맥주"],
    "섹보경아트": ["섹보", "아트", "섹보경"],
    "전차자동차": ["전차", "자동차"],
    "이리여행사": ["이리", "여행", "여행사"],
    "디코커피":   ["디코", "커피"],
    "와이제이엔터": ["와이제이", "엔터", "YJ", "YJ엔터"],
    "파피게임사": ["파피", "게임", "게임사"],
    "하틴봇전자": ["하틴봇", "전자"],
    "하틴출판사": ["하틴출", "출판"],
    "창훈버거":   ["창훈", "버거"],
    "끼룩제약":   ["끼룩", "제약"],
    "날틀식품":   ["날틀", "식품"],
    "백만통신":   ["백만", "통신"],
    "베스트보험": ["베스트", "보험"],
    "후니마트":   ["후니", "마트"],
}

# ===== DB에 저장할 주식 초기화 함수 =====
def init_stocks():
    """
    18개의 주식을 아래와 같이 초기화합니다.
      - "311유통": 1500
      - "썬더타이어": 3500 ~ 5000
      - "룡치수산": 17000 ~ 19500
      - "맥턴맥주": 32000 ~ 40000
      - "섹보경아트": 64000 ~ 70000
      - "전차자동차": 100000
      - "이리여행사": 125000
      - "디코커피": 190000 ~ 220000
      - "와이제이엔터": 300000 ~ 320000
      - "파피게임사": 410000 ~ 430000
      - "하틴봇전자": 520000 ~ 550000
      - "하틴출판사": 630000 ~ 660000
      - "창훈버거": 750000
      - "끼룩제약": 875000 ~ 900000
      - "날틀식품": 1475000
      - "백만통신": 1000000
      - "베스트보험": 10000
      - "후니마트": 2000000

    각 종목은 추가적으로 아래 필드를 가집니다.
      - last_change, percent_change: 최근 가격 변동 내역
      - listed: 상장 여부
      - history: 최근 5회 가격 기록 (최초값 포함)
      - aliases: 수동 등록 약어 리스트 (부분일치 사용하지 않음)
    """
    stocks = {}
    stocks["1"] = {
        "_id": "1",
        "name": "311유통",
        "price": random.randint(1500, 1501),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["2"] = {
        "_id": "2",
        "name": "썬더타이어",
        "price": random.randint(3500, 5000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["3"] = {
        "_id": "3",
        "name": "룡치수산",
        "price": random.randint(17000, 19500),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["4"] = {
        "_id": "4",
        "name": "맥턴맥주",
        "price": random.randint(32000, 40000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["5"] = {
        "_id": "5",
        "name": "섹보경아트",
        "price": random.randint(64000, 70000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["6"] = {
        "_id": "6",
        "name": "전차자동차",
        "price": random.randint(100000, 100001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["7"] = {
        "_id": "7",
        "name": "이리여행사",
        "price": random.randint(125000, 125001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["8"] = {
        "_id": "8",
        "name": "디코커피",
        "price": random.randint(190000, 220000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["9"] = {
        "_id": "9",
        "name": "와이제이엔터",
        "price": random.randint(300000, 320000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["10"] = {
        "_id": "10",
        "name": "파피게임사",
        "price": random.randint(410000, 430000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["11"] = {
        "_id": "11",
        "name": "하틴봇전자",
        "price": random.randint(520000, 550000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["12"] = {
        "_id": "12",
        "name": "하틴출판사",
        "price": random.randint(630000, 660000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["13"] = {
        "_id": "13",
        "name": "창훈버거",
        "price": random.randint(750000, 750001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["14"] = {
        "_id": "14",
        "name": "끼룩제약",
        "price": random.randint(875000, 900000),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["15"] = {
        "_id": "15",
        "name": "날틀식품",
        "price": random.randint(1475000, 1475001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["16"] = {
        "_id": "16",
        "name": "백만통신",
        "price": random.randint(1000000, 1000001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["17"] = {
        "_id": "17",
        "name": "베스트보험",
        "price": random.randint(10000, 10001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }
    stocks["18"] = {
        "_id": "18",
        "name": "후니마트",
        "price": random.randint(2000000, 2000001),
        "last_change": 0,
        "percent_change": 0,
        "listed": True,
        "history": [],
    }

    # 각 종목의 history 및 aliases 세팅
    for s in stocks.values():
        s["history"].append(s["price"])
        s["aliases"] = ALIAS_MAP.get(s["name"], [])

    return stocks

# ===== Discord Cog: StockMarket =====

# 대출 명령어 내에 사용할 확인용 View 클래스
class LoanConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, loan_amount: int, timeout=30):
        super().__init__(timeout=timeout)
        self.author = author
        self.value = None  # True: 대출 진행, False: 취소
        self.loan_amount = loan_amount  # 실제 대출 원금

    @discord.ui.button(label="예", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("이 명령어를 실행한 사용자가 아닙니다.", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.send_message("대출을 진행합니다.", ephemeral=True)

    @discord.ui.button(label="아니요", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("이 명령어를 실행한 사용자가 아닙니다.", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.send_message("대출 진행이 취소되었습니다.", ephemeral=True)

# 주식 소각 명령어 내에 사용할 확인용 View 클래스
class StockBurnConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, stock_name: str, burn_amount: int, timeout=30):
        super().__init__(timeout=timeout)
        self.author = author
        self.stock_name = stock_name
        self.burn_amount = burn_amount
        self.value = None  # True: 소각 진행, False: 취소

    @discord.ui.button(label="예", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("이 명령어를 실행한 사용자가 아닙니다.", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.send_message("주식 소각을 진행합니다.", ephemeral=True)

    @discord.ui.button(label="아니요", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("이 명령어를 실행한 사용자가 아닙니다.", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.send_message("주식 소각이 취소되었습니다.", ephemeral=True)

class StockMarket(commands.Cog):
    def __init__(self, bot):
        # ---- MongoDB 연결 및 진단 로그 ----
        if not MONGO_URI:
            raise RuntimeError("MONGODB_URI 환경변수가 설정되지 않았습니다.")
        parsed = urlparse(MONGO_URI)
        print(f"[MongoDB] connecting host={parsed.hostname}, scheme={parsed.scheme}")

        self.bot = bot
        try:
            self.mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
            self.mongo_client.admin.command("ping")
        except Exception as e:
            raise RuntimeError(f"MongoDB 연결 실패: {e}")

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

        # 시즌 컬렉션 초기화
        if self.db.season.find_one({"_id": "season"}) is None:
            season_doc = {
                "_id": "season",
                "year": self.get_seoul_time().year,
                "season_no": 1,
                "last_reset": None
            }
            self.db.season.insert_one(season_doc)

        # stocks 컬렉션 초기화 (문서가 없으면 생성)
        if self.db.stocks.count_documents({}) == 0:
            stocks = init_stocks()
            for stock in stocks.values():
                self.db.stocks.insert_one(stock)

        # (마이그레이션) 기존 문서에 aliases 필드 없으면 추가
        self.db.stocks.update_many({"aliases": {"$exists": False}}, {"$set": {"aliases": []}})
        # (중요) 기존 DB 문서에도 전역 ALIAS_MAP을 강제 동기화
        for name, aliases in ALIAS_MAP.items():
            self.db.stocks.update_one({"name": name}, {"$set": {"aliases": aliases}})

        # 내부 상태
        self.prev_stock_order = {}
        self.last_update_min = None
        self.last_reset_month = None
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

    # ===== 유틸 & 검색 =====
    def _normalize(self, s: str) -> str:
        return "".join(s.split()).lower() if isinstance(s, str) else ""

    def find_stock_by_alias_or_name(self, key: str):
        """
        수동 약어(aliases) 또는 정식 이름으로 '정확히' 매칭.
        - 공백 제거/소문자 변환 후 정확 일치만 허용(부분 일치 없음)
        - 여러 종목에 같은 약어가 있으면 모호 에러
        return: (stock_doc or None, error_message or None)
        """
        if not key:
            return None, "종목명을 입력해주세요."
        q = self._normalize(key)

        all_stocks = list(self.db.stocks.find({}))
        hits = []
        for s in all_stocks:
            names = [self._normalize(s.get("name", ""))] + [self._normalize(a) for a in s.get("aliases", [])]
            if q in names:
                hits.append(s)

        if len(hits) == 1:
            return hits[0], None
        if len(hits) == 0:
            return None, f"해당하는 종목을 찾지 못했습니다: `{key}` (등록된 약어/정식명만 인식)"
        return None, f"여러 종목에 같은 약어가 등록되어 모호합니다: {', '.join(s['name'] for s in hits[:10])}"

    def get_seoul_time(self):
        return datetime.now(pytz.timezone("Asia/Seoul"))

    def is_trading_open(self):
        """
        거래 가능 여부를 결정합니다.
        거래는 매월 1일 0시 10분부터 28일 0시 10분까지 진행됩니다.
        """
        now = self.get_seoul_time()
        tz = pytz.timezone("Asia/Seoul")
        season_start = tz.localize(datetime(year=now.year, month=now.month, day=1, hour=0, minute=10, second=0))
        season_end = tz.localize(datetime(year=now.year, month=now.month, day=28, hour=0, minute=10, second=0))
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
        모든 주식의 가격을 18.98% ~ -17.12% 변동폭 내에서 변동합니다.
        가격이 13원 미만이 되면 상장폐지되며, 가격이 0원이 되고 변동이 중단됩니다.
        """
        if not self.is_trading_open():
            return

        cursor = self.db.stocks.find({})
        for stock in cursor:
            if not stock.get("listed", True):
                self.db.stocks.update_one({"_id": stock["_id"]}, {"$set": {"price": 0}})
                continue

            old_price = stock["price"]
            percent_change = random.uniform(-17.12, 18.98)
            new_price = int(old_price * (1 + percent_change / 100))
            new_price = max(new_price, 1)

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
            history = history[-6:]
            update_fields["history"] = history

            self.db.stocks.update_one({"_id": stock["_id"]}, {"$set": update_fields})

    def update_loan_interest(self, user):
        loan_info = user.get("loan", {"amount": 0, "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")})
        last_update_str = loan_info.get("last_update")
        try:
            tz = pytz.timezone("Asia/Seoul")
            last_update = tz.localize(datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S"))
        except Exception:
            last_update = self.get_seoul_time()
        now = self.get_seoul_time()
        days_passed = (now - last_update).days
        if days_passed > 0 and loan_info.get("amount", 0) > 0:
            new_amount = int(loan_info["amount"] * (1.03 ** days_passed))
            loan_info["amount"] = new_amount
            loan_info["last_update"] = now.strftime("%Y-%m-%d %H:%M:%S")
            self.db.users.update_one({"_id": user["_id"]}, {"$set": {"loan": loan_info}})
        return loan_info.get("amount", 0)

    # ===== 루프 태스크 =====
    @tasks.loop(seconds=10)
    async def stock_update_loop(self):
        now = self.get_seoul_time()
        if not self.is_trading_open():
            return
        if now.minute in [0, 20, 40]:
            if self.last_update_min != now.minute:
                self.update_stocks()
                self.last_update_min = now.minute

    @tasks.loop(minutes=1)
    async def season_reset_loop(self):
        now = self.get_seoul_time()
        if now.day == 28 and now.hour == 0 and now.minute == 10:
            if self.last_reset_month != (now.year, now.month):
                await self.process_season_end(now)
                self.last_reset_month = (now.year, now.month)

    @tasks.loop(minutes=1)
    async def trading_resume_loop(self):
        current_status = self.is_trading_open()
        if current_status and not self._last_trading_status:
            self.last_update_min = None
        self._last_trading_status = current_status

    @tasks.loop(minutes=1)
    async def bank_interest_loop(self):
        now = self.get_seoul_time()
        current_day = now.date()
        if now.hour == 0 and now.minute == 0:
            if self.last_interest_day != current_day:
                result = self.db.users.update_many(
                    {},
                    [{"$set": {"bank": {"$floor": {"$multiply": ["$bank", 1.005]}}}}]
                )
                print(f"은행 예금 이자 적용: {result.modified_count}명의 유저에게 0.5% 이자 지급됨.")
                self.last_interest_day = current_day

    async def process_season_end(self, now):
        ranking = []
        for user in self.db.users.find({}):
            total = user.get("money", DEFAULT_MONEY) + user.get("bank", 0)
            portfolio = user.get("portfolio", {})
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if stock:
                    total += stock["price"] * holding.get("amount", 0)
            loan_info = user.get("loan")
            if loan_info and isinstance(loan_info, dict):
                total -= loan_info.get("amount", 0)
            ranking.append((user["_id"], total))
        ranking.sort(key=lambda x: x[1], reverse=True)
        season = self.db.season.find_one({"_id": "season"})
        season_name = f"{season['year']} 시즌{season['season_no']}"

        tz = pytz.timezone("Asia/Seoul")
        season_start = tz.localize(datetime(year=now.year, month=now.month, day=1, hour=0, minute=10, second=0))
        season_end = tz.localize(datetime(year=now.year, month=now.month, day=28, hour=0, minute=10, second=0))

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
                    "total_assets": int(total_assets)
                })
        self.db.season_results.insert_one(season_result_doc)

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
        if not username:
            await ctx.send("경고: 주식 게임에 참가하려면 반드시 이름을 입력해야 합니다. 예: `#주식참가 홍길동`")
            return

        username = username.strip()
        if not username:
            await ctx.send("경고: 올바른 닉네임을 입력해주세요. (공백만 입력할 수 없습니다.)")
            return

        if self.db.users.find_one({"username": username}):
            await ctx.send("경고: 이미 사용 중인 닉네임입니다. 다른 닉네임을 입력해주세요.")
            return

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
            "bank": 0,
            "loan": {"amount": 0, "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")}
        }
        self.db.users.insert_one(user_doc)
        await ctx.send(f"{ctx.author.mention}님, '{username}'이라는 이름으로 주식 게임에 참가하셨습니다! 초기 자금 {JOIN_BONUS}원을 지급받았습니다.")

    @commands.command(name="주식이름변경")
    async def change_username(self, ctx, *, new_name: str = None):
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
        self.db.users.update_many({}, {"$set": {"money": DEFAULT_MONEY, "portfolio": {}}})
        self.db.stocks.delete_many({})
        stocks = init_stocks()
        for stock in stocks.values():
            self.db.stocks.insert_one(stock)
        await ctx.send("주식 게임이 초기화되었습니다. (칭호는 유지됩니다.)")

    @commands.command(name="주식", aliases=["주식목록", "현재가", "가격","주가"])
    async def show_stocks(self, ctx):
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
                arrow = f"🔺{abs(stock['last_change']):,}"
            elif stock.get("last_change", 0) < 0:
                arrow = f"🔻{abs(stock['last_change']):,}"
            else:
                arrow = "⏺0"

            stock_info = f"{arrow_change}**{stock['name']}**: `{stock['price']:,}원` ({arrow}) (변동율: `{stock['percent_change']}%`)"
            if not stock.get("listed", True):
                stock_info = f"~~{stock_info}~~"
            msg_lines.append(stock_info)

        self.prev_stock_order = new_order

        if not msg_lines:
            await ctx.send("📉 현재 등록된 주식이 없습니다.")
            return

        output = "\n".join(msg_lines)
        if len(output) > 1900:
            chunks = [output[i:i + 1900] for i in range(0, len(output), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(output)

    @commands.command(name="다음변동", aliases=["변동", "변동시간","갱신","다음갱신"])
    async def next_update(self, ctx):
        next_time, delta = self.get_next_update_info()
        await ctx.send(f"다음 변동 시각: {next_time.strftime('%H:%M:%S')} (남은 시간: {str(delta).split('.')[0]})")

    @commands.command(name="주식구매", aliases=["매수"])
    async def buy_stock(self, ctx, stock_name: str = None, amount: str = None):
        special_tokens = ["all", "전부", "올인", "다", "풀매수"]
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return

        # 랜덤 구매 분기
        if stock_name is not None and stock_name.lower() in special_tokens:
            try:
                current_money = user.get("money", 0)
                stocks_list = list(self.db.stocks.find({"listed": True}))
                if not stocks_list:
                    await ctx.send("구매 가능한 주식이 없습니다.")
                    return

                min_price = min(stock["price"] for stock in stocks_list)
                if current_money < min_price:
                    await ctx.send("잔액이 부족하여 어떤 주식도 구매할 수 없습니다.")
                    return

                purchases = {}
                while True:
                    affordable_stocks = [s for s in stocks_list if s["price"] <= current_money]
                    if not affordable_stocks:
                        break
                    chosen_stock = random.choice(affordable_stocks)
                    price = chosen_stock["price"]
                    max_possible = int(current_money // price)
                    if max_possible < 1:
                        break
                    random_quantity = random.randint(1, max_possible)
                    cost = price * random_quantity
                    current_money -= cost
                    sid = chosen_stock["_id"]
                    purchases[sid] = purchases.get(sid, 0) + random_quantity

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
            except Exception as e:
                await ctx.send(f"랜덤 매수 중 오류가 발생했습니다. 오류 코드: {e}")
            return

        # 지정 종목 구매 처리 (약어/정식명 '정확 매칭' 사용)
        if stock_name is None or amount is None:
            await ctx.send("구매할 종목명과 수량을 입력해주세요. 예: `#주식구매 썬더타이어 10` 또는 `#주식구매 썬더 10`")
            return

        stock, err = self.find_stock_by_alias_or_name(stock_name)
        if err:
            await ctx.send(err)
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
        if not self.is_trading_open():
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return

        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return

        if stock_name.lower() in ["다", "전부", "전체", "풀매도", "올인", "all"]:
            portfolio = user.get("portfolio", {})
            if not portfolio:
                await ctx.send("판매할 주식이 없습니다.")
                return

            total_revenue = 0
            messages = []
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if not stock:
                    continue
                current_amount = holding.get("amount", 0)
                if current_amount <= 0:
                    continue
                revenue = stock["price"] * current_amount
                total_revenue += revenue
                messages.append(f"- {stock['name']} 주식 {current_amount:,.0f}주 매도하여 {revenue:,.0f}원 획득")
            new_money = user["money"] + total_revenue

            self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "portfolio": {}}})
            await ctx.send(
                f"{ctx.author.mention}님, 보유한 모든 주식을 매도하였습니다.\n"
                f"총 {total_revenue:,.0f}원을 획득하였습니다. (현재 잔액: {new_money:,.0f}원)\n" +
                "\n".join(messages)
            )
            return

        if amount is None:
            await ctx.send("판매할 주식 수량을 입력해주세요. (예: `#매도 종목명 10` 또는 `#매도 종목명 다`)")
            return

        stock, err = self.find_stock_by_alias_or_name(stock_name)
        if err:
            await ctx.send(err)
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
            f"{ctx.author.mention}님이 {stock['name']} 주식을 {sell_amount:,.0f}주 판매하여 {revenue:,.0f}원을 획득하였습니다. (현재 잔액: {new_money:,.0f}원)"
        )

    @commands.command(name="프로필", aliases=["보관함", "자산", "자본"])
    async def profile(self, ctx):
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
                f"{stock.get('name', 'Unknown')}: {amount:,.0f}주 (현재가: {current_price:,}원, 총액: {stock_value:,.0f}원, 평균구매가: {avg_buy:,}원)"
            )
        portfolio_str = "\n".join(portfolio_lines) if portfolio_lines else "보유 주식 없음"

        cash = user.get("money", DEFAULT_MONEY)
        bank = user.get("bank", 0)
        loan_amount = user.get("loan", {}).get("amount", 0)
        total_assets = cash + bank + total_stock_value - loan_amount
        titles_str = ", ".join(user.get("titles", [])) if user.get("titles", []) else "없음"
        username = user.get("username", ctx.author.display_name)

        lines = []
        header = f"\u001b[1;37;48;5;27m {username}님의 프로필 \u001b[0m"
        lines.append(header)
        lines.append("")

        lines.append(f"현금 잔액 : {cash:,.0f}원")
        lines.append(f"은행 예금 : {bank:,.0f}원")
        lines.append(f"대출 금액 : {loan_amount:,.0f}원")
        lines.append(f"주식 총액 : {total_stock_value:,.0f}원")
        lines.append(f"전체 자산 : {total_assets:,.0f}원")

        lines.append("")
        lines.append("보유 주식:")
        lines.append(portfolio_str)
        lines.append("")
        lines.append("칭호:")
        lines.append(titles_str)

        ansi_content = "```ansi\n" + "\n".join(lines) + "\n```"
        await ctx.send(ansi_content)

    @commands.command(name="랭킹", aliases=["순위"])
    async def ranking_ansi(self, ctx):
        ranking_list = []
        for user in self.db.users.find({}):
            username = user.get("username", "알 수 없음")
            money = user.get("money", DEFAULT_MONEY)
            bank = user.get("bank", 0)
            portfolio = user.get("portfolio", {})
            loan_info = user.get("loan", {})

            total_assets = money + bank
            for sid, holding in portfolio.items():
                stock = self.db.stocks.find_one({"_id": sid})
                if stock:
                    total_assets += stock["price"] * holding.get("amount", 0)
            if isinstance(loan_info, dict):
                total_assets -= loan_info.get("amount", 0)

            ranking_list.append((username, total_assets))

        ranking_list.sort(key=lambda x: x[1], reverse=True)
        top_10 = ranking_list[:10]

        lines = []
        lines.append("---- 랭킹 TOP 10 ----")
        for idx, (username, total) in enumerate(top_10, start=1):
            line_text = f"{idx}. {username} : {total:,.0f}원"
            if idx == 1:
                ansi_line = f"\u001b[1;37;48;5;202m{line_text}\u001b[0m"
            elif idx in [2, 3]:
                ansi_line = f"\u001b[1m{line_text}\u001b[0m"
            else:
                ansi_line = line_text
            lines.append(ansi_line)

        ansi_content = "```ansi\n" + "\n".join(lines) + "\n```"
        await ctx.send(ansi_content)

    @commands.command(name="시즌")
    async def season_info(self, ctx):
        season = self.db.season.find_one({"_id": "season"})
        season_name = f"{season['year']} 시즌{season['season_no']}"
        now = self.get_seoul_time()
        tz = pytz.timezone("Asia/Seoul")

        if now.day < 28:
            season_start = tz.localize(datetime(year=now.year, month=now.month, day=1, hour=0, minute=10, second=0))
            season_end = tz.localize(datetime(year=now.year, month=now.month, day=28, hour=0, minute=10, second=0))
            remaining = season_end - now
        else:
            if now.month == 12:
                next_year = now.year + 1
                next_month = 1
            else:
                next_year = now.year
                next_month = now.month + 1
            season_start = tz.localize(datetime(year=next_year, month=next_month, day=1, hour=0, minute=10, second=0))
            season_end = tz.localize(datetime(year=next_year, month=next_month, day=28, hour=0, minute=10, second=0))
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
        # 시즌 중에만 사용
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
    
        status_msg = await ctx.send("📈 그래프를 생성 중입니다... 잠시만 기다려주세요.")
    
        try:
            # 약어/정식명 매칭
            stock, err = self.find_stock_by_alias_or_name(stock_name)
            if err:
                await status_msg.edit(content=err)
                return
    
            history_full = stock.get("history", [])
            if not history_full:
                await status_msg.edit(content="해당 주식의 변동 내역이 없습니다.")
                return
    
            # 최근 5개만 표시(−4 ~ 0), 첫 점의 변동률 계산을 위해 −5 값 보관
            if len(history_full) >= 6:
                prev_for_first = history_full[-6]
            else:
                prev_for_first = None
            history = history_full[-5:]  # (−4, −3, −2, −1, 0)
    
            # 폰트 설정(있으면 사용)
            font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "온글잎 나나양.ttf")
            custom_font = "sans-serif"
            if os.path.exists(font_path):
                try:
                    fm.fontManager.addfont(font_path)
                    font_prop = fm.FontProperties(fname=font_path)
                    custom_font = font_prop.get_name()
                except Exception:
                    pass
            plt.rcParams["font.family"] = custom_font
            plt.rcParams["axes.unicode_minus"] = False
    
            # 그래프 생성
            plt.figure(figsize=(6, 4))
            ax = plt.gca()
            ax.plot(range(len(history)), history, marker="o", linestyle="-", linewidth=2, color="royalblue")
    
            ax.set_title(f"{stock['name']} 변동 내역", fontsize=16, fontweight="bold")
            ax.set_xlabel("측정 횟수", fontsize=12)
            ax.set_ylabel("주가 (원)", fontsize=12)
            ax.grid(True, alpha=0.3)
    
            # X축: -4 ~ 0 고정(데이터 길이에 맞춰 앞쪽 절단)
            ax.set_xticks(range(len(history)))
            ax.set_xticklabels([-4, -3, -2, -1, 0][-len(history):])
    
            # ✅ Y축은 Matplotlib이 자동으로 계산하도록 (최대/최소 강제 추가 제거)
            y_min = min(history)
            y_max = max(history)
            pad = max(1, int((y_max - y_min) * 0.05))
            y_bottom = y_min - pad
            y_top = y_max + pad
            ax.set_ylim(y_bottom, y_top)
    
            # ✅ ticks 자동 계산 (강제 추가 X)
            ticks = plt.MaxNLocator(nbins=6).tick_values(y_bottom, y_top)
            ax.set_yticks(ticks)
            ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    
            # 각 점 라벨: 가격(+직전 대비 변동률)
            for i, price in enumerate(history):
                prev = history[i - 1] if i > 0 else prev_for_first
                if prev and prev > 0:
                    pct = (price / prev - 1) * 100
                    label = f"{price:,} ({pct:+.2f}%)"
                else:
                    label = f"{price:,}"
    
                ax.annotate(
                    label,
                    xy=(i, price),
                    xytext=(8, 0),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=10,
                )
    
            # 이미지 전송
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            plt.close()
    
            file = discord.File(fp=buf, filename="price_history.png")
            await ctx.send(file=file)
            await status_msg.edit(content="✅ 그래프 생성이 완료되었습니다!")
    
        except Exception as e:
            await status_msg.edit(content=f"❌ 그래프 생성 중 오류가 발생했습니다: {e}")
            try:
                plt.close()
            except Exception:
                pass

    @commands.command(name="주식완전초기화")
    @commands.is_owner()
    async def reset_full_game(self, ctx):
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

        self.db.users.delete_many({})
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
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가` 명령어로 참가해주세요.")
            return

        tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(tz)

        if now.hour < 12:
            period_reset = tz.localize(datetime(now.year, now.month, now.day, 0, 0, 0))
        else:
            period_reset = tz.localize(datetime(now.year, now.month, now.day, 12, 0, 0))

        last_support_str = user.get("last_support_time", None)
        last_support = None
        if last_support_str:
            try:
                last_support = tz.localize(datetime.strptime(last_support_str, "%Y-%m-%d %H:%M:%S"))
            except Exception:
                last_support = None

        if last_support is not None and last_support >= period_reset:
            await ctx.send(f"{ctx.author.mention}님, 이번 기간에는 이미 지원금을 받으셨습니다!")
            return

        new_money = user.get("money", 0) + SUPPORT_AMOUNT
        self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"money": new_money, "last_support_time": now.strftime("%Y-%m-%d %H:%M:%S")}}
        )

        await ctx.send(
            f"{ctx.author.mention}님, {SUPPORT_AMOUNT:,.0f}원의 지원금을 받았습니다! 현재 잔액: {new_money:,.0f}원\n"
            f"지원금은 매일 0시, 12시에 초기화됩니다."
        )

    @commands.command(name="유저데이터삭제", aliases=["유저삭제"])
    @commands.is_owner()
    async def delete_user_data(self, ctx, user_id: str):
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("해당 유저 데이터를 찾을 수 없습니다.")
            return

        self.db.users.delete_one({"_id": user_id})
        await ctx.send(f"유저 ID `{user_id}`의 모든 데이터가 삭제되었습니다. 다시 참가하려면 `#주식참가`를 사용해야 합니다.")

    @commands.command(name="주식추가")
    @commands.is_owner()
    async def add_stock(self, ctx, stock_name: str, min_price: int, max_price: int):
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
            "history": [],
            "aliases": ALIAS_MAP.get(stock_name, [])
        }
        new_stock["history"].append(new_stock["price"])
        self.db.stocks.insert_one(new_stock)
        await ctx.send(f"✅ 새로운 주식 `{stock_name}`이 추가되었습니다! 초기 가격: {new_stock['price']:,}원")

    @commands.command(name="주식쿠폰입력")
    async def redeem_stock_coupon(self, ctx, coupon_code: str):
        if not self.is_trading_open():
            await ctx.send("현재 시즌 종료 중입니다. 명령어는 거래 가능 시간에만 사용할 수 있습니다.")
            return
        valid_coupons = {
            "2025Season3": {"reward": 300000, "max_usage": 1},
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
            f"현재 잔액: `{new_money:,.0f}원`\n"
            f"이 쿠폰은 총 {max_coupon_usage}회 사용 가능하며, 현재 사용 횟수: {coupon_usage[coupon_code]}회 사용했습니다."
        )

    @commands.command(name="유저정보", aliases=["유저조회"])
    @commands.has_permissions(administrator=True)
    async def get_user_info(self, ctx, user: discord.Member = None):
        if user:
            user_id = str(user.id)
            user_data = self.db.users.find_one({"_id": user_id})

            if not user_data:
                await ctx.send(f"❌ `{user.display_name}`님은 주식 시스템에 등록되지 않았습니다.")
                return

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

            user_list = user_list[:10]

            embed = discord.Embed(title="📜 전체 유저 정보 (상위 10명)", color=discord.Color.green())
            embed.description = "\n".join(user_list)
            await ctx.send(embed=embed)

    @get_user_info.error
    async def get_user_info_error(ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 이 명령어는 관리자만 사용할 수 있습니다.")

    @commands.command(name="주식종목초기화")
    @commands.is_owner()
    async def reset_stock_items(self, ctx):
        class ConfirmResetView(discord.ui.View):
            def __init__(self, timeout=30):
                super().__init__(timeout=timeout)
                self.value = None

            @discord.ui.button(label="계속하기", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        await view.wait()

        if view.value is None:
            await ctx.send("시간 초과로 초기화가 취소되었습니다.")
            return

        if not view.value:
            await ctx.send("초기화가 취소되었습니다.")
            return

        self.db.users.update_many({}, {"$set": {"portfolio": {}}})

        self.db.stocks.delete_many({})
        stocks = init_stocks()
        for stock in stocks.values():
            self.db.stocks.insert_one(stock)

        await ctx.send("✅ 모든 주식 종목이 초기화되었습니다. 모든 유저의 보유 주식이 제거되었습니다.")

    @commands.command(name="칭호지급")
    @commands.is_owner()
    async def award_title(self, ctx, target: str, *, title: str):
        if target == "다":
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
        #시즌결과 [시즌명?]
        - 시즌명을 주면 해당 시즌의 TOP3를 보여줍니다.
        - 시즌명을 생략하면 기록된 모든 시즌을 페이지(10개/페이지)로 3버튼 UI(이전/표시/다음)로 탐색합니다.
        """
        # 1) 단일 시즌 조회 모드
        if season_name is not None:
            season_doc = self.db.season_results.find_one({"season_name": season_name})
            if not season_doc:
                await ctx.send(f"'{season_name}' 시즌 결과를 찾을 수 없습니다.")
                return
    
            results = season_doc.get("results", [])
            lines = [
                f"**{season_doc['season_name']} 시즌 TOP3**",
                f"기간: {season_doc.get('start_time', 'N/A')} ~ {season_doc.get('end_time', 'N/A')}",
            ]
            if results:
                for entry in results:
                    lines.append(f"{entry['rank']}위: {entry['username']} - {entry['total_assets']:,}원")
            else:
                lines.append("TOP3 기록이 없습니다.")
            await ctx.send("\n".join(lines))
            return
    
        # 2) 목록 페이지네이션 모드
        seasons = list(self.db.season_results.find({}))
        if not seasons:
            await ctx.send("아직 기록된 시즌 결과가 없습니다.")
            return
    
        # 정렬(시즌명 오름차순; 필요시 시간 기준으로 바꿔도 됨)
        seasons.sort(key=lambda doc: doc["season_name"])
    
        ITEMS_PER_PAGE = 10
        total_pages = (len(seasons) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
        class SeasonPager(discord.ui.View):
            def __init__(self, seasons, per_page):
                super().__init__(timeout=90)
                self.seasons = seasons
                self.per_page = per_page
                self.page = 0  # 0-indexed
                self.total_pages = (len(seasons) + per_page - 1) // per_page
                # 미리 버튼을 3개만 배치
                self.prev_btn = PrevButton(self)
                self.page_btn = PageIndicatorButton(self)
                self.next_btn = NextButton(self)
                self.add_item(self.prev_btn)
                self.add_item(self.page_btn)   # disabled indicator
                self.add_item(self.next_btn)
    
            def page_text(self) -> str:
                start = self.page * self.per_page
                end = start + self.per_page
                chunk = self.seasons[start:end]
                lines = [
                    f"**기록된 시즌 결과 목록** (총 {len(self.seasons)}개) — 페이지 {self.page+1}/{self.total_pages}",
                    ""
                ]
                for i, doc in enumerate(chunk, start=start + 1):
                    lines.append(f"{i}. {doc['season_name']}: {doc.get('start_time', 'N/A')} ~ {doc.get('end_time', 'N/A')}")
                return "\n".join(lines)
    
        class PageIndicatorButton(discord.ui.Button):
            def __init__(self, pager: SeasonPager):
                super().__init__(label=f"{pager.page+1}/{pager.total_pages}",
                                 style=discord.ButtonStyle.secondary, disabled=True)
                self.pager = pager
    
            async def refresh(self, interaction: discord.Interaction):
                # 버튼 라벨 업데이트
                self.label = f"{self.pager.page+1}/{self.pager.total_pages}"
                await interaction.response.edit_message(content=self.pager.page_text(), view=self.pager)
    
        class PrevButton(discord.ui.Button):
            def __init__(self, pager: SeasonPager):
                super().__init__(label="이전", style=discord.ButtonStyle.primary)
                self.pager = pager
    
            async def callback(self, interaction: discord.Interaction):
                if self.pager.page <= 0:
                    await interaction.response.send_message("첫번째 페이지입니다.", ephemeral=True)
                    return
                self.pager.page -= 1
                # 가운데 버튼 라벨 갱신
                self.pager.page_btn.label = f"{self.pager.page+1}/{self.pager.total_pages}"
                await interaction.response.edit_message(content=self.pager.page_text(), view=self.pager)
    
        class NextButton(discord.ui.Button):
            def __init__(self, pager: SeasonPager):
                super().__init__(label="다음", style=discord.ButtonStyle.primary)
                self.pager = pager
    
            async def callback(self, interaction: discord.Interaction):
                if self.pager.page >= self.pager.total_pages - 1:
                    await interaction.response.send_message("마지막 페이지입니다.", ephemeral=True)
                    return
                self.pager.page += 1
                # 가운데 버튼 라벨 갱신
                self.pager.page_btn.label = f"{self.pager.page+1}/{self.pager.total_pages}"
                await interaction.response.edit_message(content=self.pager.page_text(), view=self.pager)
    
        view = SeasonPager(seasons, ITEMS_PER_PAGE)
        await ctx.send(view.page_text(), view=view)

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
        # 소수점 금지
        if '.' in amount:
            await ctx.send("소수점 이하의 금액은 입력할 수 없습니다. 정수 금액만 입력해주세요.")
            return

        # 거래 가능 시간 체크
        if not self.is_trading_open():
            await ctx.send("대출 기능은 거래 가능 시간(시즌)에서만 사용할 수 있습니다.")
            return

        # 유저 조회
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가`로 참가해주세요.")
            return

        # 현재 부채(이자 포함) 최신화
        current_loan = self.update_loan_interest(user)
        # 최신 값 재조회(중요)
        user = self.db.users.find_one({"_id": user_id})
        loan_info = user.get("loan", {})
        current_loan = int(loan_info.get("amount", 0))
    
        max_loan = 5_000_000
        available = max(0, max_loan - current_loan)  # 한도 체크는 '부채총액' 대비 남은 여지

        # 신청 금액 결정
        try:
            if amount.lower() in ["다", "all", "전부", "풀대출", "올인"]:
                loan_amount = available
            else:
                loan_amount = int(amount)
                if loan_amount <= 0:
                    await ctx.send("대출 금액은 1원 이상이어야 합니다.")
                    return
        except Exception as e:
            await ctx.send(f"[LOAN_004] 대출 금액 처리 오류: {e}")
            return

        if loan_amount == 0:
            await ctx.send(f"이미 최대 대출 한도({max_loan:,}원)에 도달했습니다. 현재 부채: {current_loan:,}원")
            return

        if loan_amount > available:
            await ctx.send(f"대출 한도 초과입니다. 남은 한도: {available:,}원")
            return

        # 확인 뷰
        view = LoanConfirmView(ctx.author, loan_amount)
        await ctx.send(
            "⚠️ **대출 요청 확인**\n"
            f"대출 금액(원금): {loan_amount:,}원\n"
            f"대출 후 부채 총액(이자 별도 누적): {current_loan + loan_amount:,}원\n"
            f"(최대 한도: {max_loan:,}원)\n"
            f"계속 진행하시겠습니까?",
            view=view
        )
        await view.wait()
        if view.value is None or view.value is False:
            await ctx.send("대출 진행이 취소되었습니다.")
            return

        # DB 반영 (수수료 없음: 현금은 loan_amount만큼 증가, 부채도 loan_amount만 증가)
        new_money = user.get("money", 0) + loan_amount
        new_loan_total = current_loan + loan_amount
        self.db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "money": new_money,
                "loan": {
                    "amount": new_loan_total,
                    "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")
                }
            }}
        )

        await ctx.send(
            f"{ctx.author.mention}님, **{loan_amount:,}원** 대출이 완료되었습니다.\n"
            f"(현재 부채: {new_loan_total:,}원, 현금: {new_money:,}원)"
        )

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
            repay_amount = current_loan
        new_money = user["money"] - repay_amount
        new_loan = current_loan - repay_amount
        loan_update = {
            "amount": new_loan,
            "last_update": self.get_seoul_time().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money, "loan": loan_update}})
        await ctx.send(f"{ctx.author.mention}님, {repay_amount:,}원을 대출 상환하였습니다. (남은 대출 잔액: {new_loan:,.0f}원, 현금: {new_money:,.0f}원)")

    @commands.command(name="다음시즌")
    async def next_season(self, ctx):
        """
        #다음시즌:
        현재 진행 중인 시즌이 아닌, 다음에 진행될 시즌에 대한 정보를 출력합니다.
        (시즌 기간은 매월 1일 0시 10분부터 28일 0시 10분까지로 설정)
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
        next_season_end = tz.localize(datetime(next_year, next_month, 28, 0, 10, 0))
        
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

    @commands.command(name="주식소각", aliases=["소각"])
    async def burn_stock(self, ctx, stock_name: str = None, amount: str = None):
        """
        #주식소각 [주식명] [수량]:
        보유 중인 주식을 환급 없이 소각합니다.
        예시: `#주식소각 썬더타이어 10`
            `#주식소각 맥턴맥주 all`
        """
        if stock_name is None or amount is None:
            await ctx.send("사용법: `#주식소각 주식명 수량` (예: `#주식소각 썬더타이어 10`)")
            return

        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. `#주식참가` 명령어로 참가해주세요.")
            return

        # 주식 종목 존재 여부 확인 (주식명으로 DB 조회)
        stock = self.db.stocks.find_one({"name": stock_name})
        if not stock:
            await ctx.send("존재하지 않는 주식 종목입니다.")
            return

        portfolio = user.get("portfolio", {})
        if stock["_id"] not in portfolio:
            await ctx.send("해당 주식을 보유하고 있지 않습니다.")
            return

        current_amount = portfolio[stock["_id"]].get("amount", 0)
        # 'all', '전부', '다' 등의 토큰 입력 시 전량 소각
        if amount.lower() in ["all", "전부", "올인", "다", "풀소각"]:
            burn_amount = current_amount
        else:
            try:
                burn_amount = int(amount)
                if burn_amount <= 0:
                    await ctx.send("소각할 주식 수량은 1 이상이어야 합니다.")
                    return
            except Exception:
                await ctx.send("소각할 주식 수량을 올바르게 입력해주세요.")
                return

        if burn_amount > current_amount:
            await ctx.send("소각할 주식 수량이 보유 수량보다 많습니다.")
            return

        # 경고 메시지와 함께 확인 버튼 표시
        view = StockBurnConfirmView(ctx.author, stock_name, burn_amount)
        await ctx.send(
            f"⚠️ **주식 소각 확인**\n"
            f"소각할 주식: **{stock_name}**\n"
            f"소각할 수량: **{burn_amount:,}주**\n"
            f"※ 소각 시 보유 주식은 환급되지 않습니다.\n"
            f"계속 진행하시겠습니까?",
            view=view
        )
        await view.wait()
        if view.value is None or view.value is False:
            await ctx.send("주식 소각이 취소되었습니다.")
            return

        # 소각 진행: 소유 주식 수량에서 burn_amount만큼 차감
        remaining = current_amount - burn_amount
        if remaining > 0:
            # 평균 구매 단가에 비례하여 total_cost도 갱신 (비례 배분)
            avg_price = portfolio[stock["_id"]].get("total_cost", 0) / current_amount
            new_total_cost = int(avg_price * remaining)
            portfolio[stock["_id"]] = {"amount": remaining, "total_cost": new_total_cost}
        else:
         portfolio.pop(stock["_id"])

        self.db.users.update_one({"_id": user_id}, {"$set": {"portfolio": portfolio}})
        await ctx.send(f"{ctx.author.mention}님, **{stock_name}** 주식 {burn_amount:,.0f}주가 소각되었습니다. (남은 보유량: {remaining:,.0f}주)")

    @commands.command(name="시장그래프", aliases=["전체그래프", "종목그래프"])
    async def market_graph(self, ctx, *names: str):
        """
        #시장그래프 [종목명 ...]
        - 인자가 없으면: 전체 종목 표시
        - 인자가 있으면: 지정한 종목(약어/정식명 모두 허용)을 n개까지 표시
        - 각 구간의 변동률(직전 대비 %) 기준으로 그림 (누적 아님)
        - Y축 범위: -20% ~ +20%, 5% 단위 눈금
        - 중앙 0% 기준선 표시
        """
        status_msg = await ctx.send("📊 변동률 기반 시장 그래프 생성 중...")
    
        try:
            # --- 종목 필터링 ---
            target_stocks = []
            not_found = []
    
            if names:
                seen_ids = set()
                for key in names:
                    stock, err = self.find_stock_by_alias_or_name(key)
                    if err or not stock:
                        not_found.append(key)
                        continue
                    if stock["_id"] not in seen_ids:
                        target_stocks.append(stock)
                        seen_ids.add(stock["_id"])
            else:
                target_stocks = list(self.db.stocks.find({}).sort("_id", 1))
    
            if not target_stocks:
                msg = "📉 그릴 종목이 없습니다."
                if not_found:
                    msg += f" (인식 실패: {', '.join(f'`{x}`' for x in not_found[:10])})"
                await status_msg.edit(content=msg)
                return
    
            # --- 폰트 설정 ---
            try:
                font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "온글잎 나나양.ttf")
                if os.path.exists(font_path):
                    fm.fontManager.addfont(font_path)
                    font_prop = fm.FontProperties(fname=font_path)
                    plt.rcParams["font.family"] = font_prop.get_name()
            except Exception:
                pass
            plt.rcParams["axes.unicode_minus"] = False
    
            # --- 그래프 초기화 ---
            plt.figure(figsize=(8, 5))
            ax = plt.gca()
    
            line_styles = ["-", "--", "-.", ":"]
            style_idx = 0
            plotted_any = False
            max_len = 0
    
            # --- 종목별 변동률 계산 ---
            for stock in target_stocks:
                history = stock.get("history", [])
                if len(history) < 2 or all(v == 0 for v in history):
                    continue
            
                step_changes = [0.0]
                for i in range(1, len(history)):
                    prev = history[i - 1]
                    curr = history[i]
                    if prev <= 0:
                        step_changes.append(0.0)
                    else:
                        pct = (curr / prev - 1) * 100
                        pct = max(-20, min(20, pct))  # ±20% 클램프
                        step_changes.append(pct)
            
                # ✅ 마지막 5개만 시각화 (-4 ~ 0 구간)
                if len(step_changes) > 5:
                    step_changes = step_changes[-5:]
            
                ls = line_styles[style_idx % len(line_styles)]
                style_idx += 1
            
                ax.plot(
                    range(len(step_changes)),
                    step_changes,
                    linestyle=ls,
                    linewidth=2,
                    label=stock.get("name", "Unknown"),
                )
                max_len = max(max_len, len(step_changes))
                plotted_any = True
            
            # ✅ X축 라벨을 -4 ~ 0으로 고정
            ax.set_xticks(range(5))
            ax.set_xticklabels([-4, -3, -2, -1, 0])

            if not plotted_any:
                msg = "⚠️ 그릴 데이터가 없습니다. (대상 종목 기록이 비었거나 변환 불가)"
                if not_found:
                    msg += f"\n인식 실패: {', '.join(f'`{x}`' for x in not_found[:10])}"
                await status_msg.edit(content=msg)
                plt.close()
                return
    
            # --- X축: -n+1 ~ 0 ---
            ax.set_xticks(list(range(max_len)))
            ax.set_xticklabels(list(range(-max_len + 1, 1)))
    
            # --- Y축: -20 ~ +20 ---
            ax.set_ylim(-20, 20)
            ax.set_yticks(range(-20, 25, 5))
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d%%"))
            ax.axhline(0, color="gray", linewidth=1.5, linestyle="-")
    
            # --- 제목 및 라벨 ---
            if names:
                title_list = [s.get("name", "Unknown") for s in target_stocks[:5]]
                extra = "" if len(target_stocks) <= 5 else f" 외 {len(target_stocks) - 5}개"
                ax.set_title(
                    f"선택 종목 구간별 변동률 (±20%) — {', '.join(title_list)}{extra}",
                    fontsize=14,
                    fontweight="bold",
                )
            else:
                ax.set_title("전체 종목 구간별 변동률 (±20%)", fontsize=14, fontweight="bold")
    
            ax.set_xlabel("측정 간격 (최근=0)")
            ax.set_ylabel("변동률 (%)")
            ax.grid(True, alpha=0.3)
    
            # --- 범례 ---
            ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0., fontsize=9)
            plt.tight_layout()
    
            # --- 결과 전송 ---
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            plt.close()
    
            file = discord.File(fp=buf, filename="market_range_graph.png")
            await ctx.send(file=file)
    
            # 상태 메시지 마무리
            if not_found:
                await status_msg.edit(
                    content=f"✅ 그래프 생성 완료 (인식 실패: {', '.join(f'`{x}`' for x in not_found[:10])})"
                )
            else:
                await status_msg.edit(content="✅ 그래프 생성 완료")
    
        except Exception as e:
            await status_msg.edit(content=f"❌ 시장 그래프 생성 중 오류가 발생했습니다: {e}")
            try:
                plt.close()
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(StockMarket(bot))

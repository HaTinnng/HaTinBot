import discord
from discord.ext import commands, tasks
import random, json, os
from datetime import datetime, timedelta
import pytz

# 상수 설정
JOIN_BONUS = 500000        # #주식참가 시 지급 자금
DEFAULT_MONEY = 100000     # 시즌 초기화 후 유저 기본 잔액
DATA_FILE = "stock_data.json"  # JSON 저장 파일명

def init_stocks():
    """
    11개의 주식을 아래와 같이 초기화합니다.
      - "311유통": 100
      - "썬더타이어", "룡치수산": 100 ~ 1000
      - "맥턴맥주", "섹보경컬쳐": 1000 ~ 5000
      - "전차수리점", "디코커피": 5000 ~ 20000
      - "와이제이엔터", "이리여행사": 20000 ~ 50000
      - "하틴봇전자": 50000 ~ 75000
      - "하틴출판사": 75000 ~ 100000
    """
    stocks = {}
    stocks["1"] = {"name": "311유통", "price": random.randint(99, 100), "last_change": 0, "percent_change": 0}
    stocks["2"] = {"name": "썬더타이어", "price": random.randint(100, 1000), "last_change": 0, "percent_change": 0}
    stocks["3"] = {"name": "룡치수산", "price": random.randint(100, 1000), "last_change": 0, "percent_change": 0}
    stocks["4"] = {"name": "맥턴맥주", "price": random.randint(1000, 5000), "last_change": 0, "percent_change": 0}
    stocks["5"] = {"name": "섹보경컬쳐", "price": random.randint(1000, 5000), "last_change": 0, "percent_change": 0}
    stocks["6"] = {"name": "전차수리점", "price": random.randint(5000, 20000), "last_change": 0, "percent_change": 0}
    stocks["7"] = {"name": "디코커피", "price": random.randint(5000, 20000), "last_change": 0, "percent_change": 0}
    stocks["8"] = {"name": "와이제이엔터", "price": random.randint(20000, 50000), "last_change": 0, "percent_change": 0}
    stocks["9"] = {"name": "이리여행사", "price": random.randint(20000, 50000), "last_change": 0, "percent_change": 0}
    stocks["10"] = {"name": "하틴봇전자", "price": random.randint(50000, 75000), "last_change": 0, "percent_change": 0}
    stocks["11"] = {"name": "하틴출판사", "price": random.randint(75000, 100000), "last_change": 0, "percent_change": 0}
    return stocks

def load_data():
    """
    JSON 파일을 로드합니다.
    파일이 없거나 'stocks' 항목이 없으면 새 데이터를 생성합니다.
    """
    data = None
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "stocks" not in data or not data["stocks"]:
                data["stocks"] = init_stocks()
        except Exception as e:
            print("JSON 파일 로드 중 오류 발생:", e)
    if data is None:
        data = {
            "stocks": init_stocks(),
            "users": {},
            "season": {
                "year": datetime.now(pytz.timezone("Asia/Seoul")).year,
                "season_no": 1,
                "last_reset": None
            }
        }
    save_data(data)
    return data

def save_data(data):
    """데이터를 JSON 파일에 저장합니다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.last_update_min = None  # 같은 분 내 중복 업데이트 방지
        self.stock_update_loop.start()
        self.season_reset_loop.start()

    def cog_unload(self):
        self.stock_update_loop.cancel()
        self.season_reset_loop.cancel()

    def get_seoul_time(self):
        return datetime.now(pytz.timezone("Asia/Seoul"))

    def update_stocks(self):
        """
        주식 가격을 현재 가격의 최대 ±12.3% 범위 내에서 랜덤하게 변동합니다.
        단, 매월 1일과 2일은 거래가 중단되므로 변동하지 않습니다.
        """
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            return
        for stock in self.data["stocks"].values():
            old_price = stock["price"]
            percent_change = random.uniform(-12.3, 12.3)
            new_price = int(old_price * (1 + percent_change / 100))
            new_price = max(new_price, 1)
            stock["last_change"] = new_price - old_price
            stock["percent_change"] = round(percent_change, 2)
            stock["price"] = new_price
        save_data(self.data)

    @tasks.loop(seconds=10)
    async def stock_update_loop(self):
        """
        매 10초마다 현재 시간이 한국시간의 0분, 20분, 40분(초 0)인지 확인하고 주식 가격을 업데이트합니다.
        거래 중단 기간(1일, 2일)에는 업데이트하지 않습니다.
        """
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            return
        if now.second == 0 and now.minute in [0, 20, 40]:
            if self.last_update_min != now.minute:
                self.update_stocks()
                self.last_update_min = now.minute
                # 필요 시 채널에 업데이트 알림 전송 가능

    @tasks.loop(minutes=1)
    async def season_reset_loop(self):
        """
        매 분마다 현재 날짜를 확인하여, 매월 1일이면 시즌 종료 및 초기화 처리를 진행합니다.
        1일과 2일은 거래 중단 기간입니다.
        """
        now = self.get_seoul_time()
        if now.day == 1:
            await self.process_season_end(now)

    async def process_season_end(self, now):
        """
        시즌 종료 시 모든 유저의 자산(현금 + 보유 주식 평가액)을 산출하여 상위 3명에게 칭호("YYYY 시즌N TOP{순위}")를 부여하고,
        모든 유저의 잔액과 포트폴리오, 그리고 주식 데이터를 초기화합니다.
        칭호는 영구 보관됩니다.
        """
        ranking = []
        for user_id, user_data in self.data["users"].items():
            total = user_data.get("money", DEFAULT_MONEY)
            for sid, amount in user_data.get("portfolio", {}).items():
                price = self.data["stocks"].get(sid, {}).get("price", 0)
                total += price * amount
            ranking.append((user_id, total))
        ranking.sort(key=lambda x: x[1], reverse=True)
        for idx, (user_id, _) in enumerate(ranking[:3], start=1):
            title = f"{self.data['season']['year']} 시즌{self.data['season']['season_no']} TOP{idx}"
            user = self.data["users"].setdefault(user_id, {"money": DEFAULT_MONEY, "portfolio": {}, "titles": []})
            if title not in user["titles"]:
                user["titles"].append(title)
        # 모든 유저의 잔액과 포트폴리오 초기화 (칭호는 유지)
        for user in self.data["users"].values():
            user["money"] = DEFAULT_MONEY
            user["portfolio"] = {}
        self.data["stocks"] = init_stocks()
        self.data["season"]["season_no"] += 1
        self.data["season"]["last_reset"] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(self.data)
        # 필요 시 시즌 종료 알림 전송 가능

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

    @commands.command(name="주식참가", aliases=["주식참여","주식시작"])
    async def join_stock(self, ctx):
        """#주식참가: 처음 참가 시 500,000원을 지급받습니다."""
        user_id = str(ctx.author.id)
        if user_id in self.data["users"]:
            await ctx.send("이미 주식 게임에 참가하셨습니다.")
            return
        self.data["users"][user_id] = {"money": JOIN_BONUS, "portfolio": {}, "titles": []}
        save_data(self.data)
        await ctx.send(f"{ctx.author.mention}님, 주식 게임에 참가하셨습니다! 초기 자금 {JOIN_BONUS}원을 지급받았습니다.")

    @commands.command(name="주식",aliases=["주식목록","현재가"])
    async def show_stocks(self, ctx):
        """#주식: 전체 주식 목록(종목명, 가격, 변동 내역)을 출력합니다."""
        msg_lines = []
        for stock in self.data["stocks"].values():
            if stock["last_change"] > 0:
                arrow = f"🔺{abs(stock['last_change'])}"
            elif stock["last_change"] < 0:
                arrow = f"🔻{abs(stock['last_change'])}"
            else:
                arrow = "⏺0"
            line = f"{stock['name']}: {stock['price']}원 ({arrow}) (변동율: {stock['percent_change']}%)"
            msg_lines.append(line)
        await ctx.send("\n".join(msg_lines))

    @commands.command(name="다음변동",aliases=["변동","변동시간"])
    async def next_update(self, ctx):
        """#다음변동: 다음 주식 변동 시각과 남은 시간을 안내합니다."""
        next_time, delta = self.get_next_update_info()
        await ctx.send(f"다음 변동 시각: {next_time.strftime('%H:%M:%S')} (남은 시간: {str(delta).split('.')[0]})")

    @commands.command(name="주식구매")
    async def buy_stock(self, ctx, stock_name: str, amount: int):
        """
        #주식구매 [종목명] [수량]
        예: #주식구매 썬더타이어 10
        해당 주식 종목의 주식을 지정 수량만큼 구매합니다.
        """
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return
        user_id = str(ctx.author.id)
        if user_id not in self.data["users"]:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return
        found_sid = None
        for sid, stock in self.data["stocks"].items():
            if stock["name"] == stock_name:
                found_sid = sid
                break
        if not found_sid:
            await ctx.send("존재하지 않는 주식 종목입니다.")
            return
        stock = self.data["stocks"][found_sid]
        total_cost = stock["price"] * amount
        user = self.data["users"][user_id]
        if user["money"] < total_cost:
            await ctx.send("잔액이 부족합니다.")
            return
        user["money"] -= total_cost
        user["portfolio"][found_sid] = user["portfolio"].get(found_sid, 0) + amount
        save_data(self.data)
        await ctx.send(f"{ctx.author.mention}님이 {stock['name']} 주식을 {amount}주 구매하였습니다. (총 {total_cost}원)")

    @commands.command(name="주식판매")
    async def sell_stock(self, ctx, stock_name: str, amount: int):
        """
        #주식판매 [종목명] [수량]
        예: #주식판매 썬더타이어 5
        해당 주식 종목의 주식을 지정 수량만큼 판매합니다.
        """
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return
        user_id = str(ctx.author.id)
        if user_id not in self.data["users"]:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return
        found_sid = None
        for sid, stock in self.data["stocks"].items():
            if stock["name"] == stock_name:
                found_sid = sid
                break
        if not found_sid:
            await ctx.send("존재하지 않는 주식 종목입니다.")
            return
        user = self.data["users"][user_id]
        if user["portfolio"].get(found_sid, 0) < amount:
            await ctx.send("판매할 주식 보유 수량이 부족합니다.")
            return
        stock = self.data["stocks"][found_sid]
        revenue = stock["price"] * amount
        user["money"] += revenue
        user["portfolio"][found_sid] -= amount
        if user["portfolio"][found_sid] <= 0:
            del user["portfolio"][found_sid]
        save_data(self.data)
        await ctx.send(f"{ctx.author.mention}님이 {stock['name']} 주식을 {amount}주 판매하여 {revenue}원을 획득하였습니다.")

    @commands.command(name="프로필",aliases=["보관함"])
    async def profile(self, ctx):
        """
        #프로필: 자신의 잔액, 보유 주식(종목명 및 현재가)과 획득한 칭호(예: '2025 시즌2 TOP2')를 보여줍니다.
        """
        user_id = str(ctx.author.id)
        if user_id not in self.data["users"]:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return
        user = self.data["users"][user_id]
        portfolio_lines = []
        for sid, amount in user.get("portfolio", {}).items():
            stock = self.data["stocks"].get(sid, {})
            portfolio_lines.append(f"{stock.get('name', 'Unknown')}: {amount}주 (현재가: {stock.get('price', 0)}원)")
        portfolio_str = "\n".join(portfolio_lines) if portfolio_lines else "보유 주식 없음"
        titles_str = ", ".join(user.get("titles", [])) if user.get("titles", []) else "없음"
        msg = (f"**{ctx.author.display_name}님의 프로필**\n"
               f"잔액: {user['money']}원\n"
               f"보유 주식:\n{portfolio_str}\n"
               f"칭호: {titles_str}")
        await ctx.send(msg)

    @commands.command(name="랭킹")
    async def ranking(self, ctx):
        """
        #랭킹: 전체 유저의 자산(현금+보유 주식 평가액) 기준 상위 10명의 랭킹과 자산을 출력합니다.
        """
        ranking_list = []
        for uid, user_data in self.data["users"].items():
            total = user_data.get("money", DEFAULT_MONEY)
            for sid, amount in user_data.get("portfolio", {}).items():
                total += self.data["stocks"].get(sid, {}).get("price", 0) * amount
            ranking_list.append((uid, total))
        ranking_list.sort(key=lambda x: x[1], reverse=True)
        msg_lines = ["**랭킹 TOP 10**"]
        for idx, (uid, total) in enumerate(ranking_list[:10], start=1):
            user_obj = self.bot.get_user(int(uid))
            name = user_obj.display_name if user_obj else f"ID:{uid}"
            msg_lines.append(f"{idx}. {name} - {total}원")
        await ctx.send("\n".join(msg_lines))

      await ctx.send(f"⏳ 다음 주식 변동까지 {remaining_time.seconds // 60}분 남았습니다. 갱신 시간: {next_update_time.strftime('%H:%M')} KST")

    @commands.command(name="시즌")
    async def season_info(self, ctx):
        now = datetime.now(self.kst)
        season_end = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=self.kst)
        if now >= season_end:
            season_end = datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=self.kst)
        remaining_time = season_end - now
        await ctx.send(f"📅 현재 시즌 종료까지 {remaining_time.days}일 {remaining_time.seconds // 3600}시간 남았습니다. 종료 시간: {season_end.strftime('%Y-%m-%d %H:%M')} KST")


async def setup(bot):
    await bot.add_cog(StockMarket(bot))

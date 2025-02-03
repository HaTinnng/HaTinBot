import discord
from discord.ext import commands, tasks
import random, json, os
from datetime import datetime, timedelta
import pytz

# 상수 설정
JOIN_BONUS = 500000        # #주식참가 시 지급되는 금액
DEFAULT_MONEY = 100000     # 시즌 초기화 시 기본 자금
DATA_FILE = "stock_data.json"  # 데이터 저장 파일

def load_data():
    """저장된 파일이 있으면 불러오고, 없으면 기본 데이터 생성"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    data = {
        "stocks": init_stocks(),
        "users": {},  # 구조: { user_id: {"money": int, "portfolio": {stock_id: 수량}, "titles": [칭호들]} }
        "season": {
            "year": datetime.now(pytz.timezone("Asia/Seoul")).year,
            "season_no": 1,
            "last_reset": None
        }
    }
    save_data(data)
    return data

def save_data(data):
    """데이터를 JSON 파일에 저장"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def init_stocks():
    """11개의 주식을 지정된 이름과 가격 범위로 초기화"""
    stocks = {}
    # 1. 311유통: 10 ~ 100
    stocks["1"] = {"name": "311유통", "price": random.randint(10, 100), "last_change": 0, "percent_change": 0}
    # 2. 썬더타이어: 100 ~ 1000
    stocks["2"] = {"name": "썬더타이어", "price": random.randint(100, 1000), "last_change": 0, "percent_change": 0}
    # 3. 룡치수산: 100 ~ 1000
    stocks["3"] = {"name": "룡치수산", "price": random.randint(100, 1000), "last_change": 0, "percent_change": 0}
    # 4. 맥턴맥주: 1000 ~ 5000
    stocks["4"] = {"name": "맥턴맥주", "price": random.randint(1000, 5000), "last_change": 0, "percent_change": 0}
    # 5. 섹보경컬쳐: 1000 ~ 5000
    stocks["5"] = {"name": "섹보경컬쳐", "price": random.randint(1000, 5000), "last_change": 0, "percent_change": 0}
    # 6. 전차수리점: 5000 ~ 20000
    stocks["6"] = {"name": "전차수리점", "price": random.randint(5000, 20000), "last_change": 0, "percent_change": 0}
    # 7. 디코커피: 5000 ~ 20000
    stocks["7"] = {"name": "디코커피", "price": random.randint(5000, 20000), "last_change": 0, "percent_change": 0}
    # 8. 와이제이엔터: 20000 ~ 50000
    stocks["8"] = {"name": "와이제이엔터", "price": random.randint(20000, 50000), "last_change": 0, "percent_change": 0}
    # 9. 이리여행사: 20000 ~ 50000
    stocks["9"] = {"name": "이리여행사", "price": random.randint(20000, 50000), "last_change": 0, "percent_change": 0}
    # 10. 하틴봇전자: 50000 ~ 75000
    stocks["10"] = {"name": "하틴봇전자", "price": random.randint(50000, 75000), "last_change": 0, "percent_change": 0}
    # 11. 하틴출판사: 75075 ~ 100000
    stocks["11"] = {"name": "하틴출판사", "price": random.randint(75075, 100000), "last_change": 0, "percent_change": 0}
    return stocks

class StockCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.last_update_min = None  # 동일 분 내 중복 실행 방지
        self.stock_update_loop.start()
        self.season_reset_loop.start()

    def cog_unload(self):
        self.stock_update_loop.cancel()
        self.season_reset_loop.cancel()

    def get_seoul_time(self):
        """현재 한국시간 반환"""
        return datetime.now(pytz.timezone("Asia/Seoul"))

    def update_stocks(self):
        """거래 가능일(매월 3일부터)일 경우, 각 주식 가격을 ±12.3% 범위 내에서 변동"""
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            return  # 시즌 종료 및 휴식기간에는 업데이트하지 않음
        for stock_id, stock in self.data["stocks"].items():
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
        """한국시간 기준 0초, 20초, 40초에 주식 변동 처리 (단, 1일 및 2일은 거래 중단)"""
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            return
        if now.second == 0 and now.minute in [0, 20, 40]:
            if self.last_update_min != now.minute:
                self.update_stocks()
                self.last_update_min = now.minute
                # 원한다면 특정 채널에 업데이트 알림 전송 가능
                # channel = self.bot.get_channel(채널_ID)
                # if channel:
                #     await channel.send("주식 변동이 발생했습니다!")

    @tasks.loop(minutes=1)
    async def season_reset_loop(self):
        """매 분마다 현재 날짜를 확인하여 매월 1일이면 시즌 종료 처리 (상위 3위 칭호 부여 후 초기화)"""
        now = self.get_seoul_time()
        if now.day == 1:
            await self.process_season_end(now)
        # 2일은 거래 중단 기간이므로 별도 처리 없이 유지

    async def process_season_end(self, now):
        """시즌 종료 시 – 유저 자산(현금+주식 평가액) 계산 후 상위 3위에게 칭호 부여, 이후 모든 유저의 계좌와 주식 초기화"""
        ranking = []
        for user_id, user_data in self.data["users"].items():
            total = user_data.get("money", DEFAULT_MONEY)
            for stock_id, amount in user_data.get("portfolio", {}).items():
                stock_price = self.data["stocks"].get(stock_id, {}).get("price", 0)
                total += stock_price * amount
            ranking.append((user_id, total))
        ranking.sort(key=lambda x: x[1], reverse=True)
        # 상위 3위에게 칭호 부여 (칭호는 영구 보관)
        for idx, (user_id, total) in enumerate(ranking[:3], start=1):
            title = f"{self.data['season']['year']} 시즌{self.data['season']['season_no']} TOP{idx}"
            user = self.data["users"].setdefault(user_id, {"money": DEFAULT_MONEY, "portfolio": {}, "titles": []})
            if title not in user["titles"]:
                user["titles"].append(title)
        # 모든 유저 계좌와 주식 초기화 (칭호는 유지)
        for user_id, user_data in self.data["users"].items():
            user_data["money"] = DEFAULT_MONEY
            user_data["portfolio"] = {}
        self.data["stocks"] = init_stocks()
        self.data["season"]["season_no"] += 1
        self.data["season"]["last_reset"] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(self.data)
        # 시즌 종료 후 알림 메시지 전송 (원하는 채널에)
        # channel = self.bot.get_channel(채널_ID)
        # if channel:
        #     await channel.send("시즌 종료 및 초기화가 완료되었습니다.")

    def get_next_update_info(self):
        """다음 주식 변동 시각과 남은 시간을 계산"""
        now = self.get_seoul_time()
        # 매 분의 0, 20, 40초 기준
        candidate_times = []
        for m in [0, 20, 40]:
            candidate = now.replace(minute=m, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(hours=1)
            candidate_times.append(candidate)
        next_time = min(candidate_times, key=lambda t: t)
        delta = next_time - now
        return next_time, delta

    @commands.command(name="주식참가")
    async def join_stock(self, ctx):
        """주식 게임에 처음 참가할 때 500,000원을 지급받습니다."""
        user_id = str(ctx.author.id)
        if user_id in self.data["users"]:
            await ctx.send("이미 주식 게임에 참가하셨습니다.")
            return
        self.data["users"][user_id] = {"money": JOIN_BONUS, "portfolio": {}, "titles": []}
        save_data(self.data)
        await ctx.send(f"{ctx.author.mention}님, 주식 게임에 참가하셨습니다! 초기 자금 {JOIN_BONUS}원을 지급받았습니다.")

    @commands.command(name="주식")
    async def show_stocks(self, ctx):
        """전체 주식 목록 및 가격, 변동 내역을 보여줍니다."""
        msg_lines = []
        for stock_id, stock in self.data["stocks"].items():
            if stock["last_change"] > 0:
                arrow = f"🔺{abs(stock['last_change'])}"
            elif stock["last_change"] < 0:
                arrow = f"🔻{abs(stock['last_change'])}"
            else:
                arrow = "⏺0"
            line = f"{stock['name']}: {stock['price']}원 ({arrow}) (변동율: {stock['percent_change']}%)"
            msg_lines.append(line)
        await ctx.send("\n".join(msg_lines))

    @commands.command(name="다음변동")
    async def next_update(self, ctx):
        """다음 주식 변동 시각과 남은 시간을 안내합니다."""
        next_time, delta = self.get_next_update_info()
        await ctx.send(f"다음 변동 시각: {next_time.strftime('%H:%M:%S')} (남은 시간: {str(delta).split('.')[0]})")

    @commands.command(name="주식구매")
    async def buy_stock(self, ctx, stock_id: str, amount: int):
        """예시: #주식구매 3 10 – 해당 주식 번호의 주식을 지정 수량만큼 구매합니다."""
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return
        if stock_id not in self.data["stocks"]:
            await ctx.send("존재하지 않는 주식 번호입니다.")
            return
        user_id = str(ctx.author.id)
        if user_id not in self.data["users"]:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return
        user = self.data["users"][user_id]
        price = self.data["stocks"][stock_id]["price"]
        total_cost = price * amount
        if user["money"] < total_cost:
            await ctx.send("잔액이 부족합니다.")
            return
        user["money"] -= total_cost
        user["portfolio"][stock_id] = user["portfolio"].get(stock_id, 0) + amount
        save_data(self.data)
        await ctx.send(f"{ctx.author.mention}님이 {self.data['stocks'][stock_id]['name']} 주식을 {amount}주 구매하였습니다. (총 {total_cost}원)")

    @commands.command(name="주식판매")
    async def sell_stock(self, ctx, stock_id: str, amount: int):
        """예시: #주식판매 3 5 – 해당 주식 번호의 주식을 지정 수량만큼 판매합니다."""
        now = self.get_seoul_time()
        if now.day in [1, 2]:
            await ctx.send("현재 주식 거래가 중단되어 있습니다. (시즌 종료 및 휴식 기간)")
            return
        user_id = str(ctx.author.id)
        if user_id not in self.data["users"]:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return
        user = self.data["users"][user_id]
        if user["portfolio"].get(stock_id, 0) < amount:
            await ctx.send("판매할 주식 보유 수량이 부족합니다.")
            return
        price = self.data["stocks"][stock_id]["price"]
        revenue = price * amount
        user["money"] += revenue
        user["portfolio"][stock_id] -= amount
        if user["portfolio"][stock_id] <= 0:
            del user["portfolio"][stock_id]
        save_data(self.data)
        await ctx.send(f"{ctx.author.mention}님이 {self.data['stocks'][stock_id]['name']} 주식을 {amount}주 판매하여 {revenue}원을 획득하였습니다.")

    @commands.command(name="프로필")
    async def profile(self, ctx):
        """자신의 잔액, 보유 주식 내역 및 획득한 칭호(예: 2025 시즌2 TOP2)를 보여줍니다."""
        user_id = str(ctx.author.id)
        if user_id not in self.data["users"]:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. #주식참가 명령어로 참가해주세요.")
            return
        user = self.data["users"][user_id]
        portfolio_lines = []
        for stock_id, amount in user.get("portfolio", {}).items():
            price = self.data["stocks"].get(stock_id, {}).get("price", 0)
            portfolio_lines.append(f"{self.data['stocks'][stock_id]['name']}: {amount}주 (현재가: {price}원)")
        portfolio_str = "\n".join(portfolio_lines) if portfolio_lines else "보유 주식 없음"
        titles_str = ", ".join(user.get("titles", [])) if user.get("titles", []) else "없음"
        msg = (f"**{ctx.author.display_name}님의 프로필**\n"
               f"잔액: {user['money']}원\n"
               f"보유 주식:\n{portfolio_str}\n"
               f"칭호: {titles_str}")
        await ctx.send(msg)

    @commands.command(name="랭킹")
    async def ranking(self, ctx):
        """현재 자산(현금+보유 주식 평가액) 기준 상위 10명의 랭킹을 보여줍니다."""
        ranking_list = []
        for user_id, user_data in self.data["users"].items():
            total = user_data.get("money", DEFAULT_MONEY)
            for stock_id, amount in user_data.get("portfolio", {}).items():
                total += self.data["stocks"].get(stock_id, {}).get("price", 0) * amount
            ranking_list.append((user_id, total))
        ranking_list.sort(key=lambda x: x[1], reverse=True)
        msg_lines = ["**랭킹 TOP 10**"]
        for idx, (user_id, total) in enumerate(ranking_list[:10], start=1):
            user_obj = self.bot.get_user(int(user_id))
            name = user_obj.display_name if user_obj else f"ID:{user_id}"
            msg_lines.append(f"{idx}. {name} - {total}원")
        await ctx.send("\n".join(msg_lines))

def setup(bot):
    await bot.add_cog(StockCog(bot))

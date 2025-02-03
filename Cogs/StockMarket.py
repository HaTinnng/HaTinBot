import discord
from discord.ext import commands, tasks
import random
import sqlite3
from datetime import datetime, timedelta
import pytz

class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "stock_market.db"
        self.base_fund = 500000  # 기본금 500,000원
        self.kst = pytz.timezone("Asia/Seoul")
        self.previous_prices = {}
        self.update_stocks.start()
        self.reset_season.start()

        self.initialize_database()
        self.load_stocks()

    def initialize_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 500000
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                user_id INTEGER,
                stock TEXT,
                shares INTEGER,
                PRIMARY KEY (user_id, stock),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS titles (
                user_id INTEGER,
                title TEXT,
                PRIMARY KEY (user_id, title)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                stock TEXT PRIMARY KEY,
                price INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def load_stocks(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT stock, price FROM stocks")
        data = c.fetchall()
        if data:
            self.stocks = {stock: price for stock, price in data}
        else:
            self.stocks = {
                "PENNY": random.randint(10, 100),
                "AAPL": random.randint(100, 500),
                "TSLA": random.randint(100, 500),
                "GOOGL": random.randint(100, 500),
                "AMZN": random.randint(500, 2000),
                "MSFT": random.randint(500, 2000),
                "NVDA": random.randint(500, 2000),
                "FB": random.randint(2000, 10000),
                "DIS": random.randint(2000, 10000),
                "NFLX": random.randint(2000, 10000),
                "BRK.A": random.randint(10000, 50000),
                "GOOG": random.randint(10000, 50000),
                "TSMC": random.randint(10000, 50000),
                "VISA": random.randint(10000, 50000),
            }
            for stock, price in self.stocks.items():
                c.execute("INSERT INTO stocks (stock, price) VALUES (?, ?)", (stock, price))
            conn.commit()
        conn.close()

    def save_stocks(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        for stock, price in self.stocks.items():
            c.execute("UPDATE stocks SET price = ? WHERE stock = ?", (price, stock))
        conn.commit()
        conn.close()

    @tasks.loop(seconds=60)
    async def update_stocks(self):
        now = datetime.now(self.kst)
        if now.minute % 20 == 0:
            self.previous_prices = self.stocks.copy()
            for stock in self.stocks.keys():
                if self.stocks[stock] > 0:
                    change_percentage = random.uniform(-12.5, 12.5)
                    new_price = int(self.stocks[stock] * (1 + change_percentage / 100))
                    self.stocks[stock] = max(new_price, 0)
            self.save_stocks()

    @commands.command(name="프로필")
    async def profile(self, ctx):
        user_id = ctx.author.id
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = c.fetchone()
        balance = balance[0] if balance else 0
        c.execute("SELECT stock, shares FROM portfolio WHERE user_id = ?", (user_id,))
        portfolio = c.fetchall()
        c.execute("SELECT title FROM titles WHERE user_id = ?", (user_id,))
        titles = [row[0] for row in c.fetchall()]
        conn.close()
        desc = f"💰 보유 자금: {balance:,}원\n📈 보유 주식:\n"
        if portfolio:
            desc += "\n".join([f"{stock}: {shares}주" for stock, shares in portfolio])
        else:
            desc += "없음"
        desc += "\n🏆 보유 칭호:\n"
        if titles:
            desc += "\n".join(titles)
        else:
            desc += "없음"
        embed = discord.Embed(title=f"{ctx.author.display_name}님의 프로필", description=desc, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="주식랭킹")
    async def stock_ranking(self, ctx):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
        rankings = c.fetchall()
        conn.close()

        if not rankings:
            await ctx.send("📉 현재 주식 시장에 참여한 유저가 없습니다.")
            return

        ranking_list = []
        for i, (user_id, balance) in enumerate(rankings, start=1):
            user = self.bot.get_user(user_id)
            username = user.name if user else f"유저 {user_id}"
            ranking_list.append(f"**{i}등**: {username} - 💰 {balance:,}원")

        embed = discord.Embed(title="🏆 주식 랭킹 (보유 자산 TOP 10)", description="\n".join(ranking_list), color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StockMarket(bot))

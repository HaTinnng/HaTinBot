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

        # 주식 초기 가격 설정
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

        self.initialize_database()

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
            
    @tasks.loop(hours=1)
    async def reset_season(self):
        now = datetime.now(self.kst)
        if now.day == 1 and now.hour == 0:
            await self.end_season()
        elif now.day == 3 and now.hour == 0:
            await self.start_new_season()

    async def end_season(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 3")
        top_players = c.fetchall()
        year, month = datetime.now(self.kst).year, datetime.now(self.kst).month
        season_title = f"{year} 시즌{month} TOP"
        for rank, (user_id, _) in enumerate(top_players, start=1):
            c.execute("INSERT OR IGNORE INTO titles (user_id, title) VALUES (?, ?)", 
                      (user_id, f"{season_title}{rank}"))
        conn.commit()
        conn.close()

    @commands.command(name="주식정보")
    async def stock_info(self, ctx):
        embed = discord.Embed(title="📈 현재 주식 시장 상황", color=discord.Color.blue())
        for stock, price in self.stocks.items():
            prev_price = self.previous_prices.get(stock, price)
            change = price - prev_price
            change_symbol = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
            formatted_change = f"({change_symbol}{abs(change)})(변동률: {change / prev_price * 100:.1f}%)"
            value = f"{price:,}원 {formatted_change}" if price > 0 else "**상장폐지**"
            embed.add_field(name=f"🟢 {stock}" if price > 0 else f"🔴 {stock}", value=value, inline=False)
        embed.set_footer(text="💡 20분 후 가격이 변동됩니다.")
        await ctx.send(embed=embed)

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
        desc = f"💰 보유 자금: {balance:,}원\n📈 보유 주식:\n" + "\n".join([f"{s}: {sh}주" for s, sh in portfolio])
        desc += f"\n🏆 보유 칭호:\n" + "\n".join(titles) if titles else "없음"
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

    @commands.command(name="다음갱신")
    async def next_update(self, ctx):
        now = datetime.now(self.kst)
        next_update_minute = (now.minute // 20 + 1) * 20 % 60
        next_update_time = now.replace(minute=next_update_minute, second=0)
        if next_update_minute == 0:
            next_update_time += timedelta(hours=1)
        remaining_time = next_update_time - now
        await ctx.send(f"⏳ 다음 주식 변동까지 {remaining_time.seconds // 60}분 남았습니다. 갱신 시간: {next_update_time.strftime('%H:%M')} KST")

    @commands.command(name="시즌")
    async def season_info(self, ctx):
        now = datetime.now(self.kst)
        season_end = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=self.kst)
        if now >= season_end:
            season_end = datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=self.kst)
        remaining_time = season_end - now
        await ctx.send(f"📅 현재 시즌 종료까지 {remaining_time.days}일 {remaining_time.seconds // 3600}시간 남았습니다. 종료 시간: {season_end.strftime('%Y-%m-%d %H:%M')} KST")

    @commands.command(name="주식시작")
    async def join_stock_market(self, ctx):
        user_id = ctx.author.id
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone():
            await ctx.send(f"✅ {ctx.author.mention}님은 이미 주식 시장에 참여하고 있습니다!")
            conn.close()
            return
        c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, self.base_fund))
        conn.commit()
        conn.close()
        await ctx.send(f"🎉 {ctx.author.mention}님이 주식 시장에 참여했습니다! 기본금 {self.base_fund:,}원이 지급됩니다.")

    @commands.command(name="주식구매")
    async def buy_stock(self, ctx, stock: str, amount: int):
        user_id = ctx.author.id
        stock = stock.upper()
        if stock not in self.stocks or self.stocks[stock] == 0:
            await ctx.send("❌ 해당 주식은 존재하지 않거나 상장폐지되었습니다.")
            return
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result is None:
            await ctx.send("❌ 주식 시장에 참여하지 않았습니다. `#주식시작`을 입력하세요.")
            conn.close()
            return
        balance = result[0]
        total_price = self.stocks[stock] * amount
        if balance < total_price:
            await ctx.send("❌ 잔고가 부족합니다.")
            conn.close()
            return
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (total_price, user_id))
        c.execute("INSERT INTO portfolio (user_id, stock, shares) VALUES (?, ?, ?) ON CONFLICT(user_id, stock) DO UPDATE SET shares = shares + ?",
                  (user_id, stock, amount, amount))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ {ctx.author.mention}님이 {stock} {amount}주를 구매하였습니다.")

    @commands.command(name="주식판매")
    async def sell_stock(self, ctx, stock: str, amount: int):
        user_id = ctx.author.id
        stock = stock.upper()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT shares FROM portfolio WHERE user_id = ? AND stock = ?", (user_id, stock))
        result = c.fetchone()
        if result is None or result[0] < amount:
            await ctx.send("❌ 보유 주식이 부족합니다.")
            conn.close()
            return
        total_price = self.stocks[stock] * amount
        c.execute("UPDATE portfolio SET shares = shares - ? WHERE user_id = ? AND stock = ?", (amount, user_id, stock))
        c.execute("DELETE FROM portfolio WHERE user_id = ? AND stock = ? AND shares = 0", (user_id, stock))
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total_price, user_id))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ {ctx.author.mention}님이 {stock} {amount}주를 판매하였습니다.")




async def setup(bot):
    await bot.add_cog(StockMarket(bot))

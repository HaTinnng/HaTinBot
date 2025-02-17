import discord
import random
from discord.ext import commands
from pymongo import MongoClient
import os

# MongoDB 설정
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]

    @commands.command(name="룰렛")
    async def roulette(self, ctx, bet_amount: int):
        """
        #룰렛 [금액]: 해당 금액을 배팅하고 777 룰렛을 진행합니다.
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})

        if not user:
            await ctx.send("❌ 주식 게임에 참가하지 않았습니다. `#주식참가`를 먼저 입력하세요!")
            return
        
        if bet_amount <= 0:
            await ctx.send("❌ 배팅 금액은 1원 이상이어야 합니다!")
            return

        if user["money"] < bet_amount:
            await ctx.send("❌ 잔액이 부족합니다!")
            return

        # 룰렛 심볼과 확률 설정 (가중치 기반)
        symbol_weights = {
            "7": 1,   # 1% 확률
            "★": 2,   # 2% 확률
            "☆": 3,   # 3% 확률
            "💎": 5,   # 5% 확률
            "🍒": 10,   # 10% 확률
            "🍀": 14,  # 14%
            "🔔": 65   # 65% (꽝)
        }

        # 3개의 슬롯을 가중치에 따라 랜덤 선택
        symbols = random.choices(list(symbol_weights.keys()), weights=list(symbol_weights.values()), k=3)
        result = "".join(symbols)

        # 당첨 확률 및 배당률 설정
        payout_multiplier = 0  # 기본적으로 0배
        if result == "777":
            payout_multiplier = 40  # 777: 40배
        elif result == "★★★":
            payout_multiplier = 25  # ★★★: 25배
        elif result == "☆☆☆":
            payout_multiplier = 18  # ☆☆☆: 18배
        elif result == "💎💎💎":
            payout_multiplier = 10  # 10배
        elif result == "🍒🍒🍒":
            payout_multiplier = 8 # 8배
        elif result == "🍀🍀🍀":
            payout_multiplier = 4 # 4배
          
        else:
            # 2개 일치 보상 (차등 지급)
            if symbols.count("7") == 2:
                payout_multiplier = 12  # 7이 2개 → 12배
            elif symbols.count("★") == 2:
                payout_multiplier = 9  # ★가 2개 → 9배
            elif symbols.count("☆") == 2:
                payout_multiplier = 7  # ☆가 2개 → 7배
            elif symbols.count("💎") == 2:
                payout_multiplier = 4  # 💎이 2개 → 4배
            elif symbols.count("🍒") == 2:
                payout_multiplier = 2 # 🍒이 2개 → 2배
            elif symbols.count("🍀") == 2:
                payout_multiplier = 1 # 🍀이 2개 → 1배

        payout = bet_amount * payout_multiplier  # 지급 금액 계산
        new_balance = user["money"] - bet_amount + payout  # 배팅 금액 차감 후 계산

        # 데이터베이스에 반영
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_balance}})

        # 결과 메시지
        embed = discord.Embed(title="🎰 777 룰렛 결과 🎰", color=discord.Color.gold())
        embed.add_field(name="🎲 룰렛 결과", value=f"`| {symbols[0]} | {symbols[1]} | {symbols[2]} |`", inline=False)

        if payout_multiplier > 0:
            embed.add_field(name="🎉 당첨!", value=f"💰 {payout:,}원 획득! (배팅금 {bet_amount:,}원 × {payout_multiplier}배)", inline=False)
        else:
            embed.add_field(name="💸 꽝!", value=f"😭 {bet_amount:,}원을 잃었습니다!", inline=False)

        embed.add_field(name="💰 현재 잔액", value=f"{new_balance:,}원", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roulette(bot))

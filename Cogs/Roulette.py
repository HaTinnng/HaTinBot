import discord
import random
import asyncio  # asyncio 모듈 추가
from discord.ext import commands
from pymongo import MongoClient
import os
from datetime import datetime
import pytz

# MongoDB 설정
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

def is_season_active() -> bool:
    tz = pytz.timezone("Asia/Seoul")
    now = datetime.now(tz)
    start = tz.localize(datetime(now.year, now.month, 1, 0, 10))
    end = tz.localize(datetime(now.year, now.month, 26, 0, 10))
    return start <= now < end

class AllInConfirmationView(discord.ui.View):
    def __init__(self, author: discord.User, timeout=30):
        super().__init__(timeout=timeout)
        self.author = author
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("이 명령어를 실행한 본인만 사용할 수 있습니다.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="진행하기", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.edit_message(content="진행 중...", embed=None, view=None)

    @discord.ui.button(label="그만두기", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.edit_message(content="룰렛이 취소되었습니다.", embed=None, view=None)

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]

    @commands.command(name="룰렛", aliases=["슬롯"])
    async def roulette(self, ctx, bet: str):
        """
        #룰렛 [금액/다/전부/올인]:
        숫자를 입력하면 해당 금액을 배팅하고 777 룰렛을 진행합니다.
        '다', '전부', '올인'을 입력하면 가지고 있는 돈을 모두 배팅합니다.
        """
        # 시즌 활성 여부 체크 (매월 1일 0시 10분 ~ 26일 0시 10분)
        if not is_season_active():
            await ctx.send("❌ 현재 시즌은 종료되었습니다. 다음 시즌(매월 1일 0시 10분 이후)에 이용해주세요!")
            return

        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})

        if not user:
            await ctx.send("❌ 주식 게임에 참가하지 않았습니다. `#주식참가`를 먼저 입력하세요!")
            return

        # '다', '전부', '올인' 키워드 처리 (전 재산 배팅)
        if bet in ["다", "전부", "올인"]:
            bet_amount = user["money"]
            if bet_amount <= 0:
                await ctx.send("❌ 잔액이 부족합니다!")
                return

            warning_embed = discord.Embed(
                title="경고",
                description=f"모든 돈({bet_amount:,}원)을 배팅합니다. 진행하시겠습니까?",
                color=discord.Color.red()
            )
            view = AllInConfirmationView(ctx.author, timeout=30)
            await ctx.send(embed=warning_embed, view=view)
            await view.wait()
            if view.value is None:
                await ctx.send(f"{ctx.author.mention}님, 시간 초과로 룰렛이 취소되었습니다.")
                return
            if not view.value:
                return
        else:
            try:
                bet_amount = int(bet)
            except ValueError:
                await ctx.send("❌ 올바른 금액 또는 키워드를 입력해주세요!")
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
            "★": 3,   # 3% 확률
            "☆": 5,   # 5% 확률
            "💎": 7,   # 7% 확률
            "🍒": 10,  # 10% 확률
            "🍀": 15,  # 15%
            "🔔": 21,  # 21%
            "❌": 38   # 38% (꽝)
        }

        # 3개의 슬롯을 가중치에 따라 랜덤 선택
        symbols = random.choices(list(symbol_weights.keys()), weights=list(symbol_weights.values()), k=3)
        result = "".join(symbols)

        # 당첨 확률 및 배당률 설정
        payout_multiplier = 0  # 기본적으로 0배
        if result == "777":
            payout_multiplier = 77  # 777: 77배
        elif result == "★★★":
            payout_multiplier = 52  # ★★★: 52배
        elif result == "☆☆☆":
            payout_multiplier = 38  # ☆☆☆: 38배
        elif result == "💎💎💎":
            payout_multiplier = 25  # 25배
        elif result == "🍒🍒🍒":
            payout_multiplier = 18  # 18배
        elif result == "🍀🍀🍀":
            payout_multiplier = 12   # 12배
        elif result == "🔔🔔🔔":
            payout_multiplier = 5   # 5배    
        else:
            # 2개 일치 보상 (차등 지급)
            if symbols.count("7") == 2:
                payout_multiplier = 27  # 7이 2개 → 27배
            elif symbols.count("★") == 2:
                payout_multiplier = 18  # ★가 2개 → 18배
            elif symbols.count("☆") == 2:
                payout_multiplier = 12   # ☆가 2개 → 12배
            elif symbols.count("💎") == 2:
                payout_multiplier = 8   # 💎이 2개 → 8배
            elif symbols.count("🍒") == 2:
                payout_multiplier = 4   # 🍒이 2개 → 4배
            elif symbols.count("🍀") == 2:
                payout_multiplier = 2   # 🍀이 2개 → 2배
            elif symbols.count("🔔") == 2:
                payout_multiplier = 1 # 🔔이 2개 → 1배    

        payout = bet_amount * payout_multiplier  # 지급 금액 계산
        new_balance = user["money"] - bet_amount + payout  # 배팅 금액 차감 후 계산

        # 데이터베이스에 반영
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_balance}})

        # 슬롯머신 돌리는 동안 메시지 전송
        loading_message = await ctx.send("⏳슬롯머신을 돌리고 있습니다...")
        await asyncio.sleep(3)
        await loading_message.delete()

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

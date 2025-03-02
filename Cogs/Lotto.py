import discord
import random
from discord.ext import commands, tasks
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import pytz

# MongoDB 설정
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

###############################################
# PaginationView (페이지네이션 뷰) 및 관련 버튼
###############################################
class PaginationView(discord.ui.View):
    def __init__(self, data, title, per_page=10):
        super().__init__(timeout=180)
        self.data = data
        self.title = title
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = (len(data) - 1) // per_page + 1 if data else 1
        self.update_buttons()
    
    def update_buttons(self):
        self.clear_items()
        # 이전 버튼
        self.add_item(PrevButton(self))
        # 페이지 표시 (비활성)
        page_label = f"{self.current_page+1}/{self.total_pages}"
        self.add_item(PageIndicatorButton(page_label))
        # 다음 버튼
        self.add_item(NextButton(self))
    
    def get_page_content(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_data = self.data[start:end]
        content = "\n".join(page_data) if page_data else "표시할 데이터가 없습니다."
        return f"**{self.title}**\n\n" + content

class PrevButton(discord.ui.Button):
    def __init__(self, view: PaginationView):
        super().__init__(style=discord.ButtonStyle.primary, label="이전")
        self.pagination_view = view

    async def callback(self, interaction: discord.Interaction):
        if self.pagination_view.current_page == 0:
            await interaction.response.send_message("첫번째 페이지입니다", ephemeral=True)
        else:
            self.pagination_view.current_page -= 1
            self.pagination_view.update_buttons()
            new_content = self.pagination_view.get_page_content()
            await interaction.response.edit_message(content=new_content, view=self.pagination_view)

class PageIndicatorButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(style=discord.ButtonStyle.secondary, label=label, disabled=True)

class NextButton(discord.ui.Button):
    def __init__(self, view: PaginationView):
        super().__init__(style=discord.ButtonStyle.primary, label="다음")
        self.pagination_view = view

    async def callback(self, interaction: discord.Interaction):
        if self.pagination_view.current_page >= self.pagination_view.total_pages - 1:
            await interaction.response.send_message("마지막페이지입니다", ephemeral=True)
        else:
            self.pagination_view.current_page += 1
            self.pagination_view.update_buttons()
            new_content = self.pagination_view.get_page_content()
            await interaction.response.edit_message(content=new_content, view=self.pagination_view)

###############################################
# 1. 전역 체크 함수 (주식 시즌 체크)
###############################################
def global_stock_season_check(ctx):
    """
    모든 명령어는 매월 1일 0시 10분부터 26일 0시 10분까지 사용 가능합니다.
    """
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    try:
        season_start = now.replace(day=1, hour=0, minute=10, second=0, microsecond=0)
        season_end = now.replace(day=26, hour=0, minute=10, second=0, microsecond=0)
    except ValueError:
        # 예외 발생 시 기본적으로 허용
        return True

    if season_start <= now < season_end:
        return True
    else:
        raise commands.CheckFailure(
            "현재는 시즌 기간이 아닙니다. 명령어는 매월 1일 0시 10분부터 26일 0시 10분까지 사용 가능합니다!"
        )

###############################################
# 2. Lotto Cog (복권 관련 명령어)
###############################################
class Lotto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]
        self.last_reset_month = None

        # 봇 실행 시 복권 추첨 태스크와 초기화 태스크 시작
        self.lotto_draw_task.start()
        self.lotto_reset_task.start()

    def cog_unload(self):
        """Cog이 언로드될 때 태스크 종료"""
        self.lotto_draw_task.cancel()
        self.lotto_reset_task.cancel()

    def get_seoul_time(self):
        """현재 한국 시간 반환"""
        return datetime.now(pytz.timezone("Asia/Seoul"))

    def get_next_lotto_draw_time(self):
        """
        현재 시각을 기준으로 다음 로또 추첨일(매주 일요일 21:00)을 계산합니다.
        """
        now = self.get_seoul_time()
        days_until_sunday = (6 - now.weekday()) % 7
        candidate = now.replace(hour=21, minute=0, second=0, microsecond=0) + timedelta(days=days_until_sunday)
        if now.weekday() == 6 and now >= now.replace(hour=21, minute=0, second=0, microsecond=0):
            candidate += timedelta(days=7)
        return candidate

    @commands.command(name="복권구매")
    async def buy_lotto(self, ctx, ticket_count: int):
        """
        #복권구매 [n] : 1장당 5,000원, 최대 30장까지 구매 가능
        ※ 복권은 주식 돈을 사용하지만, 복권 명령어는 언제든 사용할 수 있습니다.
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        now = self.get_seoul_time()
        season_start = now.replace(day=1, hour=0, minute=10, second=0, microsecond=0)
        season_end = now.replace(day=26, hour=0, minute=10, second=0, microsecond=0)
        next_draw = self.get_next_lotto_draw_time()
        if not (season_start <= next_draw < season_end):
            await ctx.send("❌ 다음 로또 추첨일이 현재 주식 시즌에 포함되지 않으므로 복권 구매가 불가능합니다!")
            return

        if not user:
            await ctx.send("❌ 주식 게임에 참가하지 않았습니다. `#주식참가`를 먼저 입력하세요!")
            return

        if ticket_count <= 0:
            await ctx.send("❌ 최소 1장 이상 구매해야 합니다!")
            return

        if ticket_count > 30:
            await ctx.send("❌ 한 주에 최대 30장까지만 구매할 수 있습니다!")
            return

        cost = ticket_count * 5000

        current_week = now.strftime("%Y-%W")
        doc_id = f"{user_id}_{current_week}"
        user_lotto = self.db.lotto.find_one({"_id": doc_id})

        if user_lotto:
            if len(user_lotto["tickets"]) + ticket_count > 30:
                await ctx.send("❌ 한 주에 최대 30장까지만 구매할 수 있습니다!")
                return

        # 1~45 중 6개 랜덤 선택으로 복권 티켓 생성
        tickets = [sorted(random.sample(range(1, 46), 6)) for _ in range(ticket_count)]
        self.db.users.update_one({"_id": user_id}, {"$inc": {"money": -cost}})
        self.db.lotto.update_one(
            {"_id": doc_id},
            {"$set": {"week": current_week}, "$push": {"tickets": {"$each": tickets}}},
            upsert=True
        )

        await ctx.send(f"🎟 {ctx.author.mention}, {ticket_count}장 복권을 구매했습니다! (총 {cost:,}원)")

    @commands.command(name="복권확인")
    async def check_lotto(self, ctx):
        """
        #복권확인 : 본인의 복권 번호 및 당첨 여부 확인 (추첨 전에도 확인 가능)
        지난주와 이번주 구매 내역을 각각 표시합니다.
        """
        user_id = str(ctx.author.id)
        now = self.get_seoul_time()
        current_week = now.strftime("%Y-%W")
        last_week = (now - timedelta(weeks=1)).strftime("%Y-%W")
        doc_id_current = f"{user_id}_{current_week}"
        doc_id_last = f"{user_id}_{last_week}"

        # 지난주 복권 구매 내역
        user_lotto_last = self.db.lotto.find_one({"_id": doc_id_last})
        if user_lotto_last and user_lotto_last.get("tickets"):
            tickets = user_lotto_last["tickets"]
            ticket_lines = [f"🎟 `{i+1}번`: `{ticket}`" for i, ticket in enumerate(tickets)]
            view = PaginationView(ticket_lines, title=f"지난주({last_week}) 복권 구매 내역")
            await ctx.send(content=view.get_page_content(), view=view)
        else:
            await ctx.send("🎟 지난주에 구매한 복권이 없습니다!")

        # 이번주 복권 구매 내역
        user_lotto_current = self.db.lotto.find_one({"_id": doc_id_current})
        if user_lotto_current and user_lotto_current.get("tickets"):
            tickets = user_lotto_current["tickets"]
            ticket_lines = [f"🎟 `{i+1}번`: `{ticket}`" for i, ticket in enumerate(tickets)]
            view = PaginationView(ticket_lines, title=f"이번주({current_week}) 복권 구매 내역")
            await ctx.send(content=view.get_page_content(), view=view)
        else:
            await ctx.send("🎟 이번 주에 구매한 복권이 없습니다!")

    @commands.command(name="복권결과")
    async def lotto_result(self, ctx):
        """
        #복권결과 : 지난주와 이번주 당첨 번호 확인
        각 주별로 당첨 번호를 10개씩 나누어 표시합니다.
        """
        now = self.get_seoul_time()
        current_week = now.strftime("%Y-%W")
        last_week = (now - timedelta(weeks=1)).strftime("%Y-%W")

        # 지난주 복권 결과
        result_last = self.db.lotto_result.find_one({"_id": last_week})
        if result_last and result_last.get("numbers"):
            numbers = result_last["numbers"]
            result_line = f"📢 당첨 번호: `{' '.join(map(str, numbers))}`"
            view = PaginationView([result_line], title=f"지난주({last_week}) 복권 결과")
            await ctx.send(content=view.get_page_content(), view=view)
        else:
            await ctx.send("📢 지난 주 복권 당첨 번호가 아직 추첨되지 않았습니다!")

        # 이번주 복권 결과
        result_current = self.db.lotto_result.find_one({"_id": current_week})
        if result_current and result_current.get("numbers"):
            numbers = result_current["numbers"]
            result_line = f"📢 당첨 번호: `{' '.join(map(str, numbers))}`"
            view = PaginationView([result_line], title=f"이번주({current_week}) 복권 결과")
            await ctx.send(content=view.get_page_content(), view=view)
        else:
            await ctx.send("📢 이번 주 복권 당첨 번호가 아직 추첨되지 않았습니다!")

    @tasks.loop(hours=1)
    async def lotto_draw_task(self):
        """매주 일요일 21:00 자동 복권 추첨"""
        now = self.get_seoul_time()
        if now.weekday() == 6 and now.hour == 21:
            current_week = now.strftime("%Y-%W")
            winning_numbers = sorted(random.sample(range(1, 46), 6))
            self.db.lotto_result.update_one(
                {"_id": current_week},
                {"$set": {"numbers": winning_numbers}},
                upsert=True
            )
            channel = self.bot.get_channel(YOUR_CHANNEL_ID)  # 결과 발표 채널 ID 설정
            if channel:
                await channel.send(f"🎉 이번 주 복권 당첨 번호: `{' '.join(map(str, winning_numbers))}`")

    @lotto_draw_task.before_loop
    async def before_lotto_draw(self):
        """봇이 준비될 때까지 대기"""
        await self.bot.wait_until_ready()
    
    @tasks.loop(minutes=1)
    async def lotto_reset_task(self):
        """매월 26일 0시 10분에 복권 데이터 초기화"""
        now = self.get_seoul_time()
        if now.day == 26 and now.hour == 0 and now.minute == 10:
            if self.last_reset_month != now.month:
                self.db.lotto.delete_many({})
                self.db.lotto_result.delete_many({})
                self.last_reset_month = now.month
                channel = self.bot.get_channel(YOUR_CHANNEL_ID)  # 결과 발표 채널 ID 설정
                if channel:
                    await channel.send("📢 복권 데이터가 초기화되었습니다. 새로운 시즌을 시작합니다!")

async def setup(bot):
    await bot.add_cog(Lotto(bot))

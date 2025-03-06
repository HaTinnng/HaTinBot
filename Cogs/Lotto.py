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
    async def buy_lotto(self, ctx, ticket_arg: str):
        """
        #복권구매 [숫자 또는 다/전부/올인] : 1장당 5,000원, 최대 30장까지 구매 가능
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

        special_keywords = ["다", "전부", "올인"]
        current_week = now.strftime("%Y-%W")
        doc_id = f"{user_id}_{current_week}"
        user_lotto = self.db.lotto.find_one({"_id": doc_id})
        already_bought = len(user_lotto["tickets"]) if user_lotto and user_lotto.get("tickets") else 0

        if ticket_arg in special_keywords:
            available_money = user.get("money", 0)
            max_affordable = available_money // 5000
            remaining_limit = 30 - already_bought
            ticket_count = min(max_affordable, remaining_limit)
            if ticket_count <= 0:
                await ctx.send("❌ 구매 가능한 복권 티켓이 없습니다. (자금 부족 또는 최대 구매량 도달)")
                return
        else:
            try:
                ticket_count = int(ticket_arg)
            except ValueError:
                await ctx.send("❌ 구매할 복권 티켓 수는 숫자 또는 '다', '전부', '올인' 중 하나여야 합니다!")
                return

            if ticket_count <= 0:
                await ctx.send("❌ 최소 1장 이상 구매해야 합니다!")
                return
            if ticket_count > 30:
                await ctx.send("❌ 한 주에 최대 30장까지만 구매할 수 있습니다!")
                return
            if already_bought + ticket_count > 30:
                await ctx.send("❌ 한 주에 최대 30장까지만 구매할 수 있습니다!")
                return

        cost = ticket_count * 5000
        if user.get("money", 0) < cost:
            await ctx.send("❌ 보유한 현금이 부족합니다!")
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
        구매 내역을 추첨일 기준으로 분리하여 표시합니다.
        당첨 번호가 기록된 티켓은 '지난주', 아직 추첨되지 않은 티켓은 '이번주'로 분류됩니다.
        """
        user_id = str(ctx.author.id)
        now = self.get_seoul_time()
        current_week = now.strftime("%Y-%W")
        last_week = (now - timedelta(weeks=1)).strftime("%Y-%W")
        
        # 사용자 복권 구매 내역 조회 (현재 주와 지난 주)
        doc_id_current = f"{user_id}_{current_week}"
        doc_id_last = f"{user_id}_{last_week}"
        user_lotto_current = self.db.lotto.find_one({"_id": doc_id_current})
        user_lotto_last = self.db.lotto.find_one({"_id": doc_id_last})
        
        # 각 주의 당첨 결과 여부 확인
        result_current = self.db.lotto_result.find_one({"_id": current_week})
        result_last = self.db.lotto_result.find_one({"_id": last_week})
        
        drawn_tickets_lines = []    # 당첨 번호가 이미 발표된 티켓 (지난주)
        undrawn_tickets_lines = []  # 아직 당첨번호 발표 전 티켓 (이번주)
        
        # 지난 주 복권 내역 처리
        if user_lotto_last and user_lotto_last.get("tickets"):
            if result_last:  # 지난 주 당첨 번호가 존재하면 이미 추첨된 티켓
                ticket_lines = [f"🎟 `{i+1}번`: `{ticket}`" for i, ticket in enumerate(user_lotto_last["tickets"])]
                drawn_tickets_lines.extend(ticket_lines)
            else:  # 드물지만 결과가 없는 경우 undrawn 처리
                ticket_lines = [f"🎟 `{i+1}번`: `{ticket}`" for i, ticket in enumerate(user_lotto_last["tickets"])]
                undrawn_tickets_lines.extend(ticket_lines)
        
        # 이번 주 복권 내역 처리
        if user_lotto_current and user_lotto_current.get("tickets"):
            if result_current:  # 당첨 결과가 있으면 이미 추첨된 것으로 간주
                ticket_lines = [f"🎟 `{i+1}번`: `{ticket}`" for i, ticket in enumerate(user_lotto_current["tickets"])]
                drawn_tickets_lines.extend(ticket_lines)
            else:
                ticket_lines = [f"🎟 `{i+1}번`: `{ticket}`" for i, ticket in enumerate(user_lotto_current["tickets"])]
                undrawn_tickets_lines.extend(ticket_lines)
        
        # 지난주(추첨 완료) 티켓 표시
        if drawn_tickets_lines:
            view = PaginationView(drawn_tickets_lines, title="지난주 복권 구매 내역")
            await ctx.send(content=view.get_page_content(), view=view)
        else:
            await ctx.send("🎟 지난주에 구매한 복권이 없습니다!")
        
        # 이번주(추첨 전) 티켓 표시
        if undrawn_tickets_lines:
            view = PaginationView(undrawn_tickets_lines, title="이번주 복권 구매 내역")
            await ctx.send(content=view.get_page_content(), view=view)
        else:
            await ctx.send("🎟 이번 주에 구매한 복권이 없습니다!")

    # 복권결과 명령어는 당첨금 지급 여부와 결과를 확인하기 위한 용도로 남겨두었습니다.
    @commands.command(name="복권결과")
    async def lotto_result(self, ctx):
        """
        #복권결과 : 지난주와 이번주 당첨 번호 확인
        이미 당첨금이 지급된 티켓은 지급 여부와 당첨 금액을 표시합니다.
        """
        user_id = str(ctx.author.id)
        now = self.get_seoul_time()
        current_week = now.strftime("%Y-%W")
        last_week = (now - timedelta(weeks=1)).strftime("%Y-%W")

        messages = []
        # 지난주 복권 결과 확인
        result_last = self.db.lotto_result.find_one({"_id": last_week})
        if result_last and result_last.get("numbers"):
            numbers = result_last["numbers"]
            result_line = f"📢 당첨 번호: `{' '.join(map(str, numbers))}`"
            user_lotto_last = self.db.lotto.find_one({"_id": f"{user_id}_{last_week}"})
            if user_lotto_last:
                if user_lotto_last.get("paid", False):
                    messages.append("지난주 복권 당첨금은 지급되었습니다.")
                else:
                    messages.append("지난주 복권 당첨금이 아직 지급되지 않았습니다.")
            else:
                messages.append("지난주 복권 구매 기록이 없습니다.")
            messages.insert(0, result_line)
        else:
            messages.append("📢 지난 주 복권 당첨 번호가 아직 추첨되지 않았습니다!")

        # 이번주 복권 결과 확인
        result_current = self.db.lotto_result.find_one({"_id": current_week})
        if result_current and result_current.get("numbers"):
            numbers = result_current["numbers"]
            result_line = f"📢 당첨 번호: `{' '.join(map(str, numbers))}`"
            user_lotto_current = self.db.lotto.find_one({"_id": f"{user_id}_{current_week}"})
            if user_lotto_current:
                if user_lotto_current.get("paid", False):
                    messages.append("이번주 복권 당첨금은 지급되었습니다.")
                else:
                    messages.append("이번주 복권 당첨금이 아직 지급되지 않았습니다.")
            else:
                messages.append("이번주 복권 구매 기록이 없습니다.")
            messages.insert(0, result_line)
        else:
            messages.append("📢 이번 주 복권 당첨 번호가 아직 추첨되지 않았습니다!")

        view = PaginationView(messages, title="복권 결과 확인")
        await ctx.send(content=view.get_page_content(), view=view)

    @tasks.loop(hours=1)
    async def lotto_draw_task(self):
        """매주 일요일 21:00 자동 복권 추첨 및 당첨금 자동 지급"""
        now = self.get_seoul_time()
        if now.weekday() == 6 and now.hour == 21:
            current_week = now.strftime("%Y-%W")
            # 당첨 번호 생성
            winning_numbers = sorted(random.sample(range(1, 46), 6))
            self.db.lotto_result.update_one(
                {"_id": current_week},
                {"$set": {"numbers": winning_numbers}},
                upsert=True
            )
            # 해당 주의 모든 복권 구매 기록 중 아직 지급되지 않은 문서를 조회
            docs = list(self.db.lotto.find({"_id": {"$regex": f"_{current_week}$"}, "paid": {"$ne": True}}))
            for doc in docs:
                user_id, _ = doc["_id"].split("_")
                tickets = doc.get("tickets", [])
                total_prize = 0
                prize_details = []  # 각 티켓별 당첨 내역 기록
                winning_count = 0  # 당첨 티켓 개수

                # 각 티켓별 맞춘 번호 개수에 따라 당첨금 산정
                for ticket in tickets:
                    match_count = len(set(ticket) & set(winning_numbers))
                    if match_count == 6:
                        prize = 100000000
                    elif match_count == 5:
                        prize = 20000000
                    elif match_count == 4:
                        prize = 5000000
                    elif match_count == 3:
                        prize = 50000
                    else:
                        prize = 0
                    total_prize += prize
                    if prize > 0:
                        winning_count += 1
                    prize_details.append(f"티켓 {ticket} : {match_count}개 맞음 -> {prize:,}원")

                try:
                    user_obj = await self.bot.fetch_user(int(user_id))
                    if total_prize > 0:
                        # 사용자 잔액 업데이트
                        self.db.users.update_one({"_id": user_id}, {"$inc": {"money": total_prize}})
                        # 개인 DM으로 당첨 내역 전송 (당첨 티켓 개수와 총 지급 금액 포함)
                        await user_obj.send(
                            f"🎊 이번 주 복권 당첨 결과:\n당첨 번호: `{' '.join(map(str, winning_numbers))}`\n"
                            + "\n".join(prize_details)
                            + f"\n\n당첨 티켓 수: 복권 {winning_count}개가 당첨되었습니다.\n총 {total_prize:,}원이 지급되었습니다."
                        )
                    else:
                        await user_obj.send(
                            f"😢 이번 주 복권 당첨 결과:\n당첨 번호: `{' '.join(map(str, winning_numbers))}`\n"
                            "당첨 내역이 없습니다."
                        )
                except Exception as e:
                    print(f"Error sending DM to user {user_id}: {e}")

                # 지급 완료 후 중복 지급 방지 처리
                self.db.lotto.update_one({"_id": doc["_id"]}, {"$set": {"paid": True}})

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

async def setup(bot):
    await bot.add_cog(Lotto(bot))

# CloverFit5x3.py
import os, random, asyncio
from datetime import datetime
import pytz
import discord
from discord.ext import commands
from pymongo import MongoClient
from urllib.parse import urlparse

MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME    = "stock_game"           # reuse your existing DB; collections are separate

GRID_W = 5
GRID_H = 3

SPINS_PER_ROUND     = 5              # max spins per round
ROUND_BASE_QUOTA    = 1200           # quota for round 1
ROUND_QUOTA_STEP    = 600            # quota increase per next round
BET_UNIT            = 100            # each scoring pattern win is multiplied by this

# Symbol table: name, weight (rarity), base (payout base for a 3-match)
SYMBOLS = [
    {"ch":"🍀", "weight": 42, "base": 10},   # common
    {"ch":"⭐", "weight": 22, "base": 20},
    {"ch":"🔔", "weight": 16, "base": 30},
    {"ch":"💎", "weight": 12, "base": 50},
    {"ch":"7️⃣", "weight":  8, "base":100},
]

# Pattern multipliers
HORIZON_3X   = 1.0   # 3-in-a-row (horizontal contiguous)
HORIZON_4X   = 1.5
HORIZON_5X   = 2.0
DIAGONAL_3X  = 1.6   # any 3-length diagonal (↘ / ↙)
TRIANGLE_3X  = 2.5   # ▲ or ▼ triangle of size 3 cells (window width=3)

# Emojis for animation
SPIN_PLACEHOLDER = "🔄"
DIVIDER = "\n"

TZ = pytz.timezone("Asia/Seoul")

def kr_now():
    return datetime.now(TZ)

class CloverFit5x3(commands.Cog):
    def __init__(self, bot):
        if not MONGO_URI:
            raise RuntimeError("MONGODB_URI is not set")
        parsed = urlparse(MONGO_URI)
        print(f"[MongoDB] CloverFit5x3 connecting host={parsed.hostname}")
        self.bot   = bot
        self.mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
        self.mongo.admin.command("ping")
        self.db    = self.mongo[DB_NAME]
        self.users = self.db["clover5_users"]
        self.runs  = self.db["clover5_runs"]

        # 유예 타이머(60초) 관리: user_id -> asyncio.Task
        self.grace_tasks = {}

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _ensure_user(self, uid:str):
        doc = self.users.find_one({"_id": uid})
        if not doc:
            doc = {"_id": uid, "coins": 0, "charms": {}, "nickname": None}
            self.users.insert_one(doc)
        return doc

    def _current_run(self, uid:str):
        return self.runs.find_one({"user_id": uid, "status": "playing"})

    def _new_run(self, uid:str):
        run = {
            "_id": f"{uid}:{int(kr_now().timestamp())}",
            "user_id": uid,
            "status": "playing",
            "round": 1,
            "quota": ROUND_BASE_QUOTA,
            "bank": 0,
            "spins_left": SPINS_PER_ROUND,
            "created_at": kr_now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.runs.insert_one(run)
        return run

    def _roll_grid(self):
        table = []
        weights = [s["weight"] for s in SYMBOLS]
        names   = [s["ch"] for s in SYMBOLS]
        for _r in range(GRID_H):
            row = random.choices(names, weights=weights, k=GRID_W)
            table.append(row)
        return table

    def _render_grid(self, grid, reveal_cols:int=None):
        # reveal_cols: show from left; rest as placeholder
        lines = []
        for r in range(GRID_H):
            cells = []
            for c in range(GRID_W):
                if reveal_cols is None or c < reveal_cols:
                    cells.append(grid[r][c])
                else:
                    cells.append(SPIN_PLACEHOLDER)
            lines.append("".join(cells))
        return DIVIDER.join(lines)

    def _symbol_base(self, ch:str):
        for s in SYMBOLS:
            if s["ch"] == ch:
                return s["base"]
        return 0

    def _score_grid(self, grid):
        # Returns (total_reward:int, breakdown:list[str])
        total = 0
        logs  = []

        # Horizontal contiguous 3+
        for r in range(GRID_H):
            c = 0
            while c < GRID_W:
                ch = grid[r][c]
                run_len = 1
                j = c+1
                while j < GRID_W and grid[r][j] == ch:
                    run_len += 1
                    j += 1
                if run_len >= 3:
                    base = self._symbol_base(ch)
                    if run_len == 3:
                        mult = HORIZON_3X
                    elif run_len == 4:
                        mult = HORIZON_4X
                    else:
                        mult = HORIZON_5X
                    gain = int(base * mult * BET_UNIT)
                    total += gain
                    logs.append(f"가로 {run_len}연속 {ch} +{gain:,}")
                c = j

        # Diagonals length 3 (↘ and ↙) in sliding windows of width 3
        for sc in range(GRID_W - 2):
            # ↘ : (0,sc) (1,sc+1) (2,sc+2)
            a,b,c = grid[0][sc], grid[1][sc+1], grid[2][sc+2]
            if a == b == c:
                base = self._symbol_base(a)
                gain = int(base * DIAGONAL_3X * BET_UNIT)
                total += gain
                logs.append(f"대각선↘ 3연속 {a} +{gain:,}")
            # ↙ : (0,sc+2) (1,sc+1) (2,sc)
            a,b,c = grid[0][sc+2], grid[1][sc+1], grid[2][sc]
            if a == b == c:
                base = self._symbol_base(a)
                gain = int(base * DIAGONAL_3X * BET_UNIT)
                total += gain
                logs.append(f"대각선↙ 3연속 {a} +{gain:,}")

        # Triangles (▲/▼) within any 3-column window: columns [w, w+1, w+2]
        for w in range(GRID_W - 2):
            # ▲ top triangle: (0,w+1),(1,w),(1,w+2)
            a,b,c = grid[0][w+1], grid[1][w], grid[1][w+2]
            if a == b == c:
                base = self._symbol_base(a)
                gain = int(base * TRIANGLE_3X * BET_UNIT)
                total += gain
                logs.append(f"삼각형▲ {a} +{gain:,}")
            # ▼ bottom triangle: (1,w+1),(0,w),(0,w+2)
            a,b,c = grid[1][w+1], grid[0][w], grid[0][w+2]
            if a == b == c:
                base = self._symbol_base(a)
                gain = int(base * TRIANGLE_3X * BET_UNIT)
                total += gain
                logs.append(f"삼각형▼ {a} +{gain:,}")

        return total, logs

    # Grace timer helpers
    def _cancel_grace(self, uid:str):
        """해당 유저의 유예 타이머가 있으면 취소하고 삭제"""
        task = self.grace_tasks.pop(uid, None)
        if task and not task.done():
            task.cancel()

    def _start_grace_timer(self, uid:str, channel:discord.abc.Messageable, run_id:str):
        """60초 유예 타이머 시작: quota 미달이면 자동 탈락"""
        # 기존 타이머가 있으면 새로 시작하기 전에 취소
        self._cancel_grace(uid)

        async def worker():
            try:
                await channel.send(
                    "🕒 스핀을 모두 사용했습니다. **60초 안에** `#클로버입금 [금액|all]`으로 ATM 목표를 채우면 다음 라운드로 넘어갈 수 있어요.\n"
                    "⏳ 60초 후에도 목표 미달이면 자동 탈락합니다."
                )
                await asyncio.sleep(60)
                # 종료 시점 재검사
                r = self._current_run(uid)
                if not r or r.get("_id") != run_id:  # 런이 바뀌었거나 종료됨
                    return
                if r.get("status") != "playing":
                    return
                if r.get("bank", 0) >= r.get("quota", 0):
                    return  # 이미 quota 달성
                # 자동 탈락 처리
                self.runs.update_one({"_id": run_id}, {
                    "$set": {"status": "dead", "ended_at": kr_now().strftime('%Y-%m-%d %H:%M:%S')}
                })
                await channel.send("⏰ 시간이 초과되었습니다. 목표 미달성으로 **탈락**했습니다. `#클로버시작`으로 재도전하세요.")
            except asyncio.CancelledError:
                # 정상 취소(입금 성공/종료 등) 시 조용히 종료
                pass
            finally:
                # 정리
                self.grace_tasks.pop(uid, None)

        self.grace_tasks[uid] = asyncio.create_task(worker())

    # ── Commands ─────────────────────────────────────────────────────────────
    @commands.command(name="클로버참가")
    async def join(self, ctx, *, nickname: str = None):
        uid = str(ctx.author.id)
        u = self._ensure_user(uid)

        async def invalid_name(msg="올바른 닉네임을 입력하세요. (최대 8글자, 공백 없이)"):
            await ctx.send(msg + "\n사용법: `#클로버참가 닉네임`")

        # 최초 참가인데 닉네임 미입력 → 안내
        if not u.get("nickname") and not nickname:
            await invalid_name("닉네임이 필요합니다.")
            return

        # 닉네임이 들어온 경우 검증 및 저장
        if nickname is not None:
            n = nickname.strip()
            if not n or any(ch.isspace() for ch in n) or len(n) > 8:
                await invalid_name("올바르지 않은 닉네임입니다.")
                return
            # 저장
            self.users.update_one({"_id": uid}, {"$set": {"nickname": n}})
            u["nickname"] = n

        await ctx.send(
            f"{ctx.author.mention} 클로버핏(5x3) 준비 완료!\n"
            f"닉네임: **{u.get('nickname')}** | 보유 코인: {u.get('coins',0):,}"
        )

    @commands.command(name="클로버시작")
    async def start(self, ctx):
        uid = str(ctx.author.id)
        self._ensure_user(uid)
        cur = self._current_run(uid)
        if cur:
            await ctx.send("이미 진행 중인 런이 있습니다. `#클로버스핀`, `#클로버입금`을 사용하세요.")
            return
        run = self._new_run(uid)
        await ctx.send(
            f"🎰 **클로버핏 5x3 시작!** 라운드 {run['round']} / 목표 {run['quota']:,} / 남은 스핀 {run['spins_left']}\n"
            f"`#클로버스핀` 으로 돌리고, `#클로버입금 [금액|all]`로 ATM에 입금하세요."
        )

    @commands.command(name="클로버보유", aliases=["클로버프로필"])
    async def inv(self, ctx):
        uid = str(ctx.author.id)
        u = self._ensure_user(uid)
        run = self._current_run(uid)
        if run:
            await ctx.send(
                f"🏷️ 닉네임: {u.get('nickname') or '-'}\n"
                f"보유 코인: {u.get('coins',0):,}\n"
                f"▶️ 진행중: 라운드 {run['round']} | 목표 {run['quota']:,} | ATM {run['bank']:,} | 남은 스핀 {run['spins_left']}"
            )
        else:
            await ctx.send(
                f"🏷️ 닉네임: {u.get('nickname') or '-'}\n"
                f"보유 코인: {u.get('coins',0):,}\n진행중인 런 없음. `#클로버시작`으로 시작하세요."
            )

    @commands.command(name="클로버스핀")
    async def spin(self, ctx):
        uid = str(ctx.author.id)
        u   = self._ensure_user(uid)
        run = self._current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다. `#클로버시작`으로 시작하세요.")
            return
        if run["spins_left"] <= 0:
            await ctx.send("이번 라운드에서 더 이상 스핀할 수 없습니다. ATM 목표를 채우지 못했다면 `#클로버입금`을 사용하세요.")
            return

        # Roll final grid
        final_grid = self._roll_grid()

        # Initial rendering (all hidden) — backticks 분리
        render0 = self._render_grid(final_grid, reveal_cols=0)
        content0 = (
            "```\n"
            f"{render0}\n"
            "```\n"
            "🎞️ 스핀 중…"
        )
        msg = await ctx.send(content0)

        # Animate reveal columns 1..5
        for col in range(1, GRID_W+1):
            await asyncio.sleep(0.25)
            render = self._render_grid(final_grid, reveal_cols=col)
            content = (
                "```\n"
                f"{render}\n"
                "```\n"
                f"🎞️ 스핀 중… {col}/{GRID_W}"
            )
            await msg.edit(content=content)

        # Score
        reward, logs = self._score_grid(final_grid)
        self.users.update_one({"_id": uid}, {"$inc": {"coins": reward}})
        self.runs.update_one({"_id": run["_id"]}, {"$inc": {"spins_left": -1}})
        run = self._current_run(uid)  # refresh

        if logs:
            detail = "\n".join(f"• {x}" for x in logs)
        else:
            detail = "• 당첨 없음"

        # refresh user coins for display
        u = self._ensure_user(uid)
        final_content = (
            "```\n"
            f"{self._render_grid(final_grid, reveal_cols=None)}\n"
            "```\n"
            f"💰 수익: **{reward:,}** (보유 {u.get('coins',0):,})\n"
            f"{detail}\n"
            f"남은 스핀: {run['spins_left']}"
        )
        await msg.edit(content=final_content)

        # 유예 타이머 로직: 스핀을 모두 사용했다면 60초 유예
        run = self._current_run(uid)
        if run and run["spins_left"] == 0:
            if run["bank"] < run["quota"]:
                self._start_grace_timer(uid, ctx.channel, run["_id"])
            else:
                await ctx.send("🎯 목표 달성 상태입니다. `#클로버입금`으로 정산하면 다음 라운드가 시작됩니다.")

    @commands.command(name="클로버입금")
    async def deposit(self, ctx, amount:str=None):
        uid = str(ctx.author.id)
        u   = self._ensure_user(uid)
        run = self._current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다. `#클로버시작`으로 시작하세요.")
            return
        if not amount:
            await ctx.send("사용법: `#클로버입금 [금액|all]`")
            return
        if amount.lower() in ["all","전부","올인","다"]:
            pay = u.get("coins",0)
        else:
            try:
                pay = int(amount.replace(",",""))
            except:
                await ctx.send("금액은 정수로 입력하세요.")
                return
        if pay <= 0:
            await ctx.send("1 이상의 금액만 입금할 수 있습니다.")
            return
        if u.get("coins",0) < pay:
            await ctx.send("코인이 부족합니다.")
            return

        new_bank = run["bank"] + pay
        self.users.update_one({"_id": uid}, {"$inc": {"coins": -pay}})
        self.runs.update_one({"_id": run["_id"]}, {"$set": {"bank": new_bank}})

        msg_lines = [f"🏦 입금 완료: {pay:,} (ATM {new_bank:,}/{run['quota']:,})"]

        # Quota met -> next round + 유예 타이머 취소
        if new_bank >= run["quota"]:
            # 유예 타이머 취소
            self._cancel_grace(uid)

            next_round = run["round"] + 1
            next_quota = ROUND_BASE_QUOTA + (next_round-1) * ROUND_QUOTA_STEP
            self.runs.update_one({"_id": run["_id"]}, {"$set": {
                "round": next_round,
                "quota": next_quota,
                "bank": 0,
                "spins_left": SPINS_PER_ROUND,
            }})
            msg_lines.append(f"🎯 목표 달성! → 라운드 {next_round} 시작 (새 목표 {next_quota:,}, 스핀 {SPINS_PER_ROUND}회 갱신)")
        else:
            # 아직 미달이면, 스핀이 0인 상태에서 계속 유예 중일 수 있음
            fresh = self._current_run(uid)
            if fresh and fresh["spins_left"] == 0 and uid not in self.grace_tasks:
                self._start_grace_timer(uid, ctx.channel, fresh["_id"])

        await ctx.send("\n".join(msg_lines))

    @commands.command(name="클로버종료")
    async def end(self, ctx):
        uid = str(ctx.author.id)
        run = self._current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다.")
            return

        # 유예 타이머 취소
        self._cancel_grace(uid)

        self.runs.update_one({"_id": run["_id"]}, {"$set": {"status":"dead", "ended_at": kr_now().strftime('%Y-%m-%d %H:%M:%S')}})
        await ctx.send(f"🛑 런을 종료했습니다. (라운드 {run['round']}, ATM {run['bank']:,})")

    @commands.command(name="클로버랭킹")
    async def rank(self, ctx):
        pipeline = [
            {"$match": {"status": {"$in":["playing","dead","cleared"]}}},
            {"$group": {"_id":"$user_id", "best_round":{"$max":"$round"}, "max_bank":{"$max":"$bank"}}},
            {"$sort": {"best_round": -1, "max_bank": -1}},
            {"$limit": 10}
        ]
        tops = list(self.runs.aggregate(pipeline))
        if not tops:
            await ctx.send("랭킹 데이터가 없습니다.")
            return
        lines = ["🏆 클로버핏 5x3 랭킹 TOP10"]
        for i,row in enumerate(tops, start=1):
            uid = row["_id"]
            udoc = self.users.find_one({"_id": uid}, {"nickname": 1})
            nickname = (udoc or {}).get("nickname")
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            display = nickname or (member.display_name if member else uid)
            lines.append(f"{i}. {display} — 최고 라운드 {row['best_round']} / ATM최대 {row['max_bank']:,}")
        await ctx.send("\n".join(lines))

async def setup(bot):
    await bot.add_cog(CloverFit5x3(bot))

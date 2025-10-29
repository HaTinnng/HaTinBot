# CloverFit5x3.py — CloverFit 규칙 반영판
import os, random, asyncio
from datetime import datetime
import pytz
import discord
from discord.ext import commands
from pymongo import MongoClient
from urllib.parse import urlparse

MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME    = "stock_game"

GRID_W = 5
GRID_H = 3

SPINS_PER_ROUND     = 5
ROUND_BASE_QUOTA    = 1200
ROUND_QUOTA_STEP    = 600
BET_UNIT            = 100

# ─────────────────────────────────────────────────────────────────────────────
# CloverFit 심볼 정의 (Φ = 심볼 기본 가치 배수)
# prob은 제공한 "기본 확률"을 그대로 쓰고, 총합으로 정규화하여 사용
SYMBOLS_CF = [
    {"ch":"🍒", "name":"체리",     "phi":2, "prob":19.4},
    {"ch":"🍋", "name":"레몬",     "phi":2, "prob":19.4},
    {"ch":"🍀", "name":"클로버",   "phi":3, "prob":14.9},
    {"ch":"🔔", "name":"종",       "phi":3, "prob":14.9},
    {"ch":"💎", "name":"다이아",   "phi":5, "prob":11.9},
    {"ch":"🪙", "name":"보물",     "phi":5, "prob":11.9},   # (코인→보물)
    {"ch":"7️⃣", "name":"세븐",    "phi":7, "prob":7.5},
    {"ch":"6️⃣", "name":"육",      "phi":0, "prob":1.5},    # 특수(666)
]
# 정규화된 확률 테이블
_prob_sum = sum(s["prob"] for s in SYMBOLS_CF)
for s in SYMBOLS_CF:
    s["p"] = max(0.0, s["prob"] / _prob_sum)

SYMBOL_INDEX = {s["ch"]: s for s in SYMBOLS_CF}

# 패턴 배수(상위가 하위를 내포하면 하위 미발동)
PAT_MULT = {
    "H3": 1.0,     # 가로 연속3
    "V3": 1.0,     # 세로 연속3
    "D3": 1.0,     # 대각 길이3(↘↙)
    "H4": 2.0,     # 가로-L(연속4)
    "H5": 3.0,     # 가로-XL(연속5)
    "ZIG": 4.0,    # 지그
    "RZIG": 4.0,   # 재그
    "GROUND": 7.0, # 지상
    "SKY": 7.0,    # 천상
    "EYE": 8.0,    # 눈
    "JACKPOT": 10.0, # 잭팟(별도 가산)
}

# 우선순위(높을수록 먼저 판정하고 하위 억제)
PAT_PRIORITY = ["EYE", "GROUND", "SKY", "ZIG", "RZIG", "H5", "H4", "D3", "V3", "H3"]
# Zig/재그가 터지면 대각 미발동, Ground/Sky가 터지면 Zig/재그 및 가로 상위 일부 억제 등
# 구현 단순화를 위해 "상위가 같은 심볼에서 덮은 셀"에 대해 하위 패턴 억제 + 특수 규칙 반영.

# 애니메이션 표시
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
        self.grace_tasks = {}  # 유예 타이머: uid -> asyncio.Task

    # ── DB helpers ──────────────────────────────────────────────────────────
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
            "user_id": uid, "status": "playing",
            "round": 1, "quota": ROUND_BASE_QUOTA, "bank": 0,
            "spins_left": SPINS_PER_ROUND,
            "created_at": kr_now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.runs.insert_one(run)
        return run

    # ── Spin / Render ───────────────────────────────────────────────────────
    def _roll_grid(self):
        # 셀 단위 독립 샘플링(정규화 확률 p 사용)
        names = [s["ch"] for s in SYMBOLS_CF]
        probs = [s["p"] for s in SYMBOLS_CF]
        table = []
        for _r in range(GRID_H):
            row = random.choices(names, weights=probs, k=GRID_W)
            table.append(row)
        return table

    def _render_grid(self, grid, reveal_cols:int=None):
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

    # ── Pattern helpers ─────────────────────────────────────────────────────
    def _phi(self, ch:str) -> int:
        return SYMBOL_INDEX.get(ch, {"phi":0})["phi"]

    def _cells_equal(self, grid, coords, ch) -> bool:
        return all(0 <= r < GRID_H and 0 <= c < GRID_W and grid[r][c] == ch for r,c in coords)

    def _find_runs_row(self, grid, ch):
        # returns sets for H5/H4/H3 (각각 좌표 집합들의 리스트)
        H5, H4, H3 = [], [], []
        for r in range(GRID_H):
            c = 0
            while c < GRID_W:
                if grid[r][c] != ch:
                    c += 1; continue
                j = c
                while j < GRID_W and grid[r][j] == ch:
                    j += 1
                run_len = j - c
                coords = [(r, x) for x in range(c, j)]
                if run_len >= 5:
                    H5.append(coords[:5])
                elif run_len == 4:
                    H4.append(coords)
                elif run_len == 3:
                    H3.append(coords)
                c = j
        return H5, H4, H3

    def _find_col_triples(self, grid, ch):
        V3 = []
        for c in range(GRID_W):
            coords = [(0,c),(1,c),(2,c)]
            if self._cells_equal(grid, coords, ch):
                V3.append(coords)
        return V3

    def _find_diag_triples(self, grid, ch):
        D3 = []
        for sc in range(GRID_W - 2):
            coords1 = [(0,sc),(1,sc+1),(2,sc+2)]  # ↘
            coords2 = [(0,sc+2),(1,sc+1),(2,sc)]  # ↙
            if self._cells_equal(grid, coords1, ch):
                D3.append(coords1)
            if self._cells_equal(grid, coords2, ch):
                D3.append(coords2)
        return D3

    def _mask_coords(self, mask):
        # mask: list of row strings of length GRID_W with '■' points
        coords = []
        for r, row in enumerate(mask):
            for c, ch in enumerate(row):
                if ch == '■':
                    coords.append((r,c))
        return coords

    def _pattern_coords(self, name):
        # 정의된 정형 패턴 좌표 반환
        if name == "ZIG":
            # □□■□□ / □■□■□ / ■□□□■
            return self._mask_coords(["□□■□□","□■□■□","■□□□■"])
        if name == "RZIG":
            # ■□□□■ / □■□■□ / □□■□□
            return self._mask_coords(["■□□□■","□■□■□","□□■□□"])
        if name == "GROUND":
            # □□■□□ / □■□■□ / ■■■■■
            return self._mask_coords(["□□■□□","□■□■□","■■■■■"])
        if name == "SKY":
            # ■■■■■ / □■□■□ / □□■□□
            return self._mask_coords(["■■■■■","□■□■□","□□■□□"])
        if name == "EYE":
            # □■■■□ / ■■□■■ / □■■■□
            return self._mask_coords(["□■■■□","■■□■■","□■■■□"])
        if name == "JACKPOT":
            return self._mask_coords(["■■■■■","■■■■■","■■■■■"])
        return []

    # ── Scoring (CloverFit 규칙) ────────────────────────────────────────────
    def _score_grid(self, grid):
        """
        Returns (total_reward:int, logs:list[str], special_flag:str|None)
        special_flag: '666' if 666 발생
        """
        # 666 체크: '6️⃣' 3개 이상 → 은행 전액 소멸, 당 스핀 보상 0, 패턴 무효
        six_count = sum(1 for r in range(GRID_H) for c in range(GRID_W) if grid[r][c] == "6️⃣")
        if six_count >= 3:
            return 0, ["⚠️ 666 발생: 이번 라운드 ATM이 0으로 초기화됩니다."], "666"

        total = 0
        logs  = []
        counted_cells_by_symbol = {s["ch"]: set() for s in SYMBOLS_CF}  # 상위 패턴이 덮은 셀(하위 억제용)
        triggered = {s["ch"]: set() for s in SYMBOLS_CF}  # 심볼별 발동 패턴

        # 잭팟 선판정 여부 저장(추가 가산용)
        jackpot_symbols = []

        # 심볼별로 패턴을 고우선순위→저우선순위로 탐색
        for sym in [s["ch"] for s in SYMBOLS_CF if s["ch"] != "6️⃣"]:
            phi = self._phi(sym)
            # 1) 정형 패턴: EYE, GROUND, SKY, ZIG, RZIG
            for pname in ["EYE","GROUND","SKY","ZIG","RZIG"]:
                coords = self._pattern_coords(pname)
                if coords and self._cells_equal(grid, coords, sym):
                    # 억제: 해당 심볼의 덮은 셀 기록 → 하위 패턴 억제
                    counted_cells_by_symbol[sym].update(coords)
                    gain = int(phi * PAT_MULT[pname] * BET_UNIT)
                    total += gain
                    triggered[sym].add(pname)
                    logs.append(f"{pname} {sym} +{gain:,}")

            # 2) 행/열/대각 런(연속형): H5/H4/H3, V3, D3
            # 지그/재그가 이미 터졌으면 대각(D3) 억제
            forbid_diag = ("ZIG" in triggered[sym]) or ("RZIG" in triggered[sym])

            # H5/H4/H3
            H5, H4, H3 = self._find_runs_row(grid, sym)
            # 상위부터 집계(덮은 셀은 하위 억제)
            for coords_list, tag in [(H5,"H5"), (H4,"H4"), (H3,"H3")]:
                for coords in coords_list:
                    # 이미 상위 패턴이 같은 심볼로 덮은 셀을 포함하면(내포) 하위 미발동
                    if any(cell in counted_cells_by_symbol[sym] for cell in coords):
                        continue
                    # H5가 있으면 H4/H3는 그 구간 내에서는 미발동(내포) → 셀 덮기
                    counted_cells_by_symbol[sym].update(coords)
                    mult = PAT_MULT[tag]
                    gain = int(phi * mult * BET_UNIT)
                    total += gain
                    triggered[sym].add(tag)
                    logs.append(f"{'가로-XL' if tag=='H5' else ('가로-L' if tag=='H4' else '가로') } {sym} +{gain:,}")

            # V3
            for coords in self._find_col_triples(grid, sym):
                if any(cell in counted_cells_by_symbol[sym] for cell in coords):
                    continue
                counted_cells_by_symbol[sym].update(coords)
                gain = int(phi * PAT_MULT["V3"] * BET_UNIT)
                total += gain
                triggered[sym].add("V3")
                logs.append(f"세로 {sym} +{gain:,}")

            # D3 (지그/재그가 있으면 억제)
            if not forbid_diag:
                for coords in self._find_diag_triples(grid, sym):
                    if any(cell in counted_cells_by_symbol[sym] for cell in coords):
                        continue
                    counted_cells_by_symbol[sym].update(coords)
                    gain = int(phi * PAT_MULT["D3"] * BET_UNIT)
                    total += gain
                    triggered[sym].add("D3")
                    logs.append(f"대각 {sym} +{gain:,}")

            # 3) 잭팟(전체 동일) — 다른 패턴 산정 후 추가 가산
            if self._cells_equal(grid, self._pattern_coords("JACKPOT"), sym):
                jackpot_symbols.append(sym)

        # 잭팟 가산
        for sym in jackpot_symbols:
            phi = self._phi(sym)
            jg = int(phi * PAT_MULT["JACKPOT"] * BET_UNIT)
            total += jg
            logs.append(f"JACKPOT {sym} +{jg:,}")

        if not logs:
            logs = ["• 당첨 없음"]
        return total, logs, None

    # ── Grace timer ─────────────────────────────────────────────────────────
    def _cancel_grace(self, uid:str):
        t = self.grace_tasks.pop(uid, None)
        if t and not t.done():
            t.cancel()

    def _start_grace_timer(self, uid:str, channel:discord.abc.Messageable, run_id:str):
        self._cancel_grace(uid)
        async def worker():
            try:
                await channel.send(
                    "🕒 스핀을 모두 사용했습니다. **60초 안에** `#클로버입금 [금액|all]`으로 ATM 목표를 채우면 다음 라운드로 넘어갈 수 있어요.\n"
                    "⏳ 60초 후에도 목표 미달이면 자동 탈락합니다."
                )
                await asyncio.sleep(60)
                r = self._current_run(uid)
                if not r or r.get("_id") != run_id or r.get("status") != "playing":
                    return
                if r.get("bank",0) >= r.get("quota",0):
                    return
                self.runs.update_one({"_id": run_id}, {"$set": {"status":"dead", "ended_at": kr_now().strftime('%Y-%m-%d %H:%M:%S')}})
                await channel.send("⏰ 시간이 초과되었습니다. 목표 미달성으로 **탈락**했습니다. `#클로버시작`으로 재도전하세요.")
            except asyncio.CancelledError:
                pass
            finally:
                self.grace_tasks.pop(uid, None)
        self.grace_tasks[uid] = asyncio.create_task(worker())

    # ── Commands ────────────────────────────────────────────────────────────
    @commands.command(name="클로버참가")
    async def join(self, ctx, *, nickname: str = None):
        uid = str(ctx.author.id)
        u = self._ensure_user(uid)

        async def invalid_name(msg="올바른 닉네임을 입력하세요. (최대 8글자, 공백 없이)"):
            await ctx.send(msg + "\n사용법: `#클로버참가 닉네임`")

        if not u.get("nickname") and not nickname:
            await invalid_name("닉네임이 필요합니다.")
            return

        if nickname is not None:
            n = nickname.strip()
            if not n or any(ch.isspace() for ch in n) or len(n) > 8:
                await invalid_name("올바르지 않은 닉네임입니다.")
                return
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

        # 최종 그리드
        final_grid = self._roll_grid()

        # 초기 렌더(전부 가림)
        render0 = self._render_grid(final_grid, reveal_cols=0)
        content0 = "```\n" + f"{render0}\n" + "```\n" + "🎞️ 스핀 중…"
        msg = await ctx.send(content0)

        # 애니메이션(좌→우)
        for col in range(1, GRID_W+1):
            await asyncio.sleep(0.25)
            render = self._render_grid(final_grid, reveal_cols=col)
            content = "```\n" + f"{render}\n" + "```\n" + f"🎞️ 스핀 중… {col}/{GRID_W}"
            await msg.edit(content=content)

        # 채점(CloverFit 규칙)
        reward, logs, flag = self._score_grid(final_grid)

        # 666이면 라운드 ATM 0으로
        if flag == "666":
            self.runs.update_one({"_id": run["_id"]}, {"$set": {"bank": 0}})

        # 코인/스핀 갱신
        if reward > 0:
            self.users.update_one({"_id": uid}, {"$inc": {"coins": reward}})
        self.runs.update_one({"_id": run["_id"]}, {"$inc": {"spins_left": -1}})
        run = self._current_run(uid)  # refresh
        u = self._ensure_user(uid)

        detail = "\n".join(f"• {x}" for x in logs)
        final_content = (
            "```\n" + f"{self._render_grid(final_grid, reveal_cols=None)}\n" + "```\n" +
            f"💰 수익: **{reward:,}** (보유 {u.get('coins',0):,})\n" +
            f"{detail}\n" +
            (f"⚠️ 666 발동으로 ATM이 0이 되었습니다.\n" if flag == "666" else "") +
            f"남은 스핀: {run['spins_left']}"
        )
        await msg.edit(content=final_content)

        # 스핀 소진 → 유예
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

        if new_bank >= run["quota"]:
            self._cancel_grace(uid)
            next_round = run["round"] + 1
            next_quota = ROUND_BASE_QUOTA + (next_round-1) * ROUND_QUOTA_STEP
            self.runs.update_one({"_id": run["_id"]}, {"$set": {
                "round": next_round, "quota": next_quota,
                "bank": 0, "spins_left": SPINS_PER_ROUND,
            }})
            msg_lines.append(f"🎯 목표 달성! → 라운드 {next_round} 시작 (새 목표 {next_quota:,}, 스핀 {SPINS_PER_ROUND}회 갱신)")
        else:
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

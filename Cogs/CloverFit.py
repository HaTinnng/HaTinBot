# CloverFit5x3.py — CloverFit 규칙 + 탈락 시 코인 0 초기화 + 60초 유예 + 부적 시스템(상점/리롤/구매/보유/판매)
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
_prob_sum = sum(s["prob"] for s in SYMBOLS_CF)
for s in SYMBOLS_CF:
    s["p"] = max(0.0, s["prob"] / _prob_sum)
SYMBOL_INDEX = {s["ch"]: s for s in SYMBOLS_CF}

# 패턴 배수(상위가 하위를 내포하면 하위 미발동)
PAT_MULT = {
    "H3": 1.0, "V3": 1.0, "D3": 1.0,
    "H4": 2.0, "H5": 3.0,
    "ZIG": 4.0, "RZIG": 4.0,
    "GROUND": 7.0, "SKY": 7.0,
    "EYE": 8.0,
    "JACKPOT": 10.0,
}

SPIN_PLACEHOLDER = "🔄"
DIVIDER = "\n"
TZ = pytz.timezone("Asia/Seoul")
def kr_now():
    return datetime.now(TZ)

# ─────────────────────────────────────────────────────────────────────────────
# ⬇️ 부적(CHARM) 시스템: 상점/리롤/보유/판매
# 리롤 비용 = round(quota * 0.30) × (1 + ⌊리롤횟수/2⌋)
CHARM_SHOP_SLOTS = 5
CHARM_NO_DUP_IN_LINEUP = True

# (원작 160종 전체 효과는 방대하니, 여기선 상점/보유/판매 동작 검증용 최소 카탈로그를 넣어둔다.
#  이후 네가 원작 스펙으로 얼마든지 확장/치환 가능)
CHARM_CATALOG = [
    {"id": "fake_coin",    "name": "가짜 동전",     "rarity": "일반", "price": 500,  "desc": "10% 확률로 추가 스핀(연출)."},
    {"id": "horseshoe",    "name": "편자",         "rarity": "일반", "price": 800,  "desc": "확률형 보조(효과 스텁)."},
    {"id": "cat_food",     "name": "고양이 사료",   "rarity": "일반", "price": 1200, "desc": "스핀 +2 (효과 스텁)."},
    {"id": "tarot_deck",   "name": "타로 카드 한 벌","rarity":"희귀","price": 2500, "desc": "심볼 배수 스택(효과 스텁)."},
    {"id": "grandma_purse","name": "할머니의 지갑", "rarity":"일반","price": 1000, "desc": "이자 보조(효과 스텁)."},
    {"id": "midas_touch",  "name": "미다스의 손길", "rarity":"희귀","price": 4000, "desc": "심볼 영구 강화(효과 스텁)."},
    {"id": "bell_ringer",  "name": "종 울리기",     "rarity":"희귀","price": 3500, "desc": "심볼 전체 강화(효과 스텁)."},
    {"id": "battery_pack", "name": "자동차 배터리", "rarity":"일반","price": 1800, "desc": "충전형 일괄충전(효과 스텁)."},
    {"id": "lost_brief",   "name": "서류 가방",     "rarity":"일반","price": 900,  "desc": "즉시 코인(효과 스텁)."},
    {"id": "calendar",     "name": "달력",         "rarity":"고급","price": 3000, "desc": "스킵 보정(효과 스텁)."},
]

def _reroll_cost(quota:int, rerolls:int) -> int:
    base = int(round(quota * 0.30))
    tier = 1 + (rerolls // 2)  # 0~1회:×1, 2~3회:×2, 4~5회:×3 ...
    return max(1, base * tier)

# ─────────────────────────────────────────────────────────────────────────────

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

        # ⬇️ 부적 전용 컬렉션
        self.charms_inv  = self.db["clover5_charms_inv"]   # 유저 보유 부적
        self.charms_shop = self.db["clover5_charms_shop"]  # 유저별 상점 라인업

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

    # ── Charm helpers ───────────────────────────────────────────────────────
    def _shop_doc(self, uid:str):
        return self.charms_shop.find_one({"_id": uid})

    def _ensure_shop(self, uid:str, run:dict):
        """
        유저별 상점 문서를 보장. 라운드가 바뀌면 자동 리셋(새 라인업 생성)
        """
        doc = self._shop_doc(uid)
        if doc and doc.get("round") == run["round"]:
            return doc

        # 새 라인업 생성
        lineup = []
        pool = list(CHARM_CATALOG)
        random.shuffle(pool)
        for item in pool:
            if CHARM_NO_DUP_IN_LINEUP and any(x["id"] == item["id"] for x in lineup):
                continue
            lineup.append({
                "id": item["id"], "name": item["name"], "rarity": item["rarity"],
                "price": item["price"], "desc": item["desc"], "sold": False,
            })
            if len(lineup) >= CHARM_SHOP_SLOTS:
                break

        doc = {
            "_id": uid,
            "round": run["round"],
            "rerolls": 0,
            "lineup": lineup,
            "updated_at": kr_now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.charms_shop.replace_one({"_id": uid}, doc, upsert=True)
        return doc

    def _refresh_empty_slots(self, shop_doc:dict):
        """
        라인업 중 'sold=True'로 비어있는 자리를 새 물건으로 채움(리롤 때 사용)
        """
        taken_ids = set(x["id"] for x in shop_doc["lineup"] if not x["sold"])
        refill_count = 0
        for slot in shop_doc["lineup"]:
            if slot["sold"]:
                candidates = [c for c in CHARM_CATALOG if (not CHARM_NO_DUP_IN_LINEUP) or (c["id"] not in taken_ids)]
                if not candidates:
                    continue
                pick = random.choice(candidates)
                slot.update({
                    "id": pick["id"], "name": pick["name"], "rarity": pick["rarity"],
                    "price": pick["price"], "desc": pick["desc"], "sold": False
                })
                taken_ids.add(pick["id"])
                refill_count += 1
        return refill_count

    def _reroll_shop(self, uid:str, run:dict):
        """
        유저 상점 리롤:
         - coins 차감
         - rerolls+1
         - 모든 슬롯을 새 물건으로 교체
        """
        shop = self._ensure_shop(uid, run)
        cost = _reroll_cost(run["quota"], shop.get("rerolls", 0))

        u = self._ensure_user(uid)
        if u.get("coins", 0) < cost:
            return None, f"리롤 비용이 부족합니다. 필요: {cost:,} / 보유: {u.get('coins',0):,}"

        # 코인 차감
        self.users.update_one({"_id": uid}, {"$inc": {"coins": -cost}})

        # 새 라인업 — 전부 교체
        lineup = []
        pool = list(CHARM_CATALOG)
        random.shuffle(pool)
        for item in pool:
            if CHARM_NO_DUP_IN_LINEUP and any(x["id"] == item["id"] for x in lineup):
                continue
            lineup.append({
                "id": item["id"], "name": item["name"], "rarity": item["rarity"],
                "price": item["price"], "desc": item["desc"], "sold": False,
            })
            if len(lineup) >= CHARM_SHOP_SLOTS:
                break

        self.charms_shop.update_one(
            {"_id": uid},
            {"$set": {
                "lineup": lineup,
                "updated_at": kr_now().strftime("%Y-%m-%d %H:%M:%S")
            }, "$inc": {"rerolls": 1}}
        )
        shop = self._shop_doc(uid)
        return shop, f"🔁 리롤 완료! 비용: {cost:,} (누적 리롤 {shop['rerolls']}회)"

    def _buy_charm(self, uid:str, index:int, run:dict):
        """
        상점에서 index(1-base) 슬롯 구매
         - sold 처리
         - 유저 인벤토리에 추가
        """
        shop = self._ensure_shop(uid, run)
        if not (1 <= index <= len(shop["lineup"])):
            return None, "잘못된 번호입니다."

        slot = shop["lineup"][index-1]
        if slot["sold"]:
            return None, "이미 판매된 슬롯입니다."

        price = slot["price"]
        u = self._ensure_user(uid)
        if u.get("coins", 0) < price:
            return None, f"코인이 부족합니다. 필요: {price:,} / 보유: {u.get('coins',0):,}"

        # 코인 차감 & 인벤 추가 & 슬롯 판매처리
        self.users.update_one({"_id": uid}, {"$inc": {"coins": -price}})
        self.charms_inv.update_one(
            {"_id": uid},
            {"$push": {"items": {
                "id": slot["id"], "name": slot["name"], "rarity": slot["rarity"],
                "desc": slot["desc"], "acquired_at": kr_now().strftime("%Y-%m-%d %H:%M:%S")
            }}},
            upsert=True
        )
        self.charms_shop.update_one(
            {"_id": uid, f"lineup.{index-1}.sold": {"$ne": True}},
            {"$set": {f"lineup.{index-1}.sold": True}}
        )
        return slot, f"🛒 구매 성공: **{slot['name']}** (−{price:,})"

    def _sell_charm(self, uid:str, index:int):
        """
        보유 부적 판매 (간단 환불 규칙: 구매가의 50%)
        """
        inv = self.charms_inv.find_one({"_id": uid})
        if not inv or not inv.get("items"):
            return None, "보유한 부적이 없습니다."
        if not (1 <= index <= len(inv["items"])):
            return None, "잘못된 번호입니다."

        item = inv["items"][index-1]
        cat = next((c for c in CHARM_CATALOG if c["id"] == item["id"]), None)
        price = cat["price"] if cat else 0
        refund = max(0, int(round(price * 0.5)))

        # 인벤에서 제거 & 코인 환불
        self.charms_inv.update_one({"_id": uid}, {"$pull": {"items": item}})
        self.users.update_one({"_id": uid}, {"$inc": {"coins": refund}})

        return item, f"🔄 판매 완료: **{item['name']}** (+{refund:,})"

    # ── Spin / Render ───────────────────────────────────────────────────────
    def _roll_grid(self):
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
        coords = []
        for r, row in enumerate(mask):
            for c, ch in enumerate(row):
                if ch == '■':
                    coords.append((r,c))
        return coords

    def _pattern_coords(self, name):
        if name == "ZIG":
            return self._mask_coords(["□□■□□","□■□■□","■□□□■"])
        if name == "RZIG":
            return self._mask_coords(["■□□□■","□■□■□","□□■□□"])
        if name == "GROUND":
            return self._mask_coords(["□□■□□","□■□■□","■■■■■"])
        if name == "SKY":
            return self._mask_coords(["■■■■■","□■□■□","□□■□□"])
        if name == "EYE":
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
        six_count = sum(1 for r in range(GRID_H) for c in range(GRID_W) if grid[r][c] == "6️⃣")
        if six_count >= 3:
            return 0, ["⚠️ 666 발생: 이번 라운드 ATM이 0으로 초기화됩니다."], "666"

        total = 0
        logs  = []
        counted_cells_by_symbol = {s["ch"]: set() for s in SYMBOLS_CF}
        triggered = {s["ch"]: set() for s in SYMBOLS_CF}
        jackpot_symbols = []

        for sym in [s["ch"] for s in SYMBOLS_CF if s["ch"] != "6️⃣"]:
            phi = self._phi(sym)
            for pname in ["EYE","GROUND","SKY","ZIG","RZIG"]:
                coords = self._pattern_coords(pname)
                if coords and self._cells_equal(grid, coords, sym):
                    counted_cells_by_symbol[sym].update(coords)
                    gain = int(phi * PAT_MULT[pname] * BET_UNIT)
                    total += gain
                    triggered[sym].add(pname)
                    logs.append(f"{pname} {sym} +{gain:,}")

            forbid_diag = ("ZIG" in triggered[sym]) or ("RZIG" in triggered[sym])

            H5, H4, H3 = self._find_runs_row(grid, sym)
            for coords_list, tag in [(H5,"H5"), (H4,"H4"), (H3,"H3")]:
                for coords in coords_list:
                    if any(cell in counted_cells_by_symbol[sym] for cell in coords):
                        continue
                    counted_cells_by_symbol[sym].update(coords)
                    mult = PAT_MULT[tag]
                    gain = int(phi * mult * BET_UNIT)
                    total += gain
                    triggered[sym].add(tag)
                    logs.append(f"{'가로-XL' if tag=='H5' else ('가로-L' if tag=='H4' else '가로') } {sym} +{gain:,}")

            for coords in self._find_col_triples(grid, sym):
                if any(cell in counted_cells_by_symbol[sym] for cell in coords):
                    continue
                counted_cells_by_symbol[sym].update(coords)
                gain = int(phi * PAT_MULT["V3"] * BET_UNIT)
                total += gain
                triggered[sym].add("V3")
                logs.append(f"세로 {sym} +{gain:,}")

            if not forbid_diag:
                for coords in self._find_diag_triples(grid, sym):
                    if any(cell in counted_cells_by_symbol[sym] for cell in coords):
                        continue
                    counted_cells_by_symbol[sym].update(coords)
                    gain = int(phi * PAT_MULT["D3"] * BET_UNIT)
                    total += gain
                    triggered[sym].add("D3")
                    logs.append(f"대각 {sym} +{gain:,}")

            if self._cells_equal(grid, self._pattern_coords("JACKPOT"), sym):
                jackpot_symbols.append(sym)

        for sym in jackpot_symbols:
            phi = self._phi(sym)
            jg = int(phi * PAT_MULT["JACKPOT"] * BET_UNIT)
            total += jg
            logs.append(f"JACKPOT {sym} +{jg:,}")

        if not logs:
            logs = ["• 당첨 없음"]
        return total, logs, None

    # ── 탈락/유예 ───────────────────────────────────────────────────────────
    async def _eliminate(self, uid: str, run_id: str, channel: discord.abc.Messageable, reason: str = ""):
        self._cancel_grace(uid)
        self.runs.update_one(
            {"_id": run_id},
            {"$set": {"status": "dead", "ended_at": kr_now().strftime('%Y-%m-%d %H:%M:%S')}}
        )
        self.users.update_one({"_id": uid}, {"$set": {"coins": 0}})

        msg = "💀 탈락했습니다."
        if reason:
            msg += f" ({reason})"
        msg += "\n보유 코인이 **0원**으로 초기화되었어요. `#클로버시작`으로 새롭게 도전하세요."
        await channel.send(msg)

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
                    "⏳ 60초 후에도 목표 미달이면 **즉시 탈락**하며 보유 코인은 0원이 됩니다."
                )
                await asyncio.sleep(60)
                r = self._current_run(uid)
                if not r or r.get("_id") != run_id or r.get("status") != "playing":
                    return
                if r.get("bank",0) < r.get("quota",0):
                    await self._eliminate(uid, run_id, channel, "유예 시간 종료")
            except asyncio.CancelledError:
                pass
            finally:
                self.grace_tasks.pop(uid, None)
        self.grace_tasks[uid] = asyncio.create_task(worker())

    # ── 기본 명령어 ─────────────────────────────────────────────────────────
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
            f"{ctx.author.mention} 클로버핏 준비 완료!\n"
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
            f"🎰 **클로버핏 시작!** 라운드 {run['round']} / 목표 {run['quota']:,} / 남은 스핀 {run['spins_left']}\n"
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

        final_grid = self._roll_grid()
        render0 = self._render_grid(final_grid, reveal_cols=0)
        content0 = "```\n" + f"{render0}\n" + "```\n" + "🎞️ 스핀 중…"
        msg = await ctx.send(content0)

        for col in range(1, GRID_W+1):
            await asyncio.sleep(0.25)
            render = self._render_grid(final_grid, reveal_cols=col)
            content = "```\n" + f"{render}\n" + "```\n" + f"🎞️ 스핀 중… {col}/{GRID_W}"
            await msg.edit(content=content)

        reward, logs, flag = self._score_grid(final_grid)

        if flag == "666":
            self.runs.update_one({"_id": run["_id"]}, {"$set": {"bank": 0}})

        if reward > 0:
            self.users.update_one({"_id": uid}, {"$inc": {"coins": reward}})
        self.runs.update_one({"_id": run["_id"]}, {"$inc": {"spins_left": -1}})
        run = self._current_run(uid)
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

        run = self._current_run(uid)
        if run and run["spins_left"] == 0:
            bank  = run.get("bank", 0)
            quota = run.get("quota", 0)
            coins = self._ensure_user(uid).get("coins", 0)

            if bank >= quota:
                await ctx.send("🎯 목표 달성 상태입니다. `#클로버입금`으로 정산하면 다음 라운드가 시작됩니다.")
            else:
                if bank + coins >= quota:
                    self._start_grace_timer(uid, ctx.channel, run["_id"])
                else:
                    await self._eliminate(uid, run["_id"], ctx.channel, "스핀 소진 + 목표 미달(보유 코인 부족)")

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
            if fresh and fresh["spins_left"] == 0:
                remain = fresh["quota"] - fresh["bank"]
                cur_coins = self._ensure_user(uid).get("coins", 0)
                if remain <= cur_coins:
                    if uid not in self.grace_tasks:
                        self._start_grace_timer(uid, ctx.channel, fresh["_id"])
                else:
                    await self._eliminate(uid, fresh["_id"], ctx.channel, "유예 중에도 목표 달성 불가(보유 코인 부족)")

        await ctx.send("\n".join(msg_lines))

    @commands.command(name="클로버종료")
    async def end(self, ctx):
        uid = str(ctx.author.id)
        run = self._current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다.")
            return
        await self._eliminate(uid, run["_id"], ctx.channel, "자발적 종료")

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
        lines = ["🏆 클로버핏 랭킹 TOP10"]
        for i,row in enumerate(tops, start=1):
            uid = row["_id"]
            udoc = self.users.find_one({"_id": uid}, {"nickname": 1})
            nickname = (udoc or {}).get("nickname")
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            display = nickname or (member.display_name if member else uid)
            lines.append(f"{i}. {display} — 최고 라운드 {row['best_round']} / ATM최대 {row['max_bank']:,}")
        await ctx.send("\n".join(lines))

    # ── 부적 명령어 ─────────────────────────────────────────────────────────
    @commands.command(name="부적상점")
    async def charms_shop(self, ctx):
        """항상 입장 가능. 라운드가 바뀌면 라인업 자동 갱신."""
        uid = str(ctx.author.id)
        run = self._current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다. `#클로버시작` 후 이용하세요.")
            return
        shop = self._ensure_shop(uid, run)
        cost = _reroll_cost(run["quota"], shop.get("rerolls",0))

        lines = [
            f"🛍 **부적 상점** — 라운드 {shop['round']} | 누적 리롤 {shop['rerolls']}회 | 현재 리롤 비용: **{cost:,}**",
            "구매: `#부적구매 번호` | 리롤: `#부적리롤` | 보유: `#내부적` | 판매: `#부적판매 번호`",
            "────────────────────────────────"
        ]
        for i, slot in enumerate(shop["lineup"], start=1):
            if slot["sold"]:
                lines.append(f"{i}. [팔렸습니다]")
            else:
                lines.append(f"{i}. {slot['name']} ({slot['rarity']}) — {slot['price']:,}\n   · {slot['desc']}")
        await ctx.send("\n".join(lines))

    @commands.command(name="부적리롤")
    async def charms_reroll(self, ctx):
        """리롤은 게임 코인 사용. 2회마다 비용 증가(30%×계단식), 라운드가 오를수록 자연히 비싸짐."""
        uid = str(ctx.author.id)
        run = self._current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다.")
            return
        shop, msg = self._reroll_shop(uid, run)
        if shop is None:
            await ctx.send(msg)
            return
        await self.charms_shop.update_one({"_id": uid}, {"$set": {"lineup": shop["lineup"]}})
        await self.charms_shop.update_one({"_id": uid}, {"$set": {"updated_at": kr_now().strftime("%Y-%m-%d %H:%M:%S")}})
        await self.charms_shop(ctx)  # 상점 목록 다시 출력

    @commands.command(name="부적구매")
    async def charms_buy(self, ctx, index: int = None):
        uid = str(ctx.author.id)
        run = self._current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다.")
            return
        if index is None:
            await ctx.send("사용법: `#부적구매 [번호]` — 번호는 `#부적상점` 리스트 참고")
            return
        slot, msg = self._buy_charm(uid, index, run)
        await ctx.send(msg)
        # 구매 후 자리 비우지 않음(팔렸습니다로 표기). 리롤 시 비어있는 자리도 새 물건으로 채움.

    @commands.command(name="내부적", aliases=["부적보유"])
    async def charms_inventory(self, ctx):
        uid = str(ctx.author.id)
        inv = self.charms_inv.find_one({"_id": uid})
        items = inv.get("items", []) if inv else []
        if not items:
            await ctx.send("🎒 보유 부적이 없습니다. `#부적상점`에서 구매해보세요!")
            return
        lines = ["🎒 **보유 부적 목록**"]
        for i, it in enumerate(items, start=1):
            lines.append(f"{i}. {it['name']} ({it['rarity']}) — {it['desc']}")
        await ctx.send("\n".join(lines))

    @commands.command(name="부적판매")
    async def charms_sell(self, ctx, index: int = None):
        uid = str(ctx.author.id)
        if index is None:
            await ctx.send("사용법: `#부적판매 [번호]` — 번호는 `#내부적`에서 확인")
            return
        item, msg = self._sell_charm(uid, index)
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(CloverFit5x3(bot))

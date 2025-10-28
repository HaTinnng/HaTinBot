import os, random
from datetime import datetime, timedelta
import pytz
import discord
from discord.ext import commands
from pymongo import MongoClient
from urllib.parse import urlparse

MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"  # 기존 DB 재사용 (컬렉션만 분리)

# 심볼 테이블 (기본 가중치/배수)
SYMBOLS = [
    {"name":"🍀", "weight": 40, "mult": 1.0},  # 흔함
    {"name":"💎", "weight": 20, "mult": 2.0},  # 드묾
    {"name":"⭐", "weight": 15, "mult": 3.0},
    {"name":"7️⃣", "weight": 10, "mult": 5.0},
    {"name":"🕳️", "weight": 15, "mult": 0.0},  # 꽝
]

# 부적(아이템): 간단 버프
CHARMS = {
    "lucky_leaf": {"name":"럭키 리프", "desc":"+🍀 가중치 20%", "cost": 300, "effect":{"🍀":{"w_mult":1.2}}},
    "shine_core": {"name":"샤인 코어", "desc":"+💎 배수 x2.2", "cost": 800, "effect":{"💎":{"m_mult":2.2}}},
    "jack_hint":  {"name":"잭 힌트", "desc":"+⭐ 가중치 30%", "cost": 600, "effect":{"⭐":{"w_mult":1.3}}},
    "sevens_joy": {"name":"세븐즈 조이", "desc":"+7️⃣ 가중치 20% / 배수 x1.25", "cost":1200, "effect":{"7️⃣":{"w_mult":1.2,"m_mult":1.25}}},
}

ROUND_BASE_QUOTA = 500     # 1라운드 입금 목표
ROUND_QUOTA_STEP  = 250    # 라운드마다 목표 증가
SPIN_BASE_REWARD  = 100    # 스핀 기본 코인
SPIN_COOLDOWN_S   = 7      # 스핀 쿨다운(초)

def kr_now():
    return datetime.now(pytz.timezone("Asia/Seoul"))

def weighted_choice(symbols):
    # symbols: [{"name","weight","mult"}]
    total = sum(max(0.0001, s["weight"]) for s in symbols)
    r = random.uniform(0, total)
    upto = 0.0
    for s in symbols:
        w = max(0.0001, s["weight"])
        if upto + w >= r:
            return s
        upto += w
    return symbols[-1]

class CloverFit(commands.Cog):
    def __init__(self, bot):
        if not MONGO_URI:
            raise RuntimeError("MONGODB_URI 미설정")
        parsed = urlparse(MONGO_URI)
        print(f"[MongoDB] CloverFit connecting host={parsed.hostname}")
        self.bot = bot
        self.mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
        self.mongo.admin.command("ping")
        self.db = self.mongo[DB_NAME]
        # 컬렉션
        self.users = self.db["cloverfit_users"]   # { _id: userId, coins, charms{key:qty} }
        self.runs  = self.db["cloverfit_runs"]    # 진행중/기록: see _new_run

    # ==== 내부 유틸 ====
    def _get_user(self, uid: str):
        doc = self.users.find_one({"_id": uid})
        if not doc:
            doc = {"_id": uid, "coins": 0, "charms": {}}
            self.users.insert_one(doc)
        return doc

    def _mutate_symbols_with_charms(self, charms_dict):
        # 부적 효과를 심볼 테이블에 적용한 사본 반환
        table = [{k:v for k,v in s.items()} for s in SYMBOLS]
        # name -> index 맵
        idx = {s["name"]: i for i,s in enumerate(table)}
        for ck, qty in (charms_dict or {}).items():
            if qty <= 0 or ck not in CHARMS: 
                continue
            eff = CHARMS[ck]["effect"]
            for sym, e in eff.items():
                if sym not in idx: 
                    continue
                i = idx[sym]
                if "w_mult" in e:
                    table[i]["weight"] *= (e["w_mult"] ** qty)
                if "m_mult" in e:
                    table[i]["mult"]   *= (e["m_mult"] ** qty)
        return table

    def _new_run(self, uid: str):
        run = {
            "_id": f"{uid}:{int(kr_now().timestamp())}",
            "user_id": uid,
            "round": 1,
            "quota": ROUND_BASE_QUOTA,
            "bank": 0,              # 이번 런 ATM 입금 누계
            "last_spin": None,
            "status": "playing",    # playing / dead / cleared
            "created_at": kr_now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.runs.insert_one(run)
        return run

    def _get_current_run(self, uid: str):
        return self.runs.find_one({"user_id": uid, "status": "playing"})

    # ==== 명령어 ====

    @commands.command(name="클로버참가")
    async def join(self, ctx):
        uid = str(ctx.author.id)
        u = self._get_user(uid)
        await ctx.send(f"{ctx.author.mention} 클로버핏 계정이 준비되었습니다. (보유 코인: {u.get('coins',0):,})")

    @commands.command(name="클로버시작")
    async def start(self, ctx):
        uid = str(ctx.author.id)
        self._get_user(uid)
        cur = self._get_current_run(uid)
        if cur:
            await ctx.send(f"{ctx.author.mention} 이미 진행 중인 런이 있습니다. `#클로버스핀`, `#클로버입금`을 사용하세요.")
            return
        run = self._new_run(uid)
        await ctx.send(
            f"🎰 **클로버핏 시작!** 라운드 {run['round']} / 목표 입금 {run['quota']:,}코인\n"
            f"`#클로버스핀`으로 코인을 벌고 `#클로버입금 [금액]`으로 ATM에 입금해 목표를 채우세요!"
        )

    @commands.command(name="클로버보유", aliases=["클로버프로필"])
    async def inv(self, ctx):
        uid = str(ctx.author.id)
        u = self._get_user(uid)
        run = self._get_current_run(uid)
        charms_text = []
        for k,qty in (u.get("charms") or {}).items():
            if qty>0 and k in CHARMS:
                charms_text.append(f"- {CHARMS[k]['name']} x{qty} ({CHARMS[k]['desc']})")
        charms_block = "\n".join(charms_text) if charms_text else "없음"

        if run:
            await ctx.send(
                f"🏷️ 보유 코인: {u.get('coins',0):,}\n"
                f"🎒 부적:\n{charms_block}\n\n"
                f"▶️ 진행중: 라운드 {run['round']} | 목표 {run['quota']:,} | ATM입금 {run['bank']:,}"
            )
        else:
            await ctx.send(
                f"🏷️ 보유 코인: {u.get('coins',0):,}\n"
                f"🎒 부적:\n{charms_block}\n"
                f"진행중인 런 없음. `#클로버시작`으로 시작하세요."
            )

    @commands.command(name="클로버상점")
    async def shop(self, ctx, item_key: str=None, qty: str="1"):
        uid = str(ctx.author.id)
        u = self._get_user(uid)

        if not item_key:
            lines = ["🛒 **클로버 상점** (구매: `#클로버상점 [키] [수량]`)", ""]
            for k,v in CHARMS.items():
                lines.append(f"`{k}` - {v['name']} ({v['desc']}) | 가격 {v['cost']:,}")
            await ctx.send("\n".join(lines))
            return

        if item_key not in CHARMS:
            await ctx.send("없는 아이템 키입니다. `#클로버상점`으로 목록을 확인하세요.")
            return
        try:
            q = max(1, int(qty))
        except:
            await ctx.send("수량은 정수로 입력하세요.")
            return

        price = CHARMS[item_key]["cost"] * q
        if u.get("coins",0) < price:
            await ctx.send(f"코인이 부족합니다. 필요 {price:,}, 보유 {u.get('coins',0):,}")
            return

        self.users.update_one({"_id": uid}, {
            "$inc": {"coins": -price, f"charms.{item_key}": q}
        })
        await ctx.send(f"구매 완료: {CHARMS[item_key]['name']} x{q} (−{price:,} 코인)")

    @commands.command(name="클로버스핀")
    async def spin(self, ctx):
        uid = str(ctx.author.id)
        u = self._get_user(uid)
        run = self._get_current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다. `#클로버시작`으로 시작하세요.")
            return

        # 쿨다운 체크
        last = run.get("last_spin")
        if last:
            last_dt = datetime.strptime(last, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Asia/Seoul"))
            if kr_now() < last_dt + timedelta(seconds=SPIN_COOLDOWN_S):
                remain = (last_dt + timedelta(seconds=SPIN_COOLDOWN_S) - kr_now()).total_seconds()
                await ctx.send(f"⏳ 스핀 쿨다운 {int(remain)}초 남음")
                return

        # 부적 효과 반영 테이블
        table = self._mutate_symbols_with_charms(u.get("charms", {}))
        sym = weighted_choice(table)
        reward = int(SPIN_BASE_REWARD * sym["mult"])

        # 코인 지급
        self.users.update_one({"_id": uid}, {"$inc": {"coins": reward}})
        # last_spin 업데이트
        self.runs.update_one({"_id": run["_id"]}, {"$set": {"last_spin": kr_now().strftime("%Y-%m-%d %H:%M:%S")}})

        await ctx.send(f"🎰 스핀 결과: {sym['name']}  → **+{reward:,} 코인** (보유 {u.get('coins',0)+reward:,})")

    @commands.command(name="클로버입금")
    async def deposit(self, ctx, amount: str=None):
        uid = str(ctx.author.id)
        u = self._get_user(uid)
        run = self._get_current_run(uid)
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
                await ctx.send("금액을 정수로 입력하세요.")
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

        msg = [f"🏦 입금 완료: {pay:,} (ATM 누계 {new_bank:,} / 목표 {run['quota']:,})"]
        # 목표 달성 → 다음 라운드
        if new_bank >= run["quota"]:
            next_round = run["round"] + 1
            next_quota = ROUND_BASE_QUOTA + (next_round-1) * ROUND_QUOTA_STEP
            self.runs.update_one({"_id": run["_id"]}, {"$set": {
                "round": next_round, "quota": next_quota, "bank": 0
            }})
            msg.append(f"🎯 목표 달성! → 라운드 {next_round} 시작 (새 목표 {next_quota:,})")
        await ctx.send("\n".join(msg))

    @commands.command(name="클로버종료")
    async def end(self, ctx):
        uid = str(ctx.author.id)
        run = self._get_current_run(uid)
        if not run:
            await ctx.send("진행중인 런이 없습니다.")
            return
        self.runs.update_one({"_id": run["_id"]}, {"$set": {"status":"dead", "ended_at": kr_now().strftime("%Y-%m-%d %H:%M:%S")}})
        await ctx.send(f"🛑 런을 종료했습니다. (라운드 {run['round']}, ATM {run['bank']:,})")

    @commands.command(name="클로버랭킹")
    async def rank(self, ctx):
        # 가장 높은 라운드/입금 누계 기준 상위 10
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
            user = ctx.guild.get_member(int(row["_id"]))
            name = user.display_name if user else row["_id"]
            lines.append(f"{i}. {name} — 최고 라운드 {row['best_round']} / ATM최대 {row['max_bank']:,}")
        await ctx.send("\n".join(lines))

async def setup(bot):
    await bot.add_cog(CloverFit(bot))

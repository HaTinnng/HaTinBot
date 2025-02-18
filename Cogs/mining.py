import discord
import random
import asyncio
import time
import re
from discord.ext import commands
from pymongo import MongoClient
import os

# --------------------------
# 광산 및 판매 관련 데이터 설정
# --------------------------
MINES = {
    "초보광산": {
        "req_user_level": 1,
        "req_equipment_level": 1,
        "minerals": {
            "흙": {"chance": 60, "min_qty": 1, "max_qty": 2},
            "돌": {"chance": 30, "min_qty": 1, "max_qty": 1},
            "석탄": {"chance": 8, "min_qty": 1, "max_qty": 1},
            "구리": {"chance": 2, "min_qty": 1, "max_qty": 1},
        }
    },
    "초급광산": {
        "req_user_level": 2,
        "req_equipment_level": 2,
        "minerals": {
            "돌": {"chance": 55, "min_qty": 1, "max_qty": 2},
            "석탄": {"chance": 30, "min_qty": 1, "max_qty": 1},
            "구리": {"chance": 10, "min_qty": 1, "max_qty": 1},
            "철": {"chance": 5, "min_qty": 1, "max_qty": 1},
        }
    },
    "중급광산": {
        "req_user_level": 4,
        "req_equipment_level": 3,
        "minerals": {
            "석탄": {"chance": 50, "min_qty": 1, "max_qty": 3},
            "구리": {"chance": 30, "min_qty": 1, "max_qty": 2},
            "철": {"chance": 15, "min_qty": 1, "max_qty": 1},
            "은": {"chance": 4, "min_qty": 1, "max_qty": 1},
            "금": {"chance": 1, "min_qty": 1, "max_qty": 1},
        }
    },
    "상급광산": {
        "req_user_level": 6,
        "req_equipment_level": 5,
        "minerals": {
            "구리": {"chance": 45, "min_qty": 1, "max_qty": 3},
            "철": {"chance": 30, "min_qty": 1, "max_qty": 2},
            "은": {"chance": 15, "min_qty": 1, "max_qty": 2},
            "금": {"chance": 8, "min_qty": 1, "max_qty": 1},
            "다이아몬드": {"chance": 2, "min_qty": 1, "max_qty": 1},
        }
    },
    "최상급광산": {
        "req_user_level": 8,
        "req_equipment_level": 7,
        "minerals": {
            "철": {"chance": 40, "min_qty": 1, "max_qty": 3},
            "은": {"chance": 30, "min_qty": 1, "max_qty": 2},
            "금": {"chance": 15, "min_qty": 1, "max_qty": 2},
            "다이아몬드": {"chance": 10, "min_qty": 1, "max_qty": 1},
            "에메랄드": {"chance": 5, "min_qty": 1, "max_qty": 1},
        }
    },
    "특급급광산": {
        "req_user_level": 10,
        "req_equipment_level": 9,
        "minerals": {
            "은": {"chance": 35, "min_qty": 1, "max_qty": 3},
            "금": {"chance": 25, "min_qty": 1, "max_qty": 2},
            "다이아몬드": {"chance": 20, "min_qty": 1, "max_qty": 2},
            "에메랄드": {"chance": 15, "min_qty": 1, "max_qty": 2},
            "네더라이트": {"chance": 8, "min_qty": 1, "max_qty": 1},
            "루비": {"chance": 2, "min_qty": 1, "max_qty": 1},
        }
    },
    "전설광산": {
        "req_user_level": 12,
        "req_equipment_level": 11,
        "minerals": {
            "금": {"chance": 30, "min_qty": 1, "max_qty": 3},
            "다이아몬드": {"chance": 25, "min_qty": 1, "max_qty": 2},
            "에메랄드": {"chance": 20, "min_qty": 1, "max_qty": 2},
            "네더라이트": {"chance": 20, "min_qty": 1, "max_qty": 2},
            "루비": {"chance": 10, "min_qty": 1, "max_qty": 1},
            "오리하르콘": {"chance": 5, "min_qty": 1, "max_qty": 1},
        }
    },
    "신화광산": {
        "req_user_level": 14,
        "req_equipment_level": 13,
        "minerals": {
            "다이아몬드": {"chance": 30, "min_qty": 1, "max_qty": 3},
            "에메랄드": {"chance": 25, "min_qty": 1, "max_qty": 3},
            "네더라이트": {"chance": 20, "min_qty": 1, "max_qty": 3},
            "루비": {"chance": 20, "min_qty": 1, "max_qty": 2},
            "오리하르콘": {"chance": 10, "min_qty": 1, "max_qty": 1},
            "자수정": {"chance": 5, "min_qty": 1, "max_qty": 1},
        }
    },
    "영웅광산": {
        "req_user_level": 16,
        "req_equipment_level": 15,
        "minerals": {
            "에메랄드": {"chance": 20, "min_qty": 1, "max_qty": 3},
            "네더라이트": {"chance": 25, "min_qty": 1, "max_qty": 3},
            "루비": {"chance": 20, "min_qty": 1, "max_qty": 3},
            "오리하르콘": {"chance": 19, "min_qty": 1, "max_qty": 2},
            "자수정": {"chance": 10, "min_qty": 1, "max_qty": 1},
            "오팔": {"chance": 5, "min_qty": 1, "max_qty": 1},
            "혈액팩": {"chance": 1, "min_qty": 1, "max_qty": 1},
        }
    },
    "궁극광산": {
        "req_user_level": 18,
        "req_equipment_level": 17,
        "minerals": {
            "네더라이트": {"chance": 15, "min_qty": 1, "max_qty": 2},
            "루비": {"chance": 25, "min_qty": 1, "max_qty": 2},
            "오리하르콘": {"chance": 22, "min_qty": 1, "max_qty": 3},
            "자수정": {"chance": 15, "min_qty": 1, "max_qty": 2},
            "오팔": {"chance": 12, "min_qty": 1, "max_qty": 1},
            "운석": {"chance": 8, "min_qty": 1, "max_qty": 1},
            "혈액팩": {"chance": 3, "min_qty": 1, "max_qty": 1},
        }
    },
    "최종광산": {
        "req_user_level": 20,
        "req_equipment_level": 19,
        "minerals": {
            "루비": {"chance": 10, "min_qty": 1, "max_qty": 2},
            "오리하르콘": {"chance": 20, "min_qty": 1, "max_qty": 2},
            "자수정": {"chance": 20, "min_qty": 1, "max_qty": 3},
            "오팔": {"chance": 20, "min_qty": 1, "max_qty": 2},
            "운석": {"chance": 15, "min_qty": 1, "max_qty": 1},
            "포스코어": {"chance": 10, "min_qty": 1, "max_qty": 1},
            "혈액팩": {"chance": 5, "min_qty": 1, "max_qty": 1},
        }
    },
}

SALE_PRICES = {
    "흙": 10,
    "돌": 20,
    "석탄": 30,
    "구리": 50,
    "철": 100, 
    "은": 150,
    "금": 200,
    "다이아몬드": 400,
    "에메랄드": 600,
    "네더라이트": 800,
    "루비": 1000,
    "오리하르콘": 1500,
    "자수정": 2000,
    "오팔": 5000,
    "운석": 7500,
    "포스코어": 12000,
    "혈액팩": 30000,
}

# --------------------------
# 광물 등급 설정
# --------------------------
MINERAL_GRADES = {
    "D": {"prob": 40, "xp_multiplier": 1.0, "sale_multiplier": 1.0},
    "C": {"prob": 25, "xp_multiplier": 1.2, "sale_multiplier": 1.5},
    "B": {"prob": 15, "xp_multiplier": 1.8, "sale_multiplier": 2},
    "A": {"prob": 10, "xp_multiplier": 2.5, "sale_multiplier": 4},
    "S": {"prob": 5,  "xp_multiplier": 4, "sale_multiplier": 10},
    "X": {"prob": 3,  "xp_multiplier": 6, "sale_multiplier": 18},
    "MAX": {"prob": 2, "xp_multiplier": 9, "sale_multiplier": 27},
}

# --------------------------
# 장비 이름 반환 함수
# --------------------------
def get_equipment_name(level: int) -> str:
    if level == 1:
        return "맨손"
    elif level == 2:
        return f"고무장갑 (Lv.{level})"
    elif level == 3:
        return f"가죽장갑 (Lv.{level})"
    elif level == 4:
        return f"너클 (Lv.{level})"
    elif level == 5:
        return f"독너클 (Lv.{level})"
    elif level == 6:
        return f"막대기 (Lv.{level})"
    elif level == 7:
        return f"정교한 막대기 (Lv.{level})"
    elif level == 8:
        return f"나무 곡괭이 (Lv.{level})"
    elif level == 9:
        return f"섬세한 나무 곡괭이 (Lv.{level})"
    elif level == 10:
        return f"돌 곡괭이 (Lv.{level})"
    elif level == 11:
        return f"단단한 돌 곡괭이 (Lv.{level})"
    elif level == 12:
        return f"다이아 곡괭이 (Lv.{level})"
    elif level == 13:
        return f"빛나는 다이아 곡괭이 (Lv.{level})"
    elif level == 14:
        return f"금 곡괭이 (Lv.{level})"
    elif level == 15:
        return f"오래가는 금 곡괭이 (Lv.{level})"
    elif level == 16:
        return f"네더라이트 곡괭이 (Lv.{level})"
    elif level == 17:
        return f"효율 네더라이트 곡괭이 (Lv.{level})"
    elif level == 18:
        return f"이리듐 곡괭이 (Lv.{level})"
    elif level == 19:
        return f"최강의 이리듐 곡괭이 (Lv.{level})"
    else:
        return f"갤럭시 곡괭이 (Lv.{level})"

# --------------------------
# Confirm View for 완전 초기화
# --------------------------
class ResetConfirmView(discord.ui.View):
    def __init__(self, author: discord.User, timeout=30):
        super().__init__(timeout=timeout)
        self.author = author
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("이 명령어는 봇 소유자만 사용할 수 있습니다.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="동의", style=discord.ButtonStyle.green)
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.edit_message(content="모든 광산 데이터가 삭제됩니다.", view=None)

    @discord.ui.button(label="그만두기", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.edit_message(content="초기화가 취소되었습니다.", view=None)

# --------------------------
# MiningSystem Cog
# --------------------------
class MiningSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(os.environ.get("MONGODB_URI"))
        self.db = self.mongo_client["stock_game"]
        # active_sessions: { user_id: session_data }
        self.active_sessions = {}
    
    def get_user_profile(self, user_id):
        return self.db.mining_users.find_one({"_id": user_id})
    
    def update_user_profile(self, user_id, profile):
        self.db.mining_users.update_one({"_id": user_id}, {"$set": profile})
    
    # 강화 비용과 성공 확률 (장비 최대 20)
    # 강화 비용은 100 * 현재 장비 레벨, 성공 확률은 max(25, 100 - (현재장비레벨 * 5))
    # 단, 장비 레벨 11 이상부터 강화 실패 시 하락 확률 발생 (하락 확률 = (현재장비레벨 - 10) * 2)
    def get_equipment_upgrade_requirements(self, current_level):
        req_lucy = 100 * current_level
        success_rate = max(25, 100 - current_level * 5)
        return req_lucy, success_rate
    
    def get_inventory_upgrade_cost(self, current_capacity):
        return 200 * (current_capacity - 5 + 1)
    
    # --------------------------
    # 게임 시작 명령어 (닉네임 추가, 중복 및 빈칸 체크)
    # --------------------------
    @commands.command(name="광산시작")
    async def start_game(self, ctx, *, nickname: str):
        """
        #광산시작 [닉네임]:
        이 명령어를 사용하여 광산 게임을 시작합니다.
        닉네임은 반드시 입력해야 하며, 빈칸 또는 중복된 닉네임은 허용되지 않습니다.
        """
        nickname = nickname.strip()
        if not nickname:
            await ctx.send(f"{ctx.author.mention} 닉네임은 빈칸일 수 없습니다.")
            return
        if self.db.mining_users.find_one({"nickname": nickname}):
            await ctx.send(f"{ctx.author.mention} 이미 사용 중인 닉네임입니다. 다른 닉네임을 선택해주세요.")
            return
        
        user_id = str(ctx.author.id)
        profile = self.get_user_profile(user_id)
        if profile:
            await ctx.send(f"{ctx.author.mention} 이미 게임을 시작했습니다!")
            return
        new_profile = {
            "_id": user_id,
            "nickname": nickname,
            "level": 1,
            "xp": 0,
            "next_xp": 100,  # 100 * (1^2)
            "equipment": "맨손",
            "equipment_level": 1,
            "inventory": {},
            "inventory_capacity": 5,
            "루찌": 0
        }
        self.db.mining_users.insert_one(new_profile)
        await ctx.send(f"{ctx.author.mention} 광산 게임을 시작했습니다! 환영합니다, **{nickname}**!")
    
    # --------------------------
    # 광산유저삭제 명령어 (봇 소유자 전용)
    # --------------------------
    @commands.command(name="광산유저삭제")
    @commands.is_owner()
    async def delete_user(self, ctx, *, nickname: str):
        """
        #광산유저삭제 [닉네임]:
        봇 소유자 전용 명령어입니다.
        지정한 닉네임을 가진 유저의 광산 데이터를 삭제합니다.
        """
        nickname = nickname.strip()
        if not nickname:
            await ctx.send("닉네임은 빈칸일 수 없습니다.")
            return
        result = self.db.mining_users.delete_one({"nickname": nickname})
        if result.deleted_count:
            await ctx.send(f"**{nickname}** 닉네임을 가진 유저의 데이터가 삭제되었습니다.")
        else:
            await ctx.send(f"닉네임 **{nickname}**을 가진 유저를 찾을 수 없습니다.")
    
    # --------------------------
    # 광산완전초기화 명령어 (봇 소유자 전용)
    # --------------------------
    @commands.command(name="광산완전초기화")
    @commands.is_owner()
    async def full_reset(self, ctx):
        """
        #광산완전초기화:
        봇 소유자 전용 명령어입니다.
        경고: 이 명령어를 실행하면 광산 관련 모든 데이터가 삭제됩니다.
        주식 정보는 삭제되지 않습니다.
        """
        view = ResetConfirmView(ctx.author, timeout=30)
        await ctx.send("경고: 정말로 모든 광산 데이터를 삭제하시겠습니까? 주식 정보는 삭제되지 않습니다.", view=view)
        await view.wait()
        if view.value:
            self.db.mining_users.delete_many({})
            await ctx.send("모든 광산 데이터가 삭제되었습니다.")
        else:
            await ctx.send("광산 초기화가 취소되었습니다.")
    
    # --------------------------
    # 광산프로필 명령어
    # --------------------------
    @commands.command(name="광산프로필")
    async def mine_profile(self, ctx):
        """
        #광산프로필:
        자신의 유저 레벨, 장비, 보유 루찌, 인벤토리 상태 및 경험치 진행 상황을 표시합니다.
        """
        user_id = str(ctx.author.id)
        profile = self.get_user_profile(user_id)
        if not profile:
            await ctx.send(f"{ctx.author.mention} 게임을 시작하려면 #광산시작 명령어를 사용하세요!")
            return
        inventory = profile.get("inventory", {})
        used = sum(inventory.values()) if inventory else 0
        embed = discord.Embed(title=f"{ctx.author.display_name}님의 광산 프로필", color=discord.Color.gold())
        embed.add_field(name="닉네임", value=profile.get("nickname", "N/A"), inline=True)
        embed.add_field(name="유저 레벨", value=profile["level"], inline=True)
        embed.add_field(name="장비", value=profile["equipment"], inline=True)
        embed.add_field(name="보유 루찌", value=profile["루찌"], inline=True)
        embed.add_field(name="인벤토리", value=f"{used}/{profile['inventory_capacity']}", inline=True)
        embed.add_field(name="경험치", value=f"{profile.get('xp',0)}/{profile.get('next_xp',100)}", inline=True)
        await ctx.send(embed=embed)
    
    # --------------------------
    # 연속 채취 세션 함수
    # --------------------------
    async def mining_session(self, ctx, mine_name: str):
        """
        사용자 채취 세션: 일정 주기마다 채취를 시도하며,
        인벤토리가 꽉 차거나 사용자가 중지할 때까지 진행됩니다.
        세션 데이터는 self.active_sessions에 저장됩니다.
        광물은 한 번에 하나씩 드랍하며, 각 드랍 시 등급이 부여됩니다.
        """
        user_id = str(ctx.author.id)
        session = {
            "mine_name": mine_name,
            "start_time": time.time(),
            "total_time": 0,      # 누적 채취 시간 (초)
            "collected": {},      # 세션 동안 획득한 광물 (키: "광물 (등급)")
            "xp_gained": 0,
            "active": True,
            "ctx": ctx,
            "cycle_start": None,
            "current_cycle_duration": None
        }
        self.active_sessions[user_id] = session
        await ctx.send(f"{ctx.author.mention} **{mine_name}** 채취 세션이 시작되었습니다!")
        while session["active"]:
            profile = self.get_user_profile(user_id)
            current_inventory_count = sum(profile.get("inventory", {}).values()) if profile.get("inventory") else 0
            if current_inventory_count >= profile["inventory_capacity"]:
                await ctx.send(f"{ctx.author.mention} 인벤토리가 꽉 차서 채취 세션을 종료합니다.")
                session["active"] = False
                break
            effective_time = max(int(10800 / profile["equipment_level"]), 1)
            session["cycle_start"] = time.time()
            session["current_cycle_duration"] = effective_time
            try:
                await asyncio.sleep(effective_time)
            except asyncio.CancelledError:
                break
            session["total_time"] += effective_time
            # 광물은 한 번에 하나만 드랍하며, 등급 부여
            num_drops = 1
            drops = []
            mine = MINES[mine_name]
            for _ in range(num_drops):
                minerals = list(mine["minerals"].keys())
                chances = [mine["minerals"][m]["chance"] for m in minerals]
                base_mineral = random.choices(minerals, weights=chances, k=1)[0]
                qty = random.randint(mine["minerals"][base_mineral]["min_qty"], mine["minerals"][base_mineral]["max_qty"])
                grade = random.choices(list(MINERAL_GRADES.keys()), weights=[MINERAL_GRADES[g]["prob"] for g in MINERAL_GRADES], k=1)[0]
                mineral_with_grade = f"{base_mineral} ({grade})"
                drops.append((mineral_with_grade, qty, grade))
            available_space = profile["inventory_capacity"] - current_inventory_count
            collected_this_cycle = {}
            lost_drops = []
            for mineral_with_grade, qty, grade in drops:
                if available_space <= 0:
                    lost_drops.append((mineral_with_grade, qty))
                    continue
                if qty <= available_space:
                    collected_this_cycle[mineral_with_grade] = collected_this_cycle.get(mineral_with_grade, 0) + qty
                    available_space -= qty
                else:
                    collected_this_cycle[mineral_with_grade] = collected_this_cycle.get(mineral_with_grade, 0) + available_space
                    lost_drops.append((mineral_with_grade, qty - available_space))
                    available_space = 0
            for mineral, qty in collected_this_cycle.items():
                session["collected"][mineral] = session["collected"].get(mineral, 0) + qty
            if "inventory" not in profile or not profile["inventory"]:
                profile["inventory"] = {}
            for mineral, qty in collected_this_cycle.items():
                profile["inventory"][mineral] = profile["inventory"].get(mineral, 0) + qty
            # 경험치 부여: 기본 xp (랜덤 10~25) * 등급 xp 배율 (첫 드랍의 등급 사용)
            base_xp = random.randint(10, 25)
            if drops:
                grade = drops[0][2]
                xp_multiplier = MINERAL_GRADES[grade]["xp_multiplier"]
            else:
                xp_multiplier = 1.0
            xp_gained = int(base_xp * xp_multiplier)
            profile["xp"] = profile.get("xp", 0) + xp_gained
            session["xp_gained"] += xp_gained
            while profile["xp"] >= profile.get("next_xp", 100):
                profile["xp"] -= profile["next_xp"]
                profile["level"] += 1
                profile["next_xp"] = 100 * (profile["level"] ** 2)
            self.update_user_profile(user_id, profile)
        if user_id in self.active_sessions:
            self.active_sessions.pop(user_id)
            await ctx.send(f"{ctx.author.mention} 채취 세션이 종료되었습니다.")
    
    # --------------------------
    # 광산입장 명령어 (채취 세션 시작)
    # --------------------------
    @commands.command(name="광산입장")
    async def enter_mine(self, ctx, *, mine_name: str = None):
        """
        #광산입장 [광산이름]:
        - 광산 이름을 입력하지 않으면 사용 가능한 광산 목록을 출력합니다.
        - 광산 이름을 입력하면 해당 광산에 입장하여 연속 채취 세션을 시작합니다.
          (단, 유저 레벨, 장비 레벨, 인벤토리 여유가 충족되어야 합니다.)
        """
        user_id = str(ctx.author.id)
        profile = self.get_user_profile(user_id)
        if not profile:
            await ctx.send(f"{ctx.author.mention} 게임을 시작하려면 #광산시작 명령어를 사용하세요!")
            return
        if mine_name is None:
            embed = discord.Embed(title="사용 가능한 광산 목록", color=discord.Color.blue())
            for mine, data in MINES.items():
                embed.add_field(
                    name=mine,
                    value=f"요구 유저 레벨: {data['req_user_level']}\n요구 장비 레벨: {data['req_equipment_level']}",
                    inline=False
                )
            await ctx.send(embed=embed)
            return
        if mine_name not in MINES:
            await ctx.send("❌ 존재하지 않는 광산입니다. 사용 가능한 광산 목록은 `#광산입장` 명령어로 확인하세요.")
            return
        mine = MINES[mine_name]
        if profile["level"] < mine["req_user_level"]:
            await ctx.send(f"❌ 해당 광산 입장을 위해 최소 유저 레벨 {mine['req_user_level']} 필요 (현재 레벨: {profile['level']})")
            return
        if profile["equipment_level"] < mine["req_equipment_level"]:
            await ctx.send(f"❌ 해당 광산 입장을 위해 최소 장비 레벨 {mine['req_equipment_level']} 필요 (현재: {profile['equipment']} (Lv.{profile['equipment_level']}))")
            return
        current_inventory_count = sum(profile.get("inventory", {}).values()) if profile.get("inventory") else 0
        if current_inventory_count >= profile["inventory_capacity"]:
            await ctx.send("❌ 인벤토리가 꽉 차서 채취를 시작할 수 없습니다. 먼저 인벤토리를 정리해주세요!")
            return
        if user_id in self.active_sessions:
            await ctx.send(f"{ctx.author.mention} 이미 채취 세션이 진행 중입니다! (중지하려면 #광산중지 명령어를 사용하세요.)")
            return
        self.bot.loop.create_task(self.mining_session(ctx, mine_name))
    
    # --------------------------
    # 광산중지 명령어 (채취 세션 중지 및 결과 표시)
    # --------------------------
    @commands.command(name="광산중지")
    async def stop_mining(self, ctx):
        """
        #광산중지:
        진행 중인 채취 세션을 중지시키고, 지금까지의 채취 결과를 표시합니다.
        """
        user_id = str(ctx.author.id)
        if user_id not in self.active_sessions:
            await ctx.send(f"{ctx.author.mention} 진행 중인 채취 세션이 없습니다.")
            return
        session = self.active_sessions[user_id]
        session["active"] = False
        await asyncio.sleep(1)
        elapsed = int(time.time() - session["start_time"])
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        result = f"**채취 진행 시간:** {hours}시간 {minutes}분\n"
        result += "**세션 동안 획득한 광물:**\n"
        if session["collected"]:
            for mineral, qty in session["collected"].items():
                result += f"- {mineral}: {qty}개\n"
        else:
            result += "없음\n"
        result += f"**세션 동안 획득한 경험치:** {session['xp_gained']}\n"
        profile = self.get_user_profile(user_id)
        result += f"**현재 경험치:** {profile.get('xp',0)}/{profile.get('next_xp',100)}\n"
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
        await ctx.send(f"{ctx.author.mention} 채취 세션이 중지되었습니다.\n{result}")
    
    # --------------------------
    # 광산결과 명령어 (채취 세션 결과 조회, 세션 중지 아님)
    # --------------------------
    @commands.command(name="광산결과")
    async def mining_result(self, ctx):
        """
        #광산결과:
        진행 중인 채취 세션이 있다면,
         - 채취 시작 시각부터 현재까지의 누적 시간,
         - 다음 광물 드랍까지 남은 시간,
         - 세션 동안 획득한 경험치,
         - 세션 동안 획득한 광물 목록
        을 표시합니다.
        (채취 세션은 중지되지 않습니다.)
        """
        user_id = str(ctx.author.id)
        if user_id not in self.active_sessions:
            await ctx.send(f"{ctx.author.mention} 진행 중인 채취 세션이 없습니다.")
            return
        session = self.active_sessions[user_id]
        elapsed = int(time.time() - session["start_time"])
        total_hours = elapsed // 3600
        total_minutes = (elapsed % 3600) // 60
        if session.get("cycle_start") and session.get("current_cycle_duration"):
            cycle_elapsed = time.time() - session["cycle_start"]
            remaining = max(int(session["current_cycle_duration"] - cycle_elapsed), 0)
        else:
            remaining = 0
        result = f"**채취 시작 후 누적 시간:** {total_hours}시간 {total_minutes}분\n"
        result += f"**다음 광물 드랍까지 남은 시간:** {remaining}초\n"
        result += f"**세션 동안 획득한 경험치:** {session['xp_gained']}\n"
        result += "**세션 동안 획득한 광물:**\n"
        if session["collected"]:
            for mineral, qty in session["collected"].items():
                result += f"- {mineral}: {qty}개\n"
        else:
            result += "없음\n"
        await ctx.send(f"{ctx.author.mention} 채취 세션 결과:\n{result}")
    
    # --------------------------
    # 인벤토리 조회 명령어
    # --------------------------
    @commands.command(name="인벤토리")
    async def view_inventory(self, ctx):
        """
        #인벤토리:
        현재 보유한 광물 내역과 인벤토리 용량을 확인합니다.
        """
        user_id = str(ctx.author.id)
        profile = self.get_user_profile(user_id)
        if not profile:
            await ctx.send(f"{ctx.author.mention} 게임을 시작하려면 #광산시작 명령어를 사용하세요!")
            return
        inventory = profile.get("inventory", {})
        if not inventory:
            await ctx.send(f"{ctx.author.mention} 인벤토리가 비어 있습니다.")
            return
        embed = discord.Embed(title=f"{ctx.author.display_name}님의 인벤토리", color=discord.Color.green())
        for mineral, qty in inventory.items():
            embed.add_field(name=mineral, value=f"{qty}개", inline=False)
        used = sum(inventory.values())
        embed.set_footer(text=f"인벤토리 용량: {used}/{profile['inventory_capacity']}")
        await ctx.send(embed=embed)
    
    # --------------------------
    # 광물 판매 명령어 (등급 적용, 전체 판매 지원)
    # --------------------------
    @commands.command(name="광물판매")
    async def sell_minerals(self, ctx, *, args: str):
        """
        #광물판매 [광물이름] [수량]:
        보유한 광물을 판매하여 루찌를 획득합니다.
        광물 이름에는 등급이 포함되어야 합니다. 예: "철 (S)"
        만약 [수량] 자리에 "다" 또는 "전부"를 입력하면 해당 광물을 인벤토리에서 전부 판매합니다.
        (판매 가격은 SALE_PRICES에 등급 판매 배율을 곱하여 계산됩니다.)
        """
        args = args.strip()
        user_id = str(ctx.author.id)
        profile = self.get_user_profile(user_id)
        if not profile:
            await ctx.send(f"{ctx.author.mention} 게임을 시작하려면 #광산시작 명령어를 사용하세요!")
            return
        
        # 만약 전체 판매를 원할 경우 (예: "#광물판매 다")
        if args in ["다", "전부"]:
            inventory = profile.get("inventory", {})
            if not inventory:
                await ctx.send(f"{ctx.author.mention} 인벤토리가 비어 있습니다.")
                return
            total_earnings = 0
            for mineral, qty in list(inventory.items()):
                match = re.match(r"(.+?) \((.+?)\)$", mineral)
                if match:
                    base_mineral = match.group(1).strip()
                    grade = match.group(2).strip()
                else:
                    base_mineral = mineral
                    grade = "D"
                if base_mineral not in SALE_PRICES:
                    continue
                multiplier = MINERAL_GRADES.get(grade, {"sale_multiplier": 1.0})["sale_multiplier"]
                unit_price = SALE_PRICES[base_mineral] * multiplier
                total_earnings += int(unit_price * qty)
                del inventory[mineral]
            profile["inventory"] = inventory
            profile["루찌"] = profile.get("루찌", 0) + total_earnings
            self.update_user_profile(user_id, profile)
            await ctx.send(f"{ctx.author.mention} 인벤토리 내 모든 광물을 판매하여 {total_earnings} 루찌를 획득했습니다.")
            return
        
        # 기본 판매: "#광물판매 [광물이름] [수량]"
        parts = args.rsplit(" ", 1)
        if len(parts) != 2:
            await ctx.send(f"{ctx.author.mention} 올바른 형식으로 입력해주세요. 예: #광물판매 철 (S) 1")
            return
        mineral_input, quantity_str = parts
        try:
            quantity = int(quantity_str)
        except ValueError:
            await ctx.send(f"{ctx.author.mention} 수량은 정수로 입력해주세요.")
            return
        inventory = profile.get("inventory", {})
        if mineral_input not in inventory or inventory[mineral_input] < quantity:
            await ctx.send(f"{ctx.author.mention} 보유한 {mineral_input} 수량이 부족합니다.")
            return
        match = re.match(r"(.+?) \((.+?)\)$", mineral_input)
        if match:
            base_mineral = match.group(1).strip()
            grade = match.group(2).strip()
        else:
            base_mineral = mineral_input
            grade = "D"
        if base_mineral not in SALE_PRICES:
            await ctx.send(f"{ctx.author.mention} {base_mineral}은(는) 판매할 수 없는 광물입니다.")
            return
        multiplier = MINERAL_GRADES.get(grade, {"sale_multiplier": 1.0})["sale_multiplier"]
        unit_price = SALE_PRICES[base_mineral] * multiplier
        total_earnings = int(unit_price * quantity)
        inventory[mineral_input] -= quantity
        if inventory[mineral_input] <= 0:
            del inventory[mineral_input]
        profile["inventory"] = inventory
        profile["루찌"] = profile.get("루찌", 0) + total_earnings
        self.update_user_profile(user_id, profile)
        await ctx.send(f"{ctx.author.mention} {mineral_input} {quantity}개를 판매하여 {total_earnings} 루찌를 획득했습니다.")
    
    # --------------------------
    # 장비 강화 명령어 (광물 요구사항 제거, 최대 Lv.20, 하락 확률 적용)
    # --------------------------
    @commands.command(name="장비강화")
    async def upgrade_equipment(self, ctx):
        """
        #장비강화:
        현재 장비의 강화를 시도합니다.
        - 현재 장비 레벨에 따라 필요한 루찌와 강화 성공 확률이 표시됩니다.
        - 강화는 확률에 따라 성공하며, 최대 Lv.20까지 가능합니다.
        - 장비 레벨 11 이상부터 강화 실패 시 하락 확률이 발생합니다.
          (하락 확률 = (현재장비레벨 - 10) * 2%)
        - 강화 성공 시 장비의 이름이 변경됩니다.
        """
        user_id = str(ctx.author.id)
        profile = self.get_user_profile(user_id)
        if not profile:
            await ctx.send(f"{ctx.author.mention} 게임을 시작하려면 #광산시작 명령어를 사용하세요!")
            return
        current_level = profile["equipment_level"]
        if current_level >= 20:
            await ctx.send(f"{ctx.author.mention} 이미 최대 강화 단계(20)입니다.")
            return
        req_lucy, success_rate = self.get_equipment_upgrade_requirements(current_level)
        req_str = f"**요구 루찌:** {req_lucy}\n"
        req_str += f"**강화 성공 확률:** {success_rate}%\n"
        req_str += "(※ 필요 광물은 없습니다.)"
        embed = discord.Embed(title="장비 강화 요구 사항", description=req_str, color=discord.Color.purple())
        await ctx.send(embed=embed)
        if profile.get("루찌", 0) < req_lucy:
            await ctx.send(f"{ctx.author.mention} 루찌가 부족합니다. (보유: {profile.get('루찌', 0)} 루찌)")
            return
        profile["루찌"] -= req_lucy
        if random.randint(1, 100) <= success_rate:
            profile["equipment_level"] += 1
            profile["equipment"] = get_equipment_name(profile["equipment_level"])
            result_msg = f"{ctx.author.mention} **강화 성공!** 현재 장비: {profile['equipment']}"
        else:
            if current_level >= 11:
                downgrade_chance = (current_level - 10) * 2
                if random.randint(1, 100) <= downgrade_chance:
                    profile["equipment_level"] = max(1, profile["equipment_level"] - 1)
                    profile["equipment"] = get_equipment_name(profile["equipment_level"])
                    result_msg = f"{ctx.author.mention} 강화 실패로 인해 장비가 하락하였습니다. 현재 장비: {profile['equipment']}"
                else:
                    result_msg = f"{ctx.author.mention} 강화에 실패하였습니다. 현재 장비: {profile['equipment']} (소모 자원은 회수되지 않습니다.)"
            else:
                result_msg = f"{ctx.author.mention} 강화에 실패하였습니다. 현재 장비: {profile['equipment']} (소모 자원은 회수되지 않습니다.)"
        self.update_user_profile(user_id, profile)
        await ctx.send(result_msg)
    
    # --------------------------
    # 인벤토리 증가 명령어 (최대 30 제한)
    # --------------------------
    @commands.command(name="인벤토리증가")
    async def upgrade_inventory(self, ctx):
        """
        #인벤토리증가:
        일정 루찌를 지불하여 인벤토리 용량을 1 증가시킵니다.
        단, 인벤토리 용량은 최대 30까지 증가할 수 있습니다.
        """
        user_id = str(ctx.author.id)
        profile = self.get_user_profile(user_id)
        if not profile:
            await ctx.send(f"{ctx.author.mention} 게임을 시작하려면 #광산시작 명령어를 사용하세요!")
            return
        if profile["inventory_capacity"] >= 30:
            await ctx.send(f"{ctx.author.mention} 인벤토리 용량은 최대 30까지 증가할 수 있습니다.")
            return
        current_capacity = profile["inventory_capacity"]
        cost = self.get_inventory_upgrade_cost(current_capacity)
        if profile.get("루찌", 0) < cost:
            await ctx.send(f"{ctx.author.mention} 루찌가 부족합니다. (필요: {cost} 루찌, 보유: {profile.get('루찌', 0)} 루찌)")
            return
        profile["루찌"] -= cost
        profile["inventory_capacity"] += 1
        self.update_user_profile(user_id, profile)
        await ctx.send(f"{ctx.author.mention} 인벤토리 용량이 {current_capacity}에서 {profile['inventory_capacity']}로 증가하였습니다! (소요 루찌: {cost})")

async def setup(bot):
    await bot.add_cog(MiningSystem(bot))

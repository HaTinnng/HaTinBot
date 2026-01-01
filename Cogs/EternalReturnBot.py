import discord
import random
import asyncio
from discord.ext import commands

# ─────────────────────────────────────────────────────────────────────────────
# 🧪 이터널 리턴 실험체 데이터 (샘플 20종)
# 실제로는 70명이 넘지만, 예시로 다양하게 구성했습니다. 이미지 URL은 공식 위키/팬키트 참조.
ER_CHARACTERS = [
    {"name": "재키 (Jackie)",    "role": "단검/양손검/도끼/쌍검 - 근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/87/Skin_Default_Jackie.png"},
    {"name": "아야 (Aya)",       "role": "권총/돌격소총/저격총 - 원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/07/Skin_Default_Aya.png"},
    {"name": "현우 (Hyunwoo)",   "role": "글러브/톤파 - 브루저/탱커",          "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/52/Skin_Default_Hyunwoo.png"},
    {"name": "매그너스 (Magnus)", "role": "방망이/망치 - 브루저/탱커",          "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/36/Skin_Default_Magnus.png"},
    {"name": "피오라 (Fiora)",    "role": "레이피어/양손검/창 - 근거리 딜러",    "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/87/Skin_Default_Fiora.png"},
    {"name": "나딘 (Nadine)",     "role": "활/석궁 - 원거리 딜러",              "img": "https://static.wikia.nocookie.net/eternalreturn/images/a/a2/Skin_Default_Nadine.png"},
    {"name": "자히르 (Zahir)",    "role": "투척/암기 - 스킬 증폭 메이지",        "img": "https://static.wikia.nocookie.net/eternalreturn/images/a/ab/Skin_Default_Zahir.png"},
    {"name": "하트 (Hart)",       "role": "기타 - 평타 기반 원거리 딜러",        "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/36/Skin_Default_Hart.png"},
    {"name": "아이솔 (Isol)",     "role": "권총/돌격소총 - 트랩/원거리 딜러",    "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/33/Skin_Default_Isol.png"},
    {"name": "리 다이린 (Li Dailin)","role": "글러브/쌍절곤 - 근거리 딜러/브루저","img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c5/Skin_Default_Li_Dailin.png"},
    {"name": "유키 (Yuki)",       "role": "양손검/쌍검 - 근거리 딜러",          "img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c2/Skin_Default_Yuki.png"},
    {"name": "혜진 (Hyejin)",     "role": "활/암기 - 스킬 증폭 메이지/CC",      "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/02/Skin_Default_Hyejin.png"},
    {"name": "쇼우 (Xiukai)",     "role": "단검/창 - 요리사/탱커",              "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d1/Skin_Default_Xiukai.png"},
    {"name": "시셀라 (Sissela)",  "role": "투척/암기 - 스킬 증폭 메이지",        "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/39/Skin_Default_Sissela.png"},
    {"name": "키아라 (Chiara)",   "role": "레이피어 - 근거리 딜러/브루저",       "img": "https://static.wikia.nocookie.net/eternalreturn/images/4/46/Skin_Default_Chiara.png"},
    {"name": "아드리아나 (Adriana)","role": "투척 - 화염/광역 메이지",           "img": "https://static.wikia.nocookie.net/eternalreturn/images/6/66/Skin_Default_Adriana.png"},
    {"name": "쇼이치 (Shoichi)",  "role": "단검 - 암살자",                      "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/52/Skin_Default_Shoichi.png"},
    {"name": "실비아 (Silvia)",   "role": "권총 - 기동형 스킬 딜러",            "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d9/Skin_Default_Silvia.png"},
    {"name": "엠마 (Emma)",       "role": "암기 - 포킹/트릭스터",               "img": "https://static.wikia.nocookie.net/eternalreturn/images/f/fc/Skin_Default_Emma.png"},
    {"name": "데비&마를렌 (Debi&Marlene)","role": "양손검 - 태그/근거리 딜러",  "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d8/Skin_Default_Debi_%26_Marlene.png"},
]

class EternalReturnBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 이터널 리턴 테마 색상 (오렌지/노랑 계열)
        self.er_color = 0xFFA500 

    # ── 명령어 1: 도움말 ──────────────────────────────────────────────────────────
    @commands.command(name="이터널리턴")
    async def er_help(self, ctx):
        embed = discord.Embed(
            title="🧬 루미아 섬 실험 보조 시스템",
            description="이터널 리턴 캐릭터 추천 봇입니다. 아래 명령어를 사용해보세요!",
            color=self.er_color
        )
        embed.add_field(
            name="🎲 랜덤 뽑기", 
            value="`#이터널리턴뽑기`, `#이리뽑기`, `#이리캐릭뽑기`, `#이리추천`\n👉 수많은 실험체 중 하나를 무작위로 추천해줍니다.", 
            inline=False
        )
        embed.add_field(
            name="ℹ️ 정보", 
            value=f"현재 데이터베이스에 등록된 실험체: **{len(ER_CHARACTERS)}명**", 
            inline=False
        )
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/e/e6/Eternal_Return_Logo.png") # 로고 예시
        embed.set_footer(text="영원회귀: 블랙서바이벌 | 행운을 빕니다, 실험체님.")
        
        await ctx.send(embed=embed)

    # ── 명령어 2: 캐릭터 랜덤 뽑기 ──────────────────────────────────────────────────
    @commands.command(name="이터널리턴뽑기", aliases=["이리뽑기", "이리캐릭뽑기", "이리추천", "이리랜덤"])
    async def er_gacha(self, ctx):
        # 1. 연출 메시지 (긴장감 조성)
        loading_msg = await ctx.send("🧬 **실험체를 선별하고 있습니다...** 🧬")
        await asyncio.sleep(1.5) # 1.5초 대기

        # 2. 랜덤 선택
        pick = random.choice(ER_CHARACTERS)

        # 3. 결과 임베드 생성
        embed = discord.Embed(
            title=f"✨ 당신의 실험체는 [ {pick['name']} ] 입니다!",
            description=f"**역할군/무기:**\n{pick['role']}",
            color=self.er_color
        )
        
        # 이미지 설정 (있을 경우)
        if pick["img"]:
            embed.set_image(url=pick["img"])
        
        embed.set_footer(text=f"추천인: {ctx.author.display_name} | 루미아 섬으로 떠나세요!")

        # 4. 메시지 수정 및 출력
        await loading_msg.delete() # 로딩 메시지 삭제
        await ctx.send(f"{ctx.author.mention}", embed=embed)

# ── 봇 로드 설정 ──────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(EternalReturnBot(bot))

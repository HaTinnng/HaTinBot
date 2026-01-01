import discord
import random
import asyncio
from discord.ext import commands

# ─────────────────────────────────────────────────────────────────────────────
# 🧪 이터널 리턴 실험체 데이터 (구조 업그레이드)
# weapons: 해당 캐릭터가 사용할 수 있는 무기 목록 (리스트)
# position: 캐릭터의 주 역할군
ER_CHARACTERS = [
    {"name": "재키 (Jackie)",    "weapons": ["단검", "양손검", "도끼", "쌍검"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/87/Skin_Default_Jackie.png"},
    {"name": "아야 (Aya)",       "weapons": ["권총", "돌격소총", "저격총"],    "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/07/Skin_Default_Aya.png"},
    {"name": "현우 (Hyunwoo)",   "weapons": ["글러브", "톤파"],               "position": "브루저/탱커", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/52/Skin_Default_Hyunwoo.png"},
    {"name": "매그너스 (Magnus)", "weapons": ["방망이", "망치"],               "position": "브루저/탱커", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/36/Skin_Default_Magnus.png"},
    {"name": "피오라 (Fiora)",    "weapons": ["레이피어", "양손검", "창"],      "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/87/Skin_Default_Fiora.png"},
    {"name": "나딘 (Nadine)",     "weapons": ["활", "석궁"],                   "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/a/a2/Skin_Default_Nadine.png"},
    {"name": "자히르 (Zahir)",    "weapons": ["투척", "암기"],                 "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/a/ab/Skin_Default_Zahir.png"},
    {"name": "하트 (Hart)",       "weapons": ["기타"],                         "position": "평타 원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/36/Skin_Default_Hart.png"},
    {"name": "아이솔 (Isol)",     "weapons": ["권총", "돌격소총"],             "position": "트랩/원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/33/Skin_Default_Isol.png"},
    {"name": "리 다이린 (Li Dailin)","weapons": ["글러브", "쌍절곤"],          "position": "근거리 딜러/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c5/Skin_Default_Li_Dailin.png"},
    {"name": "유키 (Yuki)",       "weapons": ["양손검", "쌍검"],               "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c2/Skin_Default_Yuki.png"},
    {"name": "혜진 (Hyejin)",     "weapons": ["활", "암기"],                   "position": "스킬 증폭 메이지/CC", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/02/Skin_Default_Hyejin.png"},
    {"name": "쇼우 (Xiukai)",     "weapons": ["단검", "창"],                   "position": "요리사/탱커", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d1/Skin_Default_Xiukai.png"},
    {"name": "시셀라 (Sissela)",  "weapons": ["투척", "암기"],                 "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/39/Skin_Default_Sissela.png"},
    {"name": "키아라 (Chiara)",   "weapons": ["레이피어"],                     "position": "근거리 딜러/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/4/46/Skin_Default_Chiara.png"},
    {"name": "아드리아나 (Adriana)","weapons": ["투척"],                       "position": "화염/광역 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/6/66/Skin_Default_Adriana.png"},
    {"name": "쇼이치 (Shoichi)",  "weapons": ["단검"],                         "position": "암살자", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/52/Skin_Default_Shoichi.png"},
    {"name": "실비아 (Silvia)",   "weapons": ["권총"],                         "position": "기동형 스킬 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d9/Skin_Default_Silvia.png"},
    {"name": "엠마 (Emma)",       "weapons": ["암기"],                         "position": "포킹/트릭스터", "img": "https://static.wikia.nocookie.net/eternalreturn/images/f/fc/Skin_Default_Emma.png"},
    {"name": "데비&마를렌",        "weapons": ["양손검"],                       "position": "태그/근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d8/Skin_Default_Debi_%26_Marlene.png"},
    {"name": "알렉스 (Alex)",     "weapons": ["권총", "양손검", "암기", "톤파"], "position": "하이브리드/전술가", "img": "https://static.wikia.nocookie.net/eternalreturn/images/e/e0/Skin_Default_Alex.png"},
]

class EternalReturnBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.er_color = 0xFFA500 

    # ── 명령어 1: 도움말 ──────────────────────────────────────────────────────────
    @commands.command(name="이터널리턴")
    async def er_help(self, ctx):
        embed = discord.Embed(
            title="🧬 루미아 섬 실험 보조 시스템",
            description="캐릭터와 **무기**까지 정해주는 추천 봇입니다.",
            color=self.er_color
        )
        embed.add_field(
            name="🎲 랜덤 뽑기", 
            value="`#이터널리턴뽑기`, `#이리뽑기`, `#이리캐릭뽑기`\n👉 실험체와 사용할 무기 하나를 지정해줍니다.", 
            inline=False
        )
        embed.set_footer(text="영원회귀: 블랙서바이벌 | 이번 판은 이 무기로 가시죠.")
        
        await ctx.send(embed=embed)

    # ── 명령어 2: 캐릭터 & 무기 랜덤 뽑기 ───────────────────────────────────────────
    @commands.command(name="이터널리턴뽑기", aliases=["이리뽑기", "이리캐릭뽑기", "이리추천", "이리랜덤"])
    async def er_gacha(self, ctx):
        # 1. 연출 메시지
        loading_msg = await ctx.send("🧬 **실험체와 무기 루트를 분석 중입니다...** 🧬")
        await asyncio.sleep(1.5)

        # 2. 랜덤 선택 로직
        # 2-1. 캐릭터 하나 선택
        character = random.choice(ER_CHARACTERS)
        
        # 2-2. 그 캐릭터의 무기 목록 중 하나 선택
        selected_weapon = random.choice(character["weapons"])

        # 3. 결과 임베드 생성
        embed = discord.Embed(
            title=f"✨ 당신의 선택: [ {character['name']} ]",
            description="루미아 섬에서의 생존 전략이 결정되었습니다.",
            color=self.er_color
        )
        
        # 핵심 정보 필드 (무기를 강조)
        embed.add_field(
            name="⚔️ 지정 무기",
            value=f"### 🎯 **{selected_weapon}**", # 큰 글씨로 강조
            inline=True
        )
        embed.add_field(
            name="🛡️ 역할군",
            value=f"{character['position']}",
            inline=True
        )

        # 이미지 설정
        if character["img"]:
            embed.set_image(url=character["img"])
        
        embed.set_footer(text=f"추천인: {ctx.author.display_name} | {selected_weapon} {character['name'].split('(')[0].strip()} 장인이 되어보세요!")

        # 4. 메시지 수정 및 출력
        await loading_msg.delete()
        await ctx.send(f"{ctx.author.mention}", embed=embed)

# ── 봇 로드 설정 ──────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(EternalReturnBot(bot))

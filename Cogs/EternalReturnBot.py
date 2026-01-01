import discord
import random
import asyncio
from discord.ext import commands

# ─────────────────────────────────────────────────────────────────────────────
# 🧪 이터널 리턴 모든 실험체 데이터 (가나다 순 정렬 추천)
# 무기군이 여러 개인 캐릭터는 weapons 리스트에 모두 포함되어 있습니다.
# ─────────────────────────────────────────────────────────────────────────────
ER_CHARACTERS = [
    # ㄱ
    {"name": "가네샤 (Ganesha)", "weapons": ["투척"], "position": "서포터/스증", "img": "https://static.wikia.nocookie.net/eternalreturn/images/thumb/e/e6/Skin_Default_Garnet.png/300px-Skin_Default_Garnet.png"}, # 가넷(Garnet)
    {"name": "그렘린 (Gremlin)", "weapons": ["암기"], "position": "원거리 딜러", "img": None}, # 예시(실제 없는 캐릭이면 제외) -> 요리는 쇼우 등

    # 실제 이터널 리턴 캐릭터 목록 (가나다/출시순 혼합 정렬)
    {"name": "가넷 (Garnet)", "weapons": ["방망이"], "position": "브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/e/e6/Skin_Default_Garnet.png"},
    {"name": "나딘 (Nadine)", "weapons": ["활", "석궁"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/a/a2/Skin_Default_Nadine.png"},
    {"name": "나타폰 (Nathapon)", "weapons": ["카메라"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/6/6b/Skin_Default_Nathapon.png"},
    {"name": "니키 (Nicky)", "weapons": ["글러브"], "position": "근거리 딜러/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/9/90/Skin_Default_Nicky.png"},
    {"name": "다르코 (Darko)", "weapons": ["글러브"], "position": "탱커/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/82/Skin_Default_Darko.png"},
    {"name": "다니엘 (Daniel)", "weapons": ["단검"], "position": "암살자", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/07/Skin_Default_Daniel.png"},
    {"name": "데비&마를렌", "weapons": ["양손검"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d8/Skin_Default_Debi_%26_Marlene.png"},
    {"name": "띠아 (Tia)", "weapons": ["방망이"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/58/Skin_Default_Tia.png"},
    {"name": "라우라 (Laura)", "weapons": ["채찍"], "position": "암살자/스증 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/09/Skin_Default_Laura.png"},
    {"name": "레니 (Lenny)", "weapons": ["권총"], "position": "서포터", "img": "https://static.wikia.nocookie.net/eternalreturn/images/4/42/Skin_Default_Lenny.png"},
    {"name": "레노스 (Lenox)", "weapons": ["채찍"], "position": "탱커/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/2/22/Skin_Default_Lenox.png"},
    {"name": "레온 (Leon)", "weapons": ["글러브", "톤파"], "position": "서포터/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/9/9b/Skin_Default_Leon.png"},
    {"name": "로지 (Rozzi)", "weapons": ["권총"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/1/10/Skin_Default_Rozzi.png"},
    {"name": "루크 (Luke)", "weapons": ["방망이"], "position": "암살자/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/2/26/Skin_Default_Luke.png"},
    {"name": "리 다이린 (Li Dailin)", "weapons": ["글러브", "쌍절곤"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c5/Skin_Default_Li_Dailin.png"},
    {"name": "리오 (Rio)", "weapons": ["활"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/53/Skin_Default_Rio.png"},
    {"name": "리안 (Ly Anh)", "weapons": ["단검"], "position": "브루저/암살자", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/8e/Skin_Default_Ly_Anh.png"},
    {"name": "마르티나 (Martina)", "weapons": ["카메라"], "position": "평타 원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/9/92/Skin_Default_Martina.png"},
    {"name": "마이 (Mai)", "weapons": ["채찍"], "position": "탱커/서포터", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d4/Skin_Default_Mai.png"},
    {"name": "마커스 (Markus)", "weapons": ["도끼"], "position": "탱커/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/6/69/Skin_Default_Markus.png"},
    {"name": "매그너스 (Magnus)", "weapons": ["방망이", "망치"], "position": "브루저/탱커", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/36/Skin_Default_Magnus.png"},
    {"name": "바냐 (Vanya)", "weapons": ["아르카나"], "position": "스킬 증폭 메이지/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d3/Skin_Default_Vanya.png"},
    {"name": "바바라 (Barbara)", "weapons": ["방망이"], "position": "스킬 증폭 메이지/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/88/Skin_Default_Barbara.png"},
    {"name": "버니스 (Bernice)", "weapons": ["저격총"], "position": "원거리 딜러/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/7/77/Skin_Default_Bernice.png"},
    {"name": "비앙카 (Bianca)", "weapons": ["아르카나"], "position": "스킬 증폭 메이지/이니시에이터", "img": "https://static.wikia.nocookie.net/eternalreturn/images/7/7f/Skin_Default_Bianca.png"},
    {"name": "샬럿 (Charlotte)", "weapons": ["아르카나"], "position": "서포터/스증", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/34/Skin_Default_Charlotte.png"},
    {"name": "셀린 (Celine)", "weapons": ["투척"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/7/74/Skin_Default_Celine.png"},
    {"name": "쇼우 (Xiukai)", "weapons": ["단검", "창"], "position": "탱커/스증", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d1/Skin_Default_Xiukai.png"},
    {"name": "쇼이치 (Shoichi)", "weapons": ["단검"], "position": "암살자", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/52/Skin_Default_Shoichi.png"},
    {"name": "수아 (Sua)", "weapons": ["망치", "방망이"], "position": "브루저/탱커", "img": "https://static.wikia.nocookie.net/eternalreturn/images/7/75/Skin_Default_Sua.png"},
    {"name": "시셀라 (Sissela)", "weapons": ["투척", "암기"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/39/Skin_Default_Sissela.png"},
    {"name": "실비아 (Silvia)", "weapons": ["권총"], "position": "스킬 증폭/기동형", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d9/Skin_Default_Silvia.png"},
    {"name": "아델라 (Adela)", "weapons": ["레이피어"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/a/a2/Skin_Default_Adela.png"},
    {"name": "아드리아나 (Adriana)", "weapons": ["투척"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/6/66/Skin_Default_Adriana.png"},
    {"name": "아르다 (Arda)", "weapons": ["아르카나"], "position": "서포터/스증", "img": "https://static.wikia.nocookie.net/eternalreturn/images/2/23/Skin_Default_Arda.png"},
    {"name": "아비게일 (Abigail)", "weapons": ["도끼"], "position": "근거리 딜러/암살자", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/06/Skin_Default_Abigail.png"},
    {"name": "아야 (Aya)", "weapons": ["권총", "돌격소총", "저격총"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/07/Skin_Default_Aya.png"},
    {"name": "아이솔 (Isol)", "weapons": ["권총", "돌격소총"], "position": "원거리 딜러/트랩", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/33/Skin_Default_Isol.png"},
    {"name": "아이작 (Isaac)", "weapons": ["톤파"], "position": "브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/4/4f/Skin_Default_Isaac.png"},
    {"name": "알렉스 (Alex)", "weapons": ["권총", "양손검", "암기", "톤파"], "position": "하이브리드/전술가", "img": "https://static.wikia.nocookie.net/eternalreturn/images/e/e0/Skin_Default_Alex.png"},
    {"name": "알론소 (Alonso)", "weapons": ["글러브"], "position": "탱커", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/87/Skin_Default_Alonso.png"},
    {"name": "얀 (Jan)", "weapons": ["글러브", "톤파"], "position": "브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/4/41/Skin_Default_Jan.png"},
    {"name": "에스텔 (Estelle)", "weapons": ["도끼"], "position": "탱커/서포터", "img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c8/Skin_Default_Estelle.png"},
    {"name": "에이든 (Aiden)", "weapons": ["양손검"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c4/Skin_Default_Aiden.png"},
    {"name": "에키온 (Echion)", "weapons": ["VF의수"], "position": "근거리 딜러/폭주", "img": "https://static.wikia.nocookie.net/eternalreturn/images/7/79/Skin_Default_Echion.png"},
    {"name": "엘레나 (Elena)", "weapons": ["레이피어"], "position": "탱커/빙결", "img": "https://static.wikia.nocookie.net/eternalreturn/images/9/91/Skin_Default_Elena.png"},
    {"name": "엠마 (Emma)", "weapons": ["암기"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/f/fc/Skin_Default_Emma.png"},
    {"name": "요한 (Johann)", "weapons": ["아르카나"], "position": "서포터/힐러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/b/bd/Skin_Default_Johann.png"},
    {"name": "윌리엄 (William)", "weapons": ["투척"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/05/Skin_Default_William.png"},
    {"name": "유민 (Yumin)", "weapons": ["아르카나"], "position": "스킬 증폭/기동형", "img": "https://static.wikia.nocookie.net/eternalreturn/images/6/65/Skin_Default_Yumin.png"},
    {"name": "유키 (Yuki)", "weapons": ["양손검", "쌍검"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/c/c2/Skin_Default_Yuki.png"},
    {"name": "이렘 (Irem)", "weapons": ["투척"], "position": "스킬 증폭 메이지(변신)", "img": "https://static.wikia.nocookie.net/eternalreturn/images/9/98/Skin_Default_Irem.png"},
    {"name": "이바 (Eva)", "weapons": ["투척"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/d/d4/Skin_Default_Eva.png"},
    {"name": "이안 (Ian)", "weapons": ["단검"], "position": "근거리 딜러/변신", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/04/Skin_Default_Ian.png"},
    {"name": "일레븐 (Eleven)", "weapons": ["망치"], "position": "탱커/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/2/21/Skin_Default_Eleven.png"},
    {"name": "자히르 (Zahir)", "weapons": ["투척", "암기"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/a/ab/Skin_Default_Zahir.png"},
    {"name": "재키 (Jackie)", "weapons": ["단검", "양손검", "도끼", "쌍검"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/87/Skin_Default_Jackie.png"},
    {"name": "제니 (Jenny)", "weapons": ["권총"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/52/Skin_Default_Jenny.png"},
    {"name": "츠바메 (Tsubame)", "weapons": ["암기"], "position": "암살자", "img": "https://static.wikia.nocookie.net/eternalreturn/images/9/9e/Skin_Default_Tsubame.png"},
    {"name": "카밀로 (Camilo)", "weapons": ["쌍검", "레이피어"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/9/91/Skin_Default_Camilo.png"},
    {"name": "카를라 (Karla)", "weapons": ["석궁"], "position": "원거리 딜러/스증", "img": "https://static.wikia.nocookie.net/eternalreturn/images/2/28/Skin_Default_Karla.png"},
    {"name": "카티야 (Katja)", "weapons": ["저격총"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/7/7b/Skin_Default_Katja.png"},
    {"name": "칼라 (Karla)", "weapons": ["석궁"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/2/28/Skin_Default_Karla.png"}, # 중복 방지용
    {"name": "캐시 (Cathy)", "weapons": ["단검", "쌍검"], "position": "암살자/근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/5e/Skin_Default_Cathy.png"},
    {"name": "케네스 (Kenneth)", "weapons": ["도끼"], "position": "브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/6/61/Skin_Default_Kenneth.png"},
    {"name": "클로에 (Chloe)", "weapons": ["암기"], "position": "인형사/원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/0a/Skin_Default_Chloe.png"},
    {"name": "키아라 (Chiara)", "weapons": ["레이피어"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/4/46/Skin_Default_Chiara.png"},
    {"name": "타지아 (Tazia)", "weapons": ["암기"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/b/b3/Skin_Default_Tazia.png"},
    {"name": "테오도르 (Theodore)", "weapons": ["저격총"], "position": "서포터/원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/7/71/Skin_Default_Theodore.png"},
    {"name": "펠릭스 (Felix)", "weapons": ["창"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/5a/Skin_Default_Felix.png"},
    {"name": "프리야 (Priya)", "weapons": ["기타"], "position": "서포터", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/3e/Skin_Default_Priya.png"},
    {"name": "피오라 (Fiora)", "weapons": ["레이피어", "양손검", "창"], "position": "근거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/8/87/Skin_Default_Fiora.png"},
    {"name": "피올로 (Piolo)", "weapons": ["쌍절곤"], "position": "스킬 증폭/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/1/1a/Skin_Default_Piolo.png"},
    {"name": "하트 (Hart)", "weapons": ["기타"], "position": "원거리 딜러", "img": "https://static.wikia.nocookie.net/eternalreturn/images/3/36/Skin_Default_Hart.png"},
    {"name": "헤이즈 (Haze)", "weapons": ["돌격소총"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/09/Skin_Default_Haze.png"},
    {"name": "현우 (Hyunwoo)", "weapons": ["글러브", "톤파"], "position": "탱커/브루저", "img": "https://static.wikia.nocookie.net/eternalreturn/images/5/52/Skin_Default_Hyunwoo.png"},
    {"name": "혜진 (Hyejin)", "weapons": ["활", "암기"], "position": "스킬 증폭 메이지", "img": "https://static.wikia.nocookie.net/eternalreturn/images/0/02/Skin_Default_Hyejin.png"},
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
            description="현재 등록된 **70명 이상의 모든 실험체**를 지원합니다.",
            color=self.er_color
        )
        embed.add_field(
            name="🎲 랜덤 뽑기", 
            value="`#이터널리턴뽑기`, `#이리뽑기`, `#이리캐릭뽑기`\n👉 실험체와 사용할 무기 하나를 지정해줍니다.", 
            inline=False
        )
        embed.set_footer(text=f"Total Characters: {len(ER_CHARACTERS)}")
        await ctx.send(embed=embed)

    # ── 명령어 2: 캐릭터 & 무기 랜덤 뽑기 ───────────────────────────────────────────
    @commands.command(name="이터널리턴뽑기", aliases=["이리뽑기", "이리캐릭뽑기", "이리추천", "이리랜덤"])
    async def er_gacha(self, ctx):
        # 1. 연출 메시지
        loading_msg = await ctx.send("🧬 **루미아 섬의 데이터를 불러오는 중입니다...** 🧬")
        await asyncio.sleep(1.0) # 1초로 단축

        # 2. 랜덤 선택 로직
        character = random.choice(ER_CHARACTERS)
        selected_weapon = random.choice(character["weapons"])

        # 3. 결과 임베드 생성
        embed = discord.Embed(
            title=f"✨ 실험체 선정 완료: [ {character['name']} ]",
            description="생존을 위한 최적의 솔루션을 제공합니다.",
            color=self.er_color
        )
        
        embed.add_field(
            name="⚔️ 추천 무기 루트",
            value=f"### 🎯 **{selected_weapon}**",
            inline=True
        )
        embed.add_field(
            name="🛡️ 포지션",
            value=f"{character['position']}",
            inline=True
        )

        # 이미지 설정 (None일 경우 기본 로고 사용)
        if character["img"]:
            embed.set_image(url=character["img"])
        else:
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/e/e6/Eternal_Return_Logo.png")
            embed.set_footer(text="⚠️ 이미지 데이터를 불러오지 못했습니다.")
        
        if character["img"]:
            embed.set_footer(text=f"추천인: {ctx.author.display_name} | {selected_weapon} {character['name'].split('(')[0].strip()} 장인이 되어보세요!")

        # 4. 메시지 수정 및 출력
        await loading_msg.delete()
        await ctx.send(f"{ctx.author.mention}", embed=embed)

# ── 봇 로드 설정 ──────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(EternalReturnBot(bot))

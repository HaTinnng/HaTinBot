import discord
from discord.ext import commands

# 주식 종목 소개 데이터
STOCK_INFO = {
    "311유통": "311이 대표로 있는 311유통입니다. 그런데 유통을 탱크로 한다고 한다는 소문이 있네요? "
              "그런 소문때문에 모든 주식 중에서 가격이 가장 낮습니다....",

    "썬더타이어": "빠른 타이어를 원한다면 썬더타이어! 우리 기매키는 형님들이 직접 만들고 판매합니다! "
               "죽은 타이어도 살려냅니다! 성능은....",

    "룡치수산": "룡치가 대표로 있는 수산계의 대표적인 회사입니다. 물고기 신선도도 좋지만 "
              "가끔 특이한 물고기들도 있다고 하네요!",

    "맥턴맥주": "맥턴이 대표로 있는 맥주회사입니다. 대표의 취향이 특이해서 다양한 맥주를 "
              "만들어보는데 반응이 좋을지는 모르겠네요...",

    "섹보경아트": "섹보경대표가 있는 아트회사입니다. 소문에 의하면 대표가 2번 미대에 떨어졌다는 말이....",

    "전차자동차": "자동차를 생산하고 판매합니다. 그런데 이걸 타고 다닐 수 있나요...?",

    "이리여행사": "우리 이리 죽지않습니다... 어디론가 떠나지도 않습니다.....",

    "디코커피": "커피하면 디코커피! 디코~디코~아이스커피~ 어디서 들어보셨다고요? 그럴리가요~",

    "와이제이엔터": "세계적인 연예인을 키우는 YJ가 대표로 있는 엔터테인먼트입니다. "
                   "그런데 세계적인 연예인이 없는데 이런 주가가....?",

    "파피게임사": "이 회사에서 만든 게임은 정말 뛰어나다고 합니다! 그런데 악몽을 꾼다던가 "
                "게임을 플레이하던 도중 사람이 사라진다는 말이 나오는...",

    "하틴봇전자": "모든 공정이 자동화되어 있습니다! 자동으로 24시간 돌아가지만 오류가 좀 많다고 하네요... "
                "오류 발견하면 문의주세요~",

    "하틴출판사": "하틴이 대표로 있는 출판사입니다. 소문으로만 무성하던 전설의 작 '와피스'를 "
                "연재하여 사람들의 집중을 이끈 회사입니다.",

    "창훈버거": "전창훈이 대표로 있는 패스트푸드 회사입니다. 이 버거를 맛본 사람은 다시 그 버거를 "
              "먹고 싶어하는 마성의 버거를 판매합니다!",

    "끼룩제약": "신기한 약을 판매하는 회사입니다. 동물에게 약을 먹이면 사람말을 한다던가, "
              "물 속에서 숨쉴수 있는 약을 개발해서 화제입니다!",

    "날틀식품": "냉동식품을 생산하고 판매하는 회사입니다. 그만 쫌 꼴아박아라.....",

    "오십만통신": "통신계의 왕입니다. 경쟁자가 없어서 모든 통신사업을 꽉쥐고 있습니다..... "
               "빨리 경쟁자가 나와야하는데....."
}


class StockInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="종목소개", aliases=["주식정보", "주식설명"])
    async def stock_info(self, ctx, *, stock_name: str = None):
        """
        #종목소개: 전체 주식 목록을 보여줍니다.
        #종목소개 [종목명]: 특정 주식 종목에 대한 정보를 확인합니다.
        """
        if stock_name:
            stock_data = STOCK_INFO.get(stock_name)
            if stock_data:
                embed = discord.Embed(
                    title=f"📈 {stock_name} 종목 정보",
                    description=stock_data,
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ 존재하지 않는 주식 종목입니다. `#종목소개`로 전체 목록을 확인하세요.")
        else:
            embed = discord.Embed(
                title="📊 주식 종목 목록",
                description="아래 종목 중 하나를 선택하여 `#종목소개 [종목명]`으로 상세 정보를 확인하세요.",
                color=discord.Color.green()
            )
            stock_list = "\n".join([f"📌 {name}" for name in STOCK_INFO.keys()])
            embed.add_field(name="📢 현재 종목", value=stock_list, inline=False)

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StockInfo(bot))

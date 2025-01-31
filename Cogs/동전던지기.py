import discord
from discord.ext import commands
import random
import asyncio

class CoinFlip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="동전던지기", aliases=["동전"])
    async def coin_flip(self, ctx, flips: str = "1"):
        """
        동전 던지기를 합니다. 뒤에 숫자를 입력하면 그 횟수만큼 던져줍니다.
        최대 10번까지 던질 수 있습니다.
        1% 확률로 옆면이 나올 수도 있습니다.
        """
        # 입력된 값이 숫자인지 체크
        if not flips.isdigit():
            await ctx.send("숫자만 입력해주세요! 예: `#동전던지기 5`")
            return
        
        flips = int(flips)  # 숫자로 변환

        if flips < 1 or flips > 10:
            await ctx.send("1번에서 10번 사이의 숫자만 입력할 수 있습니다.")
            return
        
        # 동전을 던집니다... 메시지 한 번만 출력
        await ctx.send("동전을 던집니다... 잠시만 기다려 주세요! ⏳")
        
        # 결과를 저장할 리스트
        results = []
        heads_count = 0
        tails_count = 0
        side_count = 0  # 옆면 나오는 횟수

        # 여러 번 던지기
        for _ in range(flips):
            # 1% 확률로 '옆면'이 나올 수도 있음
            if random.random() < 0.01:  # 1% 확률
                result = "놀랍게도 옆면으로 세워버렸습니다.... 😱"
                side_count += 1
            else:
                result = random.choice(["앞면", "뒷면"])
                if result == "앞면":
                    heads_count += 1
                elif result == "뒷면":
                    tails_count += 1

            # 결과 리스트에 추가
            results.append(result)
        
        # 2초 뒤에 한 번에 결과 출력
        await asyncio.sleep(2)  # 2초 대기

        # 종합 결과
        summary = f"\n앞면: {heads_count}번\n뒷면: {tails_count}번"

        # 옆면이 나왔다면 종합 결과에 추가
        if side_count > 0:
            summary += f"\n\n**놀랍게도 옆면이 {side_count}번 나왔습니다! 😱**"

        # 결과 출력
        embed = discord.Embed(
            title="**결과는!**",  # 큰 제목
            description="\n".join(results),  # 동전 던진 결과
            color=discord.Color.blue()
        )
        embed.add_field(name="종합 결과", value=summary, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))

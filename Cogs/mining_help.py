import discord
from discord.ext import commands

class MiningHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="광산", aliases=["광산도움말"])
    async def mining_help(self, ctx):
        embed = discord.Embed(
            title="광산 시스템 도움말",
            description="아래 명령어들을 통해 광산 게임을 즐길 수 있습니다.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="#광산시작 [닉네임]",
            value="광산 게임을 시작합니다. 닉네임은 빈칸이나 중복 없이 입력해야 합니다.",
            inline=False
        )
        embed.add_field(
            name="#광산프로필",
            value="자신의 프로필(유저 레벨, 장비, 보유 루찌, 인벤토리, 경험치 등)을 확인합니다.",
            inline=False
        )
        embed.add_field(
            name="#광산입장 [광산이름]",
            value="특정 광산에 입장하여 연속 채취 세션을 시작합니다.",
            inline=False
        )
        embed.add_field(
            name="#광산중지",
            value="진행 중인 채취 세션을 중지하고, 지금까지의 채취 결과를 표시합니다.",
            inline=False
        )
        embed.add_field(
            name="#광산결과",
            value="진행 중인 채취 세션의 누적 시간, 다음 광물 드랍까지 남은 시간, 획득 경험치, 획득 광물 목록을 확인합니다.",
            inline=False
        )
        embed.add_field(
            name="#광물판매 [광물이름] [수량]",
            value="보유한 광물을 판매하여 루찌를 획득합니다.",
            inline=False
        )
        embed.add_field(
            name="#장비강화",
            value="현재 장비의 강화를 시도합니다. (최대 Lv.20, Lv.11 이상부터 강화 실패 시 하락 확률 발생)",
            inline=False
        )
        embed.add_field(
            name="#인벤토리",
            value="현재 보유한 광물 및 인벤토리 용량을 확인합니다.",
            inline=False
        )
        embed.add_field(
            name="#인벤토리증가",
            value="루찌를 사용해 인벤토리 용량을 증가시킵니다. (최대 30까지)",
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MiningHelp(bot))

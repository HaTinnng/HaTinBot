import discord
from discord.ext import commands

class BombGameHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="폭탄게임도움말", aliases=["폭탄게임도움", "폭탄게임안내","폭탄게임이란"], help="폭탄게임에 대한 도움말을 제공합니다.")
    async def bomb_game_help(self, ctx):
        # 임베드 메시지 생성
        embed = discord.Embed(
            title="💣 ***폭탄게임 도움말*** 💣",
            description="폭탄게임에 대한 규칙과 참여 방법을 안내합니다.",
            color=discord.Color.blurple()  # 임베드 색상 설정 (블루)
        )

        embed.add_field(
            name="1. 게임 시작",
            value=(
                "`#폭탄게임 [버튼 개수]` 명령어로 게임을 시작할 수 있습니다.\n"
                "버튼 개수는 최소 2개, 최대 20개까지 가능합니다."
            ),
            inline=False
        )

        embed.add_field(
            name="2. 게임 규칙",
            value=(
                "게임 최소 참여인원은 1명입니다.\n"
                "게임은 참여자가 차례대로 버튼을 눌러 폭탄을 피하는 게임입니다.\n"
                "한 명이라도 폭탄을 누르면 게임이 종료됩니다."
            ),
            inline=False
        )

        embed.add_field(
            name="3. 참여하기",
            value=(
                "`참여하기` 버튼을 눌러 게임에 참가할 수 있습니다.\n"
                "이미 참가한 사람은 다시 참가할 수 없습니다.\n"
                "방장은 자동으로 참여하여 참여하기 버튼을 눌러야 할 필요가 없습니다."
            ),
            inline=False
        )

        embed.add_field(
            name="4. 게임 진행",
            value=(
                "게임은 차례대로 진행되며, 각 플레이어가 버튼을 누를 때마다 안전한지 폭탄인지 확인합니다.\n"
                "플레이어가 30초 이상 버튼을 누르지 않으면 패배합니다."
            ),
            inline=False
        )

        embed.add_field(
            name="5. 그만두기",
            value=(
                "방장만 `그만두기` 버튼을 눌러 게임을 종료할 수 있습니다.\n"
                "그만두면 방은 폭파되며 인원은 해산이 됩니다."
            ),
            inline=False
        )

        embed.add_field(
            name="6. 주의",
            value=(
                "폭탄게임은 타이머가 동작하며, 게임 진행 중 3분 동안 시작되지 않으면 자동으로 해산됩니다.\n"
                "게임 도중 30초 이상 버튼을 누르지 않으면 패배로 처리됩니다. 30초 되기 10초 전 경고 메시지가 알림됩니다."
            ),
            inline=False
        )

        embed.add_field(
            name="7. 추가사항",
            value=(
                "실시간으로 현재 인원 상황을 볼 수 있으며 방장이 누구인지 알 수 있습니다.\n"
                "`전체 인원 보기`를 누르면 현재 참가하고 있는 인원을 볼 수 있습니다."
            ),
            inline=False
        )

        # 임베드를 전송
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BombGameHelp(bot))

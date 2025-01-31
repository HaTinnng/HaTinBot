import discord
from discord.ext import commands

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="청소", help="입력한 숫자만큼 최근 메시지를 삭제합니다.")
    @commands.has_permissions(manage_messages=True)  # 메시지를 관리할 권한이 있는 사용자만 사용 가능
    async def clear(self, ctx, amount: int):
        """최근 메시지 삭제"""
        if amount <= 0:
            await ctx.send("⚠️ 삭제할 메시지 수는 1개 이상이어야 합니다.")
            return

        # 최대 삭제 가능한 메시지 수는 100개로 제한
        if amount > 100:
            await ctx.send("⚠️ 한 번에 최대 100개의 메시지만 삭제할 수 있습니다.")
            return

        deleted = await ctx.channel.purge(limit=amount + 1)  # '청소' 명령어 메시지까지 포함해 삭제하기 위해 +1
        await ctx.send(f"✅ {len(deleted) - 1}개의 메시지를 삭제했습니다.", delete_after=5)  # '청소' 메시지 제외 후 출력

    @clear.error
    async def clear_error(self, ctx, error):
        """명령어 오류 처리"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 이 명령어를 사용하려면 '메시지 관리' 권한이 필요합니다.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ 삭제할 메시지 수는 숫자로 입력해야 합니다.")
        else:
            await ctx.send("❌ 명령어 실행 중 오류가 발생했습니다.")

async def setup(bot):
    await bot.add_cog(Clear(bot))

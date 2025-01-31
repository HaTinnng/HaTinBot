from discord.ext import commands

class Hello(commands.Cog):
    """안녕 명령어를 처리하는 Cog"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="안녕")
    async def hello(self, ctx):
        """#안녕 입력 시 인사 메시지 출력"""
        await ctx.send(f"👋 안녕하세요, {ctx.author.name}님!")

    @commands.command(name="아이프라")
    async def hello(self, ctx):
        """#안녕 입력 시 인사 메시지 출력"""
        await ctx.send(f"아이프라하자!")    

async def setup(bot):
    await bot.add_cog(Hello(bot))  # ✅ Cog 등록 (await 필수)

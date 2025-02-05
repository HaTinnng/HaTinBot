import discord
from discord.ext import commands
from pymongo import MongoClient
import os

# MongoDB 연결 (환경변수 MONGODB_URI 사용)
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = "stock_game"

class UserReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]

    @commands.command(name="유저초기화", aliases=["초기화유저"])
    @commands.has_permissions(administrator=True)  # 관리자 권한 필요
    async def reset_user(self, ctx, *, nickname: str = None):
        """
        #유저초기화 [닉네임]: 특정 유저의 데이터를 완전히 삭제합니다.
        해당 유저는 다시 #주식참가를 해야 주식 게임에 참여할 수 있습니다.
        """
        if not nickname:
            await ctx.send("❌ 닉네임을 입력해주세요! `#유저초기화 [닉네임]`")
            return

        # 유저 데이터 조회 (닉네임 기준)
        user_data = self.db.users.find_one({"nickname": nickname})

        if not user_data:
            await ctx.send(f"❌ `{nickname}` 닉네임을 가진 유저가 존재하지 않습니다.")
            return

        # 유저 데이터 삭제
        self.db.users.delete_one({"_id": user_data["_id"]})
        await ctx.send(f"✅ `{nickname}` 유저의 데이터가 초기화되었습니다. 다시 `#주식참가`를 해야 합니다.")

    @reset_user.error
    async def reset_user_error(self, ctx, error):
        """ 명령어 오류 처리 (권한 부족 시) """
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 관리자 권한이 필요합니다!")
        else:
            await ctx.send(f"❌ 오류 발생: {error}")

async def setup(bot):
    await bot.add_cog(UserReset(bot))
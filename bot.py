import importlib
import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="#", intents=intents)

async def load_extensions():
    """Cogs 폴더 내의 모든 확장을 로드"""
    for filename in os.listdir("Cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await bot.load_extension(f"Cogs.{filename[:-3]}")
                print(f"✅ {filename} 로드 성공")
            except Exception as e:
                print(f"❌ {filename} 로드 실패: {e}")

@bot.command(name="리로드")
@commands.is_owner()  # 봇 소유자만 실행 가능
async def reload_cogs(ctx, cog_name: str = None):
    """Cog를 강제로 리로드하는 명령어 (Python 캐싱 문제 해결)"""
    if cog_name is None:
        # 모든 Cogs 리로드
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                cog_path = f"Cogs.{filename[:-3]}"
                try:
                    await bot.unload_extension(cog_path)  # ✅ 기존 Cog 언로드
                    importlib.reload(importlib.import_module(cog_path))  # ✅ 강제 리로드
                    await bot.load_extension(cog_path)  # ✅ 다시 로드
                    await ctx.send(f"🔄 `{filename}` 리로드 완료!")
                except Exception as e:
                    await ctx.send(f"❌ `{filename}` 리로드 실패: {e}")
        return
    
    # 특정 Cog 리로드
    cog_path = f"Cogs.{cog_name}"
    try:
        await bot.unload_extension(cog_path)  # ✅ 기존 Cog 언로드
        importlib.reload(importlib.import_module(cog_path))  # ✅ 강제 리로드
        await bot.load_extension(cog_path)  # ✅ 다시 로드
        await ctx.send(f"🔄 `{cog_name}.py` 리로드 완료!")
    except Exception as e:
        await ctx.send(f"❌ `{cog_name}.py` 리로드 실패: {e}")

@bot.command(name="로드")
@commands.is_owner()  # 봇 소유자만 실행 가능
async def load_new_cogs(ctx):
    """
    새로운 Cog 파일을 자동으로 불러오는 명령어
    """
    loaded_count = 0
    for filename in os.listdir("Cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            cog_path = f"Cogs.{filename[:-3]}"
            if cog_path not in bot.extensions:  # 새로운 파일만 로드
                try:
                    await bot.load_extension(cog_path)
                    await ctx.send(f"✅ `{filename}` 추가 완료!")
                    loaded_count += 1
                except Exception as e:
                    await ctx.send(f"❌ `{filename}` 추가 실패: {e}")
    
    if loaded_count == 0:
        await ctx.send("⚠️ 새로운 파일이 없습니다!") 

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    # 봇의 상태를 "온라인"으로 설정하고, 활동을 "폭탄 게임 중!"으로 설정
    game = discord.Game("폭탄 게임 중!")  # 활동 설정
    await bot.change_presence(status=discord.Status.online, activity=game)

async def main():
    await load_extensions()
    bot_token = os.getenv("DISCORD_TOKEN")  # ✅ 환경변수에서 토큰 가져오기
    if not bot_token:
        print("❌ [오류] 환경변수 DISCORD_TOKEN이 설정되지 않았습니다.")
        return
    await bot.start(bot_token)

# 봇 실행
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())  # ✅ 클라우드타입 환경에서 실행 가능하도록 변경

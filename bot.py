import importlib
import os
import discord
from discord.ext import commands
import asyncio
import motor.motor_asyncio  # 비동기 MongoDB 드라이버 motor

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="#", intents=intents)

# MongoDB 연결 설정
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    print("❌ MongoDB URI가 설정되지 않았습니다. 환경변수 MONGODB_URI를 설정해주세요.")
    exit(1)
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = mongo_client["discordbot"]  # 사용할 데이터베이스 이름 (원하는 이름으로 변경 가능)

async def load_disabled_cogs():
    """MongoDB에서 비활성화된 Cog 목록을 불러옵니다."""
    config = await db.config.find_one({"_id": "disabled_cogs"})
    if config and "cogs" in config:
        return config["cogs"]
    return []

async def save_disabled_cogs(disabled_cogs):
    """MongoDB에 비활성화된 Cog 목록을 저장합니다."""
    await db.config.update_one(
        {"_id": "disabled_cogs"},
        {"$set": {"cogs": disabled_cogs}},
        upsert=True
    )

async def load_extensions():
    """Cogs 폴더 내의 모든 확장을 로드합니다 (MongoDB에 기록된 비활성화된 Cog는 제외)."""
    disabled_cogs = await load_disabled_cogs()
    
    for filename in os.listdir("Cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            cog_name = filename[:-3]  # 파일 확장자(.py) 제거한 이름
            
            if cog_name in disabled_cogs:
                print(f"⏸️ {cog_name}.py 비활성화됨 (로드되지 않음)")
                continue  # 비활성화된 파일은 로드하지 않음
            
            try:
                await bot.load_extension(f"Cogs.{cog_name}")
                print(f"✅ {cog_name}.py 로드 성공")
            except Exception as e:
                print(f"❌ {cog_name}.py 로드 실패: {e}")

@bot.command(name="비활성화")
@commands.is_owner()
async def disable_cog(ctx, cog_name: str):
    """특정 Cog 파일을 즉시 비활성화합니다 (봇 소유자 전용)."""
    disabled_cogs = await load_disabled_cogs()

    if cog_name not in disabled_cogs:
        disabled_cogs.append(cog_name)
        await save_disabled_cogs(disabled_cogs)

        try:
            await bot.unload_extension(f"Cogs.{cog_name}")
            await ctx.send(f"⏸️ `{cog_name}.py` 즉시 비활성화되었습니다.")
        except Exception as e:
            await ctx.send(f"⚠️ `{cog_name}.py` 비활성화 실패: {e}")
    else:
        await ctx.send(f"⚠️ `{cog_name}.py`는 이미 비활성화 상태입니다.")

@bot.command(name="활성화")
@commands.is_owner()
async def enable_cog(ctx, cog_name: str):
    """특정 Cog 파일을 즉시 활성화합니다 (봇 소유자 전용)."""
    disabled_cogs = await load_disabled_cogs()

    if cog_name in disabled_cogs:
        disabled_cogs.remove(cog_name)
        await save_disabled_cogs(disabled_cogs)

        try:
            await bot.load_extension(f"Cogs.{cog_name}")
            await ctx.send(f"✅ `{cog_name}.py` 즉시 활성화되었습니다.")
        except Exception as e:
            await ctx.send(f"⚠️ `{cog_name}.py` 활성화 실패: {e}")
    else:
        await ctx.send(f"⚠️ `{cog_name}.py`는 이미 활성화 상태입니다.")

@bot.command(name="리로드")
@commands.is_owner()  # 봇 소유자만 실행 가능
async def reload_cogs(ctx, cog_name: str = None):
    """Cog를 강제로 리로드하는 명령어 (중복 로드 방지)"""
    if cog_name is None:
        # 모든 Cogs 리로드
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                cog_path = f"Cogs.{filename[:-3]}"
                try:
                    if cog_path in bot.extensions:  # 이미 로드된 경우 언로드 후 로드
                        await bot.unload_extension(cog_path)
                    await bot.load_extension(cog_path)  # 다시 로드
                    await ctx.send(f"🔄 `{filename}` 리로드 완료!")
                except Exception as e:
                    await ctx.send(f"❌ `{filename}` 리로드 실패: {e}")
        return
    
    # 특정 Cog 리로드
    cog_path = f"Cogs.{cog_name}"
    try:
        if cog_path in bot.extensions:  # 이미 로드된 경우 언로드 후 로드
            await bot.unload_extension(cog_path)
        await bot.load_extension(cog_path)  # 다시 로드
        await ctx.send(f"🔄 `{cog_name}.py` 리로드 완료!")
    except Exception as e:
        await ctx.send(f"❌ `{cog_name}.py` 리로드 실패: {e}")

@bot.command(name="로드")
@commands.is_owner()  # 봇 소유자만 실행 가능
async def load_new_cogs(ctx):
    """
    새로운 Cog 파일을 자동으로 불러오는 명령어 (중복 로드 방지)
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
    game = discord.Game("폭탄게임")
    await bot.change_presence(status=discord.Status.online, activity=game)

@bot.event
async def on_command_error(ctx, error):
    """소유자가 아닌 사용자가 명령어를 사용하려 할 때 오류 메시지 출력"""
    if isinstance(error, commands.NotOwner):
        await ctx.send("⛔ **이 명령어는 봇 소유자만 사용할 수 있습니다.**")
    else:
        raise error  # 다른 오류는 그대로 출력

async def main():
    await load_extensions()
    bot_token = os.getenv("DISCORD_TOKEN")
    if not bot_token:
        print("❌ [오류] 환경변수 DISCORD_TOKEN이 설정되지 않았습니다.")
        return
    await bot.start(bot_token)

if __name__ == "__main__":
    asyncio.run(main())


import importlib
import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="#", intents=intents)

DISABLED_COGS_FILE = "Cogs/disabled_cogs.txt"

def load_disabled_cogs():
    """비활성화된 파일 목록을 불러오기"""
    try:
        with open(DISABLED_COGS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return []

def save_disabled_cogs(disabled_cogs):
    """비활성화된 파일 목록을 저장"""
    with open(DISABLED_COGS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(disabled_cogs))

async def load_extensions():
    """Cogs 폴더 내의 모든 확장을 로드 (비활성화된 파일 제외)"""
    disabled_cogs = load_disabled_cogs()
    
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
    """특정 Cog 파일을 비활성화"""
    disabled_cogs = load_disabled_cogs()

    if cog_name not in disabled_cogs:
        disabled_cogs.append(cog_name)
        save_disabled_cogs(disabled_cogs)
        await ctx.send(f"⏸️ `{cog_name}.py` 비활성화되었습니다. 봇을 재시작하면 적용됩니다.")
    else:
        await ctx.send(f"⚠️ `{cog_name}.py`는 이미 비활성화 상태입니다.")

@bot.command(name="활성화")
@commands.is_owner()
async def enable_cog(ctx, cog_name: str):
    """특정 Cog 파일을 활성화"""
    disabled_cogs = load_disabled_cogs()

    if cog_name in disabled_cogs:
        disabled_cogs.remove(cog_name)
        save_disabled_cogs(disabled_cogs)
        await ctx.send(f"✅ `{cog_name}.py` 활성화되었습니다. 봇을 재시작하면 적용됩니다.")
    else:
        await ctx.send(f"⚠️ `{cog_name}.py`는 이미 활성화 상태입니다.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    game = discord.Game("봇 기능 실행 중!")
    await bot.change_presence(status=discord.Status.online, activity=game)

async def main():
    await load_extensions()
    bot_token = os.getenv("DISCORD_TOKEN")
    if not bot_token:
        print("❌ [오류] 환경변수 DISCORD_TOKEN이 설정되지 않았습니다.")
        return
    await bot.start(bot_token)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

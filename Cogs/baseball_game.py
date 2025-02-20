import discord
from discord.ext import commands
import random
import asyncio

class BaseballGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="야구게임")
    async def start_baseball_game(self, ctx, digits: int = 4):
        """
        #야구게임 [자릿수]: 컴퓨터가 랜덤으로 만든 숫자를 맞추는 야구 게임을 시작합니다.
        자릿수는 2부터 5까지 선택 가능 (기본값은 4자리).
        """
        # 자릿수 유효성 검사
        if digits < 2 or digits > 5:
            await ctx.send("⚠️ 게임 자릿수는 2부터 5까지 가능합니다. 기본값인 4자리로 진행합니다.")
            digits = 4

        # 0~9까지 숫자 중 랜덤으로 digits자리 숫자 생성 (중복 가능, 앞자리가 0이어도 상관없음)
        secret_number = ''.join(str(random.randint(0, 9)) for _ in range(digits))
        attempts = 0

        await ctx.send(f"🔢 **숫자 야구 게임**을 시작합니다!\n**{digits}자리 숫자**를 맞춰보세요.\n(게임 중단: `#야구게임그만` 입력)")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        while True:
            try:
                message = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ 시간 초과! 게임을 종료합니다. 정답은 `{secret_number}`였습니다.")
                break

            guess = message.content.strip()

            # 게임 중단 명령어 처리
            if guess == "#야구게임그만":
                await ctx.send(f"🚪 게임 종료! 정답은 `{secret_number}`였습니다.")
                break

            if not guess.isdigit() or len(guess) != digits:
                await ctx.send(f"🚫 {digits}자리 숫자를 정확히 입력해주세요.")
                continue

            attempts += 1

            # 스트라이크, 볼, 아웃 계산
            strikes = 0
            balls = 0
            for i in range(digits):
                if guess[i] == secret_number[i]:
                    strikes += 1
                elif guess[i] in secret_number:
                    balls += 1

            outs = digits - (strikes + balls)

            if strikes == digits:
                await ctx.send(f"🎉 **홈런!** 🎉\n{attempts}번 만에 정답을 맞추셨습니다!")
                break
            else:
                result_message = (
                    f"🎯 **스트라이크:** {strikes}\n"
                    f"🔄 **볼:** {balls}\n"
                    f"❌ **아웃:** {outs}"
                )
                await ctx.send(result_message)

    @commands.command(name="야구")
    async def baseball_help(self, ctx):
        """
        #야구: 숫자 야구 게임에 대한 도움말을 출력합니다.
        """
        help_text = (
            "🔢 **숫자 야구 게임 도움말** 🔢\n\n"
            "컴퓨터가 랜덤으로 생성한 숫자를 맞추는 게임입니다.\n\n"
            "**사용법:**\n"
            "• `#야구게임 [자릿수]` - 게임을 시작합니다. (자릿수는 2부터 5까지 선택 가능, 기본값은 4자리)\n"
            "  ex) `#야구게임 3` (3자리 게임 시작)\n"
            "• 게임 도중 `#야구게임그만`을 입력하면 게임을 종료할 수 있습니다.\n\n"
            "**게임 규칙:**\n"
            "• **스트라이크:** 숫자와 자리가 모두 일치할 경우\n"
            "• **볼:** 숫자는 맞지만 자리가 다를 경우\n"
            "• **아웃:** 해당 숫자가 전혀 없을 경우\n\n"
            "모든 숫자가 스트라이크이면 **홈런!**\n"
            "즐겁게 플레이하세요! 🎉"
        )
        await ctx.send(help_text)

async def setup(bot):
    await bot.add_cog(BaseballGame(bot))

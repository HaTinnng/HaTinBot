import random
from collections import Counter
from discord.ext import commands

class BaseballGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 채널별 게임 진행 상황을 저장하는 딕셔너리
        self.sessions = {}

    @commands.command(name="야구게임시작")
    async def start_game(self, ctx):
        """
        게임을 시작하고 해당 채널에 새로운 세션을 생성합니다.
        """
        # 0~9의 숫자 중 랜덤으로 4자리 숫자 생성 (동일 숫자 가능, 선행 0 가능)
        answer = ''.join(str(random.randint(0, 9)) for _ in range(4))
        self.sessions[ctx.channel.id] = {"answer": answer, "attempts": 0}
        await ctx.send("야구게임 시작! 4자리 숫자를 입력하세요. (종료하려면 `#야구게임그만` 입력)")

    @commands.command(name="야구게임")
    async def play_game(self, ctx, guess: str):
        """
        플레이어의 입력을 받아 결과를 출력합니다.
        """
        # 진행 중인 게임이 없으면 메시지 안내
        if ctx.channel.id not in self.sessions:
            await ctx.send("진행 중인 게임이 없습니다. 먼저 `야구게임시작` 명령어로 게임을 시작하세요.")
            return

        session = self.sessions[ctx.channel.id]

        # 게임 종료 입력 처리
        if guess == "#야구게임그만":
            answer = session["answer"]
            self.sessions.pop(ctx.channel.id)
            await ctx.send(f"게임 종료! 컴퓨터가 생각한 숫자는: {answer}")
            return

        # 입력이 4자리 숫자인지 검증
        if len(guess) != 4 or not guess.isdigit():
            await ctx.send("유효하지 않은 입력입니다. 4자리 숫자를 입력하세요.")
            return

        session["attempts"] += 1
        answer = session["answer"]

        # 홈런 조건: 입력한 숫자가 정답과 완전히 일치할 때
        if guess == answer:
            attempts = session["attempts"]
            self.sessions.pop(ctx.channel.id)
            await ctx.send(f"홈런! {attempts}번만에 맞추셨습니다!")
            return

        # 스트라이크와 볼 계산
        strikes = sum(1 for i in range(4) if guess[i] == answer[i])
        guess_count = Counter(guess)
        answer_count = Counter(answer)
        common = sum(min(guess_count[d], answer_count[d]) for d in guess_count)
        balls = common - strikes

        # 결과 메시지 구성 (아웃 처리 포함)
        if strikes == 0 and balls == 0:
            result = "아웃"
        else:
            parts = []
            if strikes:
                parts.append(f"{strikes} 스트라이크")
            if balls:
                parts.append(f"{balls} 볼")
            result = ", ".join(parts)

        await ctx.send(result)

def setup(bot):
    bot.add_cog(BaseballGame(bot))

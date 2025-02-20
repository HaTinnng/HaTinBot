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

    @commands.command(name="야구")
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

        # 스트라이크 계산: 같은 자리에서 동일한 숫자인 경우
        strikes = sum(1 for i in range(4) if guess[i] == answer[i])
        # 볼 계산: 두 문자열에 공통으로 등장하는 숫자의 최소 개수에서 스트라이크 수를 뺀 값
        guess_count = Counter(guess)
        answer_count = Counter(answer)
        common = sum(min(guess_count[d], answer_count[d]) for d in guess_count)
        balls = common - strikes

        # 아웃 계산: 4자리에서 스트라이크와 볼의 합을 뺀 값
        outs = 4 - (strikes + balls)

        # 결과 메시지를 각 항목별로 출력 (예: "1 스트라이크\n0 볼\n3 아웃")
        result_message = f"{strikes} 스트라이크\n{balls} 볼\n{outs} 아웃"
        await ctx.send(result_message)

async def setup(bot):
    await bot.add_cog(BaseballGame(bot))

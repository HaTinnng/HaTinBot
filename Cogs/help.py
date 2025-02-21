import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="도움", aliases=["도움말", "헬프", "메딕"])
    async def help_command(self, ctx):
        """
        봇의 도움말을 출력하는 명령어
        """
        help_text = """
        🎵 ***음악 봇 명령어 목록 (현재 사용금지!!!)*** 🎵 
        
        **#입장, #들어와** : 봇을 음성 채널에 연결합니다. (입장시켜야 노래가 재생됩니다!)
        **#추가, #재생, #p [제목], [URL]** : 플레이리스트에 곡을 추가합니다.
        **#목록, #리스트, #q** : 현재 플레이리스트를 확인합니다.
        **#삭제 [번호]** : 플레이리스트에서 특정 곡을 삭제합니다.
        **#스킵** : 현재 재생 중인 곡을 건너뛰고 다음 곡을 재생합니다.
        **#전체스킵** : 현재 재생 중인 곡과 대기열을 모두 스킵합니다.
        **#셔플, #랜덤** : 플레이리스트를 무작위로 섞습니다.
        **#멈춰, #나가, #그만** : 음악을 멈추고 음성 채널에서 봇을 퇴장시킵니다.

        ✏️ ***잡다한거!*** ✏️
        **#핑** : 핑을 알려줘요!
        **#안녕** : 인사해요!
        **시간 [나라 이름]** : 작성한 나라의 날짜와 시간을 알려줍니다.(나라가 많지 않습니다....)
        **초능력**: 당신의 숨겨진 초능력을 알려줍니다. 당신의 초능력은...?
        **날짜계산 숫자**: 현재 날짜에서 입력한 숫자의 날짜를 계산해서 알려줍니다.
        **랜덤이모지**: 서버의 이모지중 하나를 랜덤으로 출력합니다.
        **#오늘의운세, #오운, #운세**: 오늘의 운세를 한번 확인해봐요!
        **#오늘의음식, #오음, #음식추천, #추천음식: 오늘의 음식을 한번 확인해봐요!
        **#청소 숫자**: 숫자만큼 청소를 할 수 있어요! 봇메세지는 자동으로 지워줘요! (메세지 삭제 권한이 있는 사람만 이용 가능합니다.)

        🎾 ***재미난 게임!*** 🎾
        **#야바위** : 3개의 컵에서 1개의 공을 찾아보세요!
        **#똥피하기** : 똥이 떨어질것 같은 자리를 피해서 고르세요! 맞으면....
        **#폭탄게임** [전체버튼수] : 2~20개의 폭탄에서 단 하나 있는 폭탄! 1명이상 게임을 진행할 수 있습니다!
        **#폭탄게임(안내/도움/도움말/이란)**: 폭탄게임에 대한 자세한 설명을 볼 수 있습니다.
        **#블랙잭**: 블랙잭 게임을 할 수 있습니다. 딜러를 이겨보세요!
        **#가위바위보**: AI와 가위바위보를 합니다. 이길수 있을까요?
        **#업다운 숫자**: 1 ~ 입력한 숫자까지 AI가 하나를 선정해서 업다운게임을 합니다.
        **#주식**: 주식을 할 수 있어요! 주식에 대한 자세한 설명은 #주식도움말을 이용해주세요!
        **#주사위 n m**: 1에서 n까지의 수를 m개 뽑을 수 있어요! 
        **#동전(던지기) 숫자**: 숫자만큼 동전을 던져요!
        **#뽑기, #가챠**: 뽑기를 할 수 있어요! 1등을 뽑으면 당신은 럭키인!
        **#뽑기확률, #가챠확률**: 뽑기/가챠에 대한 확률을 공개합니다!
        **#룰렛 n**: 자신이 가지고 있는 돈을 가지고 룰렛을 돌려요! (#주식참가 필수!)
        **#복권**: 복권에 대한 도움말을 표시합니다.
        **#야구**: 야구게임에 대한 도움말을 표시합니다.
        **#광산**: 방치형게임인 광산시스템에 대한 도움말을 표시합니다.

        📄 ***정보*** 📄
        **#하틴봇**: 하틴봇에 대한 설명이 나와요!
        **#개발자**: 개발자에 대한 정보가 나와요!
        **#업데이트**: 최근 업데이트에 대한 내용과 계획하고 있는 내역을 볼 수 있어요!
        **#다음업데이트**: 다음 업데이트에 대한 내용을 볼 수 있습니다!
        """
        embed = discord.Embed(title="📜 도움말 (Help)", description=help_text, color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))

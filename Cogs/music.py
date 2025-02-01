import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random

# 유튜브 DL 옵션
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6로 인한 문제 방지
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = asyncio.Queue()
        self.is_playing = False
        self.current_song = None
        self.idle_timer_task = None

    async def play_next(self, ctx):
        if self.song_queue.empty():
            self.is_playing = False
            await ctx.send("🎵 플레이리스트의 모든 곡이 재생되었습니다.")
            return

        self.is_playing = True
        next_song = await self.song_queue.get()

        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_connected():
            await ctx.send("❌ 봇이 음성 채널에 연결되어 있지 않습니다.")
            return

        async with ctx.typing():
            player = await YTDLSource.from_url(next_song, loop=self.bot.loop, stream=True)
            self.current_song = player.title
            voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

        await ctx.send(f"🎶 재생 중: **{self.current_song}**")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        사용자의 음성 채널 상태가 변경될 때 실행됨.
        봇이 혼자 남으면 10초 후 자동으로 음성 채널에서 나갑니다.
        """
        voice_client = discord.utils.get(self.bot.voice_clients, guild=member.guild)

        if voice_client and voice_client.is_connected():
            if len(voice_client.channel.members) == 1:  # 봇만 남음
                await asyncio.sleep(10)  # 10초 대기
                if len(voice_client.channel.members) == 1:  # 여전히 봇만 있으면 퇴장
                    await voice_client.disconnect()
                    system_channel = member.guild.system_channel
                    if system_channel:
                        await system_channel.send(f"🛑 {voice_client.channel.name} 채널에 아무도 없어 자동으로 퇴장했습니다.")

    async def monitor_voice_activity(self, ctx, voice_client):
        """
        3분 동안 노래가 재생되지 않으면 봇이 자동으로 음성 채널에서 나감.
        2분이 지나면 경고 메시지를 출력함.
        """
        await asyncio.sleep(120)  # 2분 대기 (경고 메시지 출력)

        if voice_client.is_connected() and not voice_client.is_playing():
            await ctx.send("⚠️ 노래를 재생하지 않으면 **1분 뒤**에 봇이 자동으로 나갑니다!")

        await asyncio.sleep(60)  # 추가 1분 대기 (총 3분 경과)

        if voice_client.is_connected() and not voice_client.is_playing():
            await voice_client.disconnect()
            await ctx.send("⏳ 3분 동안 노래가 재생되지 않아 음성 채널을 떠났습니다.")

        self.idle_timer_task = None  # 타이머 리셋

    async def start_idle_timer(self, ctx, voice_client):
        """
        기존 타이머가 없을 경우 새로운 3분 타이머를 시작합니다.
        """
        if self.idle_timer_task is None:
            self.idle_timer_task = asyncio.create_task(self.monitor_voice_activity(ctx, voice_client))

    async def stop_idle_timer(self):
        """
        노래가 재생되거나 새로운 곡이 추가되었을 때 자동 퇴장 타이머를 취소합니다.
        """
        if self.idle_timer_task is not None:
            self.idle_timer_task.cancel()
            self.idle_timer_task = None  

    @commands.command(name="입장", help="음성 채널에 봇을 입장시킵니다. 사용법: #입장")
    async def join(self, ctx):
        if not ctx.author.voice:
            await ctx.send("❌ 먼저 음성 채널에 입장하세요.")
            return

        channel = ctx.author.voice.channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client is None:
            await channel.connect()
            await ctx.send(f"✅ 봇이 {channel.name} 채널에 입장했습니다.")
        else:
            await ctx.send("⚠️ 봇이 이미 음성 채널에 있습니다.")

    @commands.command(name="추가", aliases=["재생", "p"])
    async def add_to_queue(self, ctx, *, url: str):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_connected():
            await ctx.send("❌ 봇이 음성 채널에 연결되어 있지 않습니다.")
            return

        await self.song_queue.put(url)
        await ctx.send(f"✅ 플레이리스트에 추가되었습니다: {url}")

        # ✅ 자동 재생 기능 추가
        if not self.is_playing:  # 현재 재생 중이 아니면 즉시 재생
            await self.play_next(ctx)


    @commands.command(name="스킵", aliases=["넘겨"])
    async def skip(self, ctx):
        """
        현재 재생 중인 곡만 스킵하고, 다음 곡을 재생
        """
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ 현재 재생 중인 곡이 없습니다.")
            return

        voice_client.stop()  # 현재 곡 중지 → after 함수에 의해 다음 곡 자동 재생
        await ctx.send("⏭️ 현재 곡을 스킵했습니다!")

    @commands.command(name="전체스킵", aliases=["모두넘겨"])
    async def skip_all(self, ctx):
        """
        플레이리스트의 모든 곡을 스킵하고 현재 곡도 중지
        """
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ 현재 재생 중인 곡이 없습니다.")
            return

        # 전체 대기열 비우기
        self.song_queue._queue.clear()

        # 현재 곡 중지 → after 함수에 의해 다음 곡이 없음으로 플레이 종료
        voice_client.stop()
        await ctx.send("⏭️ 모든 곡을 스킵하고 재생을 중지했습니다!")

    @commands.command(name="목록", aliases=["리스트", "q"])
    async def show_queue(self, ctx):
        if self.song_queue.empty():
            await ctx.send("❌ 현재 플레이리스트에 곡이 없습니다.")
            return

        queue_list = list(self.song_queue._queue)
        playlist = "\n".join([f"{i+1}. {song}" for i, song in enumerate(queue_list)])
        await ctx.send(f"📜 **현재 플레이리스트:**\n```{playlist}```")

    @commands.command(name="멈춰", aliases=["그만", "나가"])
    async def stop(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.send("⏹️ 음악을 멈추고 봇이 퇴장했습니다.")
        else:
            await ctx.send("❌ 봇이 음성 채널에 있지 않습니다.")

    @commands.command(name="삭제", aliases=["제거"])
    async def remove_from_queue(self, ctx, index: int = None):
        """
        #삭제/제거 : 현재 플레이리스트를 보여주고, 삭제 방법을 안내
        #삭제/제거 [번호] : 해당 번호의 곡을 플레이리스트에서 삭제
        """
        if self.song_queue.empty():
            await ctx.send("❌ 플레이리스트가 비어 있습니다. 삭제할 곡이 없습니다.")
            return

        queue_list = list(self.song_queue._queue)  # 대기열을 리스트로 변환

        # 번호 없이 `#삭제`만 입력하면 플레이리스트를 보여주고 안내 메시지 출력
        if index is None:
            playlist = "\n".join([f"{i+1}. {song}" for i, song in enumerate(queue_list)])
            await ctx.send(f"📜 **현재 플레이리스트:**\n```{playlist}```\n"
                        "🎵 삭제하려면 `#삭제/제거 [번호]`를 입력하세요.")
            return
        
        # 번호 입력 시 유효성 검사
        if index < 1 or index > len(queue_list):
            await ctx.send(f"⚠️ 유효하지 않은 번호입니다. 1부터 {len(queue_list)} 사이의 숫자를 입력해주세요.")
            return

        # 선택한 곡 삭제
        removed_song = queue_list.pop(index - 1)  # 리스트에서 해당 항목 제거

        # 기존 대기열을 초기화하고 남은 곡을 다시 추가
        self.song_queue._queue.clear()
        for song in queue_list:
            await self.song_queue.put(song)

        await ctx.send(f"🗑️ 플레이리스트에서 삭제되었습니다: **{removed_song}**")

    @commands.command(name="셔플", aliases=["랜덤"])
    async def shuffle_queue(self, ctx):
        """
        #셔플 : 플레이리스트를 무작위로 섞음
        """
        if self.song_queue.empty():
            await ctx.send("❌ 플레이리스트가 비어 있습니다. 셔플할 곡이 없습니다.")
            return

        queue_list = list(self.song_queue._queue)  # asyncio.Queue의 내부 데이터를 리스트로 변환

        if len(queue_list) == 1:
            await ctx.send("⚠️ 플레이리스트가 1개밖에 없습니다! 셔플할 수 없습니다.")
            return
        
        random.shuffle(queue_list)  # 리스트를 무작위로 섞기

        # 기존 대기열 초기화 후 셔플된 곡을 다시 추가
        self.song_queue._queue.clear()  # 대기열 초기화
        for song in queue_list:
            await self.song_queue.put(song)  # 섞인 곡을 다시 대기열에 추가
        
        shuffled_playlist = "\n".join([f"{i+1}. {song}" for i, song in enumerate(queue_list)])    
        await ctx.send("🎵 플레이리스트가 무작위로 섞였습니다!")
        await ctx.send(f"🎵 현재 플레이리스트:\n```{shuffled_playlist}```") 

    @commands.command(name="현재곡")
    async def current_song(self, ctx):
        """현재 재생 중인 곡 정보를 보여주는 명령어"""
        channel_id = ctx.voice_client.channel.id if ctx.voice_client else None
        if channel_id and channel_id in self.song_queue:
            song_info = self.song_queue[channel_id]
            await ctx.send(f"🎶 현재 재생 중인 곡: **{song_info['title']}**")
        else:
            await ctx.send("🎵 현재 재생 중인 곡이 없습니다.") 

async def setup(bot):
    await bot.add_cog(Music(bot))

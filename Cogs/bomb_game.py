import discord
import random
from discord.ext import commands

class BombGame(discord.ui.View):
    def __init__(self, ctx, num_buttons, players):
        super().__init__()
        self.ctx = ctx
        self.num_buttons = num_buttons
        self.players = players
        self.current_turn = 0  # 현재 턴 (순서)
        self.bomb_position = random.randint(1, num_buttons)  # 랜덤 폭탄 위치
        self.create_buttons()
        self.timeout_task = self.ctx.bot.loop.create_task(self.start_timeout_timer())

    async def start_timeout_timer(self):
        await asyncio.sleep(30)
        if self.ctx and self.players:
            loser = self.players[self.current_turn]
            await self.ctx.send(f"⏳ {loser.mention}님이 30초 동안 버튼을 누르지 않아 패배했습니다! 게임 종료! 💥")
            self.stop()

    def reset_timeout_timer(self):
        if self.timeout_task:
            self.timeout_task.cancel()
        self.timeout_task = self.ctx.bot.loop.create_task(self.start_timeout_timer())
    def __init__(self, ctx, num_buttons, players):
        super().__init__()
        self.ctx = ctx
        self.num_buttons = num_buttons
        self.players = players
        self.current_turn = 0  # 현재 턴 (순서)
        self.bomb_position = random.randint(1, num_buttons)  # 랜덤 폭탄 위치
        self.create_buttons()
        self.timeout_task = self.ctx.bot.loop.create_task(self.start_timeout_timer())
    def __init__(self, ctx, num_buttons, players):
        super().__init__()
        self.ctx = ctx
        self.num_buttons = num_buttons
        self.players = players
        self.current_turn = 0  # 현재 턴 (순서)
        self.bomb_position = random.randint(1, num_buttons)  # 랜덤 폭탄 위치
        self.create_buttons()

    def create_buttons(self):
        """동적으로 n개의 버튼을 생성"""
        for i in range(1, self.num_buttons + 1):
            button = discord.ui.Button(label=f"{i}번", style=discord.ButtonStyle.primary)
            button.callback = self.make_callback(i)  # 버튼 클릭 이벤트 설정
            self.add_item(button)

    def make_callback(self, position: int):
        self.reset_timeout_timer()
        """각 버튼에 개별 이벤트 추가"""
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.players[self.current_turn]:  # 본인 차례인지 확인
                await interaction.response.send_message("🚫 지금은 당신의 턴이 아닙니다!", ephemeral=True)
                return

            button = self.children[position - 1]  # 눌린 버튼 객체

            # 폭탄을 눌렀다면 게임 종료
            if position == self.bomb_position:
                await interaction.response.send_message(f"💥 {interaction.user.mention}님이 폭탄을 눌렀습니다! 게임 종료! 💣", ephemeral=False)
                button.style = discord.ButtonStyle.danger  # 폭탄 버튼을 붉은 색으로 표시
                button.disabled = True  # 폭탄 버튼 비활성화
                await interaction.message.edit(view=self)
            else:
                await interaction.response.send_message(f"✅ {interaction.user.mention}님, 안전합니다! 😌", ephemeral=True)
                self.current_turn = (self.current_turn + 1) % len(self.players)  # 다음 턴으로 이동
                button.disabled = True  # 선택된 안전 버튼을 비활성화

            # 차례를 표시하는 메시지 업데이트
            await self.update_turn_message(interaction.message)

        return callback

    async def update_turn_message(self, message):
        self.reset_timeout_timer()
        current_player = self.players[self.current_turn]
        new_content = f"💣 **폭탄 게임 시작!**
현재 차례: {current_player.mention}
순서대로 버튼을 눌러주세요!"
        await message.edit(content=new_content)
        self.reset_timeout_timer()
        """현재 차례인 플레이어를 메시지에 표시"""
        current_player = self.players[self.current_turn]
        new_content = f"💣 **폭탄 게임 시작!**\n현재 차례: {current_player.mention}\n순서대로 버튼을 눌러주세요!"
        await message.edit(content=new_content)

class BombGameLobby(discord.ui.View):
    def __init__(self, ctx, num_buttons):
        super().__init__()
        self.ctx = ctx
        self.num_buttons = num_buttons
        self.players = [ctx.author]  # 방장은 자동 참가
        self.timeout_task = self.ctx.bot.loop.create_task(self.start_timeout_timer())

    async def start_timeout_timer(self):
        await asyncio.sleep(120)  # 2분 대기
        if self.ctx and self.players:
            await self.ctx.send("⏳ 2분 동안 게임이 시작되지 않아 방이 자동 삭제되었습니다! 🛑")
            self.stop()

    def reset_timeout_timer(self):
        if self.timeout_task:
            self.timeout_task.cancel()
        self.timeout_task = self.ctx.bot.loop.create_task(self.start_timeout_timer())
    def __init__(self, ctx, num_buttons):
        super().__init__()
        self.ctx = ctx
        self.num_buttons = num_buttons
        self.players = [ctx.author]  # 방장은 자동 참가
        self.timeout_task = self.ctx.bot.loop.create_task(self.start_timeout_timer())
    def __init__(self, ctx, num_buttons):
        super().__init__()
        self.ctx = ctx
        self.num_buttons = num_buttons
        self.players = [ctx.author]  # 방장은 자동 참가
    def __init__(self, ctx, num_buttons):
        super().__init__()
        self.ctx = ctx
        self.num_buttons = num_buttons
        self.players = [ctx.author]  # 방장은 자동 참가

        # ✅ 실시간 참여 인원 버튼 (이름 없이 숫자만 표시)
        self.participants_button = discord.ui.Button(label=f"참여 인원: 1명 | 방장: {ctx.author.name}", style=discord.ButtonStyle.secondary, disabled=True)
        self.add_item(self.participants_button)

        # ✅ 전체 인원 보기 버튼 추가
        self.view_participants_button = discord.ui.Button(label="전체 인원 보기", style=discord.ButtonStyle.primary)
        self.view_participants_button.callback = self.show_participants  # 버튼 클릭 시 실행될 함수 설정
        self.add_item(self.view_participants_button)

        # ✅ 그만두기 버튼 추가 (방장: 방 삭제, 참가자: 게임 나가기)
        self.quit_button = discord.ui.Button(label="그만두기", style=discord.ButtonStyle.danger)
        self.quit_button.callback = self.quit_game  # 버튼 클릭 시 실행될 함수 설정
        self.add_item(self.quit_button)

        # ✅ 참가하기 버튼 추가
        self.join_button = discord.ui.Button(label="참가하기", style=discord.ButtonStyle.success)
        self.join_button.callback = self.join_game  # 버튼 클릭 시 실행될 함수 설정
        self.add_item(self.join_button)

        # ✅ 시작하기 버튼 추가 (방장만 가능)
        self.start_button = discord.ui.Button(label="시작하기", style=discord.ButtonStyle.primary)
        self.start_button.callback = self.start_game  # 버튼 클릭 시 실행될 함수 설정
        self.add_item(self.start_button)

    async def update_participants(self, message):
        self.reset_timeout_timer()
        """참여 인원 버튼 업데이트 (이름 없이 숫자만 표시)"""
        self.participants_button.label = f"참여 인원: {len(self.players)}명 | 방장: {self.ctx.author.name}"
        await message.edit(view=self)

    async def show_participants(self, interaction: discord.Interaction):
        """전체 인원 보기 버튼 클릭 시"""
        participants_list = "\n".join([f"- {p.name}" for p in self.players])
        await interaction.response.send_message(f"🎮 **현재 참여 인원:**\n{participants_list}", ephemeral=True)

    async def join_game(self, interaction: discord.Interaction):
        """참가하기 버튼 클릭 시"""
        if interaction.user in self.players:
            await interaction.response.send_message("✅ 이미 게임에 참가했습니다!", ephemeral=True)
        else:
            self.players.append(interaction.user)
            await interaction.response.send_message(f"🎮 {interaction.user.mention}님이 게임에 참여했습니다!", ephemeral=False)
            await self.update_participants(interaction.message)

    async def start_game(self, interaction: discord.Interaction):
        self.timeout_task.cancel()
        """방장만 게임 시작 가능"""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("🚫 방장만 게임을 시작할 수 있습니다!", ephemeral=True)
            return

        if len(self.players) < 1:
            await interaction.response.send_message("⚠️ 최소 1명이 필요합니다!", ephemeral=True)
            return

        await interaction.response.send_message("🎲 게임이 시작됩니다!", ephemeral=False)
        view = BombGame(ctx=self.ctx, num_buttons=self.num_buttons, players=self.players)
        message = await interaction.message.edit(content="💣 **폭탄 게임 시작!** /n순서대로 버튼을 눌러주세요!", view=view)
        await view.update_turn_message(message)

    async def quit_game(self, interaction: discord.Interaction):
        """그만두기 버튼 클릭 시"""
        if interaction.user == self.ctx.author:
            # 방장이 나가면 방 삭제 (게임 종료)
            await interaction.response.send_message("⚠️ 게임이 종료되었습니다! 방장이 게임을 그만두었습니다.", ephemeral=False)
            await interaction.message.delete()
        elif interaction.user in self.players:
            # 참가자가 나가면 리스트에서 제거
            self.players.remove(interaction.user)
            await interaction.response.send_message(f"🚪 {interaction.user.mention}님이 게임에서 나갔습니다.", ephemeral=False)
            await self.update_participants(interaction.message)

            # 모든 참가자가 나가면 방 자동 삭제
            if len(self.players) == 0:
                await interaction.message.delete()

class Bomb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="폭탄게임")
    async def bomb_game(self, ctx, num_buttons: int = None):
        """폭탄 게임 시작 (기본 3개 버튼)"""
        if num_buttons is None:
            await ctx.send("⚠️ 사용법: `#폭탄게임 [버튼 개수]` (최소 2, 최대 20)")
            return

        if num_buttons < 2 or num_buttons > 20:  # 버튼 개수를 2~20개로 제한
            await ctx.send("⚠️ 버튼 개수는 2~20개 사이여야 합니다!")
            return

        message = await ctx.send(f"💣 **폭탄 게임 대기방**\n{num_buttons}개의 버튼이 준비되었습니다!\n🔹 참여하려면 '참여하기' 버튼을 눌러주세요.")
        view = BombGameLobby(ctx=ctx, num_buttons=num_buttons)
        await message.edit(view=view)

async def setup(bot):
    await bot.add_cog(Bomb(bot))

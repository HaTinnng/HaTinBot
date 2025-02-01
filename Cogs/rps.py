import discord
from discord.ext import commands
import random

class RPSView(discord.ui.View):
    def __init__(self, player, message):
        """플레이어를 저장하여 해당 사용자만 게임 진행 가능하도록 설정"""
        super().__init__()
        self.choices = ["가위", "바위", "보"]
        self.player = player  # 명령어를 입력한 사용자 저장
        self.message = message  # 메시지를 삭제하기 위해 저장

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """명령어 입력자만 버튼을 클릭할 수 있도록 제한"""
        if interaction.user != self.player:
            await interaction.response.send_message("⚠️ 당신은 이 게임에 참여할 수 없습니다!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="가위 ✌", style=discord.ButtonStyle.primary)
    async def scissor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_game(interaction, "가위")

    @discord.ui.button(label="바위 ✊", style=discord.ButtonStyle.success)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_game(interaction, "바위")

    @discord.ui.button(label="보 ✋", style=discord.ButtonStyle.danger)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_game(interaction, "보")

    async def process_game(self, interaction: discord.Interaction, player_choice: str):
        """가위바위보 게임의 승패 판별 및 진행"""
        bot_choice = random.choice(self.choices)  # 하틴봇의 선택

        # 승패 판별
        if player_choice == bot_choice:
            # 비긴 경우, 다시 진행 (새로운 버튼 제공)
            await interaction.response.edit_message(
                content=f"🤝 비등하네... 다시 한 번!\n가위...바위...보!",
                view=RPSView(self.player, self.message)  # 새로운 View 생성 (게임 지속)
            )
        else:
            # 버튼이 포함된 메시지를 삭제하고 결과 메시지를 출력
            await self.message.delete()

            if (player_choice == "가위" and bot_choice == "보") or \
               (player_choice == "바위" and bot_choice == "가위") or \
               (player_choice == "보" and bot_choice == "바위"):
                # 플레이어 승리
                result_message = f"🎉 축하합니다! 하틴봇을 이겼습니다!\n\n🧑 {player_choice} vs 🤖 {bot_choice}"
            else:
                # 플레이어 패배
                result_message = f"😢 하틴봇을 이기지 못했습니다.\n\n🧑 {player_choice} vs 🤖 {bot_choice}"

            # 게임 결과를 새로운 메시지로 출력
            await interaction.channel.send(result_message)

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="가위바위보", help="하틴봇과 가위바위보 게임을 합니다!")
    async def play_rps(self, ctx):
        """가위바위보 게임을 시작하는 명령어"""
        message = await ctx.send(
            "🎮 **하틴봇과 가위바위보를 시작합니다!**\n가위...바위...보!",
            view=RPSView(ctx.author, None)  # 메시지를 아직 저장하지 않음
        )
        # 메시지를 저장하여 이후 삭제할 수 있도록 설정
        view = RPSView(ctx.author, message)
        view.message = message
        await message.edit(view=view)

async def setup(bot):
    await bot.add_cog(RPS(bot))

import discord
from discord.ext import commands
import random

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choices = ["가위", "바위", "보"]  # 가위바위보 선택지

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """한 명의 사용자만 버튼을 클릭하도록 설정"""
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
        """플레이어 선택을 받아 하틴봇과 가위바위보 결과를 결정"""
        bot_choice = random.choice(self.choices)  # 하틴봇 랜덤 선택

        # 가위바위보 결과 판단
        if player_choice == bot_choice:
            # 비긴 경우, 다시 게임을 진행
            await interaction.response.edit_message(content=f"🤝 비등하네... 다시 한 번!\n가위...바위...보!", view=RPSView())
        elif (player_choice == "가위" and bot_choice == "보") or \
             (player_choice == "바위" and bot_choice == "가위") or \
             (player_choice == "보" and bot_choice == "바위"):
            # 플레이어가 이긴 경우
            await interaction.response.edit_message(content=f"🎉 축하합니다! 하틴봇을 이겼습니다!\n\n🧑 {player_choice} vs 🤖 {bot_choice}")
        else:
            # 플레이어가 진 경우
            await interaction.response.edit_message(content=f"😢 하틴봇을 이기지 못했습니다.\n\n🧑 {player_choice} vs 🤖 {bot_choice}")

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="가위바위보", help="하틴봇과 가위바위보 게임을 합니다!")
    async def play_rps(self, ctx):
        """가위바위보 게임을 시작하는 명령어"""
        await ctx.send("🎮 **하틴봇과 가위바위보를 시작합니다!**\n가위...바위...보!", view=RPSView())

async def setup(bot):
    await bot.add_cog(RPS(bot))

import discord
from discord.ext import commands
import random

class YabawiGame(discord.ui.View):
    def __init__(self, game_message):
        super().__init__()
        self.correct_choice = random.randint(1, 3)  # 1~3 중 정답 랜덤 설정
        self.game_message = game_message  # 게임 메시지 저장

    async def disable_buttons(self):
        """모든 버튼을 비활성화"""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    async def check_answer(self, interaction: discord.Interaction, choice):
        """선택한 버튼이 정답인지 확인하고 메시지를 삭제"""
        if choice == self.correct_choice:
            await interaction.response.send_message(f"🎉 정답입니다! 공은 {choice}번에 있었습니다! 🏆", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ 틀렸습니다! 공은 {self.correct_choice}번에 있었습니다. 😢", ephemeral=True)

        await self.disable_buttons()  # 버튼 비활성화
        await self.game_message.edit(view=self)  # 버튼 비활성화 적용
        await self.game_message.delete()  # ✅ 게임 메시지 삭제

    @discord.ui.button(label="1번", style=discord.ButtonStyle.primary)
    async def button_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 1)

    @discord.ui.button(label="2번", style=discord.ButtonStyle.primary)
    async def button_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 2)

    @discord.ui.button(label="3번", style=discord.ButtonStyle.primary)
    async def button_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 3)

class Yabawi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="야바위")
    async def yabawi(self, ctx):
        """야바위 게임 시작"""
        message = await ctx.send("🎲 **야바위 게임!**\n3개의 버튼 중 1개에 공이 들어있습니다!\n🔵 공이 들어있는 버튼을 맞혀보세요!")
        view = YabawiGame(game_message=message)
        await message.edit(view=view)  # 게임 메시지 업데이트

async def setup(bot):
    await bot.add_cog(Yabawi(bot))

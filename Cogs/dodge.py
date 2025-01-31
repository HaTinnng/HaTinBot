import discord
import random
from discord.ext import commands

class DodgeGame(discord.ui.View):
    def __init__(self, game_message):
        super().__init__()
        self.game_message = game_message
        self.dodge_position = random.randint(1, 3)  # 피해야 하는 위치 (랜덤)

    async def end_game(self, interaction, survived):
        """게임 종료 - 정답 확인 후 메시지 삭제"""
        if survived:
            await interaction.response.send_message(f"✅ 피했습니다! 🎉 안전한 위치였어요!", ephemeral=True)
        else:
            await interaction.response.send_message(f"💩 똥 맞았습니다! 😭 다음엔 조심하세요!", ephemeral=True)

        await self.game_message.delete()  # 게임 메시지 삭제

    @discord.ui.button(label="1번 위치", style=discord.ButtonStyle.primary)
    async def position_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.end_game(interaction, survived=(self.dodge_position != 1))

    @discord.ui.button(label="2번 위치", style=discord.ButtonStyle.primary)
    async def position_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.end_game(interaction, survived=(self.dodge_position != 2))

    @discord.ui.button(label="3번 위치", style=discord.ButtonStyle.primary)
    async def position_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.end_game(interaction, survived=(self.dodge_position != 3))

class Dodge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="똥피하기")
    async def dodge_game(self, ctx):
        """똥피하기 게임 시작"""
        message = await ctx.send("💩 **똥피하기 게임!**\n3개의 위치 중 안전한 곳을 선택하세요! 🚀")
        view = DodgeGame(game_message=message)
        await message.edit(view=view)

async def setup(bot):
    await bot.add_cog(Dodge(bot))

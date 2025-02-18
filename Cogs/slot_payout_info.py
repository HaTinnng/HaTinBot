from discord.ext import commands
import discord

# 슬롯머신 배당 정보
PAYOUTS = {
    "7️⃣7️⃣7️⃣": 77,  # 잭팟 (배팅금의 50배 지급)
    "★★★": 52,
    "☆☆☆": 38,
    "💎💎💎": 25,
    "🍒🍒🍒": 18,
    "🍀🍀🍀": 12,
    "🔔🔔🔔": 5,
    
}
PARTIAL_PAYOUTS = {  # 두 개 맞췄을 때 보상
    "7️⃣7️⃣": 27,
    "★★": 18,
    "☆☆": 12,
    "💎💎": 8,
    "🍒🍒": 4,
    "🍀🍀": 2,
    "🔔🔔": 1,
}

class SlotPayoutInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="슬롯정보",aliases=["룰렛정보"])
    async def payout_info(self, ctx):
        """ 슬롯머신 배당 정보를 보여줍니다. """
        embed = discord.Embed(title="🎰 슬롯머신 배당 정보", color=discord.Color.gold())
        
        for combination, multiplier in PAYOUTS.items():
            embed.add_field(name=combination, value=f"💰 {multiplier}배", inline=False)
        
        embed.add_field(name="🎰 부분 일치 배당", value="(두 개 일치 시)", inline=False)
        for combination, multiplier in PARTIAL_PAYOUTS.items():
            embed.add_field(name=combination, value=f"💰 {multiplier}배", inline=True)
        
        await ctx.send(embed=embed)

# 봇에 Cog 추가
def setup(bot):
    bot.add_cog(SlotPayoutInfo(bot))

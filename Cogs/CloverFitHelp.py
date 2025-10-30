import discord
from discord.ext import commands
from datetime import datetime
import pytz

# ─────────────────────────────────────────────
# ✅ CloverFit Constants (게임 설정 값)
# ─────────────────────────────────────────────
ROUND_BASE_QUOTA = 1200
ROUND_QUOTA_STEP = 600
SPINS_PER_ROUND  = 5
BET_UNIT         = 100

def kr_now():
    return datetime.now(pytz.timezone("Asia/Seoul"))


# ─────────────────────────────────────────────
# ✅ CloverFit Help Cog
# ─────────────────────────────────────────────
class CloverFitHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── #클로버 / #클로버핏 도움말 명령어 ───────────────────────
    @commands.command(name="클로버", aliases=["클로버핏"])
    async def clover_help(self, ctx: commands.Context):

        base_quota_txt = f"{ROUND_BASE_QUOTA:,} + {ROUND_QUOTA_STEP:,}×(라운드-1)"
        patterns_txt = (
            "• **가로(3), 세로(3), 대각(3)** — ×1.0\n"
            "• **가로-L(4)** — ×2.0 | **가로-XL(5)** — ×3.0\n"
            "• **지그/재그** — ×4.0\n"
            "• **지상/천상** — ×7.0\n"
            "• **눈(EYE)** — ×8.0\n"
            "• **잭팟** — ×10.0 *(모든 패턴 처리 후 추가)*\n"
            "※ 상위 패턴에 내포된 하위 패턴은 미발동"
        )
        
        symbols_txt = (
            "🍒/🍋 **Φ×2**(각 19.4%) · 🍀/🔔 **Φ×3**(각 14.9%)\n"
            "💎/🪙 **Φ×5**(각 11.9%) · 7️⃣ **Φ×7**(7.5%) · 6️⃣ *(특수, 1.5%)*"
        )
        
        rule_txt = (
            f"• **스핀**: 라운드당 {SPINS_PER_ROUND}회\n"
            f"• **ATM 목표**: `{base_quota_txt}`\n"
            "• 마지막 스핀 후\n"
            "  └ ATM+보유≥목표 → **60초 유예**\n"
            "  └ 미달 → **즉시 탈락 + 코인 0원**\n"
            "• 목표 달성 시 다음 라운드\n"
            "• **666(6️⃣×3+)**: 모든 보상 무효 + ATM 0\n"
            f"• 보상: `Φ×배수×{BET_UNIT:,}`"
        )

        embed = discord.Embed(
            title="🎰 클로버핏 — 공식 도움말",
            description="**슬롯 + 라운드 진출**로 행운과 판단력을 시험하라!",
            color=discord.Color.green()
        )
        embed.add_field(name="🔢 심볼 가치/확률", value=symbols_txt, inline=False)
        embed.add_field(name="🧩 패턴 배수", value=patterns_txt, inline=False)
        embed.add_field(name="📜 규칙 요약", value=rule_txt, inline=False)
        embed.add_field(
            name="📌 핵심 명령어",
            value=(
                "`#클로버참가 닉네임` — 닉네임 등록\n"
                "`#클로버시작` — 라운드 시작\n"
                "`#클로버스핀` — 슬롯 실행\n"
                "`#클로버입금 [금액|all]` — ATM 정산\n"
                "`#클로버보유` — 상태 조회\n"
                "`#클로버랭킹` — TOP10 랭킹\n"
                "`#클로버종료` — 포기 → **코인 0원**"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"개발자: 하틴 | {kr_now().strftime('%Y-%m-%d %H:%M')} 기준")
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)

        # ── 인터랙티브 버튼 UI ───────────────────────────
        class HelpView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)

            @discord.ui.button(label="시작하기", emoji="🚀", style=discord.ButtonStyle.success)
            async def btn_start(self, interaction, button):
                await interaction.response.send_message(
                    f"`#클로버시작` 입력!\n"
                    f"라운드1 목표: **{ROUND_BASE_QUOTA:,}원** | 스핀: {SPINS_PER_ROUND}회",
                    ephemeral=True
                )

            @discord.ui.button(label="스핀하기", emoji="🎞️", style=discord.ButtonStyle.primary)
            async def btn_spin(self, interaction, button):
                await interaction.response.send_message(
                    "`#클로버스핀` — 슬롯 1회 실행!",
                    ephemeral=True
                )

            @discord.ui.button(label="입금하기", emoji="🏦", style=discord.ButtonStyle.secondary)
            async def btn_dep(self, interaction, button):
                await interaction.response.send_message(
                    "`#클로버입금 [금액|all]` — 목표 달성하면 라운드 UP!",
                    ephemeral=True
                )

            @discord.ui.button(label="포기(탈락)", emoji="💀", style=discord.ButtonStyle.danger)
            async def btn_end(self, interaction, button):
                await interaction.response.send_message(
                    "`#클로버종료`\n포기 즉시 **잔액 0원**!",
                    ephemeral=True
                )

        await ctx.send(embed=embed, view=HelpView())

async def setup(bot):
    await bot.add_cog(CloverFitHelp(bot))

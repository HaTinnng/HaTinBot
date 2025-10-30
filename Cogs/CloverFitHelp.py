# ── Help Command: #클로버 / #클로버핏 ──────────────────────────────────────
@commands.command(name="클로버", aliases=["클로버핏"])
async def clover_help(self, ctx: commands.Context):
    """
    #클로버 / #클로버핏 : 클로버핏 도움말 임베드 + 버튼 UI
    """
    base_quota_txt = f"{ROUND_BASE_QUOTA:,} + {ROUND_QUOTA_STEP:,}×(라운드-1)"
    patterns_txt = (
        "• **가로(3), 세로(3), 대각(3)** — ×1.0\n"
        "• **가로-L(4)** — ×2.0 | **가로-XL(5)** — ×3.0\n"
        "• **지그/재그** — ×4.0\n"
        "• **지상/천상** — ×7.0\n"
        "• **눈** — ×8.0\n"
        "• **잭팟** — ×10.0 *(다른 패턴 처리 후 추가 가산)*\n"
        "※ 상위 패턴이 하위 패턴을 **내포**하면 하위는 **미발동**"
    )
    
    symbols_txt = (
        "🍒/🍋 **Φ×2**(각 19.4%) · 🍀/🔔 **Φ×3**(각 14.9%)\n"
        "💎/🪙 **Φ×5**(각 11.9%) · 7️⃣ **Φ×7**(7.5%) · 6️⃣ *(특수, 1.5%)*"
    )
    
    rule_txt = (
        f"• **스핀**: 라운드당 {SPINS_PER_ROUND}회\n"
        f"• **목표(ATM)**: `{base_quota_txt}`\n"
        "• **마지막 스핀 이후** 조건 검사\n"
        "  └ ATM+보유코인 ≥ 목표 → **60초 유예** 부여\n"
        "  └ 미만 시 **즉시 탈락 + 코인 0원 초기화**\n"
        "• 목표 달성 시 다음 라운드 + 스핀 충전\n"
        "• **666(6️⃣×3+)**: 보상 0 + ATM 0 + 모든 패턴 무효\n"
        f"• 배당: `Φ×배수×{BET_UNIT:,}`"
    )

    embed = discord.Embed(
        title="🎰 클로버핏 — 공식 도움말",
        description="**슬롯 + 라운드 진출** 시스템으로\n행운과 판단력을 시험하는 게임!",
        color=discord.Color.green()
    )
    embed.add_field(name="🔢 심볼 확률/가치(Φ)", value=symbols_txt, inline=False)
    embed.add_field(name="🧩 패턴 배수", value=patterns_txt, inline=False)
    embed.add_field(name="📜 규칙 요약", value=rule_txt, inline=False)
    embed.add_field(
        name="📌 명령어 정리",
        value=(
            "`#클로버참가 닉네임` — 닉네임 등록\n"
            "`#클로버시작` — 클로버핏 시작\n"
            "`#클로버스핀` — 슬롯 1회 스핀\n"
            "`#클로버입금 [금액|all]` — ATM 입금/정산\n"
            "`#클로버보유` — 현재 정보 확인\n"
            "`#클로버랭킹` — 랭킹 TOP10 확인\n"
            "`#클로버종료` — 포기 → **탈락 + 코인 0원**"
        ),
        inline=False
    )
    embed.set_footer(text=f"개발자: 하틴(HaTin) | {kr_now().strftime('%Y-%m-%d %H:%M')} 기준")
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)

    # ── Fancy Buttons (Quick Guide) ──
    class HelpView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)

        @discord.ui.button(label="시작하기", emoji="🚀", style=discord.ButtonStyle.success)
        async def btn_start(self, interaction, button):
            await interaction.response.send_message(
                "런을 시작하려면: `#클로버시작`\n"
                f"라운드1 목표: **{ROUND_BASE_QUOTA:,}** | 스핀: **{SPINS_PER_ROUND}회**",
                ephemeral=True
            )

        @discord.ui.button(label="스핀", emoji="🎞️", style=discord.ButtonStyle.primary)
        async def btn_spin(self, interaction, button):
            await interaction.response.send_message(
                "`#클로버스핀` — 슬롯 실행 애니메이션!",
                ephemeral=True
            )

        @discord.ui.button(label="입금", emoji="🏦", style=discord.ButtonStyle.secondary)
        async def btn_dep(self, interaction, button):
            await interaction.response.send_message(
                "`#클로버입금 [금액|all]`\n목표 달성 시 라운드 UP!",
                ephemeral=True
            )

        @discord.ui.button(label="조심! 포기", emoji="🛑", style=discord.ButtonStyle.danger)
        async def btn_end(self, interaction, button):
            await interaction.response.send_message(
                "`#클로버종료`\n포기 시 **즉시 코인 0원**이 됩니다!",
                ephemeral=True
            )

    await ctx.send(embed=embed, view=HelpView())

import discord
import random
from discord.ext import commands

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # {채널ID: BlackjackGame}
        self.lobbies = {}  # {채널ID: 참가자 리스트}

    @commands.command(name="블랙잭")
    async def start_blackjack(self, ctx):
        """개인 블랙잭 게임 시작"""
        if ctx.channel.id in self.active_games:
            await ctx.send("이미 진행 중인 블랙잭 게임이 있습니다!")
            return

        game = BlackjackGame([ctx.author])
        self.active_games[ctx.channel.id] = game
        await ctx.send(embed=game.get_embed(), view=BlackjackView(self, ctx.channel.id))

    @commands.command(name="블랙잭시작")
    async def start_blackjack_lobby(self, ctx):
        """멀티 플레이 블랙잭 로비 생성"""
        if ctx.channel.id in self.lobbies:
            await ctx.send("이미 블랙잭 로비가 존재합니다!")
            return

        self.lobbies[ctx.channel.id] = []
        await ctx.send(
            embed=discord.Embed(title="🃏 블랙잭 멀티플레이 로비", description="참가하려면 아래 버튼을 클릭하세요!", color=discord.Color.blue()),
            view=LobbyView(self, ctx.channel.id)
        )

    def start_multiplayer_game(self, channel_id):
        """멀티 플레이어 블랙잭 게임 시작"""
        if channel_id not in self.lobbies or not self.lobbies[channel_id]:
            return None

        game = BlackjackGame(self.lobbies[channel_id])
        self.active_games[channel_id] = game
        del self.lobbies[channel_id]
        return game

    def end_game(self, channel_id):
        """게임 종료 후 데이터 삭제"""
        if channel_id in self.active_games:
            del self.active_games[channel_id]

class BlackjackGame:
    def __init__(self, players):
        self.players = players
        self.current_player_index = 0
        self.deck = self.generate_deck()
        self.hands = {player: [self.draw_card(), self.draw_card()] for player in players}
        self.dealer_hand = [self.draw_card(), self.draw_card()]
        self.game_over = False
        self.standing_players = set()

    def generate_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['♠', '♥', '♦', '♣']
        return [f"{rank}{suit}" for rank in ranks for suit in suits]

    def draw_card(self):
        return self.deck.pop(random.randint(0, len(self.deck) - 1))

    def calculate_score(self, cards):
        score = 0
        ace_count = 0
        for card in cards:
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:
                score += 10
            elif rank == 'A':
                ace_count += 1
                score += 11
            else:
                score += int(rank)

        while score > 21 and ace_count:
            score -= 10
            ace_count -= 1

        return score

    def get_embed(self, reveal_dealer=False):
        embed = discord.Embed(title="♠️ 블랙잭 게임", color=discord.Color.blue())

        for player in self.players:
            score = self.calculate_score(self.hands[player])
            embed.add_field(name=f"{player.name}의 카드", value=f"{', '.join(self.hands[player])}\n점수: {score}", inline=False)

        if reveal_dealer:
            dealer_score = self.calculate_score(self.dealer_hand)
            embed.add_field(name="딜러의 카드", value=f"{', '.join(self.dealer_hand)}\n점수: {dealer_score}", inline=False)
        else:
            embed.add_field(name="딜러의 카드", value=f"{self.dealer_hand[0]}, ???", inline=False)

        return embed

class BlackjackView(discord.ui.View):
    def __init__(self, cog, channel_id):
        super().__init__()
        self.cog = cog
        self.channel_id = channel_id

    @discord.ui.button(label="Hit (카드 뽑기)", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.cog.active_games.get(self.channel_id)
        if not game:
            return await interaction.response.send_message("게임이 종료되었습니다!", ephemeral=True)

        player = game.players[game.current_player_index]
        if interaction.user != player:
            return await interaction.response.send_message("본인의 차례가 아닙니다!", ephemeral=True)

        game.hands[player].append(game.draw_card())
        if game.calculate_score(game.hands[player]) > 21:
            game.standing_players.add(player)

        if len(game.standing_players) == len(game.players):
            await self.end_game(interaction)
        else:
            game.current_player_index = (game.current_player_index + 1) % len(game.players)
            await interaction.response.edit_message(embed=game.get_embed(), view=self)

    @discord.ui.button(label="Stand (멈추기)", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.cog.active_games.get(self.channel_id)
        if not game:
            return await interaction.response.send_message("게임이 종료되었습니다!", ephemeral=True)

        player = game.players[game.current_player_index]
        if interaction.user != player:
            return await interaction.response.send_message("본인의 차례가 아닙니다!", ephemeral=True)

        game.standing_players.add(player)

        if len(game.standing_players) == len(game.players):
            await self.end_game(interaction)
        else:
            game.current_player_index = (game.current_player_index + 1) % len(game.players)
            await interaction.response.edit_message(embed=game.get_embed(), view=self)

    async def end_game(self, interaction):
        game = self.cog.active_games[self.channel_id]

        while game.calculate_score(game.dealer_hand) < 17:
            game.dealer_hand.append(game.draw_card())

        result_text = ""
        dealer_score = game.calculate_score(game.dealer_hand)

        for player in game.players:
            player_score = game.calculate_score(game.hands[player])
            if player_score > 21:
                result_text += f"❌ {player.mention} **버스트! (패배)**\n"
            elif dealer_score > 21 or player_score > dealer_score:
                result_text += f"✅ {player.mention} **승리!**\n"
            elif player_score == dealer_score:
                result_text += f"⚖️ {player.mention} **무승부!**\n"
            else:
                result_text += f"❌ {player.mention} **패배!**\n"

        embed = game.get_embed(reveal_dealer=True)
        embed.add_field(name="결과", value=result_text, inline=False)

        self.cog.end_game(self.channel_id)
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Blackjack(bot))
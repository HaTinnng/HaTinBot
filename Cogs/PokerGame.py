import os
import random
import discord
from discord.ext import commands
from pymongo import MongoClient

# 카드: (value, suit) 형태, value는 2~14 (11:J, 12:Q, 13:K, 14:A), suit는 "♠", "♥", "♦", "♣"

class PokerGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MONGO_URI = os.environ.get("MONGODB_URI")
        self.DB_NAME = "stock_game"
        self.mongo_client = MongoClient(self.MONGO_URI)
        self.db = self.mongo_client[self.DB_NAME]
    
    def cog_unload(self):
        self.mongo_client.close()
    
    def create_deck(self):
        """표준 52장 카드 덱을 생성 후 섞어 반환합니다."""
        suits = ["♠", "♥", "♦", "♣"]
        deck = [(value, suit) for value in range(2, 15) for suit in suits]
        random.shuffle(deck)
        return deck

    def card_to_str(self, card):
        """카드 튜플을 문자열로 변환합니다. 예: (14, '♠') -> 'A♠'"""
        value, suit = card
        if value == 11:
            val_str = "J"
        elif value == 12:
            val_str = "Q"
        elif value == 13:
            val_str = "K"
        elif value == 14:
            val_str = "A"
        else:
            val_str = str(value)
        return f"{val_str}{suit}"

    def evaluate_hand(self, hand):
        """
        간단한 포커 핸드 평가 함수.
        반환값은 비교 가능한 튜플로, 높은 튜플이 더 강한 핸드를 의미합니다.
        순위 카테고리:
          8: 스트레이트 플러시
          7: 포카드 (4장)
          6: 풀 하우스
          5: 플러시
          4: 스트레이트
          3: 트리플 (3장)
          2: 투 페어
          1: 원 페어
          0: 하이 카드
        """
        values = sorted([card[0] for card in hand], reverse=True)
        suits = [card[1] for card in hand]
        counts = {v: values.count(v) for v in set(values)}
        sorted_counts = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        is_flush = len(set(suits)) == 1
        is_straight = False
        unique_values = sorted(set(values))
        if len(unique_values) == 5:
            if unique_values[-1] - unique_values[0] == 4:
                is_straight = True
            # Ace-low 스트레이트 (A,2,3,4,5) 처리
            if unique_values == [2, 3, 4, 5, 14]:
                is_straight = True
                values = [5, 4, 3, 2, 1]
        
        if is_flush and is_straight:
            rank = 8
            primary = max(values)
            return (rank, primary, values)
        if sorted_counts[0][1] == 4:
            rank = 7
            four_val = sorted_counts[0][0]
            kicker = [v for v in values if v != four_val][0]
            return (rank, four_val, kicker)
        if sorted_counts[0][1] == 3 and sorted_counts[1][1] == 2:
            rank = 6
            three_val = sorted_counts[0][0]
            pair_val = sorted_counts[1][0]
            return (rank, three_val, pair_val)
        if is_flush:
            rank = 5
            return (rank, values)
        if is_straight:
            rank = 4
            primary = max(values)
            return (rank, primary, values)
        if sorted_counts[0][1] == 3:
            rank = 3
            three_val = sorted_counts[0][0]
            kickers = [v for v in values if v != three_val]
            return (rank, three_val, kickers)
        if sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
            rank = 2
            pair_high = max(sorted_counts[0][0], sorted_counts[1][0])
            pair_low = min(sorted_counts[0][0], sorted_counts[1][0])
            kicker = [v for v in values if v != pair_high and v != pair_low][0]
            return (rank, pair_high, pair_low, kicker)
        if sorted_counts[0][1] == 2:
            rank = 1
            pair_val = sorted_counts[0][0]
            kickers = [v for v in values if v != pair_val]
            return (rank, pair_val, kickers)
        rank = 0
        return (rank, values)

    def get_hand_rank_name(self, evaluation):
        """평가 튜플을 받아 해당 핸드의 이름을 반환합니다."""
        rank = evaluation[0]
        if rank == 8:
            return "스트레이트 플러시"
        elif rank == 7:
            return "포카드"
        elif rank == 6:
            return "풀 하우스"
        elif rank == 5:
            return "플러시"
        elif rank == 4:
            return "스트레이트"
        elif rank == 3:
            return "트리플"
        elif rank == 2:
            return "투 페어"
        elif rank == 1:
            return "원 페어"
        elif rank == 0:
            return "하이 카드"

    def get_hand_details(self, hand):
        """
        트리플, 투 페어, 원 페어, 하이 카드의 경우,
        해당 카드 조합의 실제 카드들을 함께 표시합니다.
        """
        evaluation = self.evaluate_hand(hand)
        rank = evaluation[0]
        basic_rank = self.get_hand_rank_name(evaluation)
        # hand 내 카드들을 value별로 그룹화 (문자열 형태)
        cards_by_value = {}
        for card in hand:
            cards_by_value.setdefault(card[0], []).append(self.card_to_str(card))
        counts = {v: len(cards_by_value[v]) for v in cards_by_value}
        sorted_counts = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        
        if rank == 3:  # 트리플
            three_val = sorted_counts[0][0]
            triple_cards = cards_by_value[three_val]
            # 트리플에 속하지 않는 나머지 카드(킥커)들
            kickers = sorted([card for card in hand if card[0] != three_val], key=lambda card: card[0], reverse=True)
            kicker_cards = [self.card_to_str(card) for card in kickers]
            return f"{basic_rank} ({', '.join(triple_cards)}) 하이카드 ({', '.join(kicker_cards)})"
        elif rank == 2:  # 투 페어
            pair_val1 = sorted_counts[0][0]
            pair_val2 = sorted_counts[1][0]
            pair_cards = cards_by_value[pair_val1] + cards_by_value[pair_val2]
            kickers = sorted([card for card in hand if card[0] not in (pair_val1, pair_val2)], key=lambda card: card[0], reverse=True)
            kicker_cards = [self.card_to_str(card) for card in kickers]
            kicker_str = ', '.join(kicker_cards) if kicker_cards else ""
            return f"{basic_rank} ({', '.join(pair_cards)}) 하이카드 ({kicker_str})"
        elif rank == 1:  # 원 페어
            pair_val = sorted_counts[0][0]
            pair_cards = cards_by_value[pair_val]
            kickers = sorted([card for card in hand if card[0] != pair_val], key=lambda card: card[0], reverse=True)
            kicker_cards = [self.card_to_str(card) for card in kickers]
            return f"{basic_rank} ({', '.join(pair_cards)}) 하이카드 ({', '.join(kicker_cards)})"
        elif rank == 0:  # 하이 카드
            sorted_hand = sorted(hand, key=lambda card: card[0], reverse=True)
            high_cards = [self.card_to_str(card) for card in sorted_hand]
            return f"{basic_rank} ({', '.join(high_cards)})"
        else:
            return basic_rank

    def compare_hands(self, player_hand, dealer_hand):
        """플레이어와 딜러의 핸드를 평가하여 승패를 결정합니다."""
        eval_player = self.evaluate_hand(player_hand)
        eval_dealer = self.evaluate_hand(dealer_hand)
        if eval_player > eval_dealer:
            return "win"
        elif eval_player < eval_dealer:
            return "lose"
        else:
            return "tie"
    
    @commands.command(name="포커")
    async def play_poker(self, ctx, bet: str):
        """
        #포커 [베팅액]:
        - 사용자는 현금을 이용해 포커 게임에 베팅할 수 있습니다.
        - "all", "전부", "올인" 등의 입력으로 전액 베팅이 가능합니다.
        - 플레이어와 딜러가 각각 5장의 카드를 받아 비교하며, 
          승리 시 베팅액 만큼의 이익을, 비길 경우 베팅액이 반환되고, 패배 시 베팅액을 잃습니다.
        """
        user_id = str(ctx.author.id)
        user = self.db.users.find_one({"_id": user_id})
        if not user:
            await ctx.send("주식 게임에 참가하지 않으셨습니다. 먼저 `#주식참가`를 통해 등록해주세요.")
            return

        # 베팅액 파싱
        try:
            if bet.lower() in ["all", "전부", "올인", "다", "풀베팅"]:
                bet_amount = user.get("money", 0)
            else:
                bet_amount = int(bet)
        except Exception:
            await ctx.send("베팅액을 올바르게 입력해주세요.")
            return
        if bet_amount <= 0:
            await ctx.send("베팅액은 1원 이상이어야 합니다.")
            return
        if user.get("money", 0) < bet_amount:
            await ctx.send("현금 잔액이 부족합니다.")
            return
        
        # 베팅액 차감
        new_money = user.get("money", 0) - bet_amount
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money}})
        
        # 덱 생성 및 카드 분배 (플레이어 5장, 딜러 5장)
        deck = self.create_deck()
        player_hand = [deck.pop() for _ in range(5)]
        dealer_hand = [deck.pop() for _ in range(5)]
        
        # 핸드 평가 및 승패 결정
        result = self.compare_hands(player_hand, dealer_hand)
        player_eval = self.evaluate_hand(player_hand)
        dealer_eval = self.evaluate_hand(dealer_hand)
        # 트리플, 투 페어, 원 페어, 하이 카드인 경우엔 상세 카드 조합을 표시합니다.
        if player_eval[0] in [3, 2, 1, 0]:
            player_hand_detail = self.get_hand_details(player_hand)
        else:
            player_hand_detail = self.get_hand_rank_name(player_eval)
        if dealer_eval[0] in [3, 2, 1, 0]:
            dealer_hand_detail = self.get_hand_details(dealer_hand)
        else:
            dealer_hand_detail = self.get_hand_rank_name(dealer_eval)
        
        # 결과에 따른 현금 처리
        if result == "win":
            winnings = bet_amount * 2
            outcome_message = f"축하합니다! 포커에서 승리하셨습니다. {bet_amount:,}원의 이익을 얻어 총 {winnings:,}원을 받습니다."
            new_money += bet_amount * 2
        elif result == "tie":
            winnings = bet_amount
            outcome_message = "비겼습니다! 베팅액이 그대로 반환됩니다."
            new_money += bet_amount
        else:
            winnings = 0
            outcome_message = "아쉽게도 졌습니다. 베팅액을 잃었습니다."
        
        # 업데이트된 현금 정보를 DB에 저장
        self.db.users.update_one({"_id": user_id}, {"$set": {"money": new_money}})
        
        # 카드 문자열 변환
        player_cards_str = " ".join(self.card_to_str(card) for card in player_hand)
        dealer_cards_str = " ".join(self.card_to_str(card) for card in dealer_hand)
        
        # 결과 임베드 메시지 전송 (각각의 카드와 패 조합 세부 정보 포함)
        embed = discord.Embed(
            title="포커 게임 결과", 
            color=discord.Color.green() if result == "win" else discord.Color.red() if result == "lose" else discord.Color.blue()
        )
        embed.add_field(name="당신의 카드", value=player_cards_str, inline=False)
        embed.add_field(name="당신의 패", value=player_hand_detail, inline=False)
        embed.add_field(name="딜러의 카드", value=dealer_cards_str, inline=False)
        embed.add_field(name="딜러의 패", value=dealer_hand_detail, inline=False)
        embed.add_field(name="결과", value=outcome_message, inline=False)
        embed.set_footer(text=f"남은 현금: {new_money:,}원")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PokerGame(bot))

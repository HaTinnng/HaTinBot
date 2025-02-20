import random
from collections import Counter

def generate_number():
    # 0부터 9까지 숫자 중 랜덤으로 4자리 숫자를 생성 (동일 숫자 가능, 선행 0 가능)
    return ''.join(str(random.randint(0, 9)) for _ in range(4))

def get_strikes_balls(guess, answer):
    # 자리와 숫자가 일치하면 스트라이크 계산
    strikes = sum(1 for i in range(4) if guess[i] == answer[i])
    # 공통으로 포함된 숫자의 최소 개수를 모두 합한 후, 스트라이크 수를 빼면 볼의 개수가 됨
    guess_count = Counter(guess)
    answer_count = Counter(answer)
    common = sum(min(guess_count[d], answer_count[d]) for d in guess_count)
    balls = common - strikes
    return strikes, balls

def play_game():
    answer = generate_number()
    attempts = 0
    while True:
        user_input = input("숫자 네자리를 입력하세요 (종료하려면 #야구게임그만 입력): ")
        # 게임 중지 입력 처리
        if user_input == "#야구게임그만":
            print("게임 종료! 컴퓨터가 생각한 숫자는:", answer)
            break
        # 입력이 4자리 숫자가 아닐 경우 처리
        if len(user_input) != 4 or not user_input.isdigit():
            print("유효하지 않은 입력입니다. 4자리 숫자를 입력하세요.")
            continue
        
        attempts += 1
        
        # 홈런 조건: 입력한 숫자가 정답과 완전히 일치할 때
        if user_input == answer:
            print(f"홈런! {attempts}번만에 맞추셨습니다!")
            break
        
        strikes, balls = get_strikes_balls(user_input, answer)
        
        # 하나도 맞는 숫자가 없으면 "아웃" 출력
        if strikes == 0 and balls == 0:
            print("아웃")
        else:
            result = []
            if strikes:
                result.append(f"{strikes} 스트라이크")
            if balls:
                result.append(f"{balls} 볼")
            print(", ".join(result))

if __name__ == '__main__':
    play_game()

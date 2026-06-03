import os, json, time, random

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def load_json() -> tuple:
    if not os.path.exists("setting.json"):
        print("Error: 未找到setting.json.")
        return None, None, None, None, None
    with open("setting.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    card_path = settings.get("cardPath")
    meaning_path = settings.get("meaningPath")
    use_llm = settings.get("useLLM", False)
    if use_llm:
        model_name = settings.get("modelName", "qwen/qwen3-4b-2507")
    if not card_path or not meaning_path:
        print("Error: 未找到有效的cardPath或meaningPath")
        return None, None, None, None, None
    if not os.path.exists(card_path):
        print(f"Error: 未找到{card_path}")
        return None, None, None, None, None
    if not os.path.exists(meaning_path):
        print(f"Error: 未找到{meaning_path}")
        return None, None, None, None, None
    if use_llm and not model_name:
        print("Error: 未指定modelName")
        return None, None, None, None, None
    # print(f"Card Path: {card_path}")
    # print(f"Meaning Path: {meaning_path}")

    with open(card_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    with open(meaning_path, "r", encoding="utf-8") as f:
        meanings = json.load(f)

    return cards, meanings, use_llm, model_name, settings.get("fastMode", False)

def shuffle_cards() -> None:
    for i in range(20):
        print(
            f"\r正在洗牌...[ {'■'*(i+1)}{'□'*(19-i)} ]",
            end="",
            flush=True
        )
        time.sleep(0.05)
    print("\r\033[K洗牌完成！")
    time.sleep(1)
    return

def draw_board(cards, orientations):
    clear()
    print("═══════════════ 塔罗占卜 ═══════════════")
    print()
    print(f"{'过去':^12}{'现在':^12}{'未来':^12}")
    row1 = []
    row2 = []
    for i in range(3):
        if cards[i] is None:
            row1.append(f"{'？？':^12}")
        else:
            row1.append(f"{cards[i]:^{12-len(cards[i])+2}}")
        if orientations[i] is None:
            row2.append(f"{'？？':^12}")
        else:
            row2.append(f"{'正位'if orientations[i] == 0 else '逆位':^12}")
    print("".join(row1))
    print("".join(row2))
    print()
    print("═══════════════════════════════════════")

def draw_one_card(cards, meanings):

    card_id = random.randrange(len(cards))
    pos = random.choice([0, 1])
    keywords = meanings.get(str(card_id), {}).get(str(pos), [])
    return (
        card_id,
        cards[card_id],
        pos,
        keywords
    )

def spin_animation(cards, true_card):
    steps = 30
    for i in range(steps):
        progress = i / steps
        delay = 0.02 + progress**2 * 0.25
        card = random.choice(cards)
        print(
            f"\r抽牌中：{card:<10}",
            end="",
            flush=True
        )
        time.sleep(delay)
    print(f"\r抽牌中：{true_card:<10}", end="", flush=True)
    time.sleep(0.5)
    print("\r\033[K", end="")
    

def main():
    cards, meanings, use_llm, model_name, fast_mode = load_json()
    if cards is None or meanings is None:
        return
    # print("成功载入牌面和含义数据！")
    print("您在追寻着什么：")
    question = input()
    if not fast_mode:
        print(f"您在寻觅它的答案：“{question}”，希望继续前进吗？（y/n）", end="")
        choice = input()
        if choice.lower() != "y":
            print("占卜已取消。")
            return
        shuffle_cards()
    revealed_cards = [None, None, None]
    revealed_orients = [None, None, None]
    reveal_keywords = [None, None, None]
    draw_board(revealed_cards, revealed_orients)
    positions = ["过去", "现在", "未来"]

    for i in range(3):
        if not fast_mode:
            print(f"\r按下回车，选择您的『{positions[i]}』...", end="", flush=True)
            input()
        _, card, orient, keywords = draw_one_card(cards, meanings)
        while card in revealed_cards:
            _, card, orient, keywords = draw_one_card(cards, meanings)
        if not fast_mode:
            spin_animation(cards, card)
        revealed_cards[i] = card
        revealed_orients[i] = orient
        reveal_keywords[i] = keywords
        draw_board(revealed_cards, revealed_orients)
        # print(f"{positions[i]}：{card}（{orient}）")
        if not fast_mode:
            time.sleep(0.5)

    if use_llm:
        print("世界正在思考...")
        try:
            from openai import OpenAI
        except ImportError:
            print("世界无法回应，因为缺少了它的语言。")
            print("Error: 未安装openai库")
            return

        client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio"
            )
        prompt = f"""
        用户的问题：“{question}”
        三张牌分别为：
        过去：{revealed_cards[0]}（{'正位' if revealed_orients[0] == 0 else '逆位'}），关键词：{ '、'.join(reveal_keywords[0]) }
        现在：{revealed_cards[1]}（{'正位' if revealed_orients[1] == 0 else '逆位'}），关键词：{ '、'.join(reveal_keywords[1]) }
        未来：{revealed_cards[2]}（{'正位' if revealed_orients[2] == 0 else '逆位'}），关键词：{ '、'.join(reveal_keywords[2]) }
        请按照整体牌面，过去，现在，未来，建议这五个部分进行解读。同时行文简略，1-2句话即可。不允许出现空行。
        按照以下例子的格式进行回答，同时保持语言的温和性、神秘性和文学感：
        例如：question：“我和他之间的关系会如何”
        您在寻找我和他之间关系的答案，而命运给出的回应是：
        【整体牌面】xxx
        【过去】xxx
        【现在】xxx
        【未来】xxx
        【建议】xxx
        """
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一位经验丰富的塔罗师。"
                        "不要提及自己是AI。"
                        "不要强调随机性。"
                        "解读要有启发性和文学感，语言要神秘、温和。"
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=1500
        )
        print(response.choices[0].message.content)

if __name__ == "__main__":
    main()

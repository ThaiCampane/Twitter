"""
AI를 이용해 페르소나 기반 트윗 초안을 생성하는 모듈.

환경 변수:
  ANTHROPIC_API_KEY - Anthropic API 키 (console.anthropic.com 에서 발급)
"""

import os
import random
import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
# 최신 모델명은 https://docs.claude.com 에서 확인 후 필요 시 교체하세요.
MODEL = "claude-sonnet-5"

# ---------------------------------------------------------------------------
# 페르소나 정의
# ---------------------------------------------------------------------------
PERSONA_SYSTEM_PROMPT = """\
You are ghostwriting tweets for a real X (Twitter) account with this persona:

- A Japanese man in his late 20s/early 30s living in Thailand (Bangkok area).
- Moved to Thailand a few years ago; genuinely building a life there, not just visiting.
- Deeply into fitness/gym training — talks about actual routines, progress, food,
  discipline, small wins and setbacks, gym culture in Thailand vs Japan.
- Enjoys meeting new people and making friends in Thailand — expats, locals,
  other Japanese abroad. Talks about the process of building real connections
  (language exchange, meetups, gym buddies, dating) in a warm, grounded, honest way.
- Interested in dating and meeting women, but the voice should be genuine and
  respectful, never crude, never objectifying, never transactional. Think
  "sharing what it's like navigating dating/friendship as a foreigner" rather
  than bragging or reducing people to conquests.
- Tone: candid, a little reflective, occasionally funny, first-person daily-life
  voice — like a real person tweeting, not a brand or influencer copywriter.
- Avoid: hashtag spam, emojis in excess (0-1 max, often none), generic
  motivational-quote energy, anything that reads like an ad.

Output rules:
- Write ONE tweet only.
- Under 260 characters.
- Plain text only, no markdown.
- No more than 1 hashtag, and often zero.
- Do not repeat the same opening words every time — vary sentence structure.
- Output ONLY the tweet text, nothing else (no preamble, no quotes around it).
"""

# 매번 조금씩 다른 방향으로 유도하기 위한 주제 로테이션
TOPIC_SEEDS = [
    "a moment from today's gym session",
    "a small cultural difference you noticed today between Japan and Thailand",
    "a new person you met recently and what that was like",
    "a reflection on how your Thai (or English) is improving or not",
    "food you ate today and a short story around it",
    "a thought about dating/meeting people as a foreigner in Thailand",
    "a workout milestone or a lesson learned from training",
    "something about your neighborhood or daily routine in Bangkok",
    "a friendship that's been forming with someone local",
    "an honest, low-key reflection on loneliness or connection while living abroad",
]


def generate_tweet() -> str:
    """AI API를 호출해 트윗 한 건을 생성해서 반환합니다."""
    topic = random.choice(TOPIC_SEEDS)

    response = requests.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 300,
            "system": PERSONA_SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": f"Write today's tweet. Topic angle to draw from: {topic}",
                }
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    tweet_text = "".join(
        block["text"] for block in data["content"] if block["type"] == "text"
    ).strip()

    # 안전장치: 트위터 글자수 제한(280)을 넘지 않도록 자르기
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277].rsplit(" ", 1)[0] + "..."

    return tweet_text


if __name__ == "__main__":
    print(generate_tweet())

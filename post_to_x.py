"""
생성된 트윗 텍스트(+ 선택적으로 이미지)를 X(트위터)에 실제로 게시하는 모듈.

환경 변수 (X Developer Portal > Project > App > Keys and tokens 에서 발급):
  X_API_KEY
  X_API_SECRET
  X_ACCESS_TOKEN
  X_ACCESS_SECRET

주의: 앱 권한이 "Read and Write"로 설정되어 있어야 합니다.
권한을 바꾼 뒤에는 Access Token/Secret을 재발급받아야 반영됩니다.

이미지 업로드는 X API v1.1 (media/upload)로, 트윗 게시는 v2로 처리합니다.
(v2는 아직 미디어 업로드를 직접 지원하지 않아 v1.1과 병행 사용이 표준적인 방식입니다.)
"""

import os
import tweepy


def get_client() -> tweepy.Client:
    """트윗 게시(v2)용 클라이언트."""
    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )


def get_api_v1() -> tweepy.API:
    """미디어 업로드(v1.1)용 클라이언트."""
    auth = tweepy.OAuth1UserHandler(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )
    return tweepy.API(auth)


def post_tweet(text: str) -> str:
    """텍스트만 트윗을 게시하고 tweet id를 반환합니다."""
    client = get_client()
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return tweet_id


def post_tweet_with_image(text: str, image_path: str) -> str:
    """이미지를 첨부한 트윗을 게시하고 tweet id를 반환합니다."""
    api_v1 = get_api_v1()
    media = api_v1.media_upload(filename=image_path)

    client = get_client()
    response = client.create_tweet(text=text, media_ids=[media.media_id])
    tweet_id = response.data["id"]
    return tweet_id


if __name__ == "__main__":
    # 로컬 테스트용: 실제로 계정에 올라가니 문구를 확인하고 실행하세요.
    test_text = "Testing my automated posting setup. First real post coming soon."
    tid = post_tweet(test_text)
    print(f"Posted! https://x.com/i/web/status/{tid}")

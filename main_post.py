"""GitHub Actions에서 주기적으로(예: 15분마다) 실행되는 진입점.

오늘 예정된 포스팅 시각이 지났고 아직 안 올린 슬롯이 있으면
같은 주제로 트윗 텍스트와 이미지를 함께 생성해서 게시하고,
스케줄 파일에 posted=true로 표시합니다.

이미지 생성이 실패해도(API 오류, 기준 사진 누락 등) 전체 게시가
막히지 않도록, 이미지 실패 시 텍스트만 게시하는 것으로 자동 대체합니다.
"""

from generate_content import generate_tweet, pick_topic
from generate_image import generate_persona_image
from post_to_x import post_tweet, post_tweet_with_image
from schedule_manager import get_due_slot_index, mark_posted

if __name__ == "__main__":
    slot_index = get_due_slot_index()

    if slot_index is None:
        print("지금 올릴 예정된 슬롯 없음. 종료.")
    else:
        topic_text, scene_description = pick_topic()
        tweet_text = generate_tweet(topic_text)

        try:
            image_path = generate_persona_image(scene_description)
            tweet_id = post_tweet_with_image(tweet_text, image_path)
            print(f"게시 완료 (slot {slot_index}, 이미지 포함): {tweet_text}")
        except Exception as e:
            print(f"이미지 생성/첨부 실패, 텍스트만 게시합니다: {e}")
            tweet_id = post_tweet(tweet_text)
            print(f"게시 완료 (slot {slot_index}, 텍스트만): {tweet_text}")

        mark_posted(slot_index)
        print(f"https://x.com/i/web/status/{tweet_id}")

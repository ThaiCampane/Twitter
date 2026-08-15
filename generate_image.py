"""
기준 인물 사진(assets/persona_base.jpg)을 오늘의 트윗 주제에 맞는
배경/상황으로 변형해서 이미지를 생성하는 모듈.

사용 모델: Replicate 의 black-forest-labs/flux-kontext-pro
  - 입력: 기준 이미지 + 텍스트 지시
  - 출력: 인물의 얼굴/정체성은 유지하면서 배경/상황/포즈만 바뀐 새 이미지

환경 변수:
  REPLICATE_API_TOKEN - Replicate API 토큰 (replicate.com/account/api-tokens 에서 발급)

준비물:
  assets/persona_base.jpg 에 미리 스타일 변형해둔 기준 인물 사진을 넣어두세요.
  (실제 얼굴 그대로가 아니라 캐릭터화/스타일화한 버전을 권장합니다.)
"""

import os

import replicate

BASE_IMAGE_DIR = os.environ.get("PERSONA_BASE_IMAGE_DIR", "assets/persona_base")
MODEL = "black-forest-labs/flux-kontext-pro"

# 인물 정체성을 유지하라는 지시를 매번 공통으로 붙여줍니다.
IDENTITY_LOCK_INSTRUCTION = (
    "Keep the exact same person, same face, same identity, same hairstyle "
    "and same overall style as the reference image. Only change the "
    "background, setting, pose, and lighting to match this new scene: "
)


def generate_persona_image(scene_description: str, output_path: str = "output_image.png") -> str:
    """기준 인물 사진을 scene_description에 맞는 새 배경/상황으로 변형해서
    output_path에 저장하고, 저장된 경로를 반환합니다.

    실패 시 예외를 던지므로, 호출하는 쪽(main_post.py)에서 이미지 생성 실패를
    텍스트만 게시하는 것으로 처리할 수 있도록 try/except로 감싸는 것을 권장합니다.
    """
    if not os.path.exists(BASE_IMAGE_PATH):
        raise FileNotFoundError(
            f"기준 인물 사진을 찾을 수 없습니다: {BASE_IMAGE_PATH}. "
            "assets/persona_base.jpg 를 준비해서 레포에 커밋해두세요."
        )

    prompt = IDENTITY_LOCK_INSTRUCTION + scene_description

    with open(BASE_IMAGE_PATH, "rb") as base_image_file:
        output = replicate.run(
            MODEL,
            input={
                "prompt": prompt,
                "input_image": base_image_file,
                "output_format": "png",
            },
        )

    # replicate 최신 python 클라이언트는 FileOutput 객체(또는 그 리스트)를 반환합니다.
    file_output = output[0] if isinstance(output, list) else output

    with open(output_path, "wb") as f:
        f.write(file_output.read())

    return output_path


if __name__ == "__main__":
    # 로컬 테스트용
    test_scene = "at a modern gym in Pattaya, mid-workout, gym clothes"
    path = generate_persona_image(test_scene)
    print(f"이미지 생성 완료: {path}")

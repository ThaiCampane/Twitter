"""
기준 인물 사진(assets/persona_base/ 폴더 안 여러 장 중 하나)을 오늘의
트윗 주제에 맞는 배경/상황/옷차림/표정으로 변형해서 이미지를 생성하는 모듈.

사용 모델: Replicate 의 black-forest-labs/flux-kontext-pro
  - 입력: 기준 이미지 + 텍스트 지시
  - 출력: 인물의 얼굴/정체성은 유지하면서 배경/상황/포즈/옷차림/표정이 바뀐 새 이미지

환경 변수:
  REPLICATE_API_TOKEN - Replicate API 토큰 (replicate.com/account/api-tokens 에서 발급)

준비물:
  assets/persona_base/ 폴더 안에 미리 스타일 변형해둔 기준 인물 사진을
  여러 장 넣어두세요 (예: persona_base_1.jpg, persona_base_2.jpg, ...).
  각도/포즈가 다른 사진을 여러 장 준비할수록 결과물이 더 다양해집니다.
  매 실행마다 이 중 하나를 무작위로 골라 사용합니다.
"""

import glob
import os
import random

import replicate

BASE_IMAGE_DIR = os.environ.get("PERSONA_BASE_IMAGE_DIR", "assets/persona_base")
MODEL = "black-forest-labs/flux-kontext-pro"

# 인물 정체성(얼굴/신원)만 유지하고, 옷차림/표정/포즈는 장면에 맞게 자유롭게
# 바꾸도록 지시합니다. "same overall style" 같은 문구는 일부러 넣지 않았습니다.
# (넣으면 원본 사진의 옷차림까지 그대로 고정되어 버립니다.)
IDENTITY_LOCK_INSTRUCTION = (
    "Keep the exact same person, same face, same identity, and same hairstyle "
    "as the reference image. Everything else should adapt naturally to this "
    "new scene: "
)

# 태국(파타야)은 연중 덥고 습한 열대 기후이므로, 장면 설명에 계절/날씨가
# 따로 명시되지 않는 한 반팔/민소매/원피스 등 여름 옷차림을 기본으로 하도록
# 강제합니다. 이게 없으면 원본 사진의 옷차림(예: 긴팔)을 그대로 따라가기 쉽습니다.
CLIMATE_INSTRUCTION = (
    "This is Pattaya, Thailand — a tropical location that is warm and humid "
    "year-round. Unless the scene says otherwise, dress the person in light, "
    "breathable summer clothing appropriate for hot weather (short sleeves, "
    "tank tops, summer dresses, shorts, etc.), not long sleeves or heavy "
    "layers. "
)

# 매번 같은 무표정/원본 표정이 반복되지 않도록, 표정을 매번 무작위로 지정합니다.
EXPRESSIONS = [
    "smiling naturally",
    "laughing candidly",
    "relaxed with a soft smile",
    "focused and slightly serious",
    "playful, mid-laugh",
    "calm and thoughtful",
    "genuinely happy, eyes crinkled",
    "casually smirking",
]


def _pick_base_image() -> str:
    """assets/persona_base/ 폴더 안의 이미지 파일 중 하나를 무작위로 골라 경로를 반환."""
    candidates = sorted(
        glob.glob(os.path.join(BASE_IMAGE_DIR, "*.jpg"))
        + glob.glob(os.path.join(BASE_IMAGE_DIR, "*.jpeg"))
        + glob.glob(os.path.join(BASE_IMAGE_DIR, "*.png"))
    )
    if not candidates:
        raise FileNotFoundError(
            f"{BASE_IMAGE_DIR} 폴더에 기준 인물 사진이 없습니다. "
            "assets/persona_base/ 폴더를 만들고 사진을 1장 이상 넣어두세요."
        )
    return random.choice(candidates)


def generate_persona_image(scene_description: str, output_path: str = "output_image.png") -> str:
    """기준 인물 사진 중 하나를 무작위로 골라, scene_description에 맞는 새
    배경/옷차림/표정으로 변형해서 output_path에 저장하고, 저장된 경로를 반환합니다.

    실패 시 예외를 던지므로, 호출하는 쪽(main_post.py)에서 이미지 생성 실패를
    텍스트만 게시하는 것으로 처리할 수 있도록 try/except로 감싸는 것을 권장합니다.
    """
    base_image_path = _pick_base_image()
    expression = random.choice(EXPRESSIONS)

    prompt = (
        IDENTITY_LOCK_INSTRUCTION
        + CLIMATE_INSTRUCTION
        + f"Facial expression: {expression}. "
        + "Scene: "
        + scene_description
    )

    with open(base_image_path, "rb") as base_image_file:
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

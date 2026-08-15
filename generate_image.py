"""
기준 인물 사진(assets/persona_base/Photo_1.jpg)을 오늘의 트윗 주제에 맞는
배경/상황/옷차림/표정/포즈/구도/조명으로 변형해서 이미지를 생성하는 모듈.

사용 모델: Replicate 의 black-forest-labs/flux-kontext-pro
  - 입력: 기준 이미지 + 텍스트 지시
  - 출력: 인물의 얼굴/정체성은 유지하면서 나머지 요소가 모두 바뀐 새 이미지

환경 변수:
  REPLICATE_API_TOKEN - Replicate API 토큰 (replicate.com/account/api-tokens 에서 발급)

준비물:
  assets/persona_base/Photo_1.jpg 를 반드시 넣어두세요.
  이 사진이 모든 생성 이미지의 얼굴/정체성 기준점입니다.

다양성 확보 방식:
  얼굴은 항상 Photo_1로 고정하되, 아래 요소들을 매번 무작위로 조합해서
  같은 인물이라도 사진마다 느낌이 다르게 나오도록 합니다:
    - 표정 (EXPRESSIONS)
    - 포즈/동작 (POSES)
    - 카메라 구도 (FRAMINGS)
    - 조명/시간대 (LIGHTING)
  배경/상황 자체는 generate_content.py 의 TOPIC_SEEDS 에서 넘어옵니다.
"""

import os
import random

import replicate

BASE_IMAGE_DIR = os.environ.get("PERSONA_BASE_IMAGE_DIR", "assets/persona_base")
# 모든 생성 이미지의 정체성 기준점이 되는 사진. 이 파일 하나만 사용합니다.
PRIMARY_BASE_IMAGE_FILENAME = os.environ.get("PERSONA_PRIMARY_IMAGE", "Photo_1.jpg")
BASE_IMAGE_PATH = os.path.join(BASE_IMAGE_DIR, PRIMARY_BASE_IMAGE_FILENAME)

MODEL = "black-forest-labs/flux-kontext-pro"

# 인물 정체성(얼굴/신원)만 유지하고, 나머지는 장면에 맞게 자유롭게 바꾸도록
# 지시합니다. "same overall style" 같은 문구는 일부러 넣지 않았습니다.
# (넣으면 원본 사진의 옷차림/구도까지 그대로 고정되어 버립니다.)
IDENTITY_LOCK_INSTRUCTION = (
    "Keep the exact same person, same face, same identity, and same hairstyle "
    "as the reference image. Everything else should adapt naturally to this "
    "new scene: "
)

# 태국(파타야)은 연중 덥고 습한 열대 기후이므로, 장면 설명에 계절/날씨가
# 따로 명시되지 않는 한 반팔/민소매/원피스 등 여름 옷차림을 기본으로 하도록
# 강제합니다.
CLIMATE_INSTRUCTION = (
    "This is Pattaya, Thailand — a tropical location that is warm and humid "
    "year-round. Unless the scene says otherwise, dress the person in light, "
    "breathable summer clothing appropriate for hot weather (short sleeves, "
    "tank tops, summer dresses, shorts, etc.), not long sleeves or heavy "
    "layers. "
)

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

# 매번 다른 동작/포즈로 "같은 사진 재탕" 느낌을 줄입니다.
POSES = [
    "standing casually",
    "sitting down, relaxed posture",
    "mid-stride, walking naturally",
    "leaning against something nearby",
    "looking slightly off to the side, candid moment",
    "turned slightly away from camera, looking back over shoulder",
    "hands doing something natural for the scene (holding a drink, phone, gym equipment, etc.)",
    "caught in a natural, unposed candid moment",
]

# 클로즈업/반신/전신을 섞어서 매번 같은 구도가 반복되지 않도록 합니다.
FRAMINGS = [
    "close-up portrait shot, shoulders and face filling most of the frame",
    "medium shot from the waist up",
    "wider full-body shot showing the whole scene around her",
    "candid phone-camera style shot, slightly casual framing",
]

# 조명/시간대 변주. TOPIC_SEEDS의 장면 설명과 겹치지 않는 경우에만 자연스럽게 적용됩니다.
LIGHTING = [
    "soft natural daylight",
    "warm golden-hour lighting",
    "bright midday sun",
    "soft indoor lighting",
    "cozy evening lighting with warm tones",
]


def generate_persona_image(scene_description: str, output_path: str = "output_image.png") -> str:
    """기준 인물 사진(Photo_1)을 scene_description에 맞는 새 배경으로 변형하면서,
    표정/포즈/구도/조명을 무작위로 조합해 매번 다른 느낌의 이미지를 생성합니다.
    결과를 output_path에 저장하고, 저장된 경로를 반환합니다.

    실패 시 예외를 던지므로, 호출하는 쪽(main_post.py)에서 이미지 생성 실패를
    텍스트만 게시하는 것으로 처리할 수 있도록 try/except로 감싸는 것을 권장합니다.
    """
    if not os.path.exists(BASE_IMAGE_PATH):
        raise FileNotFoundError(
            f"기준 인물 사진을 찾을 수 없습니다: {BASE_IMAGE_PATH}. "
            f"{BASE_IMAGE_DIR} 폴더에 {PRIMARY_BASE_IMAGE_FILENAME} 를 넣어두세요."
        )

    expression = random.choice(EXPRESSIONS)
    pose = random.choice(POSES)
    framing = random.choice(FRAMINGS)
    lighting = random.choice(LIGHTING)

    prompt = (
        IDENTITY_LOCK_INSTRUCTION
        + CLIMATE_INSTRUCTION
        + f"Facial expression: {expression}. "
        + f"Pose: {pose}. "
        + f"Camera framing: {framing}. "
        + f"Lighting: {lighting}. "
        + "Scene: "
        + scene_description
    )

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

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
# 프롬프트 안에 바꿔야 할 요소가 많아질수록 얼굴 일관성이 흐트러지는 경향이
# 있어서, 이 지시를 맨 앞뿐 아니라 맨 뒤에도 한 번 더 반복해서 강조합니다.
IDENTITY_LOCK_INSTRUCTION = (
    "CRITICAL — most important rule: this must be the exact same person as "
    "the reference image. Keep her face, facial features, and identity "
    "completely unchanged and recognizable as the same individual — this "
    "matters more than any other instruction below. Keep the same hairstyle. "
    "Everything else (background, clothing, pose, lighting) should adapt "
    "naturally to this new scene: "
)

IDENTITY_LOCK_REMINDER = (
    " Reminder: the face must remain identical to the reference image, "
    "unchanged — same person, clearly recognizable."
)

# 태국(파타야)은 연중 덥고 습한 열대 기후이므로, 무겁고 두꺼운 옷(패딩,
# 니트, 자켓 등)은 피하도록 기본 원칙만 잡아줍니다. 구체적인 옷차림 자체는
# 아래 CLOTHING_STYLES 에서 매번 무작위로 골라 지정합니다.
CLIMATE_INSTRUCTION = (
    "This is Pattaya, Thailand — a tropical location that is hot and humid "
    "year-round. Avoid heavy, cold-weather clothing (padded jackets, thick "
    "sweaters, winter coats), unless the scene explicitly describes a cold "
    "or heavily air-conditioned indoor setting. "
)

# 체형 일관성을 위한 고정 지시 (매번 랜덤이 아니라 항상 동일하게 적용).
BODY_TYPE_INSTRUCTION = (
    "Body type: slim and slender build, with a curvy, hourglass silhouette "
    "(defined waist, fuller bust and hips proportionate to her slim frame). "
    "Keep this body type consistent in every image. "
)

# 매번 무작위로 고르는 옷차림. 치마+스타킹 조합을 포함해 여러 스타일을
# 섞어서, 매번 같은 옷차림(예: 운동복)만 반복되지 않도록 합니다.
# 장면 자체가 특정 복장을 요구하면(예: 헬스장) 그 장면 설명이 우선 적용되도록
# 프롬프트에서 안내 문구를 같이 넣습니다.
CLOTHING_STYLES = [
    "a casual skirt with sheer stockings and a fitted top",
    "a knee-length skirt with knee-high stockings and sneakers",
    "a short sundress",
    "a skirt with a simple casual blouse",
    "shorts and a casual t-shirt",
    "a tank top and shorts",
    "a casual off-shoulder top with a skirt",
    "relaxed loungewear (oversized t-shirt and shorts) for a day at home",
]

CLOTHING_INSTRUCTION_TEMPLATE = (
    "Clothing: {style}. If the scene itself clearly calls for specific "
    "attire (for example, workout clothes for a gym scene), use that "
    "instead of this default. "
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
# 얼굴이 가려지거나 잘 안 보이는 포즈(뒷모습 등)는 정체성 일관성을 해치므로 제외했습니다.
POSES = [
    "standing casually, facing the camera",
    "sitting down, relaxed posture, facing the camera",
    "mid-stride, walking naturally, facing slightly toward the camera",
    "leaning against something nearby, facing the camera",
    "looking slightly off to the side but face clearly visible, candid moment",
    "hands doing something natural for the scene (holding a drink, phone, gym equipment, etc.), facing the camera",
    "caught in a natural, unposed candid moment, face clearly visible",
]

# 클로즈업/상반신 위주로만 구성합니다. 전신 샷은 얼굴이 화면에서 작아져
# 정체성 일관성이 떨어지는 경향이 있어 제외했습니다.
FRAMINGS = [
    "close-up portrait shot, shoulders and face filling most of the frame",
    "medium shot from the waist up, face clearly visible and in focus",
    "candid phone-camera style shot, medium framing, face clearly visible",
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
    clothing_style = random.choice(CLOTHING_STYLES)

    prompt = (
        IDENTITY_LOCK_INSTRUCTION
        + BODY_TYPE_INSTRUCTION
        + CLIMATE_INSTRUCTION
        + CLOTHING_INSTRUCTION_TEMPLATE.format(style=clothing_style)
        + f"Facial expression: {expression}. "
        + f"Pose: {pose}. "
        + f"Camera framing: {framing}. "
        + f"Lighting: {lighting}. "
        + "Scene: "
        + scene_description
        + IDENTITY_LOCK_REMINDER
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
    # 로컬 테스트용: 매번 generate_content.py의 TOPIC_SEEDS 중 무작위 장면을 사용합니다.
    from generate_content import pick_topic

    _, test_scene = pick_topic()
    print(f"이번 테스트 장면: {test_scene}")
    path = generate_persona_image(test_scene)
    print(f"이미지 생성 완료: {path}")

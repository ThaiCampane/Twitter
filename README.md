# X(트위터) 자동 포스팅 봇

태국 파타야에 거주하는 여성 페르소나로, 하루 1~2건의 트윗(텍스트+이미지)을
불특정 시간에 자동 생성/게시하는 시스템입니다. 서버 없이 GitHub Actions로만
동작합니다.

> **중요 — 공개 표기 안내**
> 이 계정이 AI로 생성된 가상 캐릭터라면, X 프로필/소개글에 그 사실을
> 명시하는 것을 권장합니다 (예: "AI-generated persona / virtual character").
> 실사와 구분이 어려운 합성 이미지를 사람인 것처럼 꾸며 게시하는 계정은
> 플랫폼 정책상 제재 대상이 될 수 있습니다.

## 동작 방식

1. **매일 새벽** `schedule_daily.yml` 워크플로우가 실행되어 오늘 올릴
   랜덤 시각(1~2개, 08:00~23:00 방콕 시간 사이)을 `schedule.json`에 저장합니다.
2. **15분마다** `check_and_post.yml` 워크플로우가 실행되어, 예정 시각이
   지났고 아직 안 올린 슬롯이 있으면:
   - 오늘의 주제를 하나 뽑고
   - Claude API로 그 주제에 맞는 트윗 텍스트를 생성하고
   - Replicate(Flux Kontext)로 기준 인물 사진을 같은 주제의 배경/상황으로
     변형한 이미지를 생성하고
   - 텍스트+이미지를 함께 X에 게시합니다.
   - 이미지 생성이 실패하면 자동으로 텍스트만 게시합니다.

## 설정 방법

### 1) 이 폴더를 새 GitHub 레포에 올리기

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

### 2) X Developer 계정 준비

1. https://developer.x.com 에서 Project + App 생성
2. App 권한을 **Read and Write**로 설정 (기본값은 Read only라 반드시 바꿔야 함)
3. Keys and tokens 탭에서 아래 4개 발급:
   - API Key / API Key Secret
   - Access Token / Access Token Secret
     (권한을 바꾼 뒤라면 재발급 필요)
4. Pay-Per-Use 크레딧을 소액 충전 (하루 1~2건이면 월 $1 미만이면 충분)

### 3) Anthropic API 키 준비

https://console.anthropic.com 에서 API 키 발급.

### 4) Replicate API 토큰 준비 (이미지 생성용)

1. https://replicate.com 가입 후 https://replicate.com/account/api-tokens 에서
   토큰 발급
2. 결제 수단 등록 (이미지 1장당 과금, flux-kontext-pro 기준 장당 대략
   몇 센트 수준 — 정확한 가격은 Replicate 모델 페이지에서 확인하세요)

### 5) 기준 인물 사진 준비

- 본인 사진을 기반으로 스타일 변형/캐릭터화한 이미지 1장을 준비해서
  `assets/persona_base.jpg` 로 레포에 커밋하세요.
- 정면이 잘 보이고 배경이 단순한 사진일수록 이후 배경 합성 결과가 자연스럽습니다.
- 이 파일 경로는 `PERSONA_BASE_IMAGE` 환경변수로 바꿀 수 있습니다.

### 6) GitHub Secrets 등록

레포 → Settings → Secrets and variables → Actions → New repository secret
으로 아래 6개를 등록하세요.

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic 콘솔에서 발급받은 키 |
| `REPLICATE_API_TOKEN` | Replicate에서 발급받은 토큰 |
| `X_API_KEY` | X Developer Portal API Key |
| `X_API_SECRET` | X Developer Portal API Key Secret |
| `X_ACCESS_TOKEN` | X Developer Portal Access Token |
| `X_ACCESS_SECRET` | X Developer Portal Access Token Secret |

### 7) 동작 확인

Actions 탭에서 두 워크플로우를 각각 "Run workflow"로 수동 실행해보세요.

- `schedule_daily.yml` 실행 → `schedule.json` 파일이 생성/커밋되는지 확인
- `check_and_post.yml` 실행 → (스케줄 시각이 지나 있다면) 실제로 텍스트+이미지가
  게시되는지 확인

이후로는 cron이 자동으로 돌아갑니다.

## 커스터마이징

- **페르소나/문체**: `generate_content.py` 의 `PERSONA_SYSTEM_PROMPT`
- **주제 및 이미지 장면**: `generate_content.py` 의 `TOPIC_SEEDS`
  (텍스트 주제, 이미지 장면 설명이 쌍으로 묶여 있어 서로 어긋나지 않습니다)
- **이미지 스타일/인물 유지 지시**: `generate_image.py` 의
  `IDENTITY_LOCK_INSTRUCTION`
- **포스팅 시간대**: `schedule_manager.py` 의 `WINDOW_START_HOUR`,
  `WINDOW_END_HOUR`
- **하루 포스팅 개수**: `schedule_manager.py` 의 `MIN_POSTS_PER_DAY`,
  `MAX_POSTS_PER_DAY`
- **타임존**: `POST_TIMEZONE` 환경변수 (기본 `Asia/Bangkok`)

## 로컬 테스트

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY=...
python generate_content.py   # 트윗 문구만 생성해서 출력 (게시 안 함)

export REPLICATE_API_TOKEN=...
python generate_image.py     # 기준 사진을 테스트 장면으로 변형해서 저장 (게시 안 함)

export X_API_KEY=... X_API_SECRET=... X_ACCESS_TOKEN=... X_ACCESS_SECRET=...
python post_to_x.py          # 테스트 문구를 실제로 게시함 (주의)
```

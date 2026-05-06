"""
idol_screener/config.py
━━━━━━━━━━━━━━━━━━━━━━
설정값, 임계치, 경로 상수
"""

import os
from pathlib import Path

# ── 경로 ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
REPORT_DIR = BASE_DIR / "reports"

DOWNLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# ── 다운로드 설정 ────────────────────────────────────────
MAX_VIDEO_DURATION = 600      # 최대 10분
PREFERRED_FORMAT = "mp4"
AUDIO_FORMAT = "wav"
AUDIO_SAMPLE_RATE = 22050     # librosa 기본

# ── 오디오 분석 파라미터 ─────────────────────────────────
MFCC_N_COEFFS = 13            # MFCC 계수 수
MFCC_HOP_LENGTH = 512
MFCC_N_FFT = 2048
SEGMENT_DURATION = 3.0        # 음색 분석 세그먼트 길이 (초)
SEGMENT_HOP = 1.5             # 세그먼트 간격 (초)

# ── 영상 분석 파라미터 ───────────────────────────────────
FRAME_SAMPLE_FPS = 10         # 초당 샘플링 프레임 수
POSE_MIN_DETECTION_CONFIDENCE = 0.5
POSE_MIN_TRACKING_CONFIDENCE = 0.5
FACE_MIN_DETECTION_CONFIDENCE = 0.5

# ── 고유성 스크리닝 임계치 ───────────────────────────────
# ★ 회사 헌법: 종합 점수/합산/가중평균 영구 금지
# 통과 조건: 어느 한 차원이라도 극단값이면 통과 (OR 논리)
# PASS_AVG_THRESHOLD 삭제됨 — 합산 평균 판정은 존재하지 않음
OUTLIER_THRESHOLD = 0.7       # 이 이상이면 극단값(오른쪽 꼬리)
OUTLIER_LOW_THRESHOLD = 0.15  # 이 이하이면 극단값(왼쪽 꼬리 — 초이질)

# ── 6개 고유성 지표 ID ───────────────────────────────────
UNIQUENESS_INDICATORS = {
    1:  "음색 고유성",          # Timbre Uniqueness
    2:  "음색 판별력",          # Timbre Identifiability
    36: "리듬 인격",            # Rhythm Personality
    50: "동작 개인 식별도",     # Movement Identity
    64: "비주얼 잔상",          # Visual Afterimage
    83: "개인 표정 시그니처",   # Signature Expression
}

# ★ 지표별 가중치 삭제됨 — 차원 간 합산/가중 평균은 존재하지 않음
# 각 차원은 독립적으로 극단값 여부만 판정

# ── 신뢰도 기본값 ────────────────────────────────────────
# 각 분석 모듈이 반환하는 신뢰도는 0~1
# 아래는 입력 데이터 유형별 신뢰도 상한
CONFIDENCE_CAPS = {
    "vocal_video": 0.7,       # 보컬 영상에서 오디오 추출
    "vocal_audio": 0.85,      # 고품질 오디오 직접 입력
    "dance_video": 0.7,       # 댄스 영상 (포즈 분석)
    "face_video": 0.6,        # 표정/비주얼 (해상도 의존)
    "face_video_hd": 0.75,    # 고해상도 얼굴 영상
}

# ── 보컬 세부 지표 (v2 — 보컬 해상도 극대화) ───────────
VOCAL_SUB_INDICATORS = {
    "tone_quadrant": "톤 사분면",           # 청량/따뜻/묵직/건조
    "vocal_register": "성역대 구조",        # 흉성/두성/믹스 비율
    "vibrato_character": "비브라토 특성",    # 속도, 깊이, 규칙성
    "dynamic_range": "다이내믹 레인지",      # 성량 변화 폭
    "vocal_attack": "어택 클린도",          # 발성 시작점 선명도
    "breathiness": "호흡성(기식감)",         # 목소리의 공기 섞임 정도
    "pitch_range": "음역대 폭",            # 추정 가용 음역대
    "resonance_pattern": "공명 패턴",       # 포먼트 특성
}

# ── 톤 4사분면 정의 ──────────────────────────────────────
# X축: 밝기(Spectral Centroid) — 낮으면 어둡고, 높으면 밝다
# Y축: 무게(저주파 에너지 비율) — 낮으면 가볍고, 높으면 묵직하다
TONE_QUADRANTS = {
    "bright_light": {"ko": "청량", "desc": "밝고 가벼운 톤", "example": "솔라(마마무)"},
    "warm_light": {"ko": "따뜻", "desc": "따뜻하고 부드러운 톤", "example": "휘인(마마무)"},
    "dark_heavy": {"ko": "묵직", "desc": "어둡고 무게감 있는 톤", "example": "화사(마마무)"},
    "bright_heavy": {"ko": "건조", "desc": "밝지만 거친/각진 톤", "example": "문별(마마무)"},
}

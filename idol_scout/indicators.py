"""
idol_scout_v1/indicators.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
100개 지표 레지스트리 — 정의, 카테고리, 측정 단계, 고유성/타고남 플래그
"""

from .models import IndicatorDef, Category, Tier


def build_indicator_registry() -> dict[int, IndicatorDef]:
    """100개 지표 정의를 딕셔너리로 반환 (key = indicator_id)"""

    defs = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 一. 보컬 (1~25)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    defs.extend([
        IndicatorDef(1,  "음색 고유성",          "Timbre Uniqueness",       Category.VOCAL, Tier.SINGLE_VIDEO, is_uniqueness=True, is_innate_marker=True,
                     description="DB 샘플 대비 유사도. 낮을수록 독보적"),
        IndicatorDef(2,  "음색 판별력",          "Timbre Identifiability",  Category.VOCAL, Tier.SINGLE_VIDEO, is_uniqueness=True, is_innate_marker=True,
                     description="3초만 들어도 이 사람인 걸 아는가"),
        IndicatorDef(3,  "음정 평균 편차",       "Pitch Avg Deviation",     Category.VOCAL, Tier.SINGLE_VIDEO,
                     description="센트 단위 음정 오차"),
        IndicatorDef(4,  "음정 안정성",          "Pitch Stability",         Category.VOCAL, Tier.CROSS_VIDEO,
                     description="동일 구간 반복 시 흔들림"),
        IndicatorDef(5,  "총 음역대 폭",         "Total Range",             Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(6,  "편안한 음역대 폭",     "Comfortable Range",       Category.VOCAL, Tier.CROSS_VIDEO),
        IndicatorDef(7,  "흉성 품질",            "Chest Voice Quality",     Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(8,  "두성 품질",            "Head Voice Quality",      Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(9,  "믹스 보이스 능력",     "Mix Voice",               Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(10, "가성 품질",            "Falsetto Quality",        Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(11, "파사지오 전환",        "Passaggio Smoothness",    Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(12, "호흡 길이",            "Breath Length",           Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(13, "운동 중 호흡 안정성",  "Dance Breath Stability",  Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(14, "비브라토 자연스러움",   "Vibrato Naturalness",     Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(15, "비브라토 제어력",       "Vibrato Control",         Category.VOCAL, Tier.CROSS_VIDEO),
        IndicatorDef(16, "성량 다이내믹 범위",   "Dynamic Range",           Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(17, "딕션 명료도",          "Diction Clarity",         Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(18, "자연 성량 투사력",     "Natural Projection",      Category.VOCAL, Tier.SINGLE_VIDEO, is_innate_marker=True),
        IndicatorDef(19, "목소리 감정 변화 폭",  "Vocal Emotion Range",     Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(20, "어택 클린도",          "Attack Clarity",          Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(21, "노래 시 리듬 정확도",  "Vocal Rhythm Accuracy",   Category.VOCAL, Tier.SINGLE_VIDEO),
        IndicatorDef(22, "비트와의 본능적 관계", "Beat Relationship",       Category.VOCAL, Tier.SINGLE_VIDEO, is_innate_marker=True,
                     description="앞서가는지/정확히/뒤로 끌리는지"),
        IndicatorDef(23, "배음 풍부도",          "Harmonic Richness",       Category.VOCAL, Tier.SINGLE_VIDEO, is_innate_marker=True),
        IndicatorDef(24, "즉흥 성향",            "Improvisation Tendency",  Category.VOCAL, Tier.CROSS_VIDEO),
        IndicatorDef(25, "성대 피로 내성",       "Vocal Fatigue Resistance",Category.VOCAL, Tier.CROSS_VIDEO),
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 二. 신체 및 댄스 (26~50)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    defs.extend([
        IndicatorDef(26, "동작-비트 싱크 정밀도", "Beat Sync Precision",    Category.DANCE, Tier.SINGLE_VIDEO,
                     description="밀리초 단위"),
        IndicatorDef(27, "아이솔레이션",          "Isolation",              Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(28, "전신 코디네이션",       "Full Body Coordination", Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(29, "중심 이동 유연도",      "Center Shift Fluidity",  Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(30, "공간 인지력",           "Spatial Awareness",      Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(31, "동작 크기 조절력",      "Movement Scaling",       Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(32, "코어 안정성",           "Core Stability",         Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(33, "상체 표현력",           "Upper Body Expression",  Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(34, "하체 파워 및 제어력",   "Lower Body Control",     Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(35, "자연 그루브",           "Natural Groove",         Category.DANCE, Tier.SINGLE_VIDEO, is_innate_marker=True,
                     description="안무 없이 음악에 반응하는 본능적 움직임"),
        IndicatorDef(36, "리듬 인격",             "Rhythm Personality",     Category.DANCE, Tier.SINGLE_VIDEO, is_uniqueness=True, is_innate_marker=True,
                     description="비트와의 고유 시간 관계(ms). 불변적. 그룹 조합 핵심"),
        IndicatorDef(37, "동작 독창성",           "Movement Originality",   Category.DANCE, Tier.SINGLE_VIDEO, is_innate_marker=True),
        IndicatorDef(38, "훈련 흔적 비율",        "Training Trace Ratio",   Category.DANCE, Tier.SINGLE_VIDEO, is_innate_marker=True,
                     description="학원식 템플릿 비중 — 타고남/훈련 분리 핵심"),
        IndicatorDef(39, "즉흥 능력",             "Improvisation Ability",  Category.DANCE, Tier.CROSS_VIDEO),
        IndicatorDef(40, "습득 속도",             "Learning Speed",         Category.DANCE, Tier.CROSS_VIDEO),
        IndicatorDef(41, "신체 기억력",           "Body Memory",            Category.DANCE, Tier.CROSS_VIDEO),
        IndicatorDef(42, "동작의 음악성",         "Movement Musicality",    Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(43, "에너지 조절력",         "Energy Modulation",      Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(44, "체력 지표",             "Stamina",                Category.DANCE, Tier.CROSS_VIDEO),
        IndicatorDef(45, "동작 날카로움",         "Hit Sharpness",          Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(46, "트랜지션 매끄러움",     "Transition Smoothness",  Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(47, "플로어 무브 능력",      "Floor Move",             Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(48, "유연성",                "Flexibility",            Category.DANCE, Tier.SINGLE_VIDEO),
        IndicatorDef(49, "무대 vs 연습 갭",       "Stage-Practice Gap",     Category.DANCE, Tier.CROSS_VIDEO),
        IndicatorDef(50, "동작 개인 식별도",      "Movement Identity",      Category.DANCE, Tier.SINGLE_VIDEO, is_uniqueness=True, is_innate_marker=True,
                     description="실루엣만 보고 이 사람인 걸 아는가"),
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 三. 비주얼 및 카메라 (51~65)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    defs.extend([
        IndicatorDef(51, "얼굴 주목도",           "Face Attention",         Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(52, "얼굴 고유성",           "Face Uniqueness",        Category.VISUAL, Tier.SINGLE_VIDEO, is_innate_marker=True),
        IndicatorDef(53, "얼굴 대칭도",           "Face Symmetry",          Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(54, "카메라 전환 효과",      "Camera Transfer",        Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(55, "다각도 촬영 적합성",    "Multi-Angle Fitness",    Category.VISUAL, Tier.CROSS_VIDEO),
        IndicatorDef(56, "미소 식별도",           "Smile Identity",         Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(57, "눈빛 표현 범위",        "Eye Expression Range",   Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(58, "본능적 카메라 인지",    "Camera Awareness",       Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(59, "정지 컷 매력",          "Still Cut Appeal",       Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(60, "동적 화면 매력",        "Dynamic Appeal",         Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(61, "스타일링 가소성",       "Styling Versatility",    Category.VISUAL, Tier.CROSS_VIDEO),
        IndicatorDef(62, "신체 비율",             "Body Proportion",        Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(63, "자세 및 체태",          "Posture",                Category.VISUAL, Tier.SINGLE_VIDEO),
        IndicatorDef(64, "비주얼 잔상",           "Visual Afterimage",      Category.VISUAL, Tier.SINGLE_VIDEO, is_uniqueness=True, is_innate_marker=True,
                     description="영상 후 얼굴 기억 지속 시간"),
        IndicatorDef(65, "나이 인상",             "Age Impression",         Category.VISUAL, Tier.SINGLE_VIDEO),
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 四. 표정 및 감정 전달 (66~85)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    defs.extend([
        IndicatorDef(66, "미세 표정 빈도",        "Micro Expression Freq",  Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(67, "미세 표정 진위도",      "Micro Expression Auth",  Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(68, "감정 범위",             "Emotion Range",          Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(69, "감정 전환 속도",        "Emotion Switch Speed",   Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(70, "카메라 눈맞춤",         "Camera Eye Contact",     Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(71, "미소 진정성",           "Smile Authenticity",     Category.EXPRESSION, Tier.SINGLE_VIDEO, is_innate_marker=True),
        IndicatorDef(72, "감정 강도 조절력",      "Emotion Intensity Ctrl", Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(73, "취약함 표현 능력",      "Vulnerability Expr",     Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(74, "자신감 자연스러움",     "Confidence Naturalness", Category.EXPRESSION, Tier.SINGLE_VIDEO, is_innate_marker=True),
        IndicatorDef(75, "표정 스토리텔링",       "Facial Storytelling",    Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(76, "안면 근육군 다양성",    "Facial Muscle Variety",  Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(77, "표정-음악 매칭도",      "Expression-Music Match", Category.EXPRESSION, Tier.SINGLE_VIDEO),
        IndicatorDef(78, "감정 회복 속도",        "Emotion Recovery",       Category.EXPRESSION, Tier.CROSS_VIDEO),
        IndicatorDef(79, "진짜/연기 감정 비율",   "Real vs Act Ratio",      Category.EXPRESSION, Tier.SINGLE_VIDEO, is_innate_marker=True),
        IndicatorDef(80, "관객 반응 지표",        "Audience Response",      Category.EXPRESSION, Tier.CROSS_VIDEO),
        IndicatorDef(81, "표정 일관성",           "Expression Consistency", Category.EXPRESSION, Tier.CROSS_VIDEO),
        IndicatorDef(82, "표정 성장 변화",        "Expression Growth",      Category.EXPRESSION, Tier.CROSS_VIDEO),
        IndicatorDef(83, "개인 표정 시그니처",    "Signature Expression",   Category.EXPRESSION, Tier.SINGLE_VIDEO, is_uniqueness=True, is_innate_marker=True,
                     description="이 사람에게만 있는 고유 표정"),
        IndicatorDef(84, "압박 상황 감정 진정성", "Pressure Authenticity",  Category.EXPRESSION, Tier.CROSS_VIDEO),
        IndicatorDef(85, "비언어 커뮤니케이션",   "Nonverbal Communication",Category.EXPRESSION, Tier.SINGLE_VIDEO),
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 五. 무대 장악력 및 흡인력 (86~95)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    defs.extend([
        IndicatorDef(86, "카메라 포착 의식",      "Camera Tracking",        Category.STAGE, Tier.SINGLE_VIDEO),
        IndicatorDef(87, "에너지 투사 거리",      "Energy Projection",      Category.STAGE, Tier.SINGLE_VIDEO),
        IndicatorDef(88, "시선 포착 속도",        "Gaze Capture Speed",     Category.STAGE, Tier.SINGLE_VIDEO),
        IndicatorDef(89, "시선 유지 시간",        "Gaze Retention",         Category.STAGE, Tier.SINGLE_VIDEO),
        IndicatorDef(90, "공간 지배력",           "Space Dominance",        Category.STAGE, Tier.SINGLE_VIDEO),
        IndicatorDef(91, "관객 소통",             "Audience Communication", Category.STAGE, Tier.CROSS_VIDEO),
        IndicatorDef(92, "자신감-실력 일치도",    "Confidence-Skill Match", Category.STAGE, Tier.SINGLE_VIDEO),
        IndicatorDef(93, "실수 회복 능력",        "Mistake Recovery",       Category.STAGE, Tier.CROSS_VIDEO),
        IndicatorDef(94, "종합 시선 끌림 지수",   "Attention Magnet Index", Category.STAGE, Tier.SINGLE_VIDEO, is_uniqueness=False,
                     description="다인 화면에서 무의식적으로 따라가는 확률"),
        IndicatorDef(95, "솔로 컷 장악력",        "Solo Cut Command",       Category.STAGE, Tier.SINGLE_VIDEO),
    ])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 六. 성장 잠재력 (96~100) — 시스템 최종 출력
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    defs.extend([
        IndicatorDef(96, "보컬 성장률",           "Vocal Growth Rate",      Category.GROWTH, Tier.CROSS_VIDEO),
        IndicatorDef(97, "신체 성장률",           "Physical Growth Rate",   Category.GROWTH, Tier.CROSS_VIDEO),
        IndicatorDef(98, "표현력 성장률",         "Expression Growth Rate", Category.GROWTH, Tier.CROSS_VIDEO),
        IndicatorDef(99, "천부적 비율",           "Innate Talent Ratio",    Category.GROWTH, Tier.CROSS_VIDEO, is_innate_marker=True,
                     description="현재 실력 중 타고난 vs 훈련 추정 비율"),
        IndicatorDef(100,"종합 성장 궤적 기울기", "Overall Growth Slope",   Category.GROWTH, Tier.CROSS_VIDEO),
    ])

    return {d.id: d for d in defs}


# ── 지표 메타 통계 ────────────────────────────────────────────────────

REGISTRY = build_indicator_registry()

UNIQUENESS_IDS = sorted(d.id for d in REGISTRY.values() if d.is_uniqueness)
# → [1, 2, 36, 50, 64, 83]

INNATE_MARKER_IDS = sorted(d.id for d in REGISTRY.values() if d.is_innate_marker)

TIER1_IDS = sorted(d.id for d in REGISTRY.values() if d.tier == Tier.SINGLE_VIDEO)
TIER2_IDS = sorted(d.id for d in REGISTRY.values() if d.tier == Tier.CROSS_VIDEO)

# 11변수 ← 100지표 매핑
INTERPRET_MAPPING = {
    "SDI": [1, 2, 50, 52, 64, 83],
    "EDT": [24, 37, 39],
    "CER": [54, 58, 70, 86],
    "RMC": [26, 36, 42, 22],
    "AAC": [],      # 3단계(인간) — AI 매핑 없음
    "SCA": [],      # 3단계(인간)
    "CDR": [1, 2, 36, 50, 64, 83],  # 고유성 조합 희소성으로 산출
    "EDI": [87, 88, 89, 90, 94],
    "NVC": [],      # 3단계(인간)
    "CCI": [],      # 3단계(인간)
    "CBP": [],      # 3단계(인간)
}

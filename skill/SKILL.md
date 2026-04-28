---
name: idol-scout
description: "K-POP 아이돌 신인 발굴 AI 스크리닝 분석 도구. YouTube/Instagram URL을 입력받아 6개 고유성 지표를 자동 측정하고, 11개 해석 변수 + 복합지표 + NCPS/RNCS 실패 구조 진단을 수행합니다. 아이돌 분석, 스크리닝, 신인 발굴, URL 분석, 고유성 측정, 음색 분석, 댄스 분석, 아이돌 평가, 잠재력 분석, K-POP 스카우팅, YouTube 영상 분석과 관련된 요청에서 반드시 이 스킬을 사용하세요. 사용자가 YouTube URL을 제공하거나 '이 영상 분석해줘', '스크리닝 해줘', '이 아이돌 분석' 등을 말하면 트리거됩니다."
---

# Idol Scout — AI 아이돌 고유성 스크리닝 분석

## 개요

idol_scout는 K-POP 아이돌 후보의 영상/오디오를 AI로 분석하여 고유성 지표를 측정하고 성공/실패 구조를 진단하는 시스템입니다.

## 시스템 위치

- 패키지: `C:\Users\dkdak\Documents\idol_scout\idol_scout\`
- 대화형 프로그램: `C:\Users\dkdak\Documents\idol_scout\scout.py`
- 파이프라인 스크립트: `C:\Users\dkdak\Documents\idol_scout\run_analysis.py`
- 결과 저장: `C:\Users\dkdak\Documents\idol_scout\analysis_reports\`

## 워크플로우

사용자가 URL을 제공하면:

### Step 1: 정보 수집
AskUserQuestion으로 확인:
- URL (필수)
- 콘텐츠 유형: vocal / dance / auto
- 이름, 영문명, 그룹, 기획사 (선택)

URL이 이미 대화에 있으면 바로 진행.

### Step 2: CONFIG 업데이트
`C:\Users\dkdak\Documents\idol_scout\run_analysis.py`의 CONFIG를 Edit 도구로 수정.

### Step 3: 실행
클립보드에 명령어 복사 (파일 탐색기 접근 필요):
```
cd C:\Users\dkdak\Documents\idol_scout; python run_analysis.py
```
또는 대화형 프로그램:
```
cd C:\Users\dkdak\Documents\idol_scout; python scout.py
```
사용자에게 터미널에서 Ctrl+V → Enter 안내.

### Step 4: 결과 읽기
`analysis_reports/`에서 최신 JSON을 Glob → Read로 읽기.

### Step 5: 결과 해석

#### 6개 고유성 지표
| ID | 지표 | 해석 |
|----|------|------|
| 1 | 음색 고유성 | 0.6+ 우수, 0.4-0.6 보통, <0.4 약함 |
| 2 | 음색 판별력 | 0.7+ 강한 판별력, <0.3 일관성 부족 |
| 36 | 리듬 인격 | 일관성 + 오프셋. ahead/behind/on_beat |
| 50 | 동작 식별도 | (mediapipe 미지원 → 미측정) |
| 64 | 비주얼 잔상 | (mediapipe 미지원 → 미측정) |
| 83 | 표정 시그니처 | (mediapipe 미지원 → 미측정) |

댄스 영상에서는 MR이 재생되므로 음색 지표는 참고 수준.

#### 11개 해석 변수
AI 측정: SDI, EDT, CER, RMC, CDR, EDI
인간 관찰: AAC, SCA, NVC, CCI, CBP (기본값 MID)

#### 복합지표
- 시스템 의존도: 0.8+ 높음(위험), 0.5↓ 자립적
- 전환 준비도: 0.6+ 양호, 0.4↓ 위험
- 노출 전환 효율, 자원 수렴도, 천부적 비율, 성장 궤적

#### NCPS/RNCS 실패 진단
- NCPS 5조건 중 3+ 충족 → 비핵심 포지션 정체 증후군
- RNCS 5조건 중 3+ 충족 → 자원 비수렴 증후군

### Step 6: 후속 안내
1. 추가 URL 분석 (보컬/댄스 교차 검증)
2. 인간 변수 입력 (AAC, SCA, NVC, CCI, CBP)
3. 비교 분석
4. 메모리의 기존 사례(권지용/제니/공민지/전소미) 참조

## 주의사항
- Python 3.14에서 mediapipe 미지원 → 영상 지표(50, 64, 83) 미측정
- 오디오 지표(1, 2, 36)만 자동 측정 가능
- 인간 평가 변수는 기본값 MID
- 복수 스냅샷 없으면 CER, 성장궤적 = 0

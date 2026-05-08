# 璞玉문화 AI 캐스팅 시스템 v1 — Streamlit 대시보드

음원 분석 결과(개념도·인물 분석·검증 결과)를 인터랙티브하게 탐색하는 대시보드.

## 폴더 구조

```
streamlit_app/
├── streamlit_app.py        ← 메인 앱 (9개 페이지)
├── requirements.txt        ← Streamlit Cloud 의존성 (가벼움)
├── README.md               ← 본 파일
├── content/                ← 마크다운 콘텐츠 (선택)
├── images/                 ← 사전 생성 시각화 PNG ★ 필요
│   ├── concept_4member_tone.png
│   ├── concept_11var_radar.png
│   └── concept_hwasa_vs_wheein.png
└── results/                ← 검증 결과 JSON ★ 음원 도착 후
    └── w1_validation_latest.json
```

## 설계 원칙

- **무거운 작업은 로컬/Colab에서**: MERT, DDSP, Demucs 같은 무거운 모델은 본 앱에서 실행하지 않음
- **본 앱은 결과 표시 전용**: 사전 생성된 PNG/JSON을 인터랙티브하게 탐색
- **무료 티어 호환**: Streamlit Community Cloud 무료 등급(1GB RAM, CPU)에서 안정 작동
- **회사 헌법 정합**: 종합 점수 표시 절대 없음, OR 극단값/양쪽 꼬리 강조

## 9개 페이지

1. 🏠 프로젝트 개요
2. 📜 회사 헌법
3. 🗺 7주 로드맵
4. 📊 휘인 정밀 분석
5. 🎵 마마무 4인 톤 4사분면
6. 📈 5인 11변수 비교
7. ⚖ 화사 vs 휘인 대비
8. 🔬 W1 검증 결과 (음원 도착 후 활성)
9. 🛠 1차 모델 구조

## 배포 절차

### 1. GitHub 저장소에 파일 업로드

본 폴더의 모든 파일을 기존 Streamlit 앱의 GitHub 저장소에 push.

기존 `app.py`가 있다면:
- **옵션 A** — 기존 `app.py` 백업 후 본 `streamlit_app.py`를 `app.py`로 이름 변경
- **옵션 B** — 본 파일을 그대로 두고 Streamlit Cloud 설정에서 entry point를 `streamlit_app.py`로 변경

### 2. 시각화 PNG 사전 생성 (필수)

본 앱은 PNG 파일을 표시만 합니다. 다음 절차로 사전 생성:

```python
# 로컬 또는 Colab에서 실행
from visualizers import generate_full_report
generate_full_report('streamlit_app/images/')
```

생성된 3개 PNG를 GitHub `streamlit_app/images/` 폴더에 commit.

### 3. (음원 도착 후) 검증 결과 JSON 업로드

`colab_validation.ipynb` 실행 후 생성된 JSON을:
- 파일명: `w1_validation_latest.json`
- 위치: `streamlit_app/results/`
- GitHub에 commit → Streamlit Cloud 자동 재배포

### 4. Streamlit Cloud 자동 재배포

GitHub push 시 Streamlit Cloud가 자동으로 감지하여 재배포 (약 2~3분 소요).

## 로컬 테스트

배포 전 로컬에서 미리 테스트:

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run streamlit_app.py
```

브라우저에서 `http://localhost:8501` 자동 열림.

## 회사 헌법 정합성

본 앱은 다음 원칙을 시각적·코드적으로 적용:

- ✅ 종합 점수 표시 절대 없음 (모든 페이지에서 차원별 독립 표시)
- ✅ OR 극단값 시각화 (휘인 페이지에서 강한 차원만 굵게)
- ✅ 양쪽 꼬리 (초우월 + 초이질) — W1 결과 페이지에서 outlier_high/outlier_low 분리 표시
- ✅ 상위 0.05% 임계값 강조 (회사 헌법 페이지)

## 참고

- 메인 1차 모델 코드: `code/phase2/idol_scout_v1.py`
- 검증 노트북: `code/phase2/colab_validation.ipynb`
- 휘인 분석: `memory/project_wheein_analysis.md`

"""
╔══════════════════════════════════════════════════╗
║       idol_scout — 대화형 분석 프로그램          ║
║       K-POP 아이돌 AI 고유성 스크리닝            ║
╚══════════════════════════════════════════════════╝

사용법: python scout.py
터미널에서 실행하면 대화형으로 URL을 입력받아 분석합니다.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 패키지 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║       🎤 idol_scout — AI 스크리닝 분석          ║")
    print("║       K-POP 아이돌 고유성 측정 시스템           ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

def print_separator(char="─", width=55):
    print(char * width)

def get_input(prompt, default=""):
    val = input(f"  {prompt}" + (f" [{default}]" if default else "") + ": ").strip()
    return val if val else default

def format_score(score, width=6):
    """점수를 색상 표시와 함께 포맷"""
    if score >= 0.6:
        grade = "★★★"
    elif score >= 0.4:
        grade = "★★☆"
    elif score > 0:
        grade = "★☆☆"
    else:
        grade = "───"
    return f"{score:>{width}.3f}  {grade}"

def format_level(level):
    """레벨을 한글로 변환"""
    mapping = {
        "HIGH": "높음",
        "MID_HIGH": "중상",
        "MID": "중간",
        "MID_LOW": "중하",
        "LOW": "낮음",
    }
    return mapping.get(level, level)

def interpret_indicator(ind_id, score, content_type):
    """지표별 해석 코멘트 생성"""
    if score == 0:
        return "미측정"

    comments = {
        1: {  # 음색 고유성
            "high": "독특한 음색 특성 보유",
            "mid": "보통 수준의 음색 차별화",
            "low": "일반적인 음색 패턴",
        },
        2: {  # 음색 판별력
            "high": "높은 음색 일관성 — 쉽게 식별 가능",
            "mid": "보통 수준의 식별 가능성",
            "low": "세그먼트 간 음색 변동 큼",
        },
        36: {  # 리듬 인격
            "high": "강한 리듬 개성 — 독자적 타이밍",
            "mid": "보통 수준의 리듬 특성",
            "low": "리듬 개성 약함",
        },
        50: {"high": "독특한 동작 패턴", "mid": "보통", "low": "일반적 동작"},
        64: {"high": "강한 비주얼 임팩트", "mid": "보통", "low": "약한 인상"},
        83: {"high": "고유한 표정 패턴", "mid": "보통", "low": "일반적 표정"},
    }

    level = "high" if score >= 0.6 else ("mid" if score >= 0.4 else "low")
    base = comments.get(ind_id, {}).get(level, "")

    # 댄스 영상 음색 경고
    if content_type == "dance" and ind_id in (1, 2):
        base += " ⚠ MR 영향 가능"

    return base

def run_screening(url, content_type, name, name_en, group, agency):
    """스크리닝 + 전체 파이프라인 실행"""
    from idol_scout.api import screen, build_profile, analyze, screening_to_snapshot

    print()
    print_separator("═")
    print(f"  분석 시작: {name or '(이름 미입력)'}")
    print(f"  URL: {url[:60]}...")
    print(f"  유형: {content_type}")
    print_separator("═")

    # 1단계: 스크리닝
    print("\n  [1/5] 영상 다운로드 및 스크리닝 중...")
    try:
        result = screen(url, content_type=content_type, verbose=False, save=False)
    except Exception as e:
        print(f"\n  ❌ 스크리닝 오류: {e}")
        return None

    # 2단계: 스냅샷 변환
    print("  [2/5] 스냅샷 변환 중...")
    snapshot = screening_to_snapshot(result)

    # 3단계: 프로필 생성
    print("  [3/5] 프로필 생성 중...")
    profile = build_profile(
        name=name or "",
        name_en=name_en or "",
        group=group or "",
        agency=agency or "",
        snapshots=[snapshot],
    )

    # 4단계: 분석 실행
    print("  [4/5] 해석층 + 복합지표 + 실패진단 중...")
    try:
        profile = analyze(profile)
    except Exception as e:
        print(f"\n  ❌ 분석 오류: {e}")
        return None

    # 5단계: 리포트 저장
    print("  [5/5] 리포트 저장 중...")
    report = build_report(result, profile, url, content_type, name, name_en, group, agency)
    report_path = save_report(report, name)

    return report, report_path

def build_report(screening_result, profile, url, content_type, name, name_en, group, agency):
    """분석 결과를 딕셔너리로 구성"""
    report = {
        "meta": {
            "name": name or "",
            "name_en": name_en or "",
            "group": group or "",
            "agency": agency or "",
            "url": url,
            "content_type": content_type,
            "analysis_time": datetime.now().isoformat(),
        },
        "screening": {
            "passed": screening_result.passed,
            "max_single_score": screening_result.max_single_score,
            "outlier_count": screening_result.outlier_count,
            "outlier_dimensions": screening_result.outlier_dimensions,
            "multi_person_detected": screening_result.multi_person_detected,
            "estimated_person_count": screening_result.estimated_person_count,
            "multi_person_method": screening_result.multi_person_method,
            "multi_person_notes": screening_result.multi_person_notes,
            "indicators": {},
        },
        "interpret_11vars": {},
        "composites": {},
        "failure_diagnosis": {},
    }

    # 지표
    for iid, ir in screening_result.indicators.items():
        report["screening"]["indicators"][str(iid)] = {
            "name": ir.name,
            "score": round(ir.score, 4) if ir.measured else 0.0,
            "confidence": round(ir.confidence, 4) if ir.measured else 0.0,
            "effective": round(ir.effective_score, 4) if ir.measured else 0.0,
            "measured": ir.measured,
        }

    # 11변수
    if profile.interpret:
        var_codes = ["sdi", "edt", "cer", "rmc", "aac", "sca", "cdr", "edi", "nvc", "cci", "cbp"]
        for code in var_codes:
            var_data = getattr(profile.interpret, code, None)
            if var_data is not None:
                report["interpret_11vars"][code.upper()] = {
                    "score": round(var_data.score, 3),
                    "level": var_data.level.name if hasattr(var_data.level, 'name') else str(var_data.level),
                    "ai_measurable": var_data.ai_measurable,
                }

    # 복합지표
    if profile.composites:
        c = profile.composites
        report["composites"] = {
            "system_dependency": round(c.system_dependency, 3),
            "transition_readiness": round(c.transition_readiness, 3),
            "exposure_conversion": round(c.exposure_conversion, 3),
            "resource_convergence": round(c.resource_convergence, 3),
            "innate_ratio": round(c.innate_ratio, 3),
            "growth_trajectory": round(c.growth_trajectory, 3),
        }

    # 실패진단
    if profile.failure_diag:
        fd = profile.failure_diag
        report["failure_diagnosis"] = {
            "failure_type": fd.failure_type.name if hasattr(fd.failure_type, 'name') else str(fd.failure_type),
            "risk_level": fd.risk_level.name if hasattr(fd.risk_level, 'name') else str(fd.risk_level),
            "ncps_conditions_met": fd.ncps.conditions_met if fd.ncps else 0,
            "rncs_conditions_met": fd.rncs.conditions_met if fd.rncs else 0,
        }

    return report

def save_report(report, name):
    """JSON 리포트 저장"""
    reports_dir = Path(__file__).parent / "analysis_reports"
    reports_dir.mkdir(exist_ok=True)
    safe_name = name.replace(" ", "_") if name else ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{safe_name}_{timestamp}.json"
    filepath = reports_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return filepath

def print_report(report, content_type):
    """결과 리포트를 터미널에 출력"""
    meta = report["meta"]
    screening = report["screening"]
    vars11 = report["interpret_11vars"]
    composites = report["composites"]
    diag = report["failure_diagnosis"]

    print()
    print_separator("═")
    print("  📊 분석 결과 리포트")
    print_separator("═")

    # 메타 정보
    if meta.get("name"):
        print(f"  대상: {meta['name']}", end="")
        if meta.get("name_en"):
            print(f" ({meta['name_en']})", end="")
        print()
    if meta.get("group"):
        print(f"  그룹: {meta['group']}", end="")
        if meta.get("agency"):
            print(f" / {meta['agency']}", end="")
        print()
    print(f"  유형: {content_type}")
    print()

    # ── 1단계: 스크리닝 결과 ──
    print_separator("─")
    status = "✅ 통과" if screening["passed"] else "❌ 탈락"
    outlier_ct = screening.get('outlier_count', 0)
    print(f"  [1단계 스크리닝] {status}  (극단값 {outlier_ct}개 차원)")
    print_separator("─")
    print()

    ind_names = {
        "1": "음색 고유성    ",
        "2": "음색 판별력    ",
        "36": "리듬 인격      ",
        "50": "동작 식별도    ",
        "64": "비주얼 잔상    ",
        "83": "표정 시그니처  ",
    }

    for iid, ind in screening["indicators"].items():
        name_str = ind_names.get(iid, ind["name"])
        if ind["measured"]:
            score_str = format_score(ind["score"])
            conf_str = f"신뢰도 {ind['confidence']:.2f}"
            comment = interpret_indicator(int(iid), ind["score"], content_type)
            print(f"  {name_str}  {score_str}  ({conf_str})  {comment}")
        else:
            print(f"  {name_str}  ─────  미측정")
    print()

    # ── 11변수 ──
    print_separator("─")
    print("  [해석층 11변수]")
    print_separator("─")
    print()

    var_names = {
        "SDI": "스타일 차별성      ",
        "EDT": "감정 전달 깊이      ",
        "CER": "콘텐츠 진화율      ",
        "RMC": "리듬-무브먼트 커플링",
        "AAC": "관객 적응 능력      ",
        "SCA": "자기 분석 능력      ",
        "CDR": "핵심차원 깊이      ",
        "EDI": "감정 분화 지수      ",
        "NVC": "비음악적 가치 전환  ",
        "CCI": "크로스카테고리 영향 ",
        "CBP": "카테고리 경계 투과  ",
    }

    for code, var in vars11.items():
        name_str = var_names.get(code, code)
        level_str = format_level(var["level"])
        ai_tag = "AI" if var["ai_measurable"] else "인간"
        marker = "●" if var["ai_measurable"] else "○"
        print(f"  {marker} {code} {name_str}  {var['score']:.3f}  ({level_str})  [{ai_tag}]")
    print()
    print("  ● = AI 측정  ○ = 인간 관찰 필요 (기본값 MID)")
    print()

    # ── 복합지표 ──
    print_separator("─")
    print("  [복합지표]")
    print_separator("─")
    print()

    comp_names = {
        "system_dependency": ("시스템 의존도    ", "0.8+ 위험, 0.5↓ 자립"),
        "transition_readiness": ("전환 준비도      ", "0.6+ 양호, 0.4↓ 위험"),
        "exposure_conversion": ("노출 전환 효율   ", "노출→팬덤 전환율"),
        "resource_convergence": ("자원 수렴도      ", "역량 집중도"),
        "innate_ratio": ("천부적 비율      ", "타고난 특성 비율"),
        "growth_trajectory": ("성장 궤적        ", "시간별 성장 기울기"),
    }

    for key, val in composites.items():
        name_str, desc = comp_names.get(key, (key, ""))
        alert = ""
        if key == "system_dependency" and val >= 0.8:
            alert = " ⚠ 높음"
        elif key == "transition_readiness" and val < 0.4:
            alert = " ⚠ 낮음"
        print(f"  {name_str}  {val:.3f}{alert}   ({desc})")
    print()

    # ── 실패 진단 ──
    print_separator("─")
    print("  [실패 구조 진단]")
    print_separator("─")
    print()

    ft = diag.get("failure_type", "NONE")
    rl = diag.get("risk_level", "LOW")

    if ft == "NONE":
        print(f"  진단: 없음 (건강)   위험등급: {rl}")
    elif ft == "NCPS":
        print(f"  진단: ⚠ NCPS (비핵심 포지션 정체 증후군)   위험등급: {rl}")
    elif ft == "RNCS":
        print(f"  진단: ⚠ RNCS (자원 비수렴 증후군)   위험등급: {rl}")
    else:
        print(f"  진단: {ft}   위험등급: {rl}")

    ncps_met = diag.get("ncps_conditions_met", 0)
    rncs_met = diag.get("rncs_conditions_met", 0)
    print(f"  NCPS: {ncps_met}/5 충족   RNCS: {rncs_met}/5 충족")
    print()

    # ── 종합 코멘트 ──
    print_separator("─")
    print("  [종합 요약]")
    print_separator("─")
    print()

    measured = [ind for ind in screening["indicators"].values() if ind["measured"]]
    if not measured:
        print("  측정된 지표가 없어 판단이 어렵습니다.")
        print("  다른 영상으로 재시도하거나 URL을 확인해 주세요.")
    else:
        outlier_ct = screening.get("outlier_count", 0)
        outlier_dims = screening.get("outlier_dimensions", [])
        sd = composites.get("system_dependency", 0)

        if outlier_ct > 0:
            print(f"  극단값 {outlier_ct}개 차원에서 발견: {', '.join(outlier_dims)}")
            print("  원석 후보 가능성이 있습니다. 추가 영상으로 교차 검증을 권장합니다.")
        else:
            print("  현재 영상에서 극단값이 발견되지 않았습니다.")
            if content_type == "dance":
                print("  보컬 영상으로 추가 분석하면 다른 차원에서 발견될 수 있습니다.")

        if sd >= 0.8:
            print(f"  시스템 의존도가 {sd:.3f}로 높아, 자체 고유성 강화가 필요합니다.")

        # 인간 변수 안내
        human_vars = [c for c, v in vars11.items() if not v["ai_measurable"]]
        if human_vars:
            print(f"\n  인간 관찰 변수({', '.join(human_vars)})가 기본값입니다.")
            print("  직접 관찰 후 입력하면 더 정확한 진단이 가능합니다.")

    print()
    print_separator("═")

def list_reports():
    """기존 분석 리포트 목록 출력"""
    reports_dir = Path(__file__).parent / "analysis_reports"
    if not reports_dir.exists():
        print("  분석 리포트가 없습니다.")
        return

    files = sorted(reports_dir.glob("analysis_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        print("  분석 리포트가 없습니다.")
        return

    print()
    print_separator("─")
    print("  기존 분석 리포트")
    print_separator("─")
    for i, f in enumerate(files[:10]):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            name = data.get("meta", {}).get("name", "") or "(이름없음)"
            url = data.get("meta", {}).get("url", "")[:40]
            ct = data.get("meta", {}).get("content_type", "?")
            oc = data.get("screening", {}).get("outlier_count", 0)
            print(f"  [{i+1}] {name} | {ct} | 극단값={oc}개 | {f.name}")
        except Exception:
            print(f"  [{i+1}] {f.name}")
    print()

def view_report(index):
    """기존 리포트 상세 보기"""
    reports_dir = Path(__file__).parent / "analysis_reports"
    files = sorted(reports_dir.glob("analysis_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if 0 <= index < len(files):
        data = json.loads(files[index].read_text(encoding="utf-8"))
        ct = data.get("meta", {}).get("content_type", "auto")
        print_report(data, ct)
    else:
        print("  잘못된 번호입니다.")

def main():
    clear_screen()
    print_banner()

    print("  명령어 안내:")
    print("  ─────────────────────────────────────")
    print("  URL 입력      → 새 분석 실행")
    print("  list          → 기존 분석 리포트 목록")
    print("  view [번호]   → 리포트 상세 보기")
    print("  quit          → 종료")
    print()

    while True:
        print_separator("─")
        cmd = input("\n  🎯 URL 또는 명령어: ").strip()

        if not cmd:
            continue

        if cmd.lower() in ("quit", "exit", "q"):
            print("\n  분석 프로그램을 종료합니다. 수고하셨습니다!")
            break

        if cmd.lower() == "list":
            list_reports()
            continue

        if cmd.lower().startswith("view"):
            parts = cmd.split()
            if len(parts) >= 2:
                try:
                    idx = int(parts[1]) - 1
                    view_report(idx)
                except ValueError:
                    print("  사용법: view 1")
            else:
                print("  사용법: view 1")
            continue

        # URL로 간주
        url = cmd
        if not ("youtube.com" in url or "youtu.be" in url or "instagram.com" in url):
            print("  ⚠ YouTube 또는 Instagram URL을 입력해주세요.")
            print("  (또는 list, view, quit 명령어)")
            continue

        # 추가 정보 입력
        print()
        print("  ── 분석 대상 정보 (Enter로 건너뛰기) ──")
        name = get_input("이름 (한글)")
        name_en = get_input("영문명")
        content_type = get_input("유형 (vocal/dance/auto)", "auto")
        if content_type not in ("vocal", "dance", "auto"):
            content_type = "auto"
        group = get_input("그룹")
        agency = get_input("기획사")

        # 분석 실행
        try:
            result = run_screening(url, content_type, name, name_en, group, agency)
            if result:
                report, report_path = result
                print_report(report, content_type)
                print(f"  💾 리포트 저장: {report_path.name}")
                print()
        except KeyboardInterrupt:
            print("\n  분석이 중단되었습니다.")
        except Exception as e:
            print(f"\n  ❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()

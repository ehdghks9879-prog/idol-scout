"""idol_screener/video_analyzer.py — 영상 기반 고유성 지표 3개 측정"""
import numpy as np
import cv2
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from .config import (FRAME_SAMPLE_FPS, POSE_MIN_DETECTION_CONFIDENCE, POSE_MIN_TRACKING_CONFIDENCE,
    FACE_MIN_DETECTION_CONFIDENCE, CONFIDENCE_CAPS)
try:
    import mediapipe as mp
    # Python 3.14에서 mediapipe.solutions가 없을 수 있음
    _mp_pose = mp.solutions.pose
    _mp_face = mp.solutions.face_mesh
    MP_AVAILABLE = True
except (ImportError, AttributeError):
    MP_AVAILABLE = False

@dataclass
class MovementResult:
    joint_angle_entropy: float = 0.0
    velocity_profile_std: float = 0.0
    range_of_motion: float = 0.0
    movement_complexity: float = 0.0
    asymmetry_index: float = 0.0
    frames_analyzed: int = 0
    frames_with_pose: int = 0
    identity_score: float = 0.0
    identity_confidence: float = 0.0
    notes: str = ""

@dataclass
class VisualResult:
    face_geometry_deviation: float = 0.0
    face_symmetry: float = 0.0
    distinctive_ratio_count: int = 0
    face_area_consistency: float = 0.0
    frames_with_face: int = 0
    afterimage_score: float = 0.0
    afterimage_confidence: float = 0.0
    notes: str = ""

@dataclass
class ExpressionResult:
    expression_range: float = 0.0
    expression_change_rate: float = 0.0
    expression_entropy: float = 0.0
    mouth_expressiveness: float = 0.0
    eye_expressiveness: float = 0.0
    brow_expressiveness: float = 0.0
    signature_score: float = 0.0
    signature_confidence: float = 0.0
    notes: str = ""

@dataclass
class MultiPersonInfo:
    """다인원 감지 결과"""
    multi_person_detected: bool = False
    estimated_person_count: int = 1
    max_faces_in_frame: int = 0
    frames_with_multiple_faces: int = 0
    face_identity_switches: int = 0          # 얼굴 비율 급변 횟수
    detection_method: str = ""               # "simultaneous" | "sequential" | "none"
    notes: str = ""

@dataclass
class VideoAnalysisResult:
    movement: MovementResult = field(default_factory=MovementResult)
    visual: VisualResult = field(default_factory=VisualResult)
    expression: ExpressionResult = field(default_factory=ExpressionResult)
    multi_person: MultiPersonInfo = field(default_factory=MultiPersonInfo)
    video_duration: float = 0.0
    video_resolution: Tuple[int, int] = (0, 0)
    total_frames_sampled: int = 0
    error: str = ""

def analyze_video(video_path: Path, content_type: str = "dance_video") -> VideoAnalysisResult:
    result = VideoAnalysisResult()
    if not MP_AVAILABLE:
        result.error = "mediapipe.solutions 사용 불가 (Python 3.14 호환성 문제). 영상 분석을 건너뜁니다."
        return result
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        result.error = f"영상 파일 열기 실패: {video_path}"
        return result
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    result.video_duration = total_frames / fps
    result.video_resolution = (width, height)
    if result.video_duration < 3.0:
        result.error = "영상 길이 3초 미만 — 분석 불가"
        cap.release()
        return result
    frame_interval = max(1, int(fps / FRAME_SAMPLE_FPS))
    conf_cap = CONFIDENCE_CAPS.get(content_type, 0.6)
    mp_pose = _mp_pose
    mp_face = _mp_face
    pose_landmarks_series = []
    face_landmarks_series = []
    frame_count = 0
    sampled_count = 0
    # ── 다인원 감지용 추적 변수 ──
    faces_per_frame = []           # 프레임당 감지된 얼굴 수
    face_ratios_per_frame = []     # 프레임당 대표 얼굴 비율 벡터 (인물 전환 감지용)

    with mp_pose.Pose(min_detection_confidence=POSE_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=POSE_MIN_TRACKING_CONFIDENCE) as pose, mp_face.FaceMesh(
        max_num_faces=5, min_detection_confidence=FACE_MIN_DETECTION_CONFIDENCE,
        refine_landmarks=True) as face_mesh:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                sampled_count += 1
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pose_result = pose.process(rgb)
                if pose_result.pose_landmarks:
                    landmarks = [(lm.x, lm.y, lm.z, lm.visibility) for lm in pose_result.pose_landmarks.landmark]
                    pose_landmarks_series.append(landmarks)
                face_result = face_mesh.process(rgb)
                if face_result.multi_face_landmarks:
                    num_faces = len(face_result.multi_face_landmarks)
                    faces_per_frame.append(num_faces)
                    # 가장 큰 얼굴(주인공 추정)을 대표로 사용
                    best_face = _select_largest_face(face_result.multi_face_landmarks)
                    landmarks = [(lm.x, lm.y, lm.z) for lm in best_face.landmark]
                    face_landmarks_series.append(landmarks)
                    # 인물 전환 감지용 얼굴 비율 저장
                    ratios = _compute_face_ratios(landmarks)
                    if ratios is not None:
                        face_ratios_per_frame.append(ratios)
                else:
                    faces_per_frame.append(0)
            frame_count += 1
    cap.release()
    result.total_frames_sampled = sampled_count

    # ── 다인원 감지 판정 ──
    result.multi_person = _detect_multi_person(faces_per_frame, face_ratios_per_frame)

    result.movement = _analyze_movement(pose_landmarks_series, sampled_count, conf_cap)
    result.visual = _analyze_visual(face_landmarks_series, sampled_count, conf_cap)
    result.expression = _analyze_expression(face_landmarks_series, sampled_count, fps / frame_interval, conf_cap)
    return result

def _analyze_movement(pose_series: list, total_frames: int, conf_cap: float) -> MovementResult:
    mr = MovementResult()
    mr.frames_analyzed = total_frames
    mr.frames_with_pose = len(pose_series)
    if mr.frames_with_pose < 10:
        mr.notes = "포즈 감지 프레임 부족(10개 미만). 동작 식별도 미산출."
        return mr
    detection_rate = mr.frames_with_pose / max(total_frames, 1)
    angles_over_time = _compute_joint_angles_series(pose_series)
    if len(angles_over_time) < 5:
        mr.notes = "관절각 계산 불가."
        return mr
    angles_array = np.array(angles_over_time)
    entropies = []
    for col in range(angles_array.shape[1]):
        hist, _ = np.histogram(angles_array[:, col], bins=20, density=True)
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        entropies.append(entropy)
    mr.joint_angle_entropy = float(np.mean(entropies))
    velocities = np.diff(angles_array, axis=0)
    mr.velocity_profile_std = float(np.mean(np.std(velocities, axis=0)))
    ranges = np.ptp(angles_array, axis=0)
    mr.range_of_motion = float(np.mean(ranges) / 180.0)
    if angles_array.shape[1] > 1:
        corr_matrix = np.corrcoef(angles_array.T)
        upper_tri = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
        mr.movement_complexity = float(1.0 - np.mean(np.abs(upper_tri)))
    else:
        mr.movement_complexity = 0.5
    mr.asymmetry_index = _compute_asymmetry(pose_series)
    ent_score = _normalize(mr.joint_angle_entropy, 2.0, 4.5)
    vel_score = _normalize(mr.velocity_profile_std, 2.0, 15.0)
    rom_score = min(1.0, mr.range_of_motion / 0.6)
    comp_score = mr.movement_complexity
    asym_score = _normalize(mr.asymmetry_index, 0.05, 0.3)
    mr.identity_score = _most_extreme([ent_score, vel_score, rom_score, comp_score, asym_score])
    mr.identity_confidence = conf_cap * min(1.0, detection_rate / 0.5)
    return mr

def _analyze_visual(face_series: list, total_frames: int, conf_cap: float) -> VisualResult:
    vr = VisualResult()
    vr.frames_with_face = len(face_series)
    if vr.frames_with_face < 5:
        vr.notes = "얼굴 감지 프레임 부족(5개 미만). 비주얼 잔상 미산출."
        return vr
    detection_rate = vr.frames_with_face / max(total_frames, 1)
    ratios_list = []
    symmetry_list = []
    for face_lm in face_series:
        ratios = _compute_face_ratios(face_lm)
        sym = _compute_face_symmetry(face_lm)
        if ratios is not None:
            ratios_list.append(ratios)
            symmetry_list.append(sym)
    if len(ratios_list) < 3:
        vr.notes = "유효 얼굴 비율 계산 부족."
        return vr
    avg_ratios = np.mean(ratios_list, axis=0)
    vr.face_symmetry = float(np.mean(symmetry_list))
    TYPICAL_RATIOS = np.array([0.44, 0.36, 0.50, 0.33, 0.28])
    TYPICAL_STD = 0.06
    deviations = np.abs(avg_ratios[:len(TYPICAL_RATIOS)] - TYPICAL_RATIOS)
    vr.face_geometry_deviation = float(np.mean(deviations))
    vr.distinctive_ratio_count = int(np.sum(deviations > TYPICAL_STD))
    ratio_std = np.std(ratios_list, axis=0)
    vr.face_area_consistency = float(1.0 - min(1.0, np.mean(ratio_std) * 10))
    deviation_score = _normalize(vr.face_geometry_deviation, 0.02, 0.12)
    asymmetry_score = _normalize_visual_asymmetry(vr.face_symmetry)
    distinctive_score = min(1.0, vr.distinctive_ratio_count / 3.0)
    vr.afterimage_score = _most_extreme([deviation_score, asymmetry_score, distinctive_score])
    vr.afterimage_confidence = conf_cap * min(1.0, detection_rate / 0.3)
    return vr

def _analyze_expression(face_series: list, total_frames: int, effective_fps: float, conf_cap: float) -> ExpressionResult:
    er = ExpressionResult()
    if len(face_series) < 10:
        er.notes = "표정 분석용 프레임 부족(10개 미만)."
        return er
    detection_rate = len(face_series) / max(total_frames, 1)
    expression_vectors = []
    mouth_movements = []
    eye_movements = []
    brow_movements = []
    for i in range(1, len(face_series)):
        prev_lm = face_series[i - 1]
        curr_lm = face_series[i]
        diff = _compute_landmark_diff(prev_lm, curr_lm)
        expression_vectors.append(diff)
        mouth_movements.append(_compute_region_movement(prev_lm, curr_lm, "mouth"))
        eye_movements.append(_compute_region_movement(prev_lm, curr_lm, "eye"))
        brow_movements.append(_compute_region_movement(prev_lm, curr_lm, "brow"))
    expr_array = np.array(expression_vectors)
    er.expression_range = float(np.mean(np.abs(expr_array)))
    significant_changes = np.sum(np.abs(expr_array) > 0.005, axis=0)
    er.expression_change_rate = float(np.mean(significant_changes) / (len(expression_vectors) / max(effective_fps, 1)))
    quantized = _quantize_expressions(expr_array, n_states=8)
    hist, _ = np.histogram(quantized, bins=8, density=True)
    hist = hist[hist > 0]
    er.expression_entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
    er.mouth_expressiveness = float(np.mean(mouth_movements))
    er.eye_expressiveness = float(np.mean(eye_movements))
    er.brow_expressiveness = float(np.mean(brow_movements))
    range_score = _normalize(er.expression_range, 0.002, 0.02)
    rate_score = _normalize(er.expression_change_rate, 0.5, 5.0)
    entropy_score = _normalize(er.expression_entropy, 1.5, 3.0)
    expressiveness = [er.mouth_expressiveness, er.eye_expressiveness, er.brow_expressiveness]
    if max(expressiveness) > 0:
        diversity_score = min(expressiveness) / (max(expressiveness) + 1e-10)
    else:
        diversity_score = 0.0
    er.signature_score = _most_extreme([range_score, rate_score, entropy_score, diversity_score])
    er.signature_confidence = conf_cap * min(1.0, detection_rate / 0.3) * 0.85
    return er

def _select_largest_face(multi_face_landmarks) -> object:
    """프레임 내 여러 얼굴 중 가장 큰 얼굴(=주인공 추정)을 선택"""
    if len(multi_face_landmarks) == 1:
        return multi_face_landmarks[0]
    best = None
    best_area = -1
    for face_lm in multi_face_landmarks:
        lms = face_lm.landmark
        if len(lms) < 468:
            continue
        # 얼굴 바운딩 박스 면적으로 크기 판단
        xs = [lms[i].x for i in [234, 454, 10, 152]]  # 좌, 우, 상, 하
        ys = [lms[i].y for i in [234, 454, 10, 152]]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        area = w * h
        if area > best_area:
            best_area = area
            best = face_lm
    return best if best is not None else multi_face_landmarks[0]


def _detect_multi_person(faces_per_frame: list, face_ratios_per_frame: list) -> MultiPersonInfo:
    """프레임별 얼굴 수와 얼굴 비율 변화로 다인원 여부 판정"""
    info = MultiPersonInfo()
    if not faces_per_frame:
        info.notes = "얼굴 감지 프레임 없음"
        return info

    info.max_faces_in_frame = max(faces_per_frame)
    info.frames_with_multiple_faces = sum(1 for f in faces_per_frame if f > 1)
    total_face_frames = sum(1 for f in faces_per_frame if f > 0)

    # ── 방법 1: 동시 다인원 (한 프레임에 2명 이상) ──
    if total_face_frames > 0:
        multi_ratio = info.frames_with_multiple_faces / total_face_frames
        if multi_ratio >= 0.15:  # 15% 이상 프레임에서 2명+ 동시 등장
            info.multi_person_detected = True
            info.estimated_person_count = info.max_faces_in_frame
            info.detection_method = "simultaneous"
            info.notes = (f"전체 {total_face_frames}개 얼굴 프레임 중 {info.frames_with_multiple_faces}개에서 "
                         f"2명 이상 동시 감지 ({multi_ratio:.0%}). 최대 {info.max_faces_in_frame}명.")
            return info

    # ── 방법 2: 순차 교체 (인물이 번갈아 등장) ──
    # 연속 프레임 간 얼굴 비율 벡터의 변화량으로 판단
    if len(face_ratios_per_frame) >= 5:
        ratios_array = np.array(face_ratios_per_frame)
        # 연속 프레임 간 유클리드 거리
        diffs = np.linalg.norm(np.diff(ratios_array, axis=0), axis=1)

        if len(diffs) > 0:
            # 급격한 변화 = 인물 전환 (평균의 3배 이상이면 전환으로 판단)
            mean_diff = np.mean(diffs)
            std_diff = np.std(diffs)
            threshold = mean_diff + 2.5 * std_diff  # 통계적 이상치 기준

            # 최소 임계값: 너무 낮은 threshold 방지 (같은 사람 미세 변화 무시)
            min_threshold = 0.03
            threshold = max(threshold, min_threshold)

            switches = np.sum(diffs > threshold)
            info.face_identity_switches = int(switches)

            # 전환 횟수 기반 인물 수 추정
            if switches >= 3:  # 최소 3회 이상 인물 전환
                info.multi_person_detected = True
                # 전환 패턴으로 인원 추정 (A→B→A→B = 4번 전환, 2명)
                info.estimated_person_count = min(int(switches // 2) + 1, 10)
                info.detection_method = "sequential"
                info.notes = (f"얼굴 비율 급변 {switches}회 감지 — 인물이 교차 등장하는 것으로 추정. "
                             f"추정 인원: {info.estimated_person_count}명.")
                return info

    info.detection_method = "none"
    info.notes = "단일 인물 영상으로 판정"
    return info


def _compute_joint_angles_series(pose_series: list) -> list:
    JOINT_TRIPLETS = [(11, 13, 15), (12, 14, 16), (13, 11, 23), (14, 12, 24), (23, 25, 27), (24, 26, 28), (11, 23, 25), (12, 24, 26)]
    angles_series = []
    for landmarks in pose_series:
        angles = []
        valid = True
        for a, b, c in JOINT_TRIPLETS:
            if a < len(landmarks) and b < len(landmarks) and c < len(landmarks):
                if landmarks[a][3] > 0.3 and landmarks[b][3] > 0.3 and landmarks[c][3] > 0.3:
                    angle = _angle_between_points(landmarks[a][:2], landmarks[b][:2], landmarks[c][:2])
                    angles.append(angle)
                else:
                    valid = False
                    break
            else:
                valid = False
                break
        if valid and len(angles) == len(JOINT_TRIPLETS):
            angles_series.append(angles)
    return angles_series

def _angle_between_points(p1, p2, p3) -> float:
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))

def _compute_asymmetry(pose_series: list) -> float:
    SYMMETRIC_PAIRS = [(11, 12), (13, 14), (15, 16), (23, 24), (25, 26)]
    asymmetries = []
    for landmarks in pose_series:
        for left, right in SYMMETRIC_PAIRS:
            if left < len(landmarks) and right < len(landmarks):
                l_pos = np.array(landmarks[left][:2])
                r_pos = np.array(landmarks[right][:2])
                center_x = (l_pos[0] + r_pos[0]) / 2
                l_dist = abs(l_pos[0] - center_x)
                r_dist = abs(r_pos[0] - center_x)
                if l_dist + r_dist > 0:
                    asym = abs(l_dist - r_dist) / (l_dist + r_dist)
                    asymmetries.append(asym)
    return float(np.mean(asymmetries)) if asymmetries else 0.0

def _compute_face_ratios(face_lm: list) -> Optional[np.ndarray]:
    if len(face_lm) < 468:
        return None
    try:
        left_eye_inner = np.array(face_lm[133][:2])
        left_eye_outer = np.array(face_lm[33][:2])
        right_eye_inner = np.array(face_lm[362][:2])
        right_eye_outer = np.array(face_lm[263][:2])
        nose_top = np.array(face_lm[6][:2])
        nose_bottom = np.array(face_lm[1][:2])
        mouth_left = np.array(face_lm[61][:2])
        mouth_right = np.array(face_lm[291][:2])
        chin = np.array(face_lm[152][:2])
        forehead = np.array(face_lm[10][:2])
        face_left = np.array(face_lm[234][:2])
        face_right = np.array(face_lm[454][:2])
        face_width = np.linalg.norm(face_right - face_left) + 1e-10
        face_height = np.linalg.norm(chin - forehead) + 1e-10
        inter_eye = np.linalg.norm((left_eye_inner + left_eye_outer) / 2 - (right_eye_inner + right_eye_outer) / 2)
        nose_length = np.linalg.norm(nose_bottom - nose_top)
        mouth_width = np.linalg.norm(mouth_right - mouth_left)
        jaw_length = np.linalg.norm(chin - nose_bottom)
        eye_center_y = (left_eye_inner[1] + right_eye_inner[1]) / 2
        forehead_height = abs(eye_center_y - forehead[1])
        ratios = np.array([inter_eye / face_width, nose_length / face_height, mouth_width / (inter_eye + 1e-10), jaw_length / face_height, forehead_height / face_height])
        return ratios
    except (IndexError, ValueError):
        return None

def _compute_face_symmetry(face_lm: list) -> float:
    if len(face_lm) < 468:
        return 0.5
    SYMMETRIC_PAIRS = [(33, 263), (133, 362), (61, 291), (234, 454), (70, 300)]
    nose_center = np.array(face_lm[1][:2])
    diffs = []
    for left_idx, right_idx in SYMMETRIC_PAIRS:
        left = np.array(face_lm[left_idx][:2])
        right = np.array(face_lm[right_idx][:2])
        left_dist = np.linalg.norm(left - nose_center)
        right_dist = np.linalg.norm(right - nose_center)
        if left_dist + right_dist > 0:
            diff = abs(left_dist - right_dist) / (left_dist + right_dist)
            diffs.append(diff)
    if not diffs:
        return 0.5
    return float(1.0 - np.mean(diffs))

def _compute_landmark_diff(prev_lm: list, curr_lm: list) -> float:
    EXPR_INDICES = [13, 14, 61, 291, 78, 308, 159, 145, 386, 374, 70, 63, 300, 293]
    total_diff = 0.0
    count = 0
    for idx in EXPR_INDICES:
        if idx < len(prev_lm) and idx < len(curr_lm):
            prev = np.array(prev_lm[idx][:2])
            curr = np.array(curr_lm[idx][:2])
            total_diff += np.linalg.norm(curr - prev)
            count += 1
    return total_diff / max(count, 1)

def _compute_region_movement(prev_lm: list, curr_lm: list, region: str) -> float:
    REGIONS = {"mouth": [13, 14, 61, 291, 78, 308, 82, 312], "eye": [159, 145, 386, 374, 160, 144, 385, 373], "brow": [70, 63, 105, 300, 293, 334]}
    indices = REGIONS.get(region, [])
    total = 0.0
    count = 0
    for idx in indices:
        if idx < len(prev_lm) and idx < len(curr_lm):
            prev = np.array(prev_lm[idx][:2])
            curr = np.array(curr_lm[idx][:2])
            total += np.linalg.norm(curr - prev)
            count += 1
    return total / max(count, 1)

def _quantize_expressions(expr_array: np.ndarray, n_states: int = 8) -> np.ndarray:
    magnitudes = np.abs(expr_array).flatten()
    if len(magnitudes) == 0:
        return np.array([0])
    bins = np.linspace(0, np.percentile(magnitudes, 95), n_states + 1)
    return np.digitize(magnitudes, bins) - 1

def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))

def _normalize_visual_asymmetry(symmetry: float) -> float:
    if symmetry > 0.95:
        return 0.4
    elif 0.85 <= symmetry <= 0.95:
        return 0.8 + 0.2 * (1.0 - abs(symmetry - 0.90) / 0.05)
    elif symmetry < 0.75:
        return 0.3
    else:
        return _normalize(symmetry, 0.75, 0.85) * 0.7

def _most_extreme(scores: list) -> float:
    """
    ★ 회사 헌법: 종합 점수/합산/가중평균 금지.
    하위 측정값 중 중앙(0.5)에서 가장 먼 값을 대표값으로 사용.
    여러 하위 측정이 있을 때, 하나라도 극단이면 그것이 이 차원의 점수.
    """
    if not scores:
        return 0.0
    # 0.5(중앙)에서 가장 먼 값 선택
    most_extreme = max(scores, key=lambda s: abs(s - 0.5))
    return most_extreme

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        result = analyze_video(path, content_type="dance_video")
        print(f"\n=== 영상 분석 결과: {path.name} ===")
        print(f"길이: {result.video_duration:.1f}초  해상도: {result.video_resolution}")
        m = result.movement
        print(f"\n[동작 식별도]  점수={m.identity_score:.3f}  신뢰도={m.identity_confidence:.3f}")
        v = result.visual
        print(f"\n[비주얼 잔상]  점수={v.afterimage_score:.3f}  신뢰도={v.afterimage_confidence:.3f}")
        e = result.expression
        print(f"\n[표정시그니처] 점수={e.signature_score:.3f}  신뢰도={e.signature_confidence:.3f}")
        if result.error:
            print(f"\n오류: {result.error}")

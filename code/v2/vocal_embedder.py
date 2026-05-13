"""
vocal_embedder.py — Resemblyzer 기반 보컬 임베딩 모듈
======================================================

목적:
    Resemblyzer (Apache 2.0)로 256차원 화자 임베딩 추출.
    마마무 4인 레퍼런스 임베딩과 코사인 유사도 비교.
    → 측정값 기반 매칭의 한계 극복 (화사 vs 휘인 분별 정확도 ↑)

작동:
    1. extract_embedding(audio_bytes) → 256-dim numpy 벡터
    2. compute_similarities(emb) → 각 멤버와 코사인 유사도
    3. 레퍼런스 임베딩은 JSON으로 저장/불러오기

라이선스: Apache 2.0 (상업 사용 안전)
작성일: 2026-05-13 (v2.2 임베딩 통합)
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# 모듈 레벨 — encoder 단일 인스턴스 (로딩 비용 최소화)
_encoder = None
_preprocess_wav = None


def _load_encoder():
    """Resemblyzer VoiceEncoder를 lazy하게 로드 (CPU 모드)."""
    global _encoder, _preprocess_wav
    if _encoder is None:
        from resemblyzer import VoiceEncoder, preprocess_wav
        _encoder = VoiceEncoder("cpu", verbose=False)
        _preprocess_wav = preprocess_wav
    return _encoder, _preprocess_wav


def extract_embedding(audio_bytes: bytes) -> np.ndarray:
    """오디오 바이트에서 256차원 보컬 임베딩 추출.

    Args:
        audio_bytes: WAV/MP3/M4A 등의 raw 바이트
    Returns:
        np.ndarray, shape (256,), L2-normalized
    """
    import librosa

    # Resemblyzer는 16kHz 기대
    y, sr = librosa.load(BytesIO(audio_bytes), sr=16000, mono=True, duration=90.0)

    if len(y) < sr * 1.0:
        raise ValueError("임베딩 추출 — 음원이 너무 짧습니다 (1초 이상 필요).")

    encoder, preprocess_wav = _load_encoder()

    # Resemblyzer의 전처리 — 무음 트림 + 정규화
    wav = preprocess_wav(y, source_sr=16000)

    if len(wav) < 16000:
        raise ValueError("전처리 후 신호가 너무 짧습니다.")

    # 임베딩 추출 (256-dim, L2 정규화됨)
    embedding = encoder.embed_utterance(wav)
    return np.asarray(embedding, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """두 벡터의 코사인 유사도 ([-1, 1])."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-8 or nb < 1e-8:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def similarity_to_percent(sim: float) -> float:
    """코사인 유사도 [-1, 1] → 친화도 % [0, 100] 매핑.
    Resemblyzer 임베딩은 같은 화자 0.7~0.95, 다른 화자 0.2~0.5 분포.
    """
    # 0.3~0.85를 0~100으로 확장 (Resemblyzer 분포에 맞춤)
    scaled = (sim - 0.3) / 0.55
    return float(np.clip(scaled * 100, 0, 100))


class ReferenceLibrary:
    """마마무 4인(+ 추가 가능) 레퍼런스 임베딩 라이브러리."""

    def __init__(self, json_path: Optional[Path] = None):
        self.references: Dict[str, np.ndarray] = {}
        if json_path is not None:
            self.load(json_path)

    def load(self, json_path: Path) -> None:
        """JSON에서 레퍼런스 임베딩 로드."""
        json_path = Path(json_path)
        if not json_path.exists():
            return
        data = json.loads(json_path.read_text(encoding="utf-8"))
        self.references = {
            name: np.array(vec, dtype=np.float32) for name, vec in data.items()
        }

    def save(self, json_path: Path) -> None:
        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        serializable = {name: vec.tolist() for name, vec in self.references.items()}
        json_path.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")

    def set_reference(self, name: str, embedding: np.ndarray) -> None:
        """단일 레퍼런스 등록/갱신."""
        self.references[name] = np.asarray(embedding, dtype=np.float32)

    def compute_matches(self, query_embedding: np.ndarray) -> List[Dict]:
        """레퍼런스들과의 유사도 계산. 결과는 유사도 내림차순."""
        if not self.references:
            return []
        results = []
        for name, ref_emb in self.references.items():
            sim = cosine_similarity(query_embedding, ref_emb)
            results.append({
                "name": name,
                "raw_cosine": sim,
                "similarity": similarity_to_percent(sim),
            })
        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results

    def is_empty(self) -> bool:
        return len(self.references) == 0

    def member_names(self) -> List[str]:
        return list(self.references.keys())


# 기본 레퍼런스 라이브러리 위치 (Streamlit Cloud에서도 접근)
DEFAULT_LIBRARY_PATH = Path(__file__).resolve().parent / "mamamoo_references.json"


def get_default_library() -> ReferenceLibrary:
    """모듈 기본 위치에서 레퍼런스 라이브러리 로드."""
    return ReferenceLibrary(DEFAULT_LIBRARY_PATH)

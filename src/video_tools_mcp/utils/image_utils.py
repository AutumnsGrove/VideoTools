"""
Image processing utilities for perceptual hashing and deduplication.

This module provides utilities for computing perceptual hashes (pHash) of images
and detecting duplicate or similar frames in video processing.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import imagehash

logger = logging.getLogger(__name__)


def compute_phash(image_path: Path, hash_size: int = 8) -> imagehash.ImageHash:
    """
    Compute perceptual hash (pHash) for an image.

    Args:
        image_path: Path to image file
        hash_size: Hash size (default: 8 = 64-bit hash)

    Returns:
        ImageHash object

    Raises:
        FileNotFoundError: If image file doesn't exist
        IOError: If image cannot be loaded
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        image = Image.open(image_path)
        phash = imagehash.phash(image, hash_size=hash_size)
        logger.debug(f"Computed pHash for {image_path.name}: {phash}")
        return phash
    except Exception as e:
        raise IOError(f"Failed to compute pHash for {image_path}: {e}")


def calculate_similarity(hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> float:
    """
    Calculate similarity between two perceptual hashes.

    Uses Hamming distance to compute similarity score.

    Args:
        hash1: First image hash
        hash2: Second image hash

    Returns:
        Similarity score between 0.0 (completely different) and 1.0 (identical)
    """
    # Hamming distance = number of different bits
    hamming_distance = hash1 - hash2

    # Max possible distance for 64-bit hash
    max_distance = len(hash1.hash) ** 2

    # Convert to similarity (0.0 = different, 1.0 = identical)
    similarity = 1.0 - (hamming_distance / max_distance)

    return similarity


def is_duplicate(
    image_path1: Path,
    image_path2: Path,
    threshold: float = 0.90,
    hash_size: int = 8
) -> Tuple[bool, float]:
    """
    Check if two images are duplicates based on perceptual hash similarity.

    Args:
        image_path1: Path to first image
        image_path2: Path to second image
        threshold: Similarity threshold (0.0 to 1.0, default: 0.90)
        hash_size: Hash size for pHash computation

    Returns:
        Tuple of (is_duplicate: bool, similarity: float)

    Raises:
        FileNotFoundError: If either image file doesn't exist
        IOError: If images cannot be loaded
    """
    hash1 = compute_phash(image_path1, hash_size)
    hash2 = compute_phash(image_path2, hash_size)

    similarity = calculate_similarity(hash1, hash2)
    is_dup = similarity >= threshold

    logger.debug(
        f"Similarity between {image_path1.name} and {image_path2.name}: "
        f"{similarity:.3f} (duplicate={is_dup})"
    )

    return is_dup, similarity


def deduplicate_frames(
    frame_paths: List[Path],
    threshold: float = 0.90,
    hash_size: int = 8,
    keep_first: bool = True
) -> Tuple[List[Path], List[Path]]:
    """
    Remove duplicate frames from a list based on perceptual hash similarity.

    Args:
        frame_paths: List of paths to frame images
        threshold: Similarity threshold for considering frames duplicates (default: 0.90)
        hash_size: Hash size for pHash computation
        keep_first: If True, keep first occurrence; if False, keep last

    Returns:
        Tuple of (kept_frames: List[Path], removed_frames: List[Path])
    """
    if not frame_paths:
        return [], []

    logger.info(f"Deduplicating {len(frame_paths)} frames (threshold={threshold})")

    # Compute hashes for all frames
    frame_hashes = []
    for frame_path in frame_paths:
        try:
            phash = compute_phash(frame_path, hash_size)
            frame_hashes.append((frame_path, phash))
        except Exception as e:
            logger.warning(f"Failed to compute hash for {frame_path}: {e}")
            # Keep frames we can't hash
            frame_hashes.append((frame_path, None))

    kept = []
    removed = []

    for i, (frame_path, frame_hash) in enumerate(frame_hashes):
        if frame_hash is None:
            # Keep frames without hashes
            kept.append(frame_path)
            continue

        is_duplicate = False

        # Check against all kept frames
        for kept_path, kept_hash in [(p, h) for p, h in frame_hashes[:i] if p in kept]:
            if kept_hash is None:
                continue

            similarity = calculate_similarity(frame_hash, kept_hash)

            if similarity >= threshold:
                is_duplicate = True
                logger.debug(
                    f"Frame {frame_path.name} is duplicate of {kept_path.name} "
                    f"(similarity={similarity:.3f})"
                )
                break

        if is_duplicate:
            removed.append(frame_path)
        else:
            kept.append(frame_path)

    logger.info(
        f"Deduplication complete: kept {len(kept)}/{len(frame_paths)} frames "
        f"(removed {len(removed)} duplicates)"
    )

    return kept, removed


def get_unique_frames_with_metadata(
    frame_paths: List[Path],
    threshold: float = 0.90,
    hash_size: int = 8
) -> List[dict]:
    """
    Get unique frames with similarity metadata for debugging/analysis.

    Args:
        frame_paths: List of paths to frame images
        threshold: Similarity threshold for duplicates
        hash_size: Hash size for pHash computation

    Returns:
        List of dicts with frame metadata:
        {
            "path": Path,
            "hash": ImageHash,
            "is_unique": bool,
            "similar_to": Optional[str],  # Path of similar frame if duplicate
            "similarity_score": Optional[float]
        }
    """
    logger.info(f"Analyzing {len(frame_paths)} frames for uniqueness")

    # Compute all hashes
    frames_with_hashes = []
    for frame_path in frame_paths:
        try:
            phash = compute_phash(frame_path, hash_size)
            frames_with_hashes.append({
                "path": frame_path,
                "hash": phash,
                "is_unique": True,
                "similar_to": None,
                "similarity_score": None
            })
        except Exception as e:
            logger.warning(f"Failed to process {frame_path}: {e}")
            frames_with_hashes.append({
                "path": frame_path,
                "hash": None,
                "is_unique": True,
                "similar_to": None,
                "similarity_score": None
            })

    # Check for duplicates
    for i in range(len(frames_with_hashes)):
        if frames_with_hashes[i]["hash"] is None:
            continue

        for j in range(i):
            if frames_with_hashes[j]["hash"] is None:
                continue

            if not frames_with_hashes[j]["is_unique"]:
                continue

            similarity = calculate_similarity(
                frames_with_hashes[i]["hash"],
                frames_with_hashes[j]["hash"]
            )

            if similarity >= threshold:
                frames_with_hashes[i]["is_unique"] = False
                frames_with_hashes[i]["similar_to"] = str(frames_with_hashes[j]["path"])
                frames_with_hashes[i]["similarity_score"] = similarity
                break

    unique_count = sum(1 for f in frames_with_hashes if f["is_unique"])
    logger.info(f"Found {unique_count} unique frames out of {len(frame_paths)}")

    return frames_with_hashes

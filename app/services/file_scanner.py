import os
from typing import Dict, Any, Set

NO_EXTENSION = '<no_ext>'

def scan_for_media_recursive(
    folder_path: str,
    image_extensions: Set[str] = None,
    video_extensions: Set[str] = None,
    audio_extensions: Set[str] = None
) -> Dict[str, Any]:
    """Recursively scans folder_path and counts files by type and extension.
    
    Args:
        folder_path: Path to scan
        image_extensions: Set of image file extensions (e.g., {'.jpg', '.png'})
        video_extensions: Set of video file extensions (e.g., {'.mp4', '.avi'})
        audio_extensions: Set of audio file extensions (e.g., {'.mp3', '.wav'})
    
    Returns:
        Dict with 'totals' and 'by_extension' statistics
    """
    # Ensure we have sets to work with
    norm_image = {e.strip().lower() for e in (image_extensions or set())}
    norm_video = {e.strip().lower() for e in (video_extensions or set())}
    norm_audio = {e.strip().lower() for e in (audio_extensions or set())}

    totals = {'image': 0, 'video': 0, 'audio': 0, 'other': 0}
    by_extension = {}

    for root, _, files in os.walk(folder_path):
        for fname in files:
            _, ext = os.path.splitext(fname)
            ext_norm = ext.strip().lower()
            
            if not ext_norm:
                totals['other'] += 1
                by_extension[NO_EXTENSION] = by_extension.get(NO_EXTENSION, 0) + 1
                continue

            if ext_norm in norm_image:
                totals['image'] += 1
            elif ext_norm in norm_video:
                totals['video'] += 1
            elif ext_norm in norm_audio:
                totals['audio'] += 1
            else:
                totals['other'] += 1

            by_extension[ext_norm] = by_extension.get(ext_norm, 0) + 1

    return {'totals': totals, 'by_extension': by_extension}
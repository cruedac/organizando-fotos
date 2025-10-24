import os
from typing import Dict, Any, Set, List

NO_EXTENSION = '<no_ext>'

def scan_for_media_recursive(
    folder_path: str,
    image_extensions: Set[str] = None,
    video_extensions: Set[str] = None,
    audio_extensions: Set[str] = None,
    scan_subdirs: bool = True
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
    by_extension: Dict[str, int] = {}
    per_directory: Dict[str, Dict[str, Any]] = {}
    total_size = 0

    # Si scan_subdirs es False, solo escaneamos el directorio actual
    if scan_subdirs:
        walker = os.walk(folder_path)
    else:
        # Solo procesamos el directorio actual, sin subdirectorios
        walker = [(folder_path, [], [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])]
    
    for root, dirs, files in walker:
        folder_totals = {'image': 0, 'video': 0, 'audio': 0, 'other': 0}
        folder_extensions: Dict[str, int] = {}

        folder_size = 0
        for fname in files:
            _, ext = os.path.splitext(fname)
            ext_norm = ext.strip().lower()
            ext_key = ext_norm if ext_norm else NO_EXTENSION
            folder_extensions[ext_key] = folder_extensions.get(ext_key, 0) + 1
            by_extension[ext_key] = by_extension.get(ext_key, 0) + 1

            file_path = os.path.join(root, fname)
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                file_size = 0
            folder_size += file_size
            total_size += file_size
            
            if not ext_norm:
                totals['other'] += 1
                folder_totals['other'] += 1
                continue

            if ext_norm in norm_image:
                totals['image'] += 1
                folder_totals['image'] += 1
            elif ext_norm in norm_video:
                totals['video'] += 1
                folder_totals['video'] += 1
            elif ext_norm in norm_audio:
                totals['audio'] += 1
                folder_totals['audio'] += 1
            else:
                totals['other'] += 1
                folder_totals['other'] += 1

        if sum(folder_totals.values()) > 0:
            per_directory[root] = {
                'path': root,
                'totals': folder_totals,
                'by_extension': folder_extensions,
                'total_size': folder_size
            }

    directories: List[Dict[str, Any]] = [per_directory[path] for path in sorted(per_directory.keys())]

    return {'totals': totals, 'by_extension': by_extension, 'directories': directories, 'total_size': total_size}
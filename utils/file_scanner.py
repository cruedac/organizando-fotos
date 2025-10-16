import os
from typing import Dict, Any

def scan_for_media_recursive(folder_path: str, image_exts=None, video_exts=None, audio_exts=None) -> Dict[str, Any]:
    """Recorre folder_path recursivamente y cuenta archivos por tipo y por extensión.

    image_exts, video_exts, audio_exts: iterables de extensiones (ej: {'.jpg', '.mp4'})
    Retorna: {'totals': {...}, 'by_extension': {...}}
    """
    # Valores por defecto si no se proporcionan
    if image_exts is None:
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
    if video_exts is None:
        video_exts = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"}
    if audio_exts is None:
        audio_exts = {".mp3", ".wav", ".ogg", ".aac", ".flac"}

    norm_image = {e.strip().lower() for e in image_exts}
    norm_video = {e.strip().lower() for e in video_exts}
    norm_audio = {e.strip().lower() for e in audio_exts}

    totals = {'image': 0, 'video': 0, 'audio': 0, 'other': 0}
    by_extension = {}

    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            _, ext = os.path.splitext(fname)
            ext_norm = ext.strip().lower()
            if not ext_norm:
                totals['other'] += 1
                by_extension['<no_ext>'] = by_extension.get('<no_ext>', 0) + 1
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

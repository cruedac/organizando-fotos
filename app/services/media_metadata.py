"""Utility helpers for media metadata extraction and formatting."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

try:
    import mutagen  # type: ignore
except ImportError:  # pragma: no cover
    mutagen = None


def format_size(num_bytes: int) -> str:
    units = ["bytes", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}" if unit != "bytes" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def _ratio_to_float(value) -> Optional[float]:
    try:
        return float(value[0]) / float(value[1]) if value[1] else None
    except Exception:
        return None


def _convert_to_degrees(value) -> Optional[float]:
    if not value or len(value) < 3:
        return None
    degrees = _ratio_to_float(value[0])
    minutes = _ratio_to_float(value[1])
    seconds = _ratio_to_float(value[2])
    if None in (degrees, minutes, seconds):
        return None
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def _sanitize_exif_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return value.hex()
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return value


def read_image_metadata(image_path: Path) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
    image_info = None
    exif_clean = {}
    gps_payload = None

    with Image.open(image_path) as img:
        image_info = {
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
        }
        raw = getattr(img, "_getexif", lambda: None)() or {}

    gps_raw = {}
    for tag, value in raw.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == "GPSInfo":
            for key, gps_value in value.items():
                gps_tag = GPSTAGS.get(key, key)
                gps_raw[gps_tag] = gps_value
        else:
            exif_clean[tag_name] = _sanitize_exif_value(value)

    if gps_raw:
        lat = gps_raw.get("GPSLatitude")
        lat_ref = gps_raw.get("GPSLatitudeRef")
        lon = gps_raw.get("GPSLongitude")
        lon_ref = gps_raw.get("GPSLongitudeRef")
        alt = gps_raw.get("GPSAltitude")
        alt_ref = gps_raw.get("GPSAltitudeRef")

        lat_deg = _convert_to_degrees(lat) if lat else None
        lon_deg = _convert_to_degrees(lon) if lon else None

        if lat_deg is not None and lat_ref in ("S", "N"):
            lat_deg = lat_deg if lat_ref == "N" else -lat_deg
        if lon_deg is not None and lon_ref in ("W", "E"):
            lon_deg = lon_deg if lon_ref == "E" else -lon_deg

        gps_payload = {
            "latitude": lat_deg,
            "latitude_ref": lat_ref,
            "longitude": lon_deg,
            "longitude_ref": lon_ref,
            "altitude": _ratio_to_float(alt) if alt else None,
            "altitude_ref": alt_ref,
            "raw": {key: _sanitize_exif_value(val) for key, val in gps_raw.items()},
        }
        if lat_deg is not None and lon_deg is not None:
            gps_payload["map_url"] = f"https://www.google.com/maps?q={lat_deg},{lon_deg}"

    ordered_exif = dict(sorted(exif_clean.items())) if exif_clean else None
    return image_info, ordered_exif, gps_payload


def _format_duration(seconds) -> Optional[str]:
    if seconds is None:
        return None
    try:
        total_seconds = int(round(float(seconds)))
    except Exception:
        return str(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def read_media_tags(media_path: Path) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
    if mutagen is None:
        return None, None, 'Instala la librería "mutagen" para obtener metadatos embebidos de audio y video.'

    try:
        media = mutagen.File(str(media_path), easy=True)
    except Exception as exc:
        return None, None, f'No se pudieron leer metadatos embebidos: {exc}'

    if media is None:
        return None, None, 'El archivo no contiene etiquetas legibles por mutagen.'

    tags = {}
    for key, value in media.items():
        if isinstance(value, (list, tuple)):
            tags[key] = ", ".join(str(item) for item in value if item is not None)
        else:
            tags[key] = str(value)

    details = {}
    info = getattr(media, "info", None)
    if info is not None:
        duration = getattr(info, "length", None)
        bitrate = getattr(info, "bitrate", None)
        sample_rate = getattr(info, "sample_rate", None)
        channels = getattr(info, "channels", None)

        formatted = _format_duration(duration)
        if formatted:
            details["Duración"] = formatted
        if bitrate:
            details["Bitrate"] = f"{int(bitrate / 1000)} kbps" if bitrate > 1000 else f"{bitrate} bps"
        if sample_rate:
            details["Frecuencia de muestreo"] = f"{int(sample_rate)} Hz"
        if channels:
            details["Canales"] = str(channels)

    return tags or None, details or None, None

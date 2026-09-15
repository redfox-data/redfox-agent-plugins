from .base import BaseSource, PlatformUnavailable
from .tiktok_source import TikTokSource
from .x_source import XSource
from .youtube_source import YouTubeSource

# Platform registry: to add a new platform, register it here.
SOURCES = {
    "x": XSource,
    "tiktok": TikTokSource,
    "youtube": YouTubeSource,
}

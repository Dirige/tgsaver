"""
文件名解析器 — 从 tg-emby-streamer 移植并增强
"""
import re
from dataclasses import dataclass
from typing import Optional

CN_NUM_MAP = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
    "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20,
    "二十一": 21, "二十二": 22, "二十三": 23, "二十四": 24, "二十五": 25,
}

RE_EPISODE = re.compile(r"第\s*(\d+)\s*集")
RE_EPISODE_UNDERSCORE = re.compile(r"第_(\d+)_集")
RE_EPISODE_NUM = re.compile(r"(\d+)\s*集")
RE_SEASON = re.compile(r"第\s*(\d+|[一二三四五六七八九十百]+)\s*季")
RE_YEAR = re.compile(r"[\(\（\[]?((?:19|20)\d{2})[\)\）\]]?")
RE_RESOLUTION = re.compile(r"(\d{3,4}[pPiI]|[24][kK])")
RE_SXXEXX = re.compile(r"[Ss](\d{1,2})[Ee](\d{1,3})")
RE_EPISODE_DASH = re.compile(r"[-–—]\s*(\d{1,3})\s*(?:\(|$|\[|\s)")

ANIME_KEYWORDS = [
    "动漫", "动画", "anime", "番", "字幕组",
    "Sub", "sub", "字幕", "双语", "简体", "繁体", "CHS", "CHT", "BIG5",
    "AVC", "AAC", "WEB-DL", "WEB_DL", "WebRip", "Baha",
    "ANi", "NEST", "FLsnow", "Sakurato", "Comicat", "Lamune",
    "Dynamis", "64bitsub", "orion_origin", "STYHSub",
]

BLOCKED_KEYWORDS = ["名器", "倒模"]


def _cn_to_int(s):
    s = s.strip()
    if s in CN_NUM_MAP:
        return CN_NUM_MAP[s]
    if s.isdigit():
        return int(s)
    return None


@dataclass
class ParseResult:
    title: str = ""
    season: int = None
    episode: int = None
    year: int = None
    resolution: str = ""
    category: str = ""
    is_episode: bool = False
    raw_name: str = ""

    @property
    def folder_name(self):
        name = self.title
        if self.year:
            name = f"{name} ({self.year})"
        return name

    @property
    def file_stem(self):
        parts = [self.title]
        if self.year and not self.is_episode:
            parts[0] = f"{self.title} ({self.year})"
        if self.season is not None and self.episode is not None:
            parts.append(f"S{self.season:02d}E{self.episode:02d}")
        elif self.episode is not None:
            parts.append(f"S01E{self.episode:02d}")
        return " - ".join(parts)

    def __str__(self):
        parts = [f"标题: {self.title}"]
        if self.year:
            parts.append(f"年份: {self.year}")
        if self.season:
            parts.append(f"季: S{self.season:02d}")
        if self.episode:
            parts.append(f"集: E{self.episode:02d}")
        if self.resolution:
            parts.append(f"分辨率: {self.resolution}")
        if self.category:
            parts.append(f"类型: {self.category}")
        return " | ".join(parts)


def _is_anime(file_name, caption=""):
    text = file_name + " " + (caption or "")
    for kw in ANIME_KEYWORDS:
        if kw in text:
            return True
    return False


def _is_blocked(file_name, caption=""):
    text = (file_name + " " + caption).lower()
    for kw in BLOCKED_KEYWORDS:
        if kw in text:
            return True
    return False


def _clean_title(title):
    if not title:
        return "unknown"
    title = re.sub(r"\[.*?\]", "", title)
    title = re.sub(r"[\(【（].*?[\)】）]", "", title)
    title = re.sub(r"@[a-zA-Z0-9_]+", "", title)
    title = re.sub(r"#\S+", "", title)
    title = re.sub(r"[Ss]\d{1,2}[Ee]\d{1,3}", "", title)
    title = re.sub(r"(?:4K|2160[pP]|1080[pP]|720[pP]|480[pP])", "", title)
    title = re.sub(r"(?:REMUX|BluRay|BDRip|WEB-DL|WEB_DL|WebRip|HDTV|DVDRip)", "", title, flags=re.I)
    title = re.sub(r"(?:H264|H265|x264|x265|AVC|AAC|FLAC|DTS|MP4|MKV)", "", title, flags=re.I)
    title = re.sub(r"(?:CHS|CHT|BIG5|GB|JPN)", "", title, flags=re.I)
    title = re.sub(r"(?:ADWeb|CMSUB|Lamune|Comicat|Sakurato|FLsnow|NEST|ANi|STYHSub|orion_origin|64bitsub)", "", title, flags=re.I)
    title = re.sub(r"(?:Baha|CR|ViuTV|Netflix|Amazon)", "", title, flags=re.I)
    title = re.sub(r"\d{3,4}x\d{3,4}", "", title)
    title = re.sub(r"[A-Fa-f0-9]{6,8}", "", title)
    title = re.sub(r"[_\.]+", " ", title)
    title = re.sub(r"\s+", " ", title)
    title = title.strip(" -_\n")
    return title if title else "unknown"


def _extract_bilingual_title(file_name, caption=""):
    if not caption:
        return None
    first_line = caption.split(chr(10))[0].strip()
    m = re.match(r"^[A-Za-z][A-Za-z .&|]+ \|\s*(.+?)\s*-\s*\d+", first_line)
    if m:
        return m.group(1).strip()
    return None


def parse_filename(file_name, caption=""):
    result = ParseResult(raw_name=file_name)

    if _is_blocked(file_name, caption):
        return result

    name = file_name
    name = re.sub(r"\.(mp4|mkv|avi|wmv|flv|mov|ts|strm)$", "", name, flags=re.I)

    # SXXEXX
    m = RE_SXXEXX.search(name)
    if m:
        result.season = int(m.group(1))
        result.episode = int(m.group(2))
        result.is_episode = True

    # 第X季
    if result.season is None:
        m = RE_SEASON.search(name)
        if m:
            result.season = _cn_to_int(m.group(1))

    # 第X集
    if result.episode is None:
        m = RE_EPISODE.search(name) or RE_EPISODE_UNDERSCORE.search(name) or RE_EPISODE_NUM.search(name)
        if m:
            result.episode = int(m.group(1))
            result.is_episode = True

    # - 数字
    if result.episode is None:
        m = RE_EPISODE_DASH.search(name)
        if m:
            result.episode = int(m.group(1))
            result.is_episode = True

    # 年份
    m = RE_YEAR.search(name)
    if m:
        result.year = int(m.group(1))

    # 分辨率
    m = RE_RESOLUTION.search(name)
    if m:
        result.resolution = m.group(1)

    # 标题
    bilingual = _extract_bilingual_title(file_name, caption)
    if bilingual:
        result.title = _clean_title(bilingual)
    else:
        title_part = name
        title_part = re.sub(r"[Ss]\d{1,2}[Ee]\d{1,3}.*", "", title_part)
        title_part = re.sub(r"第\s*\d+\s*集.*", "", title_part)
        title_part = re.sub(r"(第\s*\d+\s*季).*", r"", title_part)
        title_part = re.sub(r"[-–—]\s*\d{1,3}\s*$", "", title_part)
        title_part = re.sub(r"[\(\（]?(?:19|20)\d{2}[\)\）]?.*", "", title_part)
        title_part = re.sub(r"\d{3,4}[pPiI].*", "", title_part)
        title_part = re.sub(r"[24][kK].*", "", title_part)
        result.title = _clean_title(title_part)

    # 分类
    if not result.category:
        if _is_anime(file_name, caption):
            result.category = "动漫"
        elif result.is_episode or result.season is not None:
            result.category = "电视剧"
        else:
            result.category = "电影"

    return result

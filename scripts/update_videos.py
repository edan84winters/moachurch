"""유튜브 모아교회 채널의 최신 영상 목록을 videos.json 으로 저장합니다.

GitHub Actions(.github/workflows/videos.yml)가 몇 시간마다 실행합니다.
API 키 없이 유튜브 공개 RSS 피드만 읽습니다.
- 롱폼(설교·예배): 전체 업로드(UU…) 가운데 쇼츠가 아닌 영상
- 쇼츠: 쇼츠 목록(UUSH…)
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CHANNEL = "NEwkkMrLc8X0BRmjjG4sAQ"  # UC 다음 부분
FEED = "https://www.youtube.com/feeds/videos.xml?playlist_id={}"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
OUT = Path(__file__).resolve().parent.parent / "videos.json"


def fetch(prefix):
    req = urllib.request.Request(FEED.format(prefix + CHANNEL), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    items = []
    for e in root.findall("a:entry", NS):
        items.append({
            "id": e.findtext("yt:videoId", namespaces=NS),
            "title": (e.findtext("a:title", namespaces=NS) or "").strip(),
            "published": e.findtext("a:published", namespaces=NS),
        })
    items.sort(key=lambda v: v["published"], reverse=True)
    return items


def split_title(t):
    """'제목 | 부제 #shorts #태그' → ('제목', '부제')"""
    t = re.sub(r"\s#\S+", "", " " + t).strip()
    head, _, sub = t.partition("|")
    return head.strip(), sub.strip()


def main():
    uploads = fetch("UU")
    shorts = fetch("UUSH")
    short_ids = {s["id"] for s in shorts}
    data = {
        "sermons": [v for v in uploads if v["id"] not in short_ids][:6],
        "shorts": [dict(s, title=split_title(s["title"])[0], sub=split_title(s["title"])[1]) for s in shorts][:10],
    }
    if not data["sermons"] and not data["shorts"]:
        sys.exit("피드가 비어 있습니다. 기존 파일을 그대로 둡니다.")
    new = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if OUT.exists() and OUT.read_text(encoding="utf-8") == new:
        print("변경 없음")
        return
    OUT.write_text(new, encoding="utf-8")
    print(f"갱신: 설교 {len(data['sermons'])}개, 쇼츠 {len(data['shorts'])}개")


if __name__ == "__main__":
    main()

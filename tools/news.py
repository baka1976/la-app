"""오늘의 기사 제목 목록(news.json)을 만든다 — 앱 작문 탭의 「오늘의 기사 작문」이 읽는다.
제목과 링크만 모은다(기사 본문은 가져오지 않음). GitHub Actions(.github/workflows/news.yml)가 몇 시간마다 돌린다.
출처: Yahoo!ニュース 토픽스 RSS(주제별), 아사히신문 공식 RSS. NHK RSS는 2026-08에 갱신이 멈춰 쓰지 않는다.
사용법: python tools/news.py [출력 경로=news.json]"""
import json, sys, datetime, urllib.request, xml.etree.ElementTree as ET

UA = {'User-Agent': 'Mozilla/5.0 (LA study app headline list)'}
YAHOO = [('主要', 'top-picks'), ('国内', 'domestic'), ('国際', 'world'), ('経済', 'business'), ('IT', 'it'), ('科学', 'science')]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return r.read()


def rss2(url, n=15):
    root = ET.fromstring(get(url))
    out = []
    for it in root.iter('item'):
        t, l = (it.findtext('title') or '').strip(), (it.findtext('link') or '').strip()
        if t and l.startswith('http'):
            out.append({'title': t, 'link': l.replace('?source=rss', '')})
        if len(out) >= n:
            break
    return out


def rdf(url, n=15):
    root = ET.fromstring(get(url))
    ns = '{http://purl.org/rss/1.0/}'
    out = []
    for it in root.iter(ns + 'item'):
        t, l = (it.findtext(ns + 'title') or '').strip(), (it.findtext(ns + 'link') or '').strip()
        if t and l.startswith('http'):
            out.append({'title': t, 'link': l})
        if len(out) >= n:
            break
    return out


def main():
    dst = sys.argv[1] if len(sys.argv) > 1 else 'news.json'
    groups = []
    for name, key in YAHOO:
        try:
            items = rss2(f'https://news.yahoo.co.jp/rss/topics/{key}.xml')
            if items:
                groups.append({'name': name, 'src': 'Yahoo!ニュース', 'items': items})
        except Exception as e:
            print('skip', name, e)
    try:
        items = rdf('https://www.asahi.com/rss/asahi/newsheadlines.rdf')
        if items:
            groups.append({'name': '朝日 速報', 'src': '朝日新聞', 'items': items})
    except Exception as e:
        print('skip asahi', e)
    if not groups:
        sys.exit('no feed')
    jst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    json.dump({'at': jst.strftime('%m-%d %H:%M'), 'groups': groups}, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('ok', dst, sum(len(g['items']) for g in groups))


if __name__ == '__main__':
    main()

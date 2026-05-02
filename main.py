"""
🚀 Net TV Nepal IPTV Scraper & M3U Generator
Developed by: @DIWASXD & @DIWAZZ
Version: 2.0.0
Description: Automated IPTV playlist generator for Net TV Nepal with public fallback.
"""

import requests
import json
import os
import base64
import sys
from datetime import datetime

# --- Configuration ---
CONFIG = {
    "TVG_URL": "https://raw.githubusercontent.com/JOGINDHARR/Net-Tv-Iptv-Playlist/main/webtv.xml.gz",
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "REFERER": "https://webtv.nettv.com.np/",
    "ORIGIN": "https://webtv.nettv.com.np",
    "OUTPUT_FILE": "playlist.m3u"
}

HEADERS = {
    'User-Agent': CONFIG["USER_AGENT"],
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': CONFIG["REFERER"],
    'Origin': CONFIG["ORIGIN"],
}

# --- Public Channels Fallback ---
PUBLIC_CHANNELS = [
    {"id": "p1", "name": "Kantipur TV HD", "logo": "https://upload.wikimedia.org/wikipedia/en/2/2c/Kantipur_TV_HD_Logo.png", "url": "https://kantipur-hls.ykms.com.np/kantipur/kantipur/playlist.m3u8", "group": "News"},
    {"id": "p2", "name": "Nepal TV HD", "logo": "https://upload.wikimedia.org/wikipedia/en/0/05/Nepal_Television_logo.png", "url": "https://ntv.ykms.com.np/ntv/ntv/playlist.m3u8", "group": "News"},
    {"id": "p3", "name": "AP1 HD", "logo": "https://ap1.tv/wp-content/uploads/2017/03/ap1-logo.png", "url": "https://ap1-hls.ykms.com.np/ap1/ap1/playlist.m3u8", "group": "Entertainment"},
    {"id": "p4", "name": "Himalaya TV HD", "logo": "https://himalayatv.com/wp-content/themes/himalaya/images/logo.png", "url": "https://himalaya-hls.ykms.com.np/himalaya/himalaya/playlist.m3u8", "group": "News"},
    {"id": "p5", "name": "Image Channel", "logo": "https://imagechannel.com.np/wp-content/uploads/2018/01/image-logo.png", "url": "https://image-hls.ykms.com.np/image/image/playlist.m3u8", "group": "News"},
    {"id": "p6", "name": "ABC News Nepal", "logo": "https://abcnews.com.np/wp-content/uploads/2017/08/abc-logo.png", "url": "https://abc-hls.ykms.com.np/abc/abc/playlist.m3u8", "group": "News"}
]

class NetTvEngine:
    def __init__(self, token_data=None):
        self.token_data = token_data
        self.access_token = None
        self.jwt_payload = None
        if token_data:
            self._initialize_auth(token_data)

    def _initialize_auth(self, token_data):
        try:
            data = json.loads(token_data) if isinstance(token_data, str) else token_data
            self.access_token = data.get('access_token')
            if self.access_token:
                payload_b64 = self.access_token.split('.')[1]
                payload_b64 += '=' * (4 - len(payload_b64) % 4)
                self.jwt_payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
        except Exception as e:
            print(f"[-] Auth Init Error: {e}")

    def get_wms_signature(self):
        if not self.access_token: return None
        url = 'https://ott-resources.geniustv.geniussystems.com.np/nimble/wmsauthsign'
        try:
            res = requests.get(url, headers={**HEADERS, 'Authorization': f'Bearer {self.access_token}'}, timeout=10)
            return res.json().get('wmsauthsign')
        except: return None

    def fetch_nettv_data(self):
        if not self.jwt_payload: return None
        try:
            p = self.jwt_payload['params']
            url = f"https://ott-livetv-resources.geniustv.geniussystems.com.np/subscriber/livetv/v1/namespaces/{p['reseller_id']}/subscribers/{self.jwt_payload['sub']}/serial/{p['serial']}"
            res = requests.get(url, headers={**HEADERS, 'Authorization': f'Bearer {self.access_token}'}, timeout=15)
            return res.json()
        except Exception as e:
            print(f"[-] Data Fetch Error: {e}")
            return None

    def build_m3u(self):
        print("[+] Building M3U Playlist...")
        m3u = f"#EXTM3U x-tvg-url=\"{CONFIG['TVG_URL']}\"\n"
        m3u += f"# Created by: @DIWASXD | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 1. Add Public Channels
        print(f"[+] Adding {len(PUBLIC_CHANNELS)} Public Channels...")
        for ch in PUBLIC_CHANNELS:
            m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="{ch["group"]}", {ch["name"]}\n'
            m3u += f'{ch["url"]}\n\n'

        # 2. Add Net TV Channels if Token exists
        nettv_data = self.fetch_nettv_data()
        if nettv_data and 'result' in nettv_data:
            print("[+] Net TV Token detected. Fetching premium channels...")
            wms = self.get_wms_signature()
            res = nettv_data['result']
            cats = {c['id']: c['category'] for c in res['categories']}
            for ch in res['channels']:
                group = cats.get(res['category_channel_map'][0]['category_id'], "General") # Simplified mapping
                stream = ch['channel_urls'][0]['path']
                if wms: stream += f"{'&' if '?' in stream else '?' }wmsAuthSign={wms}"
                
                m3u += f'#EXTINF:-1 tvg-id="ntv-{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="{group}", {ch["name"]}\n'
                m3u += f'#KODIPROP:inputstream=inputstream.adaptive\n'
                m3u += f'#KODIPROP:inputstream.adaptive.manifest_type=hls\n'
                m3u += f'#KODIPROP:http-origin={CONFIG["ORIGIN"]}\n'
                m3u += f'#KODIPROP:http-referrer={CONFIG["REFERER"]}\n'
                m3u += f'#KODIPROP:http-User-Agent={CONFIG["USER_AGENT"]}\n'
                m3u += f'{stream}\n\n'
        else:
            print("[!] No valid Net TV token found. Skipping premium channels.")

        return m3u

def main():
    token = os.environ.get('NETTV_TOKEN')
    if not token and os.path.exists('nettv.json'):
        try:
            with open('nettv.json', 'r') as f:
                token = json.load(f)
        except: pass

    engine = NetTvEngine(token)
    content = engine.build_m3u()
    
    with open(CONFIG["OUTPUT_FILE"], "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✅] Success! Playlist saved to {CONFIG['OUTPUT_FILE']}")

if __name__ == "__main__":
    main()

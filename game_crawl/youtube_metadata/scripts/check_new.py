import json
from datetime import datetime

with open('youtube_metadata_heartopia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
# 过滤时间戳 2026-04-01T08:13:48+00:00 之后
cutoff = datetime.fromisoformat('2026-04-01T08:13:48+00:00')
new_videos = [v for v in data['items'] if datetime.fromisoformat(v['published_at']) > cutoff]
total = len(data["items"])
print(f'Total videos: {total}')
print(f'New videos after 2026-04-01T08:13:48: {len(new_videos)}')

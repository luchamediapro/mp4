import json
import re

from .common import InfoExtractor


class France24IE(InfoExtractor):
    IE_NAME = 'france24'
    _VALID_URL = r'https?://www\.france24\.com/'
    _TESTS = [{
        'url': 'https://www.france24.com/fr/émissions/invité-du-jour/20230608-eva-jospin-plasticienne-le-propre-de-la-sculpture-c-est-le-rapport-à-l-espace',
        'info_dict': {
            'age_limit': 0,
            'availability': 'public',
            'categories': ['News & Politics'],
            'channel': 'FRANCE 24',
            'channel_follower_count': int,
            'channel_id': 'UCCCPCZNChQdGa9EkATeye4g',
            'channel_is_verified': True,
            'channel_url': 'https://www.youtube.com/channel/UCCCPCZNChQdGa9EkATeye4g',
            'chapters': [
                {'start_time': 0.0, 'title': 'Introduction', 'end_time': 30.0},
                {'start_time': 30.0, 'title': 'Palais des Papes', 'end_time': 80.0},
                {'start_time': 80.0, 'title': 'Forêt', 'end_time': 140.0},
                {'start_time': 140.0, 'title': 'Carton', 'end_time': 260.0},
                {'start_time': 260.0, 'title': 'Le repentir', 'end_time': 395.0},
                {'start_time': 395.0, 'title': 'Les architectures de fête', 'end_time': 480.0},
                {'start_time': 480.0, 'title': "L'art contemporain", 'end_time': 535.0},
                {'start_time': 535.0, 'title': "L'habitat troglodyte", 'end_time': 605.0},
                {'start_time': 605.0, 'title': "L'urgence climatique", 'end_time': 701},
            ],
            'comment_count': int,
            'description': 'md5:7a7cc352189bbc16132b5f4819f2ed8a',
            'duration': 701,
            'ext': 'mp4',
            'id': '4fFMuXLWfAo',
            'like_count': int,
            'live_status': 'not_live',
            'playable_in_embed': True,
            'tags': ['Art', 'Culture', "Festival d'Avignon", 'L_INVITE DU JOUR', 'Sculpture', 'france24', 'news'],
            'thumbnail': 'https://i.ytimg.com/vi/4fFMuXLWfAo/sddefault.jpg',
            'timestamp': 1686218017,
            'title': '''Eva Jospin, plasticienne : "Le propre de la sculpture, c'est le rapport à l'espace" • FRANCE 24''',
            'upload_date': '20230608',
            'uploader': 'FRANCE 24',
            'uploader_id': '@FRANCE24',
            'uploader_url': 'https://www.youtube.com/@FRANCE24',
            'view_count': int,
        },
    }, {
        'url': 'https://www.france24.com/en/europe/20250214-drone-warfare-stalls-progress-on-ukraine-s-front-line',
        'only_matching': True,
    }, {
        'url': 'https://www.france24.com/fr/éco-tech/20250215-cinq-questions-clés-sur-le-doge-la-commission-d-elon-musk-qui-opère-une-purge-administrative',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, None, 'Downloading video page', headers={'User-Agent': 'curl/8.12.1'})
        name, info = self._search_regex(r'<script data-media-video-id="([^"]+)" type="application/json">$([^<]*)</script>', webpage, 'video info', flags=re.MULTILINE, group=(1, 2))
        for source in json.loads(info)['sources']:
            if source['name'] == name:
                return self.url_result(source['url'])

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
    remove_start,
    str_or_none,
    traverse_obj,
    url_or_none,
    ExtractorError,
)
from urllib.error import HTTPError


class RozhlasIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?prehravac\.rozhlas\.cz/audio/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://prehravac.rozhlas.cz/audio/3421320',
        'md5': '504c902dbc9e9a1fd50326eccf02a7e2',
        'info_dict': {
            'id': '3421320',
            'ext': 'mp3',
            'title': 'Echo Pavla Klusáka (30.06.2015 21:00)',
            'description': 'Osmdesátiny Terryho Rileyho jsou skvělou příležitostí proletět se elektronickými i akustickými díly zakladatatele minimalismu, který je aktivní už přes padesát let'
        }
    }, {
        'url': 'http://prehravac.rozhlas.cz/audio/3421320/embed',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://prehravac.rozhlas.cz/audio/%s' % audio_id, audio_id)

        title = self._html_search_regex(
            r'<h3>(.+?)</h3>\s*<p[^>]*>.*?</p>\s*<div[^>]+id=["\']player-track',
            webpage, 'title', default=None) or remove_start(
            self._og_search_title(webpage), 'Radio Wave - ')
        description = self._html_search_regex(
            r'<p[^>]+title=(["\'])(?P<url>(?:(?!\1).)+)\1[^>]*>.*?</p>\s*<div[^>]+id=["\']player-track',
            webpage, 'description', fatal=False, group='url')
        duration = int_or_none(self._search_regex(
            r'data-duration=["\'](\d+)', webpage, 'duration', default=None))

        return {
            'id': audio_id,
            'url': 'http://media.rozhlas.cz/_audio/%s.mp3' % audio_id,
            'title': title,
            'description': description,
            'duration': duration,
            'vcodec': 'none',
        }


class RozhlasVltavaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.rozhlas|english\.radio)\.cz/[\w-]+-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://wave.rozhlas.cz/papej-masicko-porcujeme-a-bilancujeme-filmy-a-serialy-ktere-letos-zabily-8891337',
        'md5': 'ba2fdbc1242fc16771c7695d271ec355',
        'info_dict': {
            'id': '8891337',
            'title': 'md5:21f99739d04ab49d8c189ec711eef4ec',
        },
        'playlist_count': 1,
        'playlist': [{
            'md5': 'ba2fdbc1242fc16771c7695d271ec355',
            'info_dict': {
                'id': '10520988',
                'ext': 'mp3',
                'title': 'Papej masíčko! Porcujeme a bilancujeme filmy a seriály, které to letos zabily',
                'description': 'md5:1c6d29fb9564e1f17fc1bb83ae7da0bc',
                'duration': 1574,
                'artist': 'Aleš Stuchlý',
                'channel_id': 'radio-wave',
            },
        }]
    }, {
        'url': 'https://wave.rozhlas.cz/poslechnete-si-neklid-podcastovy-thriller-o-vine-strachu-a-vztahu-ktery-zasel-8554744',
        'info_dict': {
            'id': '8554744',
            'title': 'Poslechněte si Neklid. Podcastový thriller o vině, strachu a vztahu, který zašel příliš daleko',
        },
        'playlist_count': 5,
        'playlist': [{
            'md5': '93d4109cf8f40523699ae9c1d4600bdd',
            'info_dict': {
                'id': '9890713',
                'ext': 'mp3',
                'title': 'Neklid #1',
                'description': '1. díl: Neklid: 1. díl',
                'duration': 1025,
                'artist': 'Josef Kokta',
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #1',
                'chapter_number': 1,
            },
        }, {
            'md5': 'e9763235be4a6dcf94bc8a5bac1ca126',
            'info_dict': {
                'id': '9890716',
                'ext': 'mp3',
                'title': 'Neklid #2',
                'description': '2. díl: Neklid: 2. díl',
                'duration': 768,
                'artist': 'Josef Kokta',
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #2',
                'chapter_number': 2,
            },
        }, {
            'md5': '00b642ea94b78cc949ac84da09f87895',
            'info_dict': {
                'id': '9890722',
                'ext': 'mp3',
                'title': 'Neklid #3',
                'description': '3. díl: Neklid: 3. díl',
                'duration': 607,
                'artist': 'Josef Kokta',
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #3',
                'chapter_number': 3,
            },
        }, {
            'md5': 'faef97b1b49da7df874740f118c19dea',
            'info_dict': {
                'id': '9890728',
                'ext': 'mp3',
                'title': 'Neklid #4',
                'description': '4. díl: Neklid: 4. díl',
                'duration': 621,
                'artist': 'Josef Kokta',
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #4',
                'chapter_number': 4,
            },
        }, {
            'md5': '6e729fa39b647325b868d419c76f3efa',
            'info_dict': {
                'id': '9890734',
                'ext': 'mp3',
                'title': 'Neklid #5',
                'description': '5. díl: Neklid: 5. díl',
                'duration': 908,
                'artist': 'Josef Kokta',
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #5',
                'chapter_number': 5,
            },
        }]
    }, {
        'url': 'https://dvojka.rozhlas.cz/karel-siktanc-cerny-jezdec-bily-kun-napinava-pohadka-o-tajemnem-prizraku-8946969',
        'info_dict': {
            'id': '8946969',
            'title': 'Karel Šiktanc: Černý jezdec, bílý kůň. Napínavá pohádka o tajemném přízraku',
        },
        'playlist_count': 1,
        'playlist': [{
            'info_dict': {
                'id': '10631121',
                'ext': 'm4a',
                'title': 'Karel Šiktanc: Černý jezdec, bílý kůň. Napínavá pohádka o tajemném přízraku',
                'description': 'Karel Šiktanc: Černý jezdec, bílý kůň',
                'duration': 2656,
                'artist': 'Tvůrčí skupina Drama a literatura',
                'channel_id': 'dvojka',
            },
        }],
        'params': {'skip_download': 'dash'},
    }]
    _429_TIMEOUT = 1

    def _extract_audio(self, entry, audio_id):
        formats = []
        for audio in traverse_obj(entry, ('audioLinks', lambda _, v: url_or_none(v['url']))):
            ext = audio.get('variant')
            try:
                if ext == 'dash':
                    formats.extend(self._extract_mpd_formats(
                        audio['url'], audio_id, mpd_id=ext))
                elif ext == 'hls':
                    formats.extend(self._extract_m3u8_formats(
                        audio['url'], audio_id, 'm4a', m3u8_id=ext))
                else:
                    formats.append({
                        'url': audio['url'],
                        'ext': ext,
                        'format_id': ext,
                        'abr': int_or_none(audio.get('bitrate')),
                        'acodec': ext,
                        'vcodec': 'none',
                    })
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.code == 429:
                    self.report_warning('Getting rate limited', audio_id)
                    self._sleep(self._429_TIMEOUT, audio_id)
                else:
                    pass

        return formats

    def _extract_video(self, entry):
        audio_id = entry['meta']['ga']['contentId']

        formats = self._extract_audio(entry, audio_id)

        chapter_number = traverse_obj(entry, ('meta', 'ga', 'contentSerialPart', {int_or_none}))

        return {
            'id': audio_id,
            'chapter': traverse_obj(entry, ('meta', 'ga', 'contentNameShort')) if chapter_number else None,
            'chapter_number': chapter_number,
            'formats': formats,
            **traverse_obj(entry, {
                'title': ('meta', 'ga', 'contentName'),
                'description': 'title',
                'duration': ('duration', {int_or_none}),
                'artist': ('meta', 'ga', 'contentAuthor'),
                'channel_id': ('meta', 'ga', 'contentCreator'),
            })
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # FIXME: Use get_element_text_and_html_by_tag when it accepts less strict html
        data = self._parse_json(extract_attributes(self._search_regex(
            r'(<div class="mujRozhlasPlayer" data-player=\'[^\']+\'>)',
            webpage, 'player'))['data-player'], video_id)['data']

        return {
            '_type': 'playlist',
            'id': str_or_none(data.get('embedId')) or video_id,
            'title': traverse_obj(data, ('series', 'title')),
            'entries': map(self._extract_video, data['playlist']),
        }

import json
import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
)


class CreateAcademyBaseIE(InfoExtractor):
    _VALID_URL = r'https://www.createacademy.com/(?:[^/]+/)*lessons/(?P<id>[^/?#]+)'

    _TESTS = [
        {
            'url': 'https://www.createacademy.com/courses/dan-pearson/lessons/meet-dan',
            'info_dict': {
                'id': '265',
                'ext': 'mp4',
                'title': 'Create Academy - s10e01 - Meet Dan',
                'description': 'md5:48c8af37219020571a84d5f406e75d86',
                'display_id': 'meet-dan',
                'chapter': 'Introduction',
                'chapter_id': '34',
                'chapter_number': 1,
                'thumbnail': 'https://cf-images.eu-west-1.prod.boltdns.net/v1/static/6222962662001/22f75006-c49f-4d95-8673-1b60df4223d2/45d953e0-fa58-4cb6-9217-1c7b3c80c932/1280x720/match/image.jpg',
            },
        },
    ]

    def _get_lesson_metadata(self, data, lesson_id):
        prefix = 'Create Academy - s' + str(data['props']['course']['id']).zfill(2) + 'e'

        for section in data['props']['course']['curriculum']['sections']:
            for lesson in section['lessons']:
                if lesson['id'] == lesson_id:
                    return {
                        'section_data': section,
                        'title': prefix + str(lesson['number']).zfill(2) + ' - ' + lesson['title'].strip(),
                    }

        return {
            'section_data': {
                'id': 0,
                'number': 0,
                'title': '',
            },
            'title': prefix + '00 - ' + data['props']['lesson']['title'].strip(),
        }

    def _get_policy_key(self, data, video_id):
        accountId = data['props']['brightcove']['accountId']
        playerId = data['props']['brightcove']['playerId']

        playerData = self._download_webpage(f'https://players.brightcove.net/{accountId}/{playerId}_default/index.min.js', video_id, 'Retrieving policy key')
        obj = re.search(r'{policyKey:"(.*?)"}', playerData)
        key = re.search(r'"(.*?)"', obj.group())

        return key.group().replace('"', '')

    def _get_manifest_url(self, data, video_id):
        hostVideoId = data['props']['lesson']['video']['host_video_id']
        accountId = data['props']['brightcove']['accountId']
        policyKey = self._get_policy_key(data, video_id)

        manifestData = self._download_json(f'https://edge.api.brightcove.com/playback/v1/accounts/{accountId}/videos/{hostVideoId}', video_id, 'Retrieving manifest URL', headers={'accept': f'application/json;pk={policyKey}'})

        for source in manifestData['sources']:
            if 'master.m3u8' in source['src']:
                return source['src']

    def _get_page_data(self, url, video_id):
        webpage = self._download_webpage(url, video_id)

        page_elem = self._search_regex(r'(<div[^>]+>)', webpage, 'div')
        attributes = extract_attributes(page_elem)

        return json.loads(attributes['data-page'])

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._get_page_data(url, video_id)
        createacademy_id = data['props']['lesson']['id']

        # get media from manifest
        manifestUrl = self._get_manifest_url(data, video_id)

        formats, subtitles = [], {}
        fmts, subs = self._extract_m3u8_formats_and_subtitles(manifestUrl, str(createacademy_id), 'mp4')

        formats.extend(fmts)
        self._merge_subtitles(subs, target=subtitles)

        lesson_metadata = self._get_lesson_metadata(data, createacademy_id)

        return {
            'id': str(createacademy_id),
            'title': lesson_metadata['title'],
            'display_id': video_id,
            'description': data['props']['lesson']['description'],
            'thumbnail': data['props']['lesson']['thumbnail'],
            'formats': formats,
            'subtitles': subtitles,
            'chapter': lesson_metadata['section_data']['title'].strip(),
            'chapter_number': lesson_metadata['section_data']['number'],
            'chapter_id': str(lesson_metadata['section_data']['id']),
        }


class CreateAcademyCourseIE(CreateAcademyBaseIE):
    _VALID_URL = r'https://www.createacademy.com/courses/(?P<id>[^/?#]+)'

    _TESTS = [
        {
            'url': 'https://www.createacademy.com/courses/dan-pearson',
            'info_dict': {
                'id': '265',
                'ext': 'mp4',
                'chapter_id': '34',
                'description': 'md5:48c8af37219020571a84d5f406e75d86',
                'chapter_number': 1,
                'thumbnail': 'https://cf-images.eu-west-1.prod.boltdns.net/v1/static/6222962662001/22f75006-c49f-4d95-8673-1b60df4223d2/45d953e0-fa58-4cb6-9217-1c7b3c80c932/1280x720/match/image.jpg',
                'title': 'Create Academy - s10e01 - Meet Dan',
                'display_id': 'dan-pearson',
                'chapter': 'Introduction',
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._get_page_data(url, video_id)

        # iterate lessons
        entries = []

        for section in data['props']['curriculum']['sections']:
            for lesson in section['lessons']:
                entries.append(super()._real_extract('https://www.createacademy.com' + lesson['lessonPath']))

        return {
            '_type': 'multi_video',
            'entries': entries,
        }

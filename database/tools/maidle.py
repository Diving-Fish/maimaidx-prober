import json
import random

def is_good_music(music):
    if len(music['difficulties']['dx']) == 0 and len(music['difficulties']['standard']) == 0:
        return False
    target_diff = music['difficulties']['standard'][3] if len(music['difficulties']['standard']) > 0 else music['difficulties']['dx'][3]
    return len(target_diff['tags']) > 0 and not music.get('disabled', False)

with open('maidle/music_data.json', 'r', encoding='utf-8') as f:
    music_data = json.load(f)
    songs = list(filter(lambda x: is_good_music(x), music_data['songs']))

with open('maidle/alias.json', 'r', encoding='utf-8') as f:
    alias_data = json.load(f)
    for i in range(len(songs)):
        for alias in alias_data['aliases']:
            if songs[i]['id'] == alias['song_id']:
                songs[i]['aliases'] = alias['aliases']
                break

with open('maidle/hot_list.json', 'r', encoding='utf-8') as f:
    hot_ids = json.load(f)

songs_id_map = {}
for s in songs:
    songs_id_map[s['id']] = s

maidle_data = {
    'songs': songs,
    'genres': music_data['genres'],
    'versions': music_data['versions'],
    'hots': hot_ids,
}


def random_music(id_range):
    if len(id_range) > 0:
        f_songs = list(filter(lambda x: x['id'] in id_range, songs))
        return random.choice(f_songs)
    return random.choice(songs)

def get_version(music):
    v = music['version']
    for i in range(len(music_data['versions'])):
        if i == len(music_data['versions']) - 1:
            return music_data['versions'][-1]['title'], music_data['versions'][-1]['id']
        if music_data['versions'][i]['version'] <= v < music_data['versions'][i + 1]['version']:
            return music_data['versions'][i]['title'], music_data['versions'][i]['id']

class Maidle():
    def __init__(self, id_range=[], id=None):
        if id is not None:
            self.music = songs_id_map[id]
        else:
            self.music = random_music(id_range)
        self.maidle = self.get_maidle(self.music)

    @staticmethod
    def get_maidle(music):
        types = []
        if len(music['difficulties']['dx']) > 0:
            types.append('dx')
        if len(music['difficulties']['standard']) > 0:
            types.append('standard')
        return {
            'title': music['title'],
            'artist': music['artist'],
            'type': types,
            'genre': music['genre'],
            'bpm': music['bpm'],
            'version': get_version(music)[0],
            'version_value': get_version(music)[1],
            'map': music.get('map', '无所属区域'),
            'level': music['difficulties']['dx'][3]['level'] if ('standard' not in types) else music['difficulties']['standard'][3]['level'],
            'level_value': music['difficulties']['dx'][3]['level_value'] if ('standard' not in types) else music['difficulties']['standard'][3]['level_value'],
            'tags': music['difficulties']['dx'][3]['tags'] if ('standard' not in types) else music['difficulties']['standard'][3]['tags'],
        }
    
    def maidle_test(self, music):
        maidle = self.get_maidle(music)
        test = {}
        test['title'] = {
            'result': 'green lighten-1' if self.maidle['title'] == maidle['title'] else '',
            'value': maidle['title']
        }
        test['artist'] = {
            'result': 'green lighten-1' if self.maidle['artist'] == maidle['artist'] else '',
            'value': maidle['artist']
        }
        test['genre'] = {
            'result': 'green lighten-1' if self.maidle['genre'] == maidle['genre'] else '',
            'value': maidle['genre']
        }
        test['type'] = []
        for t in maidle['type']:
            if t not in self.maidle['type']:
                test['type'].append({
                    'result': '',
                    'value': t
                })
            else:
                test['type'].append({
                    'result': 'green lighten-1',
                    'value': t
                })
        bpm_percent = abs(self.maidle['bpm'] - maidle['bpm']) / self.maidle['bpm']
        if bpm_percent == 0:
            bpm_test = 'green lighten-1'
        elif bpm_percent < 0.1:
            bpm_test = 'amber lighten-1'
        else:
            bpm_test = ''
        test['bpm'] = {
            'result': bpm_test,
            'greater': True if maidle['bpm'] > self.maidle['bpm'] else False,
            'value': maidle['bpm']
        }

        version_abs = abs(self.maidle['version_value'] - maidle['version_value'])
        if version_abs == 0:
            version_test = 'green lighten-1'
        elif version_abs <= 1:
            version_test = 'amber lighten-1'
        else:
            version_test = ''
        test['version'] = {
            'result': version_test,
            'greater': True if maidle['version_value'] > self.maidle['version_value'] else False,
            'value': maidle['version']
        }

        # test['map'] = {
        #     'result': 'green lighten-1' if self.maidle['map'] == maidle['map'] else '',
        #     'value': maidle['map']
        # }

        level_abs = abs(self.maidle['level_value'] - maidle['level_value'])
        if level_abs == 0:
            level_test = 'green lighten-1'
        elif self.maidle['level'] == maidle['level']:
            level_test = 'amber lighten-1'
        else:
            level_test = ''
        
        test['level'] = {
            'result': level_test,
            'greater': True if maidle['level_value'] > self.maidle['level_value'] else False,
            'value': maidle['level_value']
        }

        test['tags'] = []

        for tag in maidle['tags']:
            if tag not in self.maidle['tags']:
                test['tags'].append({
                    'result': '',
                    'value': tag
                })
            else:
                test['tags'].append({
                    'result': 'green lighten-1',
                    'value': tag
                })
        return test

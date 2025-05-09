import configparser
import requests
import json
from tqdm import tqdm

class VK:
    def __init__(self, token, version='5.131'):
        self.params = {
            'access_token': token,
            'v': version
        }
        self.base = 'https://api.vk.com/method/'

    def get_photos(self, owner_id, count=5):
        url = f'{self.base}photos.get'
        params = {
            'user_id': owner_id,
            'count': count,
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1
        }
        params.update(self.params)
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f'Ошибка запроса к VK: {response.status_code}')

        data = response.json()
        if 'error' in data:
            raise Exception(f"VK API error: {data['error']['error_msg']}")

        photo_result = []
        for photo in data['response']['items']:
            max_size = max(photo['sizes'], key=lambda s: s['width'] * s['height'])
            file_name = f"{photo['likes']['count']}.jpg"
            photo_result.append({
                'file_name': file_name,
                'size_type': max_size['type']
            })

        return photo_result

class YD:
    def __init__(self, token):
        self.token = token
        self.base = 'https://cloud-api.yandex.net/v1/disk/'

    def create_folder(self, folder_name):
        url = f'{self.base}resources'
        headers = {
            'Authorization': f'OAuth {self.token}'
        }
        params = {
            'path': folder_name
        }
        response = requests.put(url, headers=headers, params=params)
        if response.status_code == 201:
            print(f"Папка '{folder_name}' создана.")
        elif response.status_code == 409:
            print(f"Папка '{folder_name}' уже существует.")
        else:
            print(f"Ошибка {response.status_code}: не удалось создать папку ;(")
        return response.status_code

    def upload_file(self, disk_path):
        url = f'{self.base}resources/upload'
        headers = {
            'Authorization': f'OAuth {self.token}'
        }
        params = {
            'path': disk_path
        }
        response = requests.post(url, headers=headers, params=params)
        if response.status_code in [201, 202]:
            print(f'Загружено: {disk_path}')
        else:
            print(f"Ошибка загрузки '{disk_path}': {response.status_code}")
        return response.status_code

def read_config(path):
    config = configparser.ConfigParser()
    config.read(path)
    return config

def save_to_json(data, filename='result.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f'Сохранена информация о фотографиях в {filename}')

if __name__ == '__main__':
    config = read_config('settings.ini')
    vk_token = config['Tokens']['vk_token']
    yd_token = config['Tokens']['yd_token']

    vk = VK(config['Tokens']['vk_token'])
    yd = YD(config['Tokens']['yd_token'])

    user_id = 158393031

    photos = vk.get_photos(user_id, 5)

    folder_name = 'vk_photos'
    yd.create_folder(folder_name)

    for photo in tqdm(photos, desc='Загрузка фото на Яндекс.Диск:'):
        file_name = photo['file_name']
        disk_path = f'{folder_name}/{file_name}'
        yd.upload_file(disk_path)

    save_to_json(
        [{'file_name': p['file_name'], 'size': p['size_type']} for p in photos]
    )
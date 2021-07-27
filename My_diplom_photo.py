from datetime import datetime
import requests
import hashlib
import json
import time
from tqdm import tqdm
import sys

# Прогресс бар
def get_progress_bar():
    for i in tqdm(range(500)):
        time.sleep(0.001)

# Класс для получения списка фотогорафий с "вконтакте"
class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, album_id, id_user, token):
        self.album_id = album_id
        self.id_user = id_user
        self.params = {
            'access_token': token,
            'v': '5.131'
        }

    def get_list_photo(self):
        list_photo_url = self.url + 'photos.get'
        list_photo_params = {
            'owner_id': self.id_user,
            'album_id': self.album_id,
            'photo_sizes': '1',
            'extended': "1"
        }

        req = requests.get(list_photo_url, params={**self.params, **list_photo_params}).json()
        error = 'error'
        if error not in req:
            return req['response']
        else:
            print('У вас недостаточно прав доступа...')
            sys.exit(0)

    def get_file(self):
        dict_files = {}
        count = 1
        file_list = []
        self.get_list = self.get_list_photo()

        for lists in self.get_list['items']:
            file_name = str(lists['likes']['count']) + '.jpg'
            for data in lists['sizes']:
                if data['type'] == 'z':
                    file_url = data["url"]
                    size = data['height'] * data['width']
                    size_type = data['type']
                    if file_name not in file_list:
                        dict_files[count] = [file_name, file_url, size, size_type]
                        file_list.append(file_name)
                        count += 1
                    else:
                        file_name = str(lists['likes']['count']) + '_' + datetime.utcfromtimestamp \
                            (lists['date']).strftime('%d_%m_%Y_%H_%M_%S') + '.jpg'
                        dict_files[count] = [file_name, file_url, size, size_type]
                        count += 1
        return dict_files

# Класс для получения списка фотогорафий с "одноклассники"
class OkUser:
    url = 'https://api.ok.ru/fb.do?method'

    def __init__(self, id_user, access_token, session_secret_key, application_key):
        self.id_user = id_user
        self.method_photos = "photos.getPhotos"
        self.method_albums = "photos.getAlbums"
        self.aid = ' '

        # Регистрационные данные
        self.access_token = access_token
        self.session_secret_key = session_secret_key
        self.application_key = application_key

    def get_params(self):
        self.params = {
            "access_token": self.access_token
        }
        return self.params

    def get_params_1(self, method):
        self.method = method
        self.params = {
            'application_key': self.application_key,
            'format': 'json',
            'method': self.method,
            'fid': self.id_user
        }
        return self.params

    def get_hash_md(self, params_res):
        self.params_res = params_res
        str = ''
        params = sorted(self.params_res.items())
        for i, v in params:
            str += (i + '=' + f'{v}')
        str += self.session_secret_key
        sig = hashlib.md5(
            str.encode('utf-8')).hexdigest()
        return sig

    def get_album(self):
        list_album_url = self.url + '=' + self.method_albums
        self.get_params()
        params = {
            'count': 100
        }
        params_1 = self.get_params_1(method=self.method_albums)
        params_1.update(params)

        self.params_res = params_1
        params_1['sig'] = self.get_hash_md(params_res=self.params_res)
        params_1.update(self.get_params())
        req = requests.get(list_album_url, params=params_1).json()
        return req['albums']

    def get_aid_album(self):
        dict_1 = {}
        list = []
        for dict in self.get_album():
            dict_1[dict['title']] = dict['aid']
            list.append(dict['title'])
        return [dict_1, list]

    def get_id_album(self):
        album = self.get_aid_album()
        while True:
            albums_name = input(
                f'Выберите альбом, откуда хотите скопировать фото (Личныефото - 0, либо введите'
                f' название альбома {album[1]}, если хотите завершить ввод - "q"): ')
            if albums_name == '0':
                self.list_photo_params = {
                    'count': 100,
                    'fields': 'user_photo.CREATED_MS, user_photo.PIC_MAX, user_photo.PIC1024MAX,'
                              ' user_photo.LIKE_COUNT, photo.STANDARD_HEIGHT, photo.STANDARD_WIDTH',

                }
                return self.list_photo_params
            elif albums_name in album[1]:
                self.aid = album[0].get(albums_name)
                self.list_photo_params = {
                    'count': 100,
                    'fields': 'user_photo.CREATED_MS, user_photo.PIC_MAX, user_photo.PIC1024MAX,'
                              ' user_photo.LIKE_COUNT, photo.STANDARD_HEIGHT, photo.STANDARD_WIDTH',
                    'aid': self.aid
                }
                return self.list_photo_params
            elif albums_name == 'q':
                sys.exit(0)
            elif albums_name not in album[1]:
                print("Вы ввели неверные данные...")

    def get_list_photo(self):
        list_photo_url = self.url + '=' + self.method_photos

        params_1 = self.get_params_1(method=self.method_photos)
        params_1.update(self.get_id_album())
        self.params_res = params_1
        params_1['sig'] = self.get_hash_md(params_res=self.params_res)
        params_1.update(self.get_params())

        req = requests.get(list_photo_url, params=params_1).json()
        return req['photos']

    def get_file(self):
        dict_files = {}
        count = 1
        file_list = []
        for lists in self.get_list_photo():
            file_name = str(lists['like_count']) + '.jpg'
            file_url = lists["pic_max"]
            size = lists['standard_height'] * lists['standard_width']
            size_type = 'pic_max'
            if file_name not in file_list:
                dict_files[count] = [file_name, file_url, size, size_type]
                file_list.append(file_name)
                count += 1
            else:
                file_name = str(lists['like_count']) + '_' + datetime.utcfromtimestamp(
                    int(str(lists['created_ms'])[0:10])).strftime('%d_%m_%Y_%H_%M_%S') + '.jpg'
                dict_files[count] = [file_name, file_url, size, size_type]
                count += 1
        return dict_files

# Класс обработки полученного списка фотографий
class List_Files:
    def __init__(self, get_file, file_count=5):
        self.get_file = get_file
        # Количество загружаемых фотографий
        self.file_count = file_count

    def get_list_sorted(self):
        list_files_1 = sorted(self.get_file.items(), key=lambda x: x[1][2], reverse=True)
        return list_files_1

    def get_file_json(self):
        list_files_1 = self.get_list_sorted()
        list_files = []
        res_dict = {}
        count = 0

        for k, v in list_files_1:
            if count < self.file_count:
                res_dict["file_name"] = v[0]
                res_dict["size"] = v[3]
                list_files.append(res_dict.copy())
                count += 1
        return list_files

    def get_file_url(self):
        list_files_1 = self.get_list_sorted()
        res_dict = {}
        count = 0
        for k, v in list_files_1:
            if count < self.file_count:
                res_dict[v[0]] = v[1]
                count += 1
        return res_dict

# Класс для записи json файла со списком фотографий
class File_Json_Write:
    def __init__(self, list_files, name_file):
        self.list_files = list_files
        self.name_file = name_file

    def get_file_json(self):
        now = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        file_name = self.name_file + '_' + now
        with open(file_name + '.json', 'w') as f:
            json.dump(self.list_files, f, ensure_ascii=False, indent=2)

# Класс загрузки файлов на "яндекс диск"
class File_Upload_Ydisk:
    def __init__(self, file_url):
        self.file_url = file_url
        # Введите token для доступа к яндекс диску
        self.token = ''

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def upload(self):
        dir_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        dir_name = input("Введите название папки, которую хотите создать: ")
        params = {"path": "/" + dir_name}
        headers = self.get_headers()
        response = requests.put(dir_url, headers=headers, params=params)

        if response.status_code == 201:
            upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
            headers = self.get_headers()

            for name in self.file_url.items():
                get_progress_bar()
                path = name[0]
                params = {"path": '/' + dir_name + '/' + path, "overwrite": "true"}
                r = requests.get(name[1])
                image_data = r.content
                response = requests.get(upload_url, headers=headers, params=params)
                href = response.json().get("href", "")
                response_1 = requests.put(href, image_data)
                response_1.raise_for_status()
                if response_1.status_code == 201:
                    ok = "Файл(ы) успешно загружен(ы)"
            return print(ok)

# Экземляры классов для работы с "вконтакте"
def get_vk(album_id):
    # Здесь введите id_user - id пользователя вконтакте, фото которого копируете и token - для доступа
    vk_1 = VkUser(album_id=album_id, id_user='1',
                  token='')
    list_files = List_Files(vk_1.get_file())
    file_jason_write = File_Json_Write(list_files.get_file_json(), 'Archiv_Vk')
    file_jason_write.get_file_json()
    yd_upload = File_Upload_Ydisk(list_files.get_file_url())
    return yd_upload.upload()

# Выбор альбома в "вконтакте"
def sel_album_vk():
    while True:
        album_id = input('Выберите папку "вконтакте" из которой хотите сохранить фото ("1" - профиль, "2" - стена,'
                         ' "3" - сохраненные фото), "q" - выход: ')
        if album_id == '1':
            get_vk('profile')
            break
        elif album_id == '2':
            get_vk('wall')
            break
        elif album_id == '3':
            get_vk('saved')
            break
        elif album_id == 'q':
            break
        else:
            print('Вы ошиблись при вводе...')

# Экземляры классов для работы с "одноклассники"
def get_ok():
    # Здесь введите id пользователя одноклассники, фото которого надо скопировать, access_token - токен для доступа,
    # session_secret_key - секретный ключ для доступа, application_key - ключ приложения
    Ok_1 = OkUser(id_user='567303295070', access_token='', session_secret_key='', application_key='')
    list_files = List_Files(Ok_1.get_file())

    file_jason_write = File_Json_Write(list_files.get_file_json(), 'Archiv_Ok')
    file_jason_write.get_file_json()

    yd_upload = File_Upload_Ydisk(list_files.get_file_url())
    return yd_upload.upload()

# Выбор соцсети, откуда будут загружаться фото
def main():
    while True:
        sel = input(f'Выберите соцсеть, из которой хотите сохранить фото '
                    f'(вконтакте - "1", одноклассники - "2", "q" - выход): ')
        if sel == '1':
            sel_album_vk()
            break
        elif sel == '2':
            get_ok()
            break
        elif sel == 'q':
            break
        else:
            print('Вы ошиблись при вводе...')


main()
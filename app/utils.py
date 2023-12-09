import re
import os
import requests
from pytube import YouTube
import requests
import psycopg2
import datetime

class Convert: #Проверка ссылки - ЮТЮБ ИНСТА

    def __init__(self) -> None:
        pass

    def which_link(self, message):
        if len(re.findall('youtu.+', str(message))) > 0:
            return 1
        if len(re.findall('https://www.instagram.com/.+', str(message))) > 0:
            return 2
        else:
            return 0


class DLYouTube:
    MAX_FILESIZE = 50000000 
    path = None 
    url = None 
    vid = None 
    vid_resolution = None 
    available_resolutions = set() 
    file_name = None 
    divide_into_count = None
    compressed_video_name = None

    def __init__(self, url) -> None: 
        try: 
            os.mkdir('./data') 
        except:
            pass
        self.path = os.path.abspath('./data')
        self.url = url
        self.vid = YouTube(self.url)
        self.file_name = fr'{self.vid.title.split()[0]}_{self.vid_resolution}.mp4' 
        self.all_resolutions() 
        
    def set_res(self, res = '720p'): 
        self.vid_resolution = res
        self.file_name = fr'{self.vid.title.split()[0]}_{self.vid_resolution}.mp4'
        self.divide_into_count = self.vid.streams.get_by_resolution(self.vid_resolution).filesize//self.MAX_FILESIZE + 2

    def getpath(self): 
        return self.path
    
    def get_filename(self):
        return self.file_name
    
    def all_resolutions(self):
        for v in self.vid.streams.filter(file_extension='mp4'):
            try:
                self.available_resolutions.append(re.findall(".+vcodec.+acodec.+", str(v))[0])
            except:
                break
            self.available_resolutions = sorted((self.available_resolutions))
        pass

    def is_big_filesize(self):
        return self.vid.streams.get_by_resolution(self.vid_resolution).filesize > self.MAX_FILESIZE 

    def is_big_audio_file_size(self):
        return self.vid.streams.filter(only_audio=True)[0].filesize > self.MAX_FILESIZE

    def video_file_size(self):
        return self.vid.streams.get_by_resolution(self.vid_resolution).filesize
    
    def audio_file_size(self):
        return self.vid.streams.filter(only_audio=True)[0].filesize
    

    def download_audio_only(self):
        self.file_name = fr'{self.vid.title.split()[0]}.mp3'
        print('download method start')
        print(self.vid.streams.filter(only_audio=True))
        self.path = self.path + '/audios'
        self.vid.streams.get_by_resolution(self.vid_resolution).download(self.path, self.file_name)
        print('download method end')
        pass

    def download_video(self):
        print('download method start')
        self.file_name = fr'{self.vid.title.split()[0]}_{self.vid_resolution}.mp4'
        print("filename = ", self.file_name)
        self.path = self.path + '/videos'
        self.vid.streams.get_by_resolution(self.vid_resolution).download(self.path, self.file_name)
        print("Download method end")

# dl = DLYouTube('https://youtu.be/twrckCZpPMA?si=wJbNR26qBePxX2hq')
# dl.download_video()

class DLIGReels: #Допиливаю класс для скачки рилзов из инсты - Подключается по апи, работает недолго
    querystring = None
    url = None
    headers = None
    host = None

    def __init__(self, url) -> None:
        self.url = url
        self.headers = {
            "X-RapidAPI-Key": "67cf633d0dmsh639553817e876f4p18e894jsne7cdd8d7a86b",
            "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com"
        }
        self.querystring = {"url":f"{str(self.url)}"}
        self.host = "https://instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com/"
        pass

    def define_headers(self):
        self.headers = {
	"X-RapidAPI-Key": "67cf633d0dmsh639553817e876f4p18e894jsne7cdd8d7a86b",
	"X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com"
}
            
    def get_download_linkIG(self):
        response = requests.get(self.host, headers=self.headers, params=self.querystring)
        return response.json()[0]

class DataBase:
    connection = None
    cursor = None
    add_data_query = None

    def __init__(self) -> None:
        try:
            self.connection = psycopg2.connect(dbname='nmfy', user='postgres', 
                            password='1405', host='localhost')
            self.cursor = self.connection.cursor()
            print('all good')
            print("Информация о сервере PostgreSQL")
            print(self.connection.get_dsn_parameters(), "\n")
            # self.create_table()
        except Exception as e:
            print(e)
        pass
    
    def create_table(self):
        try:
            create_table_query = '''CREATE TABLE userdata
                            (date_time_of_request TIMESTAMP, 
                            chat_id VARCHAR, 
                            request_url VARCHAR,
                            video_or_audio VARCHAR,
                            file_size VARCHAR, 
                            status VARCHAR, 
                            time_spent VARCHAR
                            ); '''
            self.cursor.execute(create_table_query)
            self.connection.commit()
        except:
            print("The table is probably already created!")
        pass

    def add_userdata(self, date_time_of_request, chat_id, request_url, video_or_audio, file_size, status, time_spent):
        try:
            self.add_data_query = f"""INSERT INTO userdata(
                date_time_of_request,
                chat_id,
                request_url,
                video_or_audio,
                file_size,
                status,
                time_spent
                )
                VALUES('{date_time_of_request}',
                '{chat_id}',
                '{request_url}',
                '{video_or_audio}',
                '{file_size}',
                '{status}',
                '{time_spent}'
                );"""
            self.cursor.execute(self.add_data_query)
            self.connection.commit()
            print("User успешно добавлен в таблицу!")
        except Exception as e:
            print(e)
    
    def select_all(self):
        try:
            select_all_qeury = "SELECT * FROM userdata;"
            self.cursor.execute(select_all_qeury)
            self.connection.commit()
        except Exception as e:
            print(e)

    def close_conection(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Соединение с PostgreSQL закрыто")

    def drop_table(self):
        try:
            droptable_query = "DROP TABLE userdata;"
            self.cursor.execute(droptable_query)
            self.connection.commit()
        except Exception as e:
            print(e)

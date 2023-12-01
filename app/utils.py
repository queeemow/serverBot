import re
import os
import requests
import ffmpeg
from pytube import YouTube
# from instascrape import Reel
# import instaloader
import requests
# import time
from telethon import TelegramClient

# os.environ["IMAGEIO_FFMPEG_EXE"] = "./ffmpeg/ffmpeg"
# from moviepy.editor import VideoFileClip

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
    MAX_FILESIZE = 50000000 #Максимальный размер файла в байтах(50мб) - ограничение телеграма
    path = None #Путь до папки с загруженными выидео
    url = None #Ссылка на видео
    vid = None #Объект экземпляр класса Ютюб
    vid_resolution = None #Выбранное Разрешение видоса
    available_resolutions = set() #Все доступные разрешения видоса
    file_name = None #Название файла без пути
    divide_into_count = None
    compressed_video_name = None

    def __init__(self, url) -> None: # При создании объекта, передается введенная в чат пользователем ссылка на видео в качестве url
        try: #Создаю папку если ее нет во внешней директории с именем видеос
            os.mkdir('./data/videos') 
        except:
            pass
        self.path = os.path.abspath('./data/videos')
        self.url = url
        self.vid = YouTube(self.url)
        self.file_name = fr'{self.vid.title.split()[0]}_{self.vid_resolution}.mp4' #Имя файла - первое слово из заголовка(тайтл)_разрешение видео_.мп4
        self.all_resolutions() #Автоматический вызов функции, определяющей возможные разрешения для видео при создании экземпляра класса
        pass
        
    def set_res(self, res = '720p'): #Если разрешение не указано, то по дефолту устанавливается 720п
        self.vid_resolution = res
        self.file_name = fr'{self.vid.title.split()[0]}_{self.vid_resolution}.mp4'
        self.divide_into_count = self.vid.streams.get_by_resolution(self.vid_resolution).filesize//self.MAX_FILESIZE + 2

    def getpath(self): #Инкапсуляция
        return self.path
    
    def get_filename(self):#Инкапсуляция
        return self.file_name
    
    def all_resolutions(self):#На будущее, когда добавлю возможность выбирать не только 360 или 720п
        for v in self.vid.streams.filter(file_extension='mp4'):
            try:
                self.available_resolutions.append(re.findall(".+vcodec.+acodec.+", str(v))[0])
            except:
                break
            self.available_resolutions = sorted((self.available_resolutions))
        pass

    def is_big_filesize(self):#Проверка является ли файл большим(превышает ли лимит телеграма и надо ли его делить на маленькие)
        return self.vid.streams.get_by_resolution(self.vid_resolution).filesize > self.MAX_FILESIZE 

    

    def download_audio_only(self):

        pass

    def compress_video(self):
        self.compressed_video_name = self.path+'/'+self.file_name[:-4] + '_COMPRESSED' + '.mp4'
        # Reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
        min_audio_bitrate = 32000
        max_audio_bitrate = 256000
        print("compressing....")
        probe = ffmpeg.probe(self.path+'/'+self.file_name)
        # Video duration, in s.
        duration = float(probe['format']['duration'])
        print(duration)
        # Audio bitrate, in bps.
        audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
        # Target total bitrate, in bps.
        target_total_bitrate = (self.MAX_FILESIZE * 8) / (1.073741824 * duration)

        # Target audio bitrate, in bps
        if 10 * audio_bitrate > target_total_bitrate:
            audio_bitrate = target_total_bitrate / 10
            if audio_bitrate < min_audio_bitrate < target_total_bitrate:
                audio_bitrate = min_audio_bitrate
            elif audio_bitrate > max_audio_bitrate:
                audio_bitrate = max_audio_bitrate
        # Target video bitrate, in bps.
        video_bitrate = target_total_bitrate - audio_bitrate

        i = ffmpeg.input(self.path+'/'+self.file_name)
        ffmpeg.output(i, os.devnull, passlogfile = './data/videos/ffmpeg2pass',
                    **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                    ).overwrite_output().run()
        
        ffmpeg.output(i, self.compressed_video_name, passlogfile = './data/videos/ffmpeg2pass',
                    **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                    ).overwrite_output().run()
    # def get_divide_into_count(self):
    #     return self.divide_into_count


    # def video_split(self): #Деление файла на маленькие
    #     print('divide into count = ', self.divide_into_count)
    #     print("SIZE OF FILE = ", self.vid.streams.get_by_resolution(self.vid_resolution).filesize)
    #     print('mocha1')
    #     current_duration = VideoFileClip(self.path+'/'+self.file_name).duration
    #     print('gavno2')
    #     single_duration = current_duration/self.divide_into_count
    #     i = 0
    #     while current_duration >= single_duration:
    #         clip = VideoFileClip(self.path+'/'+self.file_name).subclip(current_duration-single_duration, current_duration)
    #         current_duration = current_duration - single_duration
    #         self.current_video.append(f"{self.file_name[:-4]}_{self.divide_into_count}.mp4") #Добавляю в список текущий файл, так как первым будет файл с конца видео
    #         print(self.current_video[i])
    #         clip.to_videofile(self.current_video[i], codec="libx264", temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')
    #         os.rename('/Users/glebkuimov/hw1/python/'+self.current_video[i], self.path + '/' + self.current_video[i]) #Переношу микровидос получившийся в папку со всеми видео
    #         print(os.path.getsize(f'{self.path}/{self.current_video[i]}')/1000000)
    #         self.divide_into_count = self.divide_into_count - 1
    #         i = i + 1
    #     self.current_video.sort() #Сортирую в порядке возрастания, чтобы в мейне в цикле их в правильном порядке отослать пользователю
    #     pass

    def download_video(self): #Скачать видос на компьютр(на сервер) 
        print('download method start')
        self.file_name = fr'{self.vid.title.split()[0]}_{self.vid_resolution}.mp4'
        print("filename = ", self.file_name)
        self.vid.streams.get_by_resolution(self.vid_resolution).download(self.path, self.file_name)
        print("Download method end")
        pass

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


# def compress_video(video_full_path, output_file_name, target_size):
#     # Reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
#     min_audio_bitrate = 32000
#     max_audio_bitrate = 256000
#     print("")
#     probe = ffmpeg.probe(video_full_path)
#     # Video duration, in s.
#     duration = float(probe['format']['duration'])
#     # Audio bitrate, in bps.
#     audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
#     # Target total bitrate, in bps.
#     target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

#     # Target audio bitrate, in bps
#     if 10 * audio_bitrate > target_total_bitrate:
#         audio_bitrate = target_total_bitrate / 10
#         if audio_bitrate < min_audio_bitrate < target_total_bitrate:
#             audio_bitrate = min_audio_bitrate
#         elif audio_bitrate > max_audio_bitrate:
#             audio_bitrate = max_audio_bitrate
#     # Target video bitrate, in bps.
#     video_bitrate = target_total_bitrate - audio_bitrate

#     i = ffmpeg.input(video_full_path)
#     ffmpeg.output(i, os.devnull,
#                   **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
#                   ).overwrite_output().run()
#     ffmpeg.output(i, output_file_name,
#                   **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
#                   ).overwrite_output().run()

# Compress input.mp4 to 50MB and save as output.mp4
# yt = DLYouTube("https://youtu.be/Wdjh81uH6FU?si=tgkPHWKJz4XiBoXF")
# yt.download()
# yt.compress_video()



# ig = DLIGReels('')
# print(ig.get_download_linkIG())

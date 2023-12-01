import os
import telebot
from config import BOT_TOKEN
import config
from utils import Convert, DLYouTube, DLIGReels
from telebot import types

class DownloadBot:
    bot = None
    YT = None
    IG = None
    ENJOY = None
    WHICH_LINK = None
    CON = None
    VID_OR_AUD_MARKUP = None
    RES_MARKUP = None
    message = None

    def __init__(self) -> None:
        print('test')
        self.bot = telebot.TeleBot(BOT_TOKEN) #Передаю объекту токен бота из конфига
        self.con = Convert()
        @self.bot.message_handler(content_types=["text"])
        def get_text_message_handler(message):
            return self.get_text_messages(message)
        
    def get_text_messages(self, message): #Каждый раз при получения нового сообщения срабатывает декоратор - работает асинхронно
        print("message = ", message.text)

        self.WHICH_LINK = self.con.which_link(message) #Проверка корректности ссылки
        print(self.WHICH_LINK)
        match self.WHICH_LINK:
            case 1: #Если ссылка правильная то работаем
                self.VID_OR_AUD_MARKUP = types.ReplyKeyboardMarkup(resize_keyboard=True) #кнопки для выбора 
                video = types.KeyboardButton('video')
                audio = types.KeyboardButton('audio')
                self.VID_OR_AUD_MARKUP.add(video, audio)
                self.bot.send_message(message.chat.id, text="Would you like to get video or audio only?".format(message.from_user), reply_markup=self.VID_OR_AUD_MARKUP)
                self.YT = DLYouTube(str(message.text))
                match message.text:
                    case 'video':
                        # res240 = types.KeyboardButton("240p")
                        res360 = types.KeyboardButton('360p')
                        # res480 = types.KeyboardButton('480p')
                        res720 = types.KeyboardButton('720p') #Кнопки именно такие, так как формат видео позволяет скачать видео со звуком только в 360п или 720п
                        self.RES_MARKUP.add(res360, res720)
                        self.bot.send_message(message.chat.id, text="Choose a resolution via menu".format(message.from_user), reply_markup=self.RES_MARKUP)
                        self.bot.register_next_step_handler(message, self.choose_YT_resolution) #Бессмысленный мув
                    case 'audio':
                        'ВСТАВИТЬ МЕТОД ВЫТЯГИВАНИЯ АУДИО'
                        self.bot.send_message(message.chat.id, text="PASHOL")
                    case _:
                        self.bot.send_message(message.chat.id, text="Please, use the menu to choose an option")
            case 2:
                self.IG = DLIGReels(str(message.text))
                self.bot.send_message(message.from_user.id, 'Getting download link, Please stand by...')
                self.sendIg(message)
            case 0: #Если ссылка не на ютюб или инст то нахрен, пусть снова пробует
                self.bot.send_message(message.from_user.id, "Send me a link to a YouTube or Instagram video e.g.: https://youtu.be/IUicoBcRiCo?si=l8_zRX8ix8dKy0ai СТЕПА НЕ ЛОХ")
        # self.bot.infinity_polling(timeout=10, long_polling_timeout = 50)

    def choose_YT_resolution(self, message): #Бессмысленный мув
        self.downloadYT(message) #Бессмысленный мув

    def downloadYT(self, message): #Скачать видос
        try:
            self.YT.set_res(message.text) #В зависимости от выбранного разрешения весит видос по разному
            if self.YT.is_big_filesize():  #Если весит много то надо скачать, разбить и отправить по частям
                self.bot.send_message(message.from_user.id, f'The video weights more than 50MB, which is maximum allowed document size limit. The video will be compressed')
                self.bot.send_message(message.from_user.id, "Downloading, Please stand by...")
                self.YT.download_video()
                self.bot.send_message(message.from_user.id, "Downloading complete, compressing...")
                self.YT.compress_video()
                self.sendYT(message, True)
            else:
                self.bot.send_message(message.from_user.id, "Downloading, Please stand by...") #Если весит немного то надо скачать и отправить
                self.YT.download_video()
                self.sendYT(message)
        except Exception as e:
            self.bot.send_message(message.from_user.id, "Something went wrong! Try again with the correct download options")
            self.get_text_messages(message)
            print(str(e))

    def sendYT(self, message, is_big = False): #Отправить видео
        enjoy = True #Если все отправилось хорошо то написать пользователю что все гуд
        if is_big: #Если большой видос, который разбит на маленькие
            print("______SEND BIG VIDEO_______", self.YT.compressed_video_name)
            print("current video =    ", self.YT.compressed_video_name)
            f = open(self.YT.compressed_video_name ,"rb")
            print("ok - big")
            try:
                self.bot.send_document(message.chat.id,f, timeout=200)
                os.remove(self.YT.compressed_video_name) #Сразу удаляю маленький видос после отправки
            except Exception as e:
                # SHOULD NEVER BE SHOWN TO USER
                self.bot.send_message(message.from_user.id, "The video size exceeds 50MB limit, please FUCK OFF BLUD") 
                print(str(e))
                # Если не отправился тоже удаляю
                os.remove(self.YT.compressed_video_name) 
                enjoy = False #Если не отправился, пишу об этом пользователю и не вывожу что все хорошо
            os.remove(self.YT.getpath() + '/' + self.YT.get_filename())#В любом случае удаляю основной видос
            if enjoy: #Все хорошо - пишу пользователю
                self.bot.send_message(message.from_user.id, "Enjoy!")
            
        else: #Если видео маленькое
            f = open(self.YT.getpath() + '/' + self.YT.get_filename() ,"rb")
            print("ok - small")
            try:
                self.bot.send_document(message.chat.id,f, timeout=200)
                os.remove(self.YT.getpath() + '/' + self.YT.get_filename())
                self.bot.send_message(message.from_user.id, "Enjoy!!")
            except Exception as e:
                self.bot.send_message(message.from_user.id, "The video size exceeds 50MB limit, please FUCK OFF BLUD") #SHOULD NEVER BE SHOWN TO USER
                print(str(e))
                os.remove(self.YT.getpath() + '/' + self.YT.get_filename())

    def sendIg(self, message):
        print('SUKA')
        try:
            download_link = self.IG.get_download_linkIG()
            print("goot")
            self.bot.send_message(message.from_user.id, "Your instagram download link is ready: ")
            self.bot.send_message(message.from_user.id, download_link)
            self.bot.send_message(message.from_user.id, "Enjoy!!")
        except Exception as e:
            print(e)
            self.bot.send_message(message.from_user.id, "Something went wrong! There might be exceeded limit for free triel of instadownloader api sorry im poor")

    def start_pooling(self):
        self.bot.infinity_polling(timeout=10, long_polling_timeout = 50)
    # Зацикленное получение сообщений от пользователя 

if __name__ == '__main__':
    dl = DownloadBot()
    dl.start_pooling()

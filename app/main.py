import os
import telebot
from utils import Convert, DLYouTube, DLIGReels, DataBase
from telebot import types
from pyrogram import Client
from config import CLIENTS, SENDING_QUEUE
import asyncio
import datetime
from dotenv.main import load_dotenv
load_dotenv()

BOT_TOKEN = os.environ['BOT_TOKEN']
API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']

print(type(CLIENTS))
print(BOT_TOKEN)

class DownloadBot:
    bot = None
    YT = {}
    IG = {}
    ENJOY = None
    WHICH_LINK = None
    CON = None
    VID_OR_AUD_MARKUP = None
    RES_MARKUP = None
    message = None
    db = None
    user_data = {}


    def __init__(self) -> None:
        print('test')
        self.bot = telebot.TeleBot(BOT_TOKEN) 
        self.con = Convert()
        @self.bot.message_handler(content_types=["text"])
        def get_text_message_handler(message):
            return self.get_text_messages(message)

    def get_text_messages(self, message): 
        print("message = ", message.text)

        self.WHICH_LINK = self.con.which_link(message) 
        print(self.WHICH_LINK)
        match self.WHICH_LINK:
            case 1:
                self.VID_OR_AUD_MARKUP = types.ReplyKeyboardMarkup(resize_keyboard=True) 
                video = types.KeyboardButton('video')
                audio = types.KeyboardButton('audio')
                self.VID_OR_AUD_MARKUP.add(video, audio)
                self.YT[message.chat.id] = DLYouTube(str(message.text))
                self.user_data[message.chat.id] = {}
                self.user_data[message.chat.id]['date_time_of_request'] = '{}'.format(datetime.datetime.now())
                self.user_data[message.chat.id]['chat_id'] = str(message.chat.id)
                self.user_data[message.chat.id]['request_url'] = str(message.text)
                self.user_data[message.chat.id]['time_spent'] = datetime.datetime.now()
                self.bot.send_message(message.chat.id, text="Would you like to get video or audio only?".format(message.from_user), reply_markup=self.VID_OR_AUD_MARKUP)
                self.bot.register_next_step_handler(message, self.is_video_or_audio)
            case 2:
                self.IG[message.chat.id] = DLIGReels(str(message.text))
                self.bot.send_message(message.from_user.id, 'Getting download link, Please stand by...')
                self.sendIg(message)
            case 0: 
                self.bot.send_message(message.from_user.id, "Send me a link to a YouTube or Instagram video e.g.: https://youtu.be/IUicoBcRiCo?si=l8_zRX8ix8dKy0ai СТЕПА НЕ ЛОХ")

    def is_video_or_audio(self, message):
        print("DEFINING AUDIO OR VIDEO")
        match message.text:
            case 'video':
                self.user_data[message.chat.id]['video_or_audio'] = 'video'
                print("SENT VIDEO")
                self.RES_MARKUP = types.ReplyKeyboardMarkup(resize_keyboard=True)
                # res240 = types.KeyboardButton("240p")
                res360 = types.KeyboardButton('360p')
                # res480 = types.KeyboardButton('480p')
                res720 = types.KeyboardButton('720p') 
                self.RES_MARKUP.add(res360, res720)
                self.bot.send_message(message.chat.id, text="Choose a resolution via menu".format(message.from_user), reply_markup=self.RES_MARKUP)
                self.bot.register_next_step_handler(message, self.choose_YT_resolution)
            case 'audio':
                self.user_data[message.chat.id]['video_or_audio'] = 'audio'
                print("SENT AUDIO")
                self.download_audio(message)
            case _:
                self.bot.send_message(message.chat.id, text="Please, use the menu to choose an option")

    def choose_YT_resolution(self, message): 
        self.downloadYT(message) 

    def download_audio(self, message):
        print("DL AUDIO")
        is_big = self.YT[message.chat.id].is_big_audio_file_size()
        self.user_data[message.chat.id]['file_size'] = str(self.YT[message.chat.id].audio_file_size())
        if is_big:
            print("YES THE FILE IS BIG, IT WEIGHTS  ", self.YT[message.chat.id].is_big_audio_file_size())
            self.bot.send_message(message.from_user.id, "Downloading, Please stand by...")
            self.YT[message.chat.id].download_audio_only()
            self.sendYT(message, True)
        else:
            try:
                self.bot.send_message(message.from_user.id, "Downloading, Please stand by...")
                self.YT[message.chat.id].download_audio_only()
                self.sendYT(message, False)
            except Exception as e:
                self.bot.send_message(message.from_user.id, "Something went wrong! Try again with the correct download options")
                self.get_text_messages(message)
                print(str(e))
            pass

    def downloadYT(self, message): 
        self.user_data[message.chat.id]['file_size'] = str(self.YT[message.chat.id].video_file_size())
        try:
            self.YT[message.chat.id].set_res(message.text) 
            if self.YT[message.chat.id].is_big_filesize():  
                self.bot.send_message(message.from_user.id, "Downloading, Please stand by...") 
                self.YT[message.chat.id].download_video()
                self.sendYT(message, is_big=True)
            else:
                self.bot.send_message(message.from_user.id, "Downloading, Please stand by...") 
                self.YT[message.chat.id].download_video()
                self.sendYT(message)
        except Exception as e:
            self.bot.send_message(message.from_user.id, "Something went wrong! Try again with the correct download options")
            self.get_text_messages(message)
            print(str(e))

    def sendYT(self, message, is_big = False): 
        print("SENDING!!!!")
        if is_big:
            SENDING_QUEUE.append(message.chat.id)
            print('\n\nSESSION NUMBER = ', len(SENDING_QUEUE), "\n\n")
            try:
                self.user_data[message.chat.id]['status'] = 'done'
                if self.YT[message.chat.id].get_filename()[-1] == '4':
                    file_id = asyncio.run(self.send_large_video(message, i=len(SENDING_QUEUE))).video.file_id
                    self.bot.send_video(message.chat.id, video = file_id)
                    self.bot.send_message(message.from_user.id, "Enjoy!!")
                    os.remove(self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename())
                    SENDING_QUEUE.pop()
                else:
                    file_id = asyncio.run(self.send_large_audio(message, i=len(SENDING_QUEUE))).audio.file_id
                    self.bot.send_audio(message.chat.id, audio = file_id)
                    self.bot.send_message(message.from_user.id, "Enjoy!!")
                    os.remove(self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename())
                    SENDING_QUEUE.pop()
            except Exception as e:
                print(e)
                self.bot.send_message(message.from_user.id, "The file weights more than 1,5GB!!!!!!!!!!!!!")
                self.get_text_messages(message)
                self.user_data[message.chat.id]['status'] = 'error'
        else: 
            print("preok - small   ", self.YT[message.chat.id].getpath(), "    ", self.YT[message.chat.id].get_filename())
            f = open(self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename() ,"rb")
            print(self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename(), "<-------small filename")
            print("ok - small")
            try:
                self.user_data[message.chat.id]['status'] = 'done'
                if self.YT[message.chat.id].get_filename()[-1] == '4':
                    self.bot.send_video(message.chat.id,f, timeout=200)
                    os.remove(self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename())
                    self.bot.send_message(message.from_user.id, "Enjoy!!")
                else:
                    print("START OF SMALL AUDIO SENDNG")
                    SENDING_QUEUE.append(message.chat.id)
                    file_id = asyncio.run(self.send_large_audio(message, i=len(SENDING_QUEUE))).audio.file_id
                    self.bot.send_audio(message.chat.id, audio = file_id)
                    self.bot.send_message(message.from_user.id, "Enjoy!!")
                    os.remove(self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename())
                    SENDING_QUEUE.pop()
            except Exception as e:
                self.bot.send_message(message.from_user.id, "Something went wrong!") 
                print(str(e))
                os.remove(self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename())
                self.user_data[message.chat.id]['status'] = 'error'
                self.get_text_messages(message)
        self.user_data[message.chat.id]['time_spent'] = (datetime.datetime.now() - self.user_data[message.chat.id]['time_spent']).total_seconds()
        self.add_user_data(message)

    def sendIg(self, message):
        print('SUKA')
        try:
            download_link = self.IG[message.chat.id].get_download_linkIG()
            print("goot")
            self.bot.send_message(message.from_user.id, "Your instagram download link is ready: ")
            self.bot.send_message(message.from_user.id, download_link)
            self.bot.send_message(message.from_user.id, "Enjoy!!")
        except Exception as e:
            print(e)
            self.bot.send_message(message.from_user.id, "Something went wrong! There might be exceeded limit for free triel of instadownloader api sorry im poor")

    async def send_large_video(self, message, i):
        async with Client(CLIENTS[i], api_id=API_ID, api_hash=API_HASH) as app:
            return await app.send_video("@NMFY_BOT", self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename())
    
    async def send_large_audio(self, message, i):
        async with Client(CLIENTS[i], api_id=API_ID, api_hash=API_HASH) as app:
            return await app.send_audio("@NMFY_BOT", self.YT[message.chat.id].getpath() + '/' + self.YT[message.chat.id].get_filename())
    
    def add_user_data(self, message):
        self.db = DataBase()
        print("\n\n\n", self.user_data, "\n\n\n")
        self.db.add_userdata(date_time_of_request = self.user_data[message.chat.id]['date_time_of_request'], 
                             chat_id = self.user_data[message.chat.id]['chat_id'], 
                             request_url = self.user_data[message.chat.id]['request_url'], 
                             video_or_audio = self.user_data[message.chat.id]['video_or_audio'], 
                             file_size = self.user_data[message.chat.id]['file_size'], 
                             status = self.user_data[message.chat.id]['status'], 
                             time_spent = self.user_data[message.chat.id]['time_spent'])
        self.db.close_conection()

    def start_pooling(self):
        self.bot.infinity_polling(timeout=10, long_polling_timeout = 50)   

if __name__ == '__main__':
    dl = DownloadBot()
    dl.start_pooling()
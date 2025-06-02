import pandas as pd
import windrose
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import telebot

token = open("token.txt").readline()
bot = telebot.TeleBot(token)
userids = {}

def get_dt(dt):
    """получаем направления(слова) и скорости"""
    return (dt['DD'], dt['Ff'])

def get_winddegree(direction: str):
    """получаем градусы из направлений"""
    if type(direction) == float:
        return np.nan
    wind_direction_to_degrees = {
        "штиль": np.nan,
        "переменное": np.nan,
        "Севера": 0.0,
        "Северо-северо-востока": 22.5,
        "Северо-востока": 45.0,
        "Востоко-северо-востока": 67.5,
        "Востока": 90.0,
        "Востоко-юго-востока": 112.5,
        "Юго-востока": 135.0,
        "Юго-юго-востока": 157.5,
        "Юга": 180.0,
        "Юго-юго-запада": 202.5,
        "Юго-запада": 225.0,
        "Западо-юго-запада": 247.5,
        "Запада": 270.0,
        "Западо-северо-запада": 292.5,
        "Северо-запада": 315.0,
        "Северо-северо-запада": 337.5,
    }
    direction = direction.casefold()
    for key, val in wind_direction_to_degrees.items():
        if key.casefold() in direction:
            return val
    raise ValueError(f"unknown direction: {direction}")

def make_windrose(dt: pd.DataFrame):
    """делаем розу ветров"""
    calm_days = dt['DD'].tolist().count('Штиль, безветрие')
    (dd_dt, ff_dt) = get_dt(dt)
    angles = [get_winddegree(x) for x in dd_dt]


    ax = windrose.WindroseAxes.from_ax()

    calm_percent = calm_days / len(ff_dt) * 100
    arrs = dt.columns[0].split()
    arrs.pop(0)
    arrs.pop(0)
    name = " ".join(arrs)
    ax.set_title(f"Роза ветров {name}\nШтиль: {calm_percent:.1f}%", pad=20, fontsize=8)

    ax.bar(angles, ff_dt, normed=True, opening=0.8,edgecolor='white', cmap=plt.cm.viridis)
    ax.set_xticklabels(['С', 'СВ', 'В', 'ЮВ', 'Ю', 'ЮЗ', 'З', 'СЗ'])
    ax.set_legend(title='Скорость ветра (м/с)', loc='lower left')

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf


@bot.message_handler(commands=['start', 'help'])
def start(msg):
    """приветственное сообщение"""
    bot.send_message(msg.from_user.id, "Приветствую!"
                                       "\nЭтот бот позволяет создать розу ветров любого(в теории) места."
                                       "\nДля создания графика необходимо скинуть .csv документ в кодировке utf-8"
                                       "\nС сайта https://rp5.ru"
                                       "\nДля старта работы достаточно скинуть файл и следовать инструкциям.")


@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    """реакции на документ"""
    try:
        if not msg.document.file_name.endswith('.csv'):
            bot.reply_to(msg, 'Отправьте файл в формате CSV.')
            return
        file_info = bot.get_file(msg.document.file_id)
        file = bot.download_file(file_info.file_path)

        try:
            df = pd.read_csv(BytesIO(file), encoding='utf-8', sep=';',skiprows=6, skip_blank_lines=True, on_bad_lines='skip',index_col=False)
            bot.reply_to(msg,f"Найдено {len(df)} записей!")
            userids[msg.chat.id] = df
            bot.send_message(msg.chat.id, "Теперь можете строить график!\nНапишите для этого /windrose")
        except Exception as e:
            bot.reply_to(msg, f"Ошибка чтения файла: {str(e)}")
    except Exception as e:
        bot.reply_to(msg, f"Ошибка обработки файла: {str(e)}")

@bot.message_handler(commands=['windrose'])
def create_windrose(msg):
    """процесс создания графика"""
    try:
        if msg.chat.id not in userids:
            bot.reply_to(msg, "Нужен CSV для розы!")
            return

        df = userids[msg.chat.id]
        required_columns = ['Ff', 'DD']
        if not all(col in df.columns for col in required_columns):
            bot.reply_to(msg, f"В файле должны быть колонки: {', '.join(required_columns)}")
            return
        bot.send_chat_action(msg.chat.id, 'upload_photo')
        buf = make_windrose(df)
        bot.send_photo(msg.chat.id, buf, caption="Результат")
        buf.close()
    except Exception as e:
        bot.reply_to(msg, f"Ошибка при создании: {str(e)}")

if __name__ == '__main__':
    print('-------------бот начал работу--------------')
    bot.infinity_polling()

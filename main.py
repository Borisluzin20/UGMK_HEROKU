import mysql.connector
from mysql.connector import Error
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext import Updater, ConversationHandler
import requests

# создание клавиатуры
reply_keyboard = [['/start']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def create_connection(host_name, user_name, user_password, db_name):  # функции внешнего подключения к бд
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def get_map_params(toponym_to_find):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym_to_find,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if not response:
        # обработка ошибочной ситуации
        pass

    # Преобразуем ответ в json-объект
    json_response = response.json()
    # Получаем первый топоним из ответа геокодера.
    toponym = json_response["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]

    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    # Долгота и широта:
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

    lowercorner = toponym["boundedBy"]["Envelope"]["lowerCorner"].split()
    uppercorner = toponym["boundedBy"]["Envelope"]["upperCorner"].split()

    delta_x = str(float(uppercorner[0]) - float(lowercorner[0]))

    # Собираем параметры для запроса к StaticMapsAPI:
    return {
        "ll": ",".join([toponym_longitude, toponym_lattitude]),
        "spn": ",".join([delta_x, delta_x]),
        "l": "map"
    }


def main():
    def stop():
        pass

    updater = Updater('1658734136:AAFzFOylGxk7296zs12EKT4dLMEgg8ey2Is', use_context=True)  # Ключ получен у @BotFather
    dp = updater.dispatcher

    name = ''
    trouble = ''
    problem = ''
    lst = []

    def start(update, context):  # приветсвенное сообщение
        update.message.reply_text(
            "Добрый день, вы в боте для отправки отчетов о нарушениях!\n"
            "Напишите ваше ФИО")
        return 1

    def first_response(update, context):  # первое событие сценария

        global name
        name = update.message.text
        if len([i for i in name if 1040 <= ord(i) <= 1103 or ord(i) == 1005 or ord(i) == 1025 or ord(i) == 32]) != len(
                name):
            update.message.reply_text(
                'При вводе ФИО используйте только Кириллицу\n'
                'Повторите ввод вашего ФИО')

        else:
            lst.append(name)
            print(name)
            update.message.reply_text("Напишите место возникновения проблемы(город, цех)")
            return 2

    def second_response(update, context):  # второе событие сценария
        global problem
        problem = update.message.text
        if problem.count(',') == 0:
            update.message.reply_text('Введите город и цех через запятую')
        else:
            lst.append(problem)
            print(problem)

            update.message.reply_text(
                f"Благодрим вас за вашу бдительность, {str(lst[0])}\n"
                "Напишите номер вашей проблемы, руководствуясь списком:\n"
                "a. Обнаружено несоответствие фактического состояния производства работ \n'"
                "требованиям безопасности и охраны труда.\n"
                "b. Выявлено нарушение условий отключения технических устройств.\n"
                "c. Характер и объёмы работ изменены в такой степени,что требуется изменение схемы отключения \n"
                "ТУ и порядка выполнения работ.\n"
                "d. Появилась угроза жизни и здоровью работников.\n"
                "e. Подан ложный аварийный сигнал.\n"
                "f. Работы на высоте 1,8 метра и более без применения страховочной привязи.\n"
                "g. Работы в колодцах, котлованах и тоннелях без применения средств индивидуальной защиты (СИЗ),\n"
                " ограждений, в количестве менее трех человек.\n"
                "h. Работы в близи работающего оборудования при отсутствии ограждения.\n"
                "i. Работы в действующих электроустановках без применения СИЗ.\n"
                "j. Нарушение требований проведения огневых работ.\n"
                "k. Нарушение правил эксплуатации газобаллонного оборудования.\n"
                "l. Проведение погрузочно-разгрузочных и монтажных работ с применением неисправных\n"
                " грузозахватных приспособлений и механизмов.".format(
                    **locals()))
            return 3

    def third_response(update, context):  # третье событие сценария

        global trouble
        trouble = update.message.text
        if trouble not in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']:
            update.message.reply_text(
                'Повторите ввод проблемы\n'
                'Используйте строчные английские буквы')
        else:
            lst.append(trouble)
            print(lst)
            update.message.reply_text(f"{lst[0]}, прикрепите фотоотчет с места нарушения")
            return 4

    def photo(update, context):  # четвертое обытие сценария и загрузка фото
        photo_file = update.message.photo[-1].get_file()
        # создание подключения к базе данных
        connection = create_connection("141.8.192.151", "f0514491_ugmkbase", "UGMKbase", "f0514491_ugmkbase")
        create_users = f"""
                    INSERT INTO
                      `reports` (`reporterName`, `reportToName`, `typeProblem`, `reportText`, `typeFile`)
                    VALUES
                      ('{str(lst[0])}', '{str(lst[1])}', '{str(lst[2])}', '', '.jpg');
                    """
        execute_query(connection, create_users)

        cursor = connection.cursor()  # узнаю id последней строки
        cursor.execute("SELECT * FROM reports")  #
        sql_id = str(cursor.fetchall()[-1][0])  # Сохранение фотоотчета
        photo_file.download(f'{sql_id}.jpg')  # название = id в бд + расширение

        update.message.reply_text(f"Спасибо за помощь, {lst[0]}! Всего доброго!", reply_markup=markup)

        update.message.reply_text(f'{lst[0]}, при вашей проблеме кому-либо из сотрудников предприятия\n'
                                  f'может потребоваться помощь. Введите любой символ, чтобы увидеть карту дорог\n'
                                  f'с помеченной больницей или закончить диалог')

        return 5

    def geo(bot, update):
        try:
            toponym_to_find = lst[1].split(',')[0]
            map_params = get_map_params(toponym_to_find)

            address_ll = map_params["ll"]

            search_api_server = "https://search-maps.yandex.ru/v1/"
            api_key = "caf9d482-85c9-4643-a5ca-733c627c05d0"
            search_params = {
                "apikey": api_key,
                "text": "больница",
                "lang": "ru_RU",
                "ll": address_ll,
                "type": "biz",
                "results": "1"
            }
            response = requests.get(search_api_server, params=search_params)
            json_response = response.json()
            organization = json_response["features"][0]
            point = organization["geometry"]["coordinates"]
            org_point = f"{point[0]},{point[1]}"
            map_params["pt"] = f"{org_point},pm2dgl~{address_ll},pm2ntl"
            map_params.pop("spn")
            map_params.pop("ll")
            # ... и выполняем запрос
            map_api_server = "http://static-maps.yandex.ru/1.x/"
            response = requests.get(map_api_server, params=map_params)

            # Запишем полученное изображение в файл.
            map_file = "map.jpg"
            file = open(map_file, "wb+")
            file.write(response.content)
            update.bot.send_photo(chat_id=bot.message.chat.id, photo=open(map_file, 'rb'))  # отправляем картинку

        except Exception:
            update.bot.send_message(chat_id=bot.message.chat.id, text='Извините, карты недоступны в данный момент')
        lst.pop()  #
        lst.pop()  # Обнуление списка
        lst.pop()  #

        return ConversationHandler.END

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(Filters.text, first_response)],
            2: [MessageHandler(Filters.text, second_response)],
            3: [MessageHandler(Filters.text, third_response)],
            4: [MessageHandler(Filters.photo, photo)],
            5: [MessageHandler(Filters.text, geo)]
        },
        fallbacks=[CommandHandler('stop', stop)])  # стоп - условность конструкции библиотеки
    dp.add_handler(conv_handler)                   # за ненужностью в данной задаче заменен обычной заглушкой
    updater.start_polling()
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()

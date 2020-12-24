from typing import Dict
from collections.abc import Callable

try:
    import thread
except ImportError:
    import _thread as thread
import tornado.web
import tornado.websocket
import tornado.ioloop
import json
import asyncio
import psycopg2
import datetime
import time

con = psycopg2.connect(  # Подключение к базе данных
    database="db_chat",
    user="maks",
    password="2",
    host="musaev.online",  # Наш сервер
    port="5432"
)

clients = []  # Список подключенных клиентов
callbacks: Dict[int, Callable] = {}  # Список отправленных сообщений с callback


def my_converter(o):  # Конвертер datetime -> str
    if isinstance(o, datetime.datetime):
        return o.__str__()


class MessageController:
    @staticmethod
    def create(connection, data):  # Роут создания сообщения
        try:
            data = json.loads(data)
            cur = con.cursor()
            cur.execute(  # Запрос к бд: создание нового сообщения
                f"INSERT INTO message (text_message, time, author, chat_id) VALUES ('{data['text_message']}', '{data['time']}', '{data['author']}', '{data['chat_id']}')"
            )
            con.commit()
            cur.close()
            for client in [c for c in clients if c != connection]:  # Рассылка сообщения всем клиентам
                client.send('/messages/create', data)
            return json.dumps({'status': 'ok'})
        except Exception as e:
            print(str(e))
            cur.close()
            return json.dumps({'status': 'fail'})

    @staticmethod
    def get(connection, data):
        try:
            cur = con.cursor()
            data = json.loads(data)
            filters = f"WHERE chat_id = {data.get('chat_id')}"  # Фильтры для бд. Параметр chat_id обязателен
            since = data.get('since')
            last_id = data.get('last_id')
            if since:
                filters += f" AND time > '{since}'"  # Фильтр по времени
            if last_id:
                filters += f" AND id > {last_id}"  # Фильтр по id
            cur.execute(
                f"SELECT * FROM message " + filters
            )
            content = cur.fetchall()
            cur.close()
            return json.dumps(content, default=my_converter)
        except Exception as e:
            print(str(e))
            cur.close()
            return json.dumps({'status': 'fail'})


class ChatController:
    @staticmethod
    def get(connection, data):
        try:
            cur = con.cursor()
            cur.execute('SELECT * FROM chat')  # Получение всех чатов с бд
            content = cur.fetchall()
            cur.close()
            return json.dumps(content, default=my_converter)
        except Exception as e:
            print(str(e))
            cur.close()
            return json.dumps({'status': 'fail'})


routes = {"/messages/create": MessageController.create, "/messages/get": MessageController.get,
          # Объявляем прослушиваемые роуты
          "/chats/get": ChatController.get}


class ServerConnector(tornado.websocket.WebSocketHandler):  # Класс для работы с вебсокетами. Абстракция над вебсокетами
    def open(self):  # Обработчик событий подключения клиента
        clients.append(self)
        print("WebSocket opened")

    def on_message(self, message: str):  # Обработчик событий получения сообщения
        # print(message)
        message: Dict = json.loads(message)
        server_id = message.get('server_id')
        client_id = message.get('client_id')
        url = message.get('url')
        if url and client_id:  # В случае, если клиентское сообщения имеет Callback
            handler = routes.get(url)
            res = handler(self, message.get('data')) or None
            self.write_message(json.dumps({"client_id": client_id, "data": res}))
        elif url:  # В случае, если клиентское сообщения не имеет Callback
            handler = routes.get(url)
            handler(self, message.get('data'))
        elif server_id:  # В случае, если серверное сообщения имеет Callback
            handler = callbacks.pop(server_id)
            handler(self, message.get('data'))

    def send(self, url, message=None, callback=None):  # Метод отправки сообщения клиенту
        res = {"url": url}
        if message:
            res["data"] = message
        if callback:
            server_id = time.time_ns()  # ID сообщения получаем из функции времени
            res['server_id'] = server_id
            callbacks[server_id] = callback  # Запоминаем Callback и ID сообщения
        self.write_message(json.dumps(res))

    def on_close(self):  # Обработчик событий отсоединения клиента
        clients.remove(self)  # Удаляем клиента из списка подключенных
        print("WebSocket closed")


asyncio.set_event_loop(asyncio.new_event_loop())  # Устанавливаем цикл событий
application = tornado.web.Application([(r"/", ServerConnector)])  # Создаем экземпляр сервера tornado
server = tornado.httpserver.HTTPServer(application, ssl_options={
        "certfile": "cert.pem",
        "keyfile": "cert.key"
})
server.listen(8765, '0.0.0.0')  # Указываем прослушиваемый адрес и порт
try:
    loop = tornado.ioloop.IOLoop.current()
    loop.start()  # Запускаем сервер. Выполнение программы останавливается на этом месте
except KeyboardInterrupt:
    tornado.ioloop.IOLoop.current().stop()

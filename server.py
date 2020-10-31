from abc import ABC
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

con = psycopg2.connect(
    database="db_chat",
    user="maks",
    password="2",
    host="musaev.online",
    port="5432"
)

cur = con.cursor()


clients = []


class MessageController:
    @staticmethod
    def create(connection, data):
        data = json.loads(data)
        print(data)
        cur.execute(
            f"INSERT INTO message (text_message, time, author, chat_id) VALUES ('{data['text_message']}', '{data['time']}', '{data['author']}', '{data['chat_id']}')"
        )
        con.commit()
        for client in [c for c in clients if c != connection]:
            client.send('/messages/create', data)

    @staticmethod
    def get():
        pass


class ChatController:
    @staticmethod
    def get():
        pass


routes = {"/messages/create": MessageController.create, "/chats/get": ChatController.get,
          "/messages/get": MessageController.get}


class ServerConnector(tornado.websocket.WebSocketHandler, ABC):
    def open(self):
        clients.append(self)
        print("WebSocket opened")

    def on_message(self, message):
        print(message)
        message = json.loads(message)
        if message['url'] and message['data'] and routes[message['url']]:
            routes[message['url']](self, message['data'])

    def send(self, url, msg):
        self.write_message(json.dumps({"url": url, "data": msg}))

    def on_close(self):
        clients.remove(self)
        print("WebSocket closed")


def initServer():
    asyncio.set_event_loop(asyncio.new_event_loop())
    application = tornado.web.Application([(r"/", ServerConnector)])
    application.listen(8765, '0.0.0.0')
    try:
        loop = tornado.ioloop.IOLoop.current()
        loop.start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.current().stop()


thread.start_new_thread(initServer, ())

while True:
    pass

from abc import ABC
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

con = psycopg2.connect(
    database="db_chat",
    user="maks",
    password="2",
    host="musaev.online",
    port="5432"
)
cur = con.cursor()

clients = []
callbacks: Dict[int, Callable] = {}


def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


class MessageController:
    @staticmethod
    def create(connection, data):
        data = json.loads(data)

        cur.execute(
            f"INSERT INTO message (text_message, time, author, chat_id) VALUES ('{data['text_message']}', '{data['time']}', '{data['author']}', '{data['chat_id']}')"
        )
        con.commit()
        for client in [c for c in clients if c != connection]:
            client.send('/messages/create', data)

    @staticmethod
    def get(connection, data):
        data = json.loads(data)
        filters = f"WHERE chat_id = {data.get('chat_id')}"
        since = data.get('since')
        if since:
            filters += f" AND time > '{since}'"
        cur.execute(
            f"SELECT * FROM message " + filters
        )
        content = cur.fetchall()
        print(content)
        return json.dumps(content, default=myconverter)


class ChatController:
    @staticmethod
    def get():
        pass


routes = {"/messages/create": MessageController.create, "/messages/get": MessageController.get, "/chats/get": ChatController.get}


class ServerConnector(tornado.websocket.WebSocketHandler, ABC):
    def open(self):
        clients.append(self)
        print("WebSocket opened")

    def on_message(self, message: str):
        message: Dict = json.loads(message)
        server_id = message.get('server_id')
        client_id = message.get('client_id')
        url = message.get('url')
        if url and client_id:
            handler = routes.get(url)
            res = handler(self, message.get('data')) or None
            self.write_message(json.dumps({"client_id": client_id, "data": res}))
        elif url:
            handler = routes.get(url)
            handler(self, message.get('data'))
        elif server_id:
            handler = callbacks.pop(server_id)
            handler(self, message.get('data'))

    def send(self, url, message=None, callback=None):
        res = {"url": url}
        if message:
            res["data"] = message
        if callback:
            server_id = time.time_ns()
            res['server_id'] = server_id
            callbacks[server_id] = callback
        self.write_message(json.dumps(res))

    def on_close(self):
        clients.remove(self)
        print("WebSocket closed")


asyncio.set_event_loop(asyncio.new_event_loop())
application = tornado.web.Application([(r"/", ServerConnector)])
application.listen(8765, '0.0.0.0')
try:
    loop = tornado.ioloop.IOLoop.current()
    loop.start()
except KeyboardInterrupt:
    tornado.ioloop.IOLoop.current().stop()
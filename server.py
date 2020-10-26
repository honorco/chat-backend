try:
    import thread
except ImportError:
    import _thread as thread
from abc import ABC
import tornado.web
import tornado.websocket
import tornado.ioloop
import json
import asyncio

clients = []

class MessageController:
    @staticmethod
    def create(self, data):
        for client in [c for c in clients if c != self]:
            client.send('/messages/create', data)

routes = {"/messages/create": MessageController.create}

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
    msg = input()
    clients[0].send('/messages/create', msg)
from django.http import HttpResponse
from api.models import UserID, Chat
from django.core import serializers

def index(req):
    return HttpResponse('Hello, world!')


def getID(req):
    try:
        user = UserID.objects.all().first()
        user.count += 1
    except:
        user = UserID()
        user.count = 1

    user.save()
    return HttpResponse(user.count)


def getChats(req):
    return HttpResponse(serializers.serialize('json', Chat.objects.all()))


def createChat(req):
    chat = Chat(name=req.name)
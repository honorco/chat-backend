from django.http import HttpResponse
from api.models import UserID


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

from django.http import HttpResponse
from api.models import UserCounter

def index(req):
    return HttpResponse('Hello, world!')
def getID(req):
    user = UserCounter()
    user.save()
    return HttpResponse(user.id)
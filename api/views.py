from django.http import HttpResponse

def index(req):
    return HttpResponse('Hello, world!')
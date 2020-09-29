from django.db import models


class Chat(models.Model):
    name = models.CharField(max_length=255)


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    author = models.IntegerField()
    text = models.TextField()


class UserCounter(models.Model):
    pass

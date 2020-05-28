from django.db import models


def get_upload_to(instance):
    return 'user_icons/{0}' .format(instance.id_user)


class User(models.Model):
    class Meta:
        db_table = 'user'

    id_user = models.CharField(verbose_name='ユーザID', max_length=10, primary_key=True)
    name = models.CharField(verbose_name='ユーザ名', max_length=20)
    description = models.CharField(verbose_name='紹介文', max_length=100)
    icon = models.ImageField(verbose_name='アイコン', upload_to=get_upload_to)

    def __str__(self):
        return '{}, {}'.format(self.id_user, self.name)


class Voice(models.Model):
    class Meta:
        db_table = 'voice'

    id_voice = models.CharField(verbose_name='ボイスID', max_length=10, primary_key=True)
    message = models.CharField(verbose_name='メッセージ', max_length=100, null=True)
    like = models.IntegerField(verbose_name='いいね', default=0)
    speaker = models.ForeignKey(User, verbose_name='投稿者', on_delete=models.CASCADE)

    def __str__(self):
        return self.id_voice

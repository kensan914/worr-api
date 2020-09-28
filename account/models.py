import uuid
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import _user_has_perm
from django.db import models
from django.utils import timezone
from account.supports.modelSupport import get_default_obj


class AccountManager(BaseUserManager):
    use_in_migration = True

    def _create_user(self, **fields):
        if not 'email' in fields:
            raise ValueError('The given email must be set')
        if not 'password' in fields:
            raise ValueError('The given password must be set')
        fields['email'] = self.normalize_email(fields['email'])
        user = self.model(**fields)
        user.set_password(fields['password'])
        user.save(using=self._db)
        return user

    def create_user(self, **fields):
        fields.setdefault('is_staff', False)
        fields.setdefault('is_superuser', False)
        return self._create_user(**fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff==True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser==True.')

        return self._create_user(email=email, password=password, **extra_fields)


class ParamsModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self):
        return '{}.{}'.format(self.key, self.label)

    key = models.CharField(verbose_name='キー', max_length=30, unique=True, null=True)
    label = models.CharField(verbose_name='ラベル', max_length=30, null=True)


def get_default_status():
    return get_default_obj('static/courpus/statusList.txt', ['key', 'label', 'color'], Status)


class Status(ParamsModel):
    color = models.CharField(verbose_name='カラー', max_length=30, null=True)


class Feature(ParamsModel):
    pass


class GenreOfWorries(ParamsModel):
    value = models.CharField(verbose_name='バリュー', max_length=30, null=True)


class ScaleOfWorries(ParamsModel):
    pass


class WorriesToSympathize(ParamsModel):
    pass


class Plan(models.TextChoices):
    """
    ex) Plan(user.plan).name: 'NORMAL', Plan(user.plan).value: 'normal_plan', Plan(user.plan).label: 'ノーマルプラン'
    """
    # LIGHT = 'light', 'ライト'
    # VIP = 'vip', 'VIP'
    ONE_MONTH = '1_month_plan', '1monthプラン'
    TRIAL = 'trial_plan', 'お試しプラン'
    NORMAL = 'normal_plan', 'ノーマルプラン'


class Account(AbstractBaseUser):
    class Meta:
        verbose_name = 'アカウント'
        ordering = ['-date_joined']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(verbose_name='ユーザネーム', max_length=15)
    email = models.EmailField(verbose_name='メールアドレス', max_length=255, unique=True)
    birthday = models.DateField(verbose_name='生年月日', default=timezone.now)
    introduction = models.CharField(verbose_name='自己紹介', max_length=250, blank=True)
    num_of_thunks = models.IntegerField(verbose_name='ありがとう', default=0)
    status = models.ForeignKey(Status, verbose_name='ステータス', on_delete=models.SET_DEFAULT, default=get_default_status)
    # status = models.ForeignKey(Status, verbose_name='ステータス', on_delete=models.PROTECT, null=True)  # when init migration
    plan = models.CharField(verbose_name='プラン', max_length=10, choices=Plan.choices, default=Plan.TRIAL)
    features = models.ManyToManyField(Feature, verbose_name='特徴', blank=True)
    genre_of_worries = models.ManyToManyField(GenreOfWorries, verbose_name='対応できる悩みのジャンル', blank=True)
    scale_of_worries = models.ManyToManyField(ScaleOfWorries, verbose_name='対応できる悩みの大きさ', blank=True)
    worries_to_sympathize = models.ManyToManyField(WorriesToSympathize, verbose_name='共感できる悩み', blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(verbose_name='登録日', default=timezone.now)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def user_has_perm(user, perm, obj):
        return _user_has_perm(user, perm, obj)

    def has_perm(self, perm, obj=None):
        return _user_has_perm(self, perm, obj=obj)

    def has_module_perms(self, app_label):
        return self.is_superuser

    def get_short_name(self):
        return self.username

    objects = AccountManager()


def get_upload_to(instance, filename):
    pass
    media_dir_1 = str(instance.user.id)
    return 'profile_images/{0}/{1}' .format(media_dir_1, filename)


class ProfileImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    picture = models.ImageField(verbose_name='イメージ(original)', upload_to=get_upload_to)
    # picture_250x = models.CharField(verbose_name='イメージ(250x)', max_length=1024, null=True)
    # picture_500x = models.CharField(verbose_name='イメージ(500x)', max_length=1024, null=True)
    upload_date = models.DateTimeField(verbose_name='アップロード日', default=timezone.now)
    user = models.OneToOneField(Account, verbose_name='ユーザ', on_delete=models.CASCADE, unique=True, related_name='image')

    def __str__(self):
        return str(self.user)

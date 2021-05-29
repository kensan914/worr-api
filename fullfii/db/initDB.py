import os
from django.core.files import File
from django.core.files.images import ImageFile
from chat.models import DefaultRoomImage
import glob
from abc import ABCMeta
from account.models import Feature, GenreOfWorries, ScaleOfWorries


class InitDB(metaclass=ABCMeta):
    """
    attention: list.txtの先頭(1行目)はそのModelのデフォルトを記述
    """
    file_path = ''
    keyList = []
    model = None

    def init(self):
        fin = open(self.file_path, 'rt', encoding='utf-8')
        lines = fin.readlines()
        fin.close()

        for line in lines:
            obj = {}
            line = line.replace('\n', '')
            for key, val in zip(self.keyList, list(line.split(' '))):
                obj[key] = val
            if self.exists_obj(obj):
                self.create_obj(obj)
                print(obj['label'], 'is registered!')

    def exists_obj(self, obj):
        return not self.model.objects.filter(key=obj['key']).exists()

    def create_obj(self, obj):
        keyDict = {}
        for key in self.keyList:
            keyDict[key] = obj[key]
        self.model.objects.create(**keyDict)


class InitFeature(InitDB):
    file_path = 'static/corpus/featuresList.txt'
    keyList = ['key', 'label']
    model = Feature


class InitGenreOfWorries(InitDB):
    file_path = 'static/corpus/genreOfWorriesList.txt'
    keyList = ['key', 'value', 'label']
    model = GenreOfWorries


class InitScaleOfWorries(InitDB):
    file_path = 'static/corpus/scaleOfWorriesList.txt'
    keyList = ['key', 'label']
    model = ScaleOfWorries


def init_default_room_image():
    files = glob.glob('fullfii/db/images/default_room_images/*')
    for file_path in files:
        file_name = os.path.basename(file_path)
        if DefaultRoomImage.objects.filter(file_name=file_name).exists():
            continue
        default_room_image = DefaultRoomImage(
            file_name=file_name
        )
        image = ImageFile(open(file_path, 'rb'))
        default_room_image.image.save(file_name, image)
        default_room_image.save()
        print(f'デフォルトルーム画像「{file_name}」が登録されました。')

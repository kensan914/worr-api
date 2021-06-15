import os
from django.core.files.images import ImageFile
from chat.models import DefaultRoomImage
import glob


def init_default_room_image():
    files = glob.glob("fullfii/db/images/default_room_images/*")
    for file_path in files:
        file_name = os.path.basename(file_path)
        if DefaultRoomImage.objects.filter(file_name=file_name).exists():
            continue
        default_room_image = DefaultRoomImage(file_name=file_name)
        image = ImageFile(open(file_path, "rb"))
        default_room_image.image.save(file_name, image)
        default_room_image.save()
        print(f"デフォルトルーム画像「{file_name}」が登録されました。")

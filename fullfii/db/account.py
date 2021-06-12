from fullfii.lib.utils import calc_file_num
from config import settings
import os


def exists_std_images(image_field):
    try:
        profile_image_num = calc_file_num(
            os.path.dirname(settings.BASE_DIR + image_field.url)
        )
        return profile_image_num > 1
    except:
        return

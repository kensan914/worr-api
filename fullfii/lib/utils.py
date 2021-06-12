import os


def calc_file_num(dir_path):
    return sum(
        os.path.isfile(os.path.join(dir_path, name)) for name in os.listdir(dir_path)
    )

"""
fullfii/__init__.pyによるimport * を制限(循環importを引き起こす)
"""


def get_default_info(file_path, keyList):
    """
    statusList, planList の先頭（デフォルト）のobjを作成
    :param file_path: ex) 'static/courpus/statusList.txt'
    :param keyList: ex) ['key', 'label', 'color']
    :return: {'key': 'offline', 'label': 'オフライン', 'color': 'indianred'}
    """
    fin = open(file_path, 'rt', encoding='utf-8')
    lines = fin.readlines()
    fin.close()

    obj = {}
    line = lines[0].replace('\n', '')
    for key, val in zip(keyList, list(line.split(' '))):
        obj[key] = val
    return obj


def get_default_obj(file_path, keyList, model):
    default_info = get_default_info(file_path, keyList)
    default_objects = model.objects.filter(key=default_info['key'])
    if default_objects.exists():
        return default_objects.first().id
    else:
        default_obj = model(**default_info)
        default_obj.save()
        return default_obj.id

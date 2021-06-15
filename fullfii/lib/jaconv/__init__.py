import jaconv

from fullfii.lib.jaconv.custom_jaconv import alphabet2kana


def optimize_text(_text):
    """文字列を「半角 & ひらがな & 英語小文字」に最適化"""
    # 全角 ⇒ 半角 & ノーマライズ. ex) 'ｋAげヤmay' => 'kAげヤmay'
    cleaned_text = jaconv.normalize(_text, "NFKC")

    # カタカナ => ひらがな. ex) 'kAげヤmay' => 'kAげやmay'
    cleaned_text = jaconv.kata2hira(cleaned_text)

    # 大文字 => 小文字. ex) 'kAげやmay' => 'kaげやmay'
    cleaned_text = cleaned_text.lower()

    return cleaned_text


def translate_into_kana(_text):
    cleaned_text = optimize_text(_text)

    # 英語 => ひらがな. ex) 'kaげやmay' => {'is_success': False, 'text': 'かげやま'}
    result = alphabet2kana(cleaned_text)

    return result

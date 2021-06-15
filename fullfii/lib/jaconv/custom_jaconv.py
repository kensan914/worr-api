# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

HIRAGANA = list(
    "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすず"
    "せぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴ"
    "ふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろわ"
    "をんーゎゐゑゕゖゔゝゞ・「」。、"
)
HALF_ASCII = list(
    "!\"#$%&'()*+,-./:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ "
)
HALF_DIGIT = list("0123456789")
HALF_KANA_SEION = list(
    "ｧｱｨｲｩｳｪｴｫｵｶｷｸｹｺｻｼｽｾｿﾀﾁｯﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓｬﾔｭﾕｮﾖ" "ﾗﾘﾙﾚﾛﾜｦﾝｰヮヰヱヵヶヽヾ･｢｣｡､"
)
HALF_KANA = [
    "ｧ",
    "ｱ",
    "ｨ",
    "ｲ",
    "ｩ",
    "ｳ",
    "ｪ",
    "ｴ",
    "ｫ",
    "ｵ",
    "ｶ",
    "ｶﾞ",
    "ｷ",
    "ｷﾞ",
    "ｸ",
    "ｸﾞ",
    "ｹ",
    "ｹﾞ",
    "ｺ",
    "ｺﾞ",
    "ｻ",
    "ｻﾞ",
    "ｼ",
    "ｼﾞ",
    "ｽ",
    "ｽﾞ",
    "ｾ",
    "ｾﾞ",
    "ｿ",
    "ｿﾞ",
    "ﾀ",
    "ﾀﾞ",
    "ﾁ",
    "ﾁﾞ",
    "ｯ",
    "ﾂ",
    "ﾂﾞ",
    "ﾃ",
    "ﾃﾞ",
    "ﾄ",
    "ﾄﾞ",
    "ﾅ",
    "ﾆ",
    "ﾇ",
    "ﾈ",
    "ﾉ",
    "ﾊ",
    "ﾊﾞ",
    "ﾊﾟ",
    "ﾋ",
    "ﾋﾞ",
    "ﾋﾟ",
    "ﾌ",
    "ﾌﾞ",
    "ﾌﾟ",
    "ﾍ",
    "ﾍﾞ",
    "ﾍﾟ",
    "ﾎ",
    "ﾎﾞ",
    "ﾎﾟ",
    "ﾏ",
    "ﾐ",
    "ﾑ",
    "ﾒ",
    "ﾓ",
    "ｬ",
    "ﾔ",
    "ｭ",
    "ﾕ",
    "ｮ",
    "ﾖ",
    "ﾗ",
    "ﾘ",
    "ﾙ",
    "ﾚ",
    "ﾛ",
    "ﾜ",
    "ｦ",
    "ﾝ",
    "ｰ",
    "ヮ",
    "ヰ",
    "ヱ",
    "ヵ",
    "ヶ",
    "ｳﾞ",
    "ヽ",
    "ヾ",
    "･",
    "｢",
    "｣",
    "｡",
    "､",
]
FULL_ASCII = list(
    "！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠"
    "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
    "［＼］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔ"
    "ｕｖｗｘｙｚ｛｜｝～　"
)

FULL_DIGIT = list("０１２３４５６７８９")
FULL_KANA = list(
    "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソ"
    "ゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペ"
    "ホボポマミムメモャヤュユョヨラリルレロワヲンーヮヰヱヵヶヴ"
    "ヽヾ・「」。、"
)
FULL_KANA_SEION = list(
    "ァアィイゥウェエォオカキクケコサシスセソタチッツテト" "ナニヌネノハヒフヘホマミムメモャヤュユョヨラリルレロ" "ワヲンーヮヰヱヵヶヽヾ・「」。、"
)
HEPBURN = list("aiueoaiueo")
HEPBURN_KANA = list("ぁぃぅぇぉあいうえお")


def _to_ord_list(chars):
    return list(map(ord, chars))


HIRAGANA_ORD = _to_ord_list(HIRAGANA)
FULL_KANA_ORD = _to_ord_list(FULL_KANA)
HALF_ASCII_ORD = _to_ord_list(HALF_ASCII)
FULL_ASCII_ORD = _to_ord_list(FULL_ASCII)
HALF_DIGIT_ORD = _to_ord_list(HALF_DIGIT)
FULL_DIGIT_ORD = _to_ord_list(FULL_DIGIT)
HALF_KANA_SEION_ORD = _to_ord_list(HALF_KANA_SEION)
FULL_KANA_SEION_ORD = _to_ord_list(FULL_KANA_SEION)


def _to_dict(_from, _to):
    return dict(zip(_from, _to))


H2K_TABLE = _to_dict(HIRAGANA_ORD, FULL_KANA)
H2HK_TABLE = _to_dict(HIRAGANA_ORD, HALF_KANA)
K2H_TABLE = _to_dict(FULL_KANA_ORD, HIRAGANA)

H2Z_A = _to_dict(HALF_ASCII_ORD, FULL_ASCII)
H2Z_AD = _to_dict(HALF_ASCII_ORD + HALF_DIGIT_ORD, FULL_ASCII + FULL_DIGIT)
H2Z_AK = _to_dict(HALF_ASCII_ORD + HALF_KANA_SEION_ORD, FULL_ASCII + FULL_KANA_SEION)
H2Z_D = _to_dict(HALF_DIGIT_ORD, FULL_DIGIT)
H2Z_K = _to_dict(HALF_KANA_SEION_ORD, FULL_KANA_SEION)
H2Z_DK = _to_dict(HALF_DIGIT_ORD + HALF_KANA_SEION_ORD, FULL_DIGIT + FULL_KANA_SEION)
H2Z_ALL = _to_dict(
    HALF_ASCII_ORD + HALF_DIGIT_ORD + HALF_KANA_SEION_ORD,
    FULL_ASCII + FULL_DIGIT + FULL_KANA_SEION,
)

Z2H_A = _to_dict(FULL_ASCII_ORD, HALF_ASCII)
Z2H_AD = _to_dict(FULL_ASCII_ORD + FULL_DIGIT_ORD, HALF_ASCII + HALF_DIGIT)
Z2H_AK = _to_dict(FULL_ASCII_ORD + FULL_KANA_ORD, HALF_ASCII + HALF_KANA)
Z2H_D = _to_dict(FULL_DIGIT_ORD, HALF_DIGIT)
Z2H_K = _to_dict(FULL_KANA_ORD, HALF_KANA)
Z2H_DK = _to_dict(FULL_DIGIT_ORD + FULL_KANA_ORD, HALF_DIGIT + HALF_KANA)
Z2H_ALL = _to_dict(
    FULL_ASCII_ORD + FULL_DIGIT_ORD + FULL_KANA_ORD, HALF_ASCII + HALF_DIGIT + HALF_KANA
)
KANA2HEP = _to_dict(_to_ord_list(HEPBURN_KANA), HEPBURN)
HEP2KANA = _to_dict(_to_ord_list(HEPBURN), HEPBURN_KANA)

JULIUS_LONG_VOWEL = tuple(
    (
        (re.compile("( a){2,}"), " a:"),
        (re.compile("( i){2,}"), " i:"),
        (re.compile("( u){2,}"), " u:"),
        (re.compile("( e){2,}"), " e:"),
        (re.compile("( o){2,}"), " o:"),
    )
)

del _to_ord_list
del _to_dict
del HIRAGANA_ORD
del HIRAGANA
del HALF_KANA
del FULL_KANA_ORD
del FULL_KANA
del HALF_ASCII_ORD
del HALF_ASCII
del FULL_ASCII_ORD
del FULL_ASCII
del HALF_DIGIT_ORD
del HALF_DIGIT
del FULL_DIGIT_ORD
del FULL_DIGIT
del HALF_KANA_SEION_ORD
del HALF_KANA_SEION
del FULL_KANA_SEION_ORD
del FULL_KANA_SEION
del HEPBURN
del HEPBURN_KANA


consonants = frozenset("sdfghjklqwrtypzxcvbnm")


def _convert(text, conv_map):
    return text.translate(conv_map)


def alphabet2kana(_text):
    """
    Convert alphabets to Hiragana
    ひとつでも変換に成功した場合、成功した文字列のみ返す。全て変換失敗した場合、そのまま返す。

    Parameters
    ----------
    text : str
        Alphabets string.

    Return
    ------
    obj

    Examples
    --------
    >>> print(jaconv.alphabet2kana('nibutyan'))
    {'is_success': True, 'text': 'にぶちゃん'}

    >>> print(jaconv.alphabet2kana('nib'))
    {'is_success': False, 'text': 'に'}

    >>> print(jaconv.alphabet2kana('j'))
    {'is_success': False, 'text': 'j'}
    """
    text = _text
    text = text.replace("cya", "ちゃ").replace("cyu", "ちゅ").replace("cyo", "ちょ")
    text = text.replace("kya", "きゃ").replace("kyu", "きゅ").replace("kyo", "きょ")
    text = text.replace("gya", "ぎゃ").replace("gyu", "ぎゅ").replace("gyo", "ぎょ")
    text = text.replace("sha", "しゃ").replace("shu", "しゅ").replace("sho", "しょ")
    text = text.replace("zya", "じゃ").replace("zyu", "じゅ").replace("zyo", "じょ")
    text = text.replace("zyi", "じぃ").replace("zye", "じぇ")
    text = text.replace("ja", "じゃ").replace("ju", "じゅ").replace("jo", "じょ")
    text = text.replace("jya", "じゃ").replace("jyu", "じゅ").replace("jyo", "じょ")
    text = text.replace("cha", "ちゃ").replace("chu", "ちゅ").replace("cho", "ちょ")
    text = text.replace("tya", "ちゃ").replace("tyu", "ちゅ").replace("tyo", "ちょ")
    text = text.replace("nya", "にゃ").replace("nyu", "にゅ").replace("nyo", "にょ")
    text = text.replace("hya", "ひゃ").replace("hyu", "ひゅ").replace("hyo", "ひょ")
    text = text.replace("mya", "みゃ").replace("myu", "みゅ").replace("myo", "みょ")
    text = text.replace("rya", "りゃ").replace("ryu", "りゅ").replace("ryo", "りょ")
    text = text.replace("bya", "びゃ").replace("byu", "びゅ").replace("byo", "びょ")
    text = text.replace("pya", "ぴゃ").replace("pyu", "ぴゅ").replace("pyo", "ぴょ")
    text = text.replace("oh", "おお")
    text = text.replace("ga", "が").replace("gi", "ぎ").replace("gu", "ぐ")
    text = text.replace("ge", "げ").replace("go", "ご").replace("za", "ざ")
    text = text.replace("ji", "じ").replace("zu", "ず").replace("ze", "ぜ")
    text = (
        text.replace("zo", "ぞ").replace("da", "だ").replace("ji", "ぢ").replace("di", "ぢ")
    )
    text = text.replace("va", "ゔぁ").replace("vi", "ゔぃ").replace("vu", "ゔ")
    text = text.replace("ve", "ゔぇ").replace("vo", "ゔぉ").replace("vya", "ゔゃ")
    text = text.replace("vyi", "ゔぃ").replace("vyu", "ゔゅ").replace("vye", "ゔぇ")
    text = text.replace("vyo", "ゔょ")
    text = text.replace("zu", "づ").replace("de", "で").replace("do", "ど")
    text = text.replace("ba", "ば").replace("bi", "び").replace("bu", "ぶ")
    text = text.replace("be", "べ").replace("bo", "ぼ").replace("pa", "ぱ")
    text = text.replace("pi", "ぴ").replace("pu", "ぷ").replace("pe", "ぺ")
    text = text.replace("po", "ぽ").replace("dha", "でゃ").replace("dhi", "でぃ")
    text = text.replace("dhu", "でゅ").replace("dhe", "でぇ").replace("dho", "でょ")
    text = text.replace("ka", "か").replace("ki", "き").replace("ku", "く")
    text = text.replace("ke", "け").replace("ko", "こ").replace("sa", "さ")
    text = text.replace("tsu", "つ")
    text = text.replace("shi", "し").replace("su", "す").replace("se", "せ")
    text = text.replace("so", "そ").replace("ta", "た").replace("chi", "ち")
    text = text.replace("te", "て").replace("to", "と")
    text = text.replace("na", "な").replace("ni", "に").replace("nu", "ぬ")
    text = text.replace("ne", "ね").replace("no", "の").replace("ha", "は")
    text = text.replace("hi", "ひ").replace("fu", "ふ").replace("he", "へ")
    text = text.replace("ho", "ほ").replace("ma", "ま").replace("mi", "み")
    text = text.replace("mu", "む").replace("me", "め").replace("mo", "も")
    text = text.replace("ra", "ら").replace("ri", "り").replace("ru", "る")
    text = text.replace("re", "れ").replace("ro", "ろ")
    text = text.replace("ya", "や").replace("yu", "ゆ").replace("yo", "よ")
    text = text.replace("wa", "わ").replace("wi", "ゐ").replace("we", "ゑ")
    text = text.replace("wo", "を")
    text = text.replace("nn", "ん").replace("tu", "つ").replace("hu", "ふ")
    text = text.replace("fa", "ふぁ").replace("fi", "ふぃ").replace("fe", "ふぇ")
    text = text.replace("fo", "ふぉ").replace("-", "ー")
    text = text.replace("ti", "ち").replace("zi", "じ").replace("si", "し")
    text = (
        text.replace("ca", "か")
        .replace("ci", "し")
        .replace("cu", "く")
        .replace("ce", "せ")
        .replace("co", "こ")
    )
    text = _convert(text, HEP2KANA)

    texts = []  # 一つでも変換に成功した場合のtexts(変換失敗した文字列は含めない)
    only_eng_texts = []  # 全て変換失敗した場合のtexts(変換失敗してもそのまま返す)
    at_least_success = False  # 一つでも変換に成功
    ret = {"is_success": True, "text": ""}

    for (i, char) in enumerate(text):
        if char in consonants:
            if char != "n":
                texts.append("っ")
            else:
                texts.append("ん")
            ret["is_success"] = False
            only_eng_texts.append(char)
        else:
            at_least_success = True
            texts.append(char)

    if at_least_success:
        reversed_texts = texts[::-1]
        index = 0
        for i, text in enumerate(reversed_texts):
            index = i
            if text != "っ" and text != "ん":
                break

        reversed_texts = reversed_texts[index:]
        ret["text"] = "".join(reversed_texts[::-1])
    else:
        ret["text"] = "".join(only_eng_texts)
    return ret

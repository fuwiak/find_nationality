#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import re
import json
import sys
import argparse
from enum import Enum
import spacy
from transliterate import translit

# Проверка: установлена ли русская модель spaCy
try:
    nlp = spacy.load("ru_core_news_md")
except OSError:
    raise RuntimeError(
        "Не установлена модель 'ru_core_news_md' для spaCy.\n"
        "Установите командой: python -m spacy download ru_core_news_md"
    )

###############################################################################
# Перечисление (Enum) Национальностей
###############################################################################
class Nationality(Enum):
    RUSSIAN = "Русский"
    UKRAINIAN = "Украинец"
    BELARUSIAN = "Белорус"
    UZBEK = "Узбек"
    KAZAKH = "Казах"
    GEORGIAN = "Грузин"
    ARMENIAN = "Армянин"
    AZERBAIJANI = "Азербайджанец"
    TAJIK = "Таджик"
    MOLDOVAN = "Молдаванин"
    LITHUANIAN = "Литовец"
    LATVIAN = "Латыш"
    ESTONIAN = "Эстонец"
    TURKMEN = "Туркмен"
    KYRGYZ = "Киргиз"
    CHECHEN = "Чеченец"
    DAGESTANI = "Дагестанец"
    INGUSH = "Ингуш"
    TATAR = "Татарин"
    BURYAT = "Бурят"
    ISLAM = "Ислам"
    CAUCASIAN = "Кавказ"
    ASIAN = "Азия"
    ANGLO_SAXON = "Англосакс"
    OSSETIAN = "Осетин"
    AVAR = "Аварец"
    UNDETERMINED = "Не определено"
    SHALAVY = "Шалавы"
    VULGAR = "VULGAR"

###############################################################################
# Эмоджи-флаги -> национальность
###############################################################################
flag_emoji_nationality = {
    "🇷🇺": Nationality.RUSSIAN,
    "🇺🇦": Nationality.UKRAINIAN,
    "🇧🇾": Nationality.BELARUSIAN,
    "🇰🇿": Nationality.KAZAKH,
    "🇺🇿": Nationality.UZBEK,
    "🇹🇯": Nationality.TAJIK,
    "🇬🇪": Nationality.GEORGIAN,
    "🇦🇲": Nationality.ARMENIAN,
    "🇦🇿": Nationality.AZERBAIJANI,
    "🇲🇩": Nationality.MOLDOVAN,
    "🇱🇹": Nationality.LITHUANIAN,
    "🇱🇻": Nationality.LATVIAN,
    "🇪🇪": Nationality.ESTONIAN,
}

###############################################################################
# Список суффиксов для разных национальностей
###############################################################################
suffixes = {
    Nationality.RUSSIAN: [
        "ов", "ев", "ov", "ev", "ин", "in", "sky", "skiy", "ykh", "ikh",
        "ий", "oy", "ова", "ева", "ина", "ская"
    ],
    Nationality.UKRAINIAN: [
        "енко", "enko", "чук", "chuk", "ко", "ko", "ук", "uk", "юк", "yuk", "ык", "yk",
    ],
    Nationality.BELARUSIAN: [
        "вич", "vich", "вичус", "vichus", "вичик", "vichyk"
    ],
    Nationality.KAZAKH: [
        "ұлы", "uly", "кызы", "kyzy", "бек", "bek", "бай", "bay", "тай", "tai"
    ],
    Nationality.UZBEK: [
        "зода", "zoda", "заде", "zade", "zada", "zoda"
    ],
    Nationality.GEORGIAN: [
        "швили", "shvili", "дзе", "dze", "адзе", "adze", "ия", "ia", "ури", "uri"
    ],
    Nationality.ARMENIAN: [
        "ян", "an", "янц", "yants"
    ],
    Nationality.AZERBAIJANI: [
        "оглы", "ogly", "заде", "zade"
    ],
    Nationality.TAJIK: [
        "заде", "zade", "зода", "zoda"
    ],
    Nationality.MOLDOVAN: [
        "ару", "aru", "еску", "escu"
    ],
    Nationality.LITHUANIAN: [
        "ас", "as", "ис", "is", "ус", "us", "юс", "jus",
        "айтис", "aitis", "йте", "ytė", "ене", "iene"
    ],
    Nationality.LATVIAN: [
        "анс", "ans", "калнс", "kalns", "вецмуктанс",
        "vecmuktans", "сонс", "sons", "бергс", "bergs"
    ],
    Nationality.ESTONIAN: [
        "мяэ", "mäe", "пылд", "põld", "оя", "oja",
        "вяли", "väli", "мяги", "mägi", "метс", "mets", "соо", "soo"
    ],
    # Пример для туркмен, киргиз и т.д. можно дополнять.
}

def generate_transliterated_names_flatten(cyrillic_names):
    """ Создаём список, содержащий и кириллический, и транслитерированный варианты. """
    flattened_list = []
    for name in cyrillic_names:
        flattened_list.append(name)
        transliterated = translit(name, 'ru', reversed=True)
        flattened_list.append(transliterated)
    return flattened_list

# Применяем транслитерацию к суффиксам
for nat, names in suffixes.items():
    suffixes[nat] = generate_transliterated_names_flatten(names)

###############################################################################
# Загрузка typical_names.json, если существует
###############################################################################
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "json_data", "typical_names.json")
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        typical_names_data = json.load(f)
else:
    typical_names_data = {"typical_names": {}}

typical_names_json = typical_names_data.get("typical_names", {})
typical_names = {}

# Преобразуем ключи в Enum, если получается
for key, value in typical_names_json.items():
    try:
        nat_enum = Nationality[key]
        typical_names[nat_enum] = value
    except KeyError:
        pass

###############################################################################
# Генерируем уменьшительные формы
###############################################################################
diminutive_names = {}
for nationality, names in typical_names.items():
    diminutives = []
    for name in names:
        doc = nlp(name)
        for token in doc:
            if token.pos_ == "PROPN":
                diminutive = token.text.lower() + "ка"  # Примитивная эвристика
                diminutives.append(diminutive)
    diminutive_names[nationality] = diminutives

# Объединяем имена и уменьшительные + транслитерация
for nationality, names in typical_names.items():
    total_list = names + diminutive_names.get(nationality, [])
    typical_names[nationality] = generate_transliterated_names_flatten(total_list)

###############################################################################
# Ласкательные прозвища
###############################################################################
affectionate_nicknames = [
    "Бусинка", "Зайчик", "Котик", "Малыш", "Малышка", "Ласточка", "Солнышко",
    "Зайка", "Пупсик", "Зайчонок", "Киска", "Масик", "Крошка", "Рыбка", "Котёнок",
    "Чапа", "Васька", "Сеня", "Тоша", "Петька", "Лёша"
]

def detect_nationality_from_affectionate_nickname(name: str):
    for nickname in affectionate_nicknames:
        if nickname.lower() in name.lower():
            return Nationality.RUSSIAN
    return None

###############################################################################
# Специфические буквы в слове -> признак языка
###############################################################################
def detect_nationality_from_letters(contact_name: str):
    # Украинские буквы
    if re.search(r'[їієґІЇЄҐ]', contact_name):
        return Nationality.UKRAINIAN
    # Белорусские буквы
    if re.search(r'[ўЎ]', contact_name):
        return Nationality.BELARUSIAN
    # Грузинский алфавит
    if re.search(r'[\u10A0-\u10FF]', contact_name):
        return Nationality.GEORGIAN
    # Армянский алфавит
    if re.search(r'[\u0530-\u058F]', contact_name):
        return Nationality.ARMENIAN
    # Казахские буквы
    kazakh_letters = 'ӘәҒғҚқҢңӨөҰұҮүҺһІі'
    if re.search(f'[{kazakh_letters}]', contact_name):
        return Nationality.KAZAKH
    # И т.д. можно дополнять
    return None

###############################################################################
# Исламские имена (загружаются из файла islam_names.txt, если есть)
###############################################################################
islam_names_path = os.path.join(BASE_DIR, "islam_names.txt")
if os.path.exists(islam_names_path):
    with open(islam_names_path, "r", encoding="utf-8") as file:
        islamic_names = [line.strip() for line in file if line.strip()]
else:
    islamic_names = []

###############################################################################
# Гео-ключевые слова + сопоставление страна -> национальность
###############################################################################
geo_keywords = {
    "Russia": [
        "Москва", "Moscow", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
        "Ростов-на-Дону", "Уфа", "Казань", "Нижний Новгород"
    ],
    "Ukraine": [
        "Киев", "Kyiv", "Львов", "Lviv", "Одесса", "Odesa",
        "Харьков", "Херсон", "Запорожье"
    ],
    "Belarus": [
        "Минск", "Minsk", "Гомель", "Брест"
    ],
    "Kazakhstan": [
        "Алматы", "Almaty", "Астана", "Нур-Султан", "Шымкент", "Караганда"
    ],
    "Uzbekistan": [
        "Ташкент", "Самарканд", "Бухара"
    ],
    "Georgia": [
        "Тбилиси", "Батуми", "Кутаиси", "Сухуми"
    ],
    "Armenia": [
        "Ереван", "Гюмри", "Ванадзор"
    ],
    "Azerbaijan": [
        "Баку", "Ganja", "Сумгаит"
    ],
    "Moldova": [
        "Кишинёв", "Chisinau", "Бельцы"
    ],
    "Kyrgyzstan": [
        "Бишкек", "Ош", "Jalal-Abad"
    ],
    "Tajikistan": [
        "Душанбе", "Худжанд", "Куляб"
    ],
    "Turkmenistan": [
        "Ашхабад", "Turkmenabat", "Мары"
    ],
    "Latvia": [
        "Рига", "Даугавпилс", "Юрмала"
    ],
    "Lithuania": [
        "Вильнюс", "Каунас", "Клайпеда"
    ],
    "Estonia": [
        "Таллин", "Тарту", "Нарва"
    ],
}
country_to_nationality = {
    "Russia": Nationality.RUSSIAN,
    "Ukraine": Nationality.UKRAINIAN,
    "Belarus": Nationality.BELARUSIAN,
    "Kazakhstan": Nationality.KAZAKH,
    "Uzbekistan": Nationality.UZBEK,
    "Georgia": Nationality.GEORGIAN,
    "Armenia": Nationality.ARMENIAN,
    "Azerbaijan": Nationality.AZERBAIJANI,
    "Moldova": Nationality.MOLDOVAN,
    "Kyrgyzstan": Nationality.KYRGYZ,
    "Tajikistan": Nationality.TAJIK,
    "Turkmenistan": Nationality.TURKMEN,
    "Latvia": Nationality.LATVIAN,
    "Lithuania": Nationality.LITHUANIAN,
    "Estonia": Nationality.ESTONIAN,
}

def detect_nationality_from_geo(contact_name: str):
    for country, cities in geo_keywords.items():
        for city in cities:
            if city.lower() in contact_name.lower():
                return country_to_nationality.get(country, Nationality.UNDETERMINED)
    return None

###############################################################################
# Ключевые слова компаний -> национальность
###############################################################################
company_keywords = {
    "Russia": ["Газпром", "Сбербанк", "Роснефть", "Яндекс", "Лукойл"],
    "Ukraine": ["ПриватБанк", "УкрНафта", "Рошен", "Нафтогаз"],
    "Kazakhstan": ["КазМунайГаз", "Halyk Bank", "Казпочта"],
}

def detect_nationality_from_company(contact_name: str):
    for country, companies in company_keywords.items():
        for company in companies:
            if company.lower() in contact_name.lower():
                return country_to_nationality.get(country, Nationality.UNDETERMINED)
    return None

###############################################################################
# Профессии / семейные связи (определяем, что "русские")
###############################################################################
family_relationships = [
    "мама", "папа", "брат", "сестра", "дядя", "тетя", "бабушка", "дедушка",
    "сын", "дочь", "кума", "кум", "крестный", "крестная", "батя", "супруга",
    "муж", "жена", "любимый", "любимая", "братишка", "сестрёнка", "батюшка",
    "матушка", "отец", "мать", "дядька", "тётя", "внучка", "внук", "свекровь",
    "свекр", "тесть", "теща", "зять", "невестка", "братан", "сеструха",
    "батяня", "бабуля", "дедуля"
]
professions_and_relations = ["бармен", "врач", "учитель", "фермер"]
professions_and_relations.extend(family_relationships)

def detect_nationality_from_profession_or_relation(contact_name: str):
    for word in professions_and_relations:
        if word.lower() in contact_name.lower():
            return Nationality.RUSSIAN
    return None

###############################################################################
# Уменьшительные формы
###############################################################################
diminutive_to_formal = {
    "Саша": "Александр",
    "Коля": "Николай",
    "Ваня": "Иван",
    "Дима": "Дмитрий",
}

def normalize_diminutive(name: str):
    for diminutive, formal in diminutive_to_formal.items():
        if diminutive.lower() in name.lower():
            return name.lower().replace(diminutive.lower(), formal.lower())
    return name

###############################################################################
# Главная функция определения национальности по любому имени
###############################################################################
def detect_nationality_from_name(name: str) -> Nationality:
    # 1. Учитываем уменьшительные
    name = normalize_diminutive(name)

    # 2. Ласкательные прозвища
    aff_nat = detect_nationality_from_affectionate_nickname(name)
    if aff_nat:
        return aff_nat

    # 3. Флаг-эмоджи
    for flag, nat_enum in flag_emoji_nationality.items():
        if flag in name:
            return nat_enum

    # 4. Специфические буквы
    letter_nat = detect_nationality_from_letters(name)
    if letter_nat:
        return letter_nat

    # 5. Типичные имена
    name_parts = name.split()
    for nationality, nameset in typical_names.items():
        if any(part in nameset for part in name_parts):
            return nationality

    # 6. Исламские имена
    if any(part in islamic_names for part in name_parts):
        return Nationality.ISLAM

    # 7. Суффиксы
    for nationality, suffix_list in suffixes.items():
        for suffix in suffix_list:
            if any(part.endswith(suffix) for part in name_parts):
                return nationality

    # 8. Гео
    geo_nat = detect_nationality_from_geo(name)
    if geo_nat:
        return geo_nat

    # 9. Компании
    comp_nat = detect_nationality_from_company(name)
    if comp_nat:
        return comp_nat

    # 10. Профессии / семейные связи
    prof_nat = detect_nationality_from_profession_or_relation(name)
    if prof_nat:
        return prof_nat

    return Nationality.UNDETERMINED

###############################################################################
# Определение национальности по ФИО
###############################################################################
def detect_nationality_from_fio(fname: str, lname: str, mname: str) -> Nationality:
    full_name = " ".join(filter(None, [fname, lname, mname])).strip()
    if not full_name:
        return Nationality.UNDETERMINED
    return detect_nationality_from_name(full_name)

###############################################################################
# Основная логика
###############################################################################
def main():
    """
    Считываем два файла:
    1) CSV с данными о гражданах (id, phone, FIO, адрес и т.д.)
    2) alldata.txt (phone, user_id, как записан, ...)

    Формируем выходной CSV с объединённой информацией.
    """
    parser = argparse.ArgumentParser(
        description="Скрипт для определения национальностей по данным из двух файлов."
    )
    # Взаимоисключающие флаги -v/--verbose и -s/--silent
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-v", "--verbose", action="store_true",
                       help="Вывести подробную информацию во время работы.")
    group.add_argument("-s", "--silent", action="store_true",
                       help="Не выводить никакой дополнительной информации (тихий режим).")

    parser.add_argument("-c", "--citizen-file", default="citizen_sample.csv",
                        help="Путь к CSV-файлу с данными о гражданах (по умолчанию: citizen_sample.csv).")
    parser.add_argument("-a", "--alldata-file", default="alldata.txt",
                        help="Путь к файлу alldata.txt (по умолчанию: alldata.txt).")
    parser.add_argument("-o", "--output-file", default="output_result.csv",
                        help="Путь к выходному CSV-файлу (по умолчанию: output_result.csv).")

    args = parser.parse_args()

    citizen_file = args.citizen_file
    alldata_file = args.alldata_file
    output_file = args.output_file
    is_verbose = args.verbose
    is_silent = args.silent

    # Если включён verbose-режим, будем печатать сообщения
    def log(message):
        if is_verbose and not is_silent:
            print(message)

    log(f"Файл граждан: {citizen_file}")
    log(f"Файл alldata: {alldata_file}")
    log(f"Выходной файл: {output_file}")

    # --- 1) Считываем файл с гражданами
    if not os.path.exists(citizen_file):
        print(f"Файл {citizen_file} не найден!")
        sys.exit(1)

    citizen_dict = {}
    with open(citizen_file, 'r', encoding='utf-8') as cf:
        reader = csv.DictReader(cf, delimiter=',')
        for row in reader:
            phone = row.get("phone", "").strip()
            if not phone or phone.lower() == "none":
                continue
            citizen_dict[phone] = {
                "id": row.get("id", ""),
                "fname": row.get("fname", "").strip(),
                "lname": row.get("lname", "").strip(),
                "mname": row.get("mname", "").strip(),
                "region": row.get("region", "").strip(),
                "city": row.get("city", "").strip(),
                "street": row.get("street", "").strip(),
                "house": row.get("house", "").strip(),
                "apr": row.get("apr", "").strip(),
                "country": row.get("country", "").strip()
            }

    log(f"Считано граждан: {len(citizen_dict)}")

    # --- 2) Считываем alldata.txt
    if not os.path.exists(alldata_file):
        print(f"Файл {alldata_file} не найден!")
        sys.exit(1)

    results = []
    count = 0

    with open(alldata_file, 'r', encoding='utf-8') as adf:
        reader = csv.reader(adf, delimiter=',')
        for row in reader:
            if len(row) < 3:
                continue

            phone = row[0].strip()
            user_id = row[1].strip()
            how_recorded = row[2].strip()

            if phone.lower() == "none" or not phone:
                phone = None

            # Национальность из "как записан" (2-й док)
            nat_2nd_doc = detect_nationality_from_name(how_recorded)

            # Упрощённая логика "гео" по номеру телефона (префиксы)
            phone_geo = "Не определено"
            if phone:
                if phone.startswith("79") or phone.startswith("+79"):
                    phone_geo = "Россия"
                elif phone.startswith("77") or phone.startswith("+77"):
                    phone_geo = "Казахстан"
                elif phone.startswith("375") or phone.startswith("+375"):
                    phone_geo = "Беларусь"
                elif phone.startswith("380") or phone.startswith("+380"):
                    phone_geo = "Украина"
                elif phone.startswith("998") or phone.startswith("+998"):
                    phone_geo = "Узбекистан"
                elif phone.startswith("994") or phone.startswith("+994"):
                    phone_geo = "Азербайджан"
                elif phone.startswith("995") or phone.startswith("+995"):
                    phone_geo = "Грузия"
                elif phone.startswith("374") or phone.startswith("+374"):
                    phone_geo = "Армения"
                elif phone.startswith("996") or phone.startswith("+996"):
                    phone_geo = "Киргизия"
                elif phone.startswith("992") or phone.startswith("+992"):
                    phone_geo = "Таджикистан"
                elif phone.startswith("993") or phone.startswith("+993"):
                    phone_geo = "Туркменистан"
                # Можно расширять при необходимости

            if phone and phone in citizen_dict:
                cdata = citizen_dict[phone]
                fio_nationality = detect_nationality_from_fio(
                    cdata["fname"], cdata["lname"], cdata["mname"]
                )
                # Анонимизация адреса (до улицы)
                region = cdata["region"]
                city = cdata["city"]
                street = cdata["street"]
                address_anon = ", ".join(filter(None, [region, city, street]))

                fio_full = " ".join(filter(None, [cdata["fname"], cdata["lname"], cdata["mname"]]))

                row_out = [
                    user_id,
                    phone_geo,
                    nat_2nd_doc.value,  # из 2-го дока
                    how_recorded,
                    address_anon,
                    fio_nationality.value,
                    fio_full
                ]
            else:
                # Нет данных о гражданине в 1-м файле
                row_out = [
                    user_id,
                    phone_geo,
                    nat_2nd_doc.value,
                    how_recorded,
                    "",
                    "",
                    ""
                ]
            results.append(row_out)
            count += 1

    log(f"Обработано строк alldata: {count}")

    # --- 3) Записываем результат в CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as outf:
        writer = csv.writer(outf)
        writer.writerow([
            "ID_Telegram", "Geo_byPhone", "Nationality_2ndDoc",
            "HowRecorded", "Address_Anonymized",
            "Nationality_byFIO", "FIO"
        ])
        for row_out in results:
            writer.writerow(row_out)

    if not is_silent:
        print(f"Готово! Результат сохранён в {output_file}. Всего строк: {len(results)}.")

###############################################################################
# Точка входа
###############################################################################
if __name__ == "__main__":
    main()

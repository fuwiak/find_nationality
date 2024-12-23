import csv
import re
from enum import Enum
import spacy
from russiannames.parser import NamesParser
from transliterate import translit
from fuzzywuzzy import fuzz
import emoji  # Import emoji library to handle emojis

# Initialize the Russian NamesParser for ethnic classification
parser = NamesParser()

# Load the Russian language model from spaCy
nlp = spacy.load("ru_core_news_md")

# Enumeration for nationalities
class Nationality(Enum):
    RUSSIAN = "Русский"
    UKRAINIAN = "Украинец"
    GEORGIAN = "Грузин"
    ARMENIAN = "Армянин"
    AZERBAIJANI = "Азербайджанец"
    KAZAKH = "Казах"
    UZBEK = "Узбек"
    TAJIK = "Таджик"
    BELARUSIAN = "Белорус"
    MOLDOVAN = "Молдаванин"
    CHECHEN = "Чеченец"
    DAGESTANI = "Дагестанец"
    CAUCASIAN = "Кавказ"
    ASIAN = "Азия"
    ANGLO_SAXON = "Англосакс"
    LATVIAN = "Латыш"
    LITHUANIAN = "Литовец"
    ESTONIAN = "Эстонец"
    INGUSH = "Ингуш"
    TATAR = "Татарин"
    BURYAT = "Бурят"
    UNDETERMINED = "Не определено"
    SHALAVY = "Шалавы"
    VULGAR = "Шалопай"

# Dictionary mapping flag emojis to nationalities
flag_emoji_nationality = {
    "🇷🇺": Nationality.RUSSIAN,
    "🇺🇦": Nationality.UKRAINIAN,
    "🇬🇪": Nationality.GEORGIAN,
    "🇦🇲": Nationality.ARMENIAN,
    "🇦🇿": Nationality.AZERBAIJANI,
    "🇰🇿": Nationality.KAZAKH,
    "🇺🇿": Nationality.UZBEK,
    "🇹🇯": Nationality.TAJIK,
    "🇧🇾": Nationality.BELARUSIAN,
    "🇲🇩": Nationality.MOLDOVAN,
    "🇱🇻": Nationality.LATVIAN,
    "🇱🇹": Nationality.LITHUANIAN,
    "🇪🇪": Nationality.ESTONIAN,
}

# Suffixes dictionary
suffixes = {
    Nationality.RUSSIAN: ["ов", "ев", "ov", "ev", "ин", "in", "sky", "skiy", "ykh", "ikh", "ий", "oy", "ова", "eva", "ina", "skaya"],
    Nationality.UKRAINIAN: ["енко", "enko", "чук", "chuk", "ко", "ko", "ук", "uk", "юк", "yuk", "ык", "yk"],
    Nationality.KAZAKH: ["ұлы", "uly", "кызы", "kyzy", "бек", "bek", "бай", "bay", "тай", "tai"],
    Nationality.UZBEK: ["зода", "zoda", "заде", "zade", "zada", "zoda"],
    Nationality.BELARUSIAN: ["вич", "vich", "вичус", "vichus", "вичик", "vichyk"],
    Nationality.MOLDOVAN: ["ару", "aru", "еску", "escu"],
    Nationality.CHECHEN: ["хадж", "khadzh", "хаджи", "khadzhi", "хож", "khozh", "хаджиев", "khadzhiev"],
    Nationality.DAGESTANI: ["гаджиев", "gadzhiev", "хадж", "khadzh", "гаджи", "gadji"],
    Nationality.CAUCASIAN: ["пш", "psh", "шев", "shev"],
    Nationality.ASIAN: ["бек", "bek", "баев", "baev", "медов", "medov", "гулов", "gulov", "кулов", "kulov", "гул", "gul"],
    Nationality.ANGLO_SAXON: ["сон", "son", "тон", "ton", "лей", "ley", "форд", "ford", "вуд", "wood", "ман", "man", "филд", "field", "брук", "brook"],
    Nationality.LATVIAN: ["анс", "ans", "калнс", "kalns", "вецмуктанс", "vecmuktans", "сонс", "sons", "бергс", "bergs"],
    Nationality.LITHUANIAN: ["ас", "as", "ис", "is", "ус", "us", "юс", "jus", "айтис", "aitis", "йте", "ytė", "ене", "iene"],
    Nationality.ESTONIAN: ["мяэ", "mäe", "пылд", "põld", "оя", "oja", "вяли", "väli", "мяги", "mägi", "метс", "mets", "соо", "soo"],
    Nationality.INGUSH: ["гов", "вов", "ив", "ме"],
    Nationality.TATAR: ["уллин", "гуллин", "уллов", "улов"],
    Nationality.BURYAT: ["доржиев", "дугаров", "баир"],
}

def generate_transliterated_names_flatten(cyrillic_names):
    # Create a list that contains both Cyrillic and transliterated Latin versions
    flattened_list = []
    for name in cyrillic_names:
        flattened_list.append(name)  # Add Cyrillic name
        flattened_list.append(translit(name, 'ru', reversed=True))  # Add Latin name
    return flattened_list


# Apply the generate_transliterated_names_map function to all entries in raw_typical_names
suffixes = {nationality: generate_transliterated_names_flatten(names) for nationality, names in suffixes.items()}






# Add vulgar word detection
vulgar_words = ['идиот', 'дурак', 'шалава', 'шлюха', 'мразь', 'сволочь', 'пидор', 'Какашка','Какашка😂']

# Detect nationality based on vulgar words
def detect_vulgar_words(contact_name: str) -> Nationality:
    if any(vulgar_word in contact_name.lower() for vulgar_word in vulgar_words):
        return Nationality.VULGAR
    return None

# Detect nationality based on flag emoji
def detect_nationality_from_flag(contact_name: str) -> Nationality:
    for flag, nationality in flag_emoji_nationality.items():
        if flag in contact_name:
            return nationality
    return None

# Detect nationality based on geo-location keywords
geo_keywords = {
    "Russia": ["Москва", "Moscow", "Санкт-Петербург", "Saint Petersburg", "Новосибирск", "Novosibirsk", "Екатеринбург", "Yekaterinburg"],
    "Ukraine": ["Киев", "Kyiv", "Львов", "Lviv", "Одесса", "Odesa", "Днепр", "Dnipro", "Харьков", "Kharkiv"],
    "Georgia": ["Тбилиси", "Tbilisi", "Батуми", "Batumi", "Кутаиси", "Kutaisi", "Сухуми", "Sukhumi"],
    "Armenia": ["Ереван", "Yerevan", "Гюмри", "Gyumri", "Ванадзор", "Vanadzor"],
    "Azerbaijan": ["Баку", "Baku", "Гянджа", "Ganja", "Сумгаит", "Sumgait"],
    "Kazakhstan": ["Нур-Султан", "Nur-Sultan", "Алматы", "Almaty", "Шымкент", "Shymkent", "Караганда", "Karaganda"],
    "Uzbekistan": ["Ташкент", "Tashkent", "Самарканд", "Samarkand", "Бухара", "Bukhara"],
    "Tajikistan": ["Душанбе", "Dushanbe", "Худжанд", "Khujand", "Куляб", "Kulob"],
    "Belarus": ["Минск", "Minsk", "Гомель", "Gomel", "Могилев", "Mogilev", "Брест", "Brest"],
    "Latvia": ["Рига", "Riga", "Даугавпилс", "Daugavpils", "Юрмала", "Jurmala"],
    "Lithuania": ["Вильнюс", "Vilnius", "Каунас", "Kaunas", "Клайпеда", "Klaipeda"],
    "Estonia": ["Таллин", "Tallinn", "Тарту", "Tartu", "Нарва", "Narva"],
    "Chechnya": ["Грозный", "Grozny", "Шали", "Shali", "Аргун", "Argun"],
    "Dagestan": ["Махачкала", "Makhachkala", "Дербент", "Derbent", "Каспийск", "Kaspiysk"],
    "Ingushetia": ["Назрань", "Nazran", "Магас", "Magas"],
    "Tatarstan": ["Казань", "Kazan", "Набережные Челны", "Naberezhnye Chelny", "Альметьевск", "Almetyevsk"],
    "Buryatia": ["Улан-Удэ", "Ulan-Ude", "Северобайкальск", "Severobaykalsk", "Гусиноозёрск", "Gusinoozersk"],
    "Bashkortostan": ["Уфа", "Ufa", "Стерлитамак", "Sterlitamak", "Салават", "Salavat"],
    "Komi": ["Сыктывкар", "Syktyvkar", "Воркута", "Vorkuta", "Ухта", "Ukhta"],
    "Kalmykia": ["Элиста", "Elista", "Лагань", "Lagan", "Городовиковск", "Gorodovikovsk"],
    "Karelia": ["Петрозаводск", "Petrozavodsk", "Кондопога", "Kondopoga", "Сортавала", "Sortavala"],
    "Sakha (Yakutia)": ["Якутск", "Yakutsk", "Нерюнгри", "Neryungri", "Мирный", "Mirny"],
}





def detect_nationality_from_geo(contact_name: str) -> Nationality:
    for country, locations in geo_keywords.items():
        for location in locations:
            if location.lower() in contact_name.lower():
                return country_to_nationality.get(country, None)
    return None

# Dictionary mapping countries/regions to nationalities
country_to_nationality = {
    "Russia": Nationality.RUSSIAN,
    "Ukraine": Nationality.UKRAINIAN,
    "Georgia": Nationality.GEORGIAN,
    "Armenia": Nationality.ARMENIAN,
    "Azerbaijan": Nationality.AZERBAIJANI,
    "Kazakhstan": Nationality.KAZAKH,
    "Uzbekistan": Nationality.UZBEK,
    "Tajikistan": Nationality.TAJIK,
    "Belarus": Nationality.BELARUSIAN,
    "Latvia": Nationality.LATVIAN,
    "Lithuania": Nationality.LITHUANIAN,
    "Estonia": Nationality.ESTONIAN,
    "Chechnya": Nationality.CHECHEN,
    "Dagestan": Nationality.DAGESTANI,
    "Ingushetia": Nationality.INGUSH,
    "Tatarstan": Nationality.TATAR,
    "Buryatia": Nationality.BURYAT,
    "Bashkortostan": Nationality.TATAR,  # Можно использовать как Татарскую национальность
    "Komi": Nationality.RUSSIAN,  # Возможна классификация по русскому большинству
    "Kalmykia": Nationality.RUSSIAN,  # Можно добавить Калмыцкую национальность, если нужно
    "Karelia": Nationality.RUSSIAN,  # Также можно добавить карельскую национальность, если нужно
    "Sakha (Yakutia)": Nationality.RUSSIAN,  # Можно классифицировать как Якуты или оставить русский
}



# Detect nationality based on patronymics
def detect_nationality_from_patronymic(patronymic: str) -> Nationality:
    for nationality, suffixes in patronymic_suffixes.items():
        if any(patronymic.lower().endswith(suffix.lower()) for suffix in suffixes):
            return nationality
    return None

# Detect nationality based on company names


company_names = ["Mitsubishi", "Toyota", "Gazprom", "Lukoil", "Samsung", "Honda", "Mitsubishi_tank",]  # Extend as needed



russian_banks_companies = [
    "Сбербанк", "Тинькофф", "ВТБ", "Газпромбанк", "Роснефть", "Лукойл", "РЖД", "Яндекс",
    "Магнит", "МТС", "Мегафон", "Билайн", "Ростелеком", "Mail.ru", "Озон",
    "Wildberries", "Почта России", "Аэрофлот", "UTair", "S7 Airlines", "Школа программирования", "Код будущего",
    "Пятерочка", "Перекресток", "М.Видео", "Эльдорадо", "Детский Мир", "Тануки", "Япоша", "Росгосстрах",
    "Росатом", "Роскосмос", "Росморпорт", "Сургутнефтегаз", "Новатэк", "Норникель", "Полюс Золото",'Спартака Ремонт'
]+company_names



def detect_nationality_from_company_names(contact_name: str) -> Nationality:
    for company in russian_banks_companies:
        if company.lower() in contact_name.lower():
            return Nationality.RUSSIAN
    return None

# Detect nationality based on professions and family relationships
professions = [
    'военный', 'аниматор', 'бухгалтер', 'адвокат', 'генерал', 'пожарный', 'директор',
    'пилот', 'официант', 'эколог', 'механик', 'судья', 'лейтенант', 'видеограф',
    'шахтер', 'фармацевт', 'менеджер', 'электрик', 'профессор', 'водитель',
    'сварщик', 'бармен', 'журналист', 'хирург', 'учёный', 'майор', 'провизор',
    'повар', 'агроном', 'ученый', 'инженер', 'учасковый', 'сантехник', 'лётчик',
    'рекрутер', 'врач', 'архитектор', 'солдат', 'логист', 'программист', 'строитель',
    'фотограф', 'заводской рабочий', 'бизнесмен', 'маркетолог', 'полковник',
    'учительница', 'доктор', 'полиция', 'юрист', 'медсестра', 'диспетчер',
    'дизайнер', 'музыкант', 'капитан', 'психолог', 'летчик', 'парикмахер', 'фельдшер'
    'Точит Цепь', 'Катридж'
]

family_relationships = [
    "мама", "папа", "брат", "сестра", "дядя", "тетя", 'Теть','Тёть','Тять',"бабушка",'Дять', "дедушка", "сын", "дочь", "кума",
    "кум", "крестный", "крестная", "батя", "супруга", "муж", "жена", "любимый", "любимая", "братишка",
    "сестрёнка", "батюшка", "матушка", "отец", "мать", "дядька", "тётя", "внучка", "внук", "свекровь",
    "свекр", "тесть", "теща", "зять", "невестка", "братан", "сеструха", "батяня", "бабуля", "дедуля"
]

def detect_nationality_from_professions_family(contact_name: str) -> Nationality:
    for word in professions + family_relationships:
        if word.lower() in contact_name.lower():
            return Nationality.RUSSIAN
    return None

# Detect nationality based on language-specific letters
def detect_nationality_from_letters(contact_name: str) -> Nationality:
    # Ukrainian-specific letters
    if re.search(r'[їієґІЇЄҐ]', contact_name):
        return Nationality.UKRAINIAN

    # Belarusian-specific letters
    if re.search(r'[ўЎ]', contact_name):
        return Nationality.BELARUSIAN

    # Georgian-specific letters
    if re.search(r'[\u10A0-\u10FF]', contact_name):  # Georgian script range
        return Nationality.GEORGIAN

    # Armenian-specific letters
    if re.search(r'[\u0530-\u058F]', contact_name):  # Armenian script range
        return Nationality.ARMENIAN

    # Kazakh-specific letters
    kazakh_letters = 'ӘәҒғҚқҢңӨөҰұҮүҺһІі'
    if re.search(f'[{kazakh_letters}]', contact_name):
        return Nationality.KAZAKH

    # Add rules for other languages as needed
    return None

# Use NamesParser to detect ethnicity
def detect_ethnicity_using_parser(last_name: str, first_name: str, middle_name: str) -> Nationality:
    try:
        result = parser.classify(last_name, first_name, middle_name)
        ethnics = result.get("ethnics", [])
        if "kaz" in ethnics or "tur" in ethnics:
            return Nationality.KAZAKH
        elif "geo" in ethnics:
            return Nationality.GEORGIAN
        elif "arm" in ethnics:
            return Nationality.ARMENIAN
        elif "aze" in ethnics:
            return Nationality.AZERBAIJANI
        elif "che" in ethnics:
            return Nationality.CHECHEN
        elif "dag" in ethnics:
            return Nationality.DAGESTANI
        elif "ing" in ethnics:
            return Nationality.INGUSH
        elif "slav" in ethnics:
            return Nationality.RUSSIAN
    except Exception as e:
        return Nationality.UNDETERMINED
    return Nationality.UNDETERMINED

# Detect nationality based on typical first names
typical_names = {

    Nationality.RUSSIAN: [
        # Original names
        "Александр", "Сергей", "Дмитрий", "Андрей", "Алексей", "Максим",
        "Евгений", "Иван",
        "Михаил", "Николай", "Владимир", "Артем", "Денис", "Павел", "Антон",
        "Виктор",
        "Роман", "Игорь", "Константин", "Олег", "Василий", "Кирилл", "Юрий",
        "Илья",
        "Петр", "Никита", "Григорий", "Борис", "Георгий", "Анатолий", "Захар",
        "Татьяна", "Елена", "Ольга", "Наталья", "Ирина", "Светлана", "Анна",
        "Екатерина",
        "Мария", "Юлия", "Анастасия", "Людмила", "Галина", "Валентина", "Нина",
        "Марина",
        "Надежда", "Любовь", "Вера", "Оксана", "Дарья", "Ксения", "Алина",
        "Евгения",
        "Арсений", "Даниил", "Егор", "Матвей", "Тимофей", "Станислав",
        "Леонид", "Валерий",
        "Виталий", "Вячеслав", "Глеб", "Артур", "Тимур", "Руслан", "Владислав",
        "Степан",
        "Федор", "Семен", "Геннадий", "Аркадий", "Лев", "Эдуард", "Валентин",
        "Вадим",
        "Софья", "Полина", "Маргарита", "Лариса", "Алла", "Инна", "Яна",
        "Кристина",
        "Виктория", "Лидия", "Елизавета", "Диана", "Карина", "Жанна", "Зоя",
        "Тамара",
        "Алиса", "Варвара", "Евдокия", "Зинаида", "Клавдия", "Раиса", "Ульяна",
        "Эмма","Виталя",
        # Diminutive and slang forms
        "Саша", "Дима", "Миша", "Костя", "Коля", "Ваня", "Паша", "Женя",
        "Леша", "Андрюша",
        "Вова", "Захарка", "Ксюша", "Ксюха", "Маша", "Даша", "Наташа", "Катя",
        "Аня",
        "Оля", "Света", "Лена", "Настя", "Лиза", "Люба", "Вика", "Ника",
        "Сережа", "Жора",
        "Юля", "Гена", "Толик", "Тоха", "Макс", "Игорек", "Ярик", "Слава",
        "Витя",
        "Артемка", "Славик", "Женька", "Леха", "Гоша", "Стас", "Лева", "Лёва",
        "Левчик",
        "Миша", "Мишаня", "Мишка", "Артём", "Дениска", "Антоха", "Тёма","Данилл","Данил","Вован","Тема","Лëля","Арина"
    ],

    Nationality.UKRAINIAN:[
    "Олександр", "Сергій", "Андрій", "Володимир", "Дмитро", "Іван", "Микола", "Михайло",
    "Петро", "Василь", "Віктор", "Олег", "Юрій", "Максим", "Ярослав", "Євген", "Тарас",
    "Богдан", "Роман", "Анатолій", "Валерій", "Григорій", "Денис", "Павло", "Руслан",
    "Степан", "Ігор", "Леонід", "Артем", "Віталій", "Олексій", "Костянтин", "Антон",
    "Вадим", "Станіслав", "Геннадій", "Борис", "Владислав", "Валентин", "Артур",
    "Ольга", "Тетяна", "Наталія", "Ірина", "Світлана", "Марія", "Катерина", "Анна",
    "Юлія", "Людмила", "Оксана", "Галина", "Валентина", "Лариса", "Надія", "Вікторія",
    "Любов", "Олена", "Лідія", "Алла", "Інна", "Софія", "Дарина", "Христина",
    "Олександра", "Марина", "Євгенія", "Зоя", "Жанна", "Алла", "Поліна", "Маргарита",
    "Данило", "Назар", "Остап", "Матвій", "Захар", "Тимофій", "Арсен", "Гліб",
    "Кирило", "Федір", "Семен", "Георгій", "Едуард", "Марк", "Ростислав", "Святослав",
    "Анастасія", "Вероніка", "Діана", "Аліна", "Яна", "Карина", "Ангеліна", "Олеся",
    "Мирослава", "Лілія", "Ніна", "Тамара", "Раїса", "Зінаїда", "Алла", "Уляна",
    "Божена", "Злата", "Орися", "Соломія", "Леся", "Роксолана", "Богдана", "Емма"
    ],



    Nationality.GEORGIAN: [
        "გიორგი", "Георгий", "ნინო", "Нино", "თამარ", "Тамара", "ლაშა", "Лаша",
        "ლევან", "Леван", "ზურაბ", "Зураб", "მიხეილ", "Михаил", "დავით", "Давид",
        "ირაკლი", "Ираклий", "ბესო", "Бесо", "მარიამ", "Мариам", "ნატო", "Нато",
        "თეონა", "Теона", "შოთა", "Шота", "ეკა", "Эка", "გუგა", "Гуга",
        "ელენე", "Элене", "კახა", "Каха", "თემურ", "Теймур", "ზვიად", "Звиад"
    ],
    Nationality.ARMENIAN: [
        "Արմեն", "Армен", "Տիգրան", "Тигран", "Նարեկ", "Нарек", "Հրանտ",
        "Грант", "Գայանե", "Гаянэ", "Անահիտ", "Анахит", "Արա", "Ара", "Վարդան",
        "Вардан", "Սերժ", "Серж", "Կարեն", "Карен", "Հակոբ", "Акоб", "Արտյոմ", "Артём",
        "Սոֆիա", "София", "Մարիա", "Мария", "Լեւոն", "Левон", "Մանե", "Мане",
        "Անուշ", "Ануш", "Արման", "Арман", "Գոռ", "Гор", "Հայկ", "Айк"
    ],
    Nationality.AZERBAIJANI: [
        "Əli", "Али", "Məmməd", "Мамед", "Murad", "Мурад", "Leyla", "Лейла",
        "Rəşad", "Рашад", "Nigar", "Нигар", "Əfqan", "Афган", "Aysel", "Айсель",
        "Zaur", "Заур", "Elvin", "Эльвин", "Gülnarə", "Гюльнара", "Kamran", "Камран",
        "Cavid", "Джавид", "Sevda", "Севда", "Eldar", "Эльдар", "Xanım", "Ханым",
        "Səbinə", "Сабина", "Fərid", "Фарид", "Zeynəb", "Зейнаб", "Fuad", "Фуад"
    ],
    Nationality.CHECHEN: [
        "Ахмад", "Ахмат", "Рамзан", "Зелимхан", "Зелим", "Мовлади", "Ислам",
        "Шамиль", "Адам", "Магомед", "Мовсар", "Лема"
    ],
    Nationality.DAGESTANI: [
        "Магомед", "Шамиль", "Абдулла", "Расул", "Мурад", "Гаджи", "Рашид",
        "Абдул", "Усман", "Хабиб", "Гамзат"
    ],
    Nationality.INGUSH: [
        "Юнус-Бек", "Мурат", "Магомед", "Муса", "Али", "Беслан", "Иса",
        "Магомед-Бек"
    ],
    Nationality.UZBEK: [
        "Акром", "Улуғбек", "Беҳзод", "Жамшид", "Алишер", "Темур", "Бобур",
        "Ислом", "Мирзо", "Саидакрам", "Шавкат", "Шухрат", "Шерзод", "Азиз",
        "Акмал", "Фаррух"
    ],
    Nationality.KAZAKH: [
        "Асем", "Канат", "Нурсултан", "Бакыт", "Жанна", "Айгерим", "Данияр",
        "Алмаз", "Айсулу", "Ержан", "Багдат", "Гульжан", "Мадина", "Серик",
        "Алия", "Бахыт", "Жанар"
    ],

    Nationality.TATAR: [
        "Ринат", "Фарит", "Ильдар", "Рамиль", "Рушан", "Гульнара", "Марат", "Рафис","Дамир", "Damir"
    ]
}


typical_names = {nationality: generate_transliterated_names_flatten(names) for nationality, names in typical_names.items()}



# Suffixes for patronymics
patronymic_suffixes = {
    Nationality.RUSSIAN: ["ович", "евич", "овна", "евна"],
    Nationality.UKRAINIAN: ["ович", "евич", "овна", "евна", "івич", "іївна"],
    Nationality.BELARUSIAN: ["ович", "евич", "овна", "евна", "овіч", "евіч"],
    Nationality.GEORGIAN: ["швили", "дзе"],
    Nationality.ARMENIAN: ["ян", "янц"],
    Nationality.AZERBAIJANI: ["оглы", "кызы"],
    Nationality.KAZAKH: ["улы", "кызы"],
    Nationality.UZBEK: ["зода", "заде", "zada"],
    Nationality.TAJIK: ["зода", "заде", "zada"],
}


# List of affectionate nicknames (in Russian)
affectionate_nicknames = [
    "Бусинка", "Зайчик", "Котик", "Малыш", "Малышка", "Ласточка", "Солнышко",
    "Зайка", "Пупсик", "Зайчонок", "Киска", "Масик", "Крошка", "Рыбка", "Котёнок",
    "Чапа", "Васька", "Сеня", "Тоша", "Петька", "Лёша"
]

def detect_nationality_from_affectionate_nickname(name: str) -> Nationality:
    # Check if the name contains any affectionate nickname
    for nickname in affectionate_nicknames:
        if nickname.lower() in name.lower():
            return Nationality.RUSSIAN
    return None



ranks = ["Рядовой", "Сержант", "Лейтенант", "Капитан", "Генерал", "Полковник"]

# Additional handling for diminutives and non-name parts
diminutive_to_formal = {
    "Саня": "Александр",  # Example: map diminutive to formal names
    "Саша": "Александр",
    "Ваня": "Иван",
    "Коля": "Николай"
}

# Add common non-name parts to ignore
non_name_parts = ["Ремонт", "Танк", "Авто", "Митсубиси", "Спартака", "Рядовой"]


# Initialize an empty list to store all Islamic names
islam_names = []

# Load the islamic names from a text file
with open("islam_names.txt", "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()
        if line and not line.startswith("---"):
            islam_names.append(line)

def is_non_name_part(part: str) -> bool:
    """Check if a part of the name is a non-name element like business or service."""
    return any(non_name.lower() in part.lower() for non_name in non_name_parts)

# Handle diminutives mapping to formal names
def normalize_diminutive(name: str) -> str:
    """Replace diminutive forms with their formal names."""
    return diminutive_to_formal.get(name, name)  # Return formal name if found, otherwise return as is




def detect_nationality_from_first_name(name_parts) -> Nationality:
    first_name = name_parts[0] if name_parts else ""

    # Loop through the typical names dictionary
    for nationality, names in typical_names.items():
        # Iterate over pairs of (Cyrillic, Latin) names
        for i in range(0, len(names), 2):
            cyrillic_name = names[i]
            latin_name = names[i + 1]
            # Check if the first name matches either the Cyrillic or the Latin version
            if first_name.lower() == cyrillic_name.lower() or first_name.lower() == latin_name.lower():
                return nationality

    return None


# Match nationality based on name parts
def match_nationality(name_parts):
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    middle_name = name_parts[1] if len(name_parts) == 3 else ""

    # Ethnic classification using NamesParser
    if len(name_parts) >= 2:
        ethnicity_nationality = detect_ethnicity_using_parser(last_name, first_name, middle_name)
        if ethnicity_nationality != Nationality.UNDETERMINED:
            return ethnicity_nationality

    # Check for nationality based on typical first names
    name_nationality = detect_nationality_from_first_name(name_parts)
    if name_nationality:
        return name_nationality

    # Use suffix matching if ethnicity and name are not determined
    matches = {nationality: 0 for nationality in suffixes}
    for part in name_parts:
        for nationality, suff in suffixes.items():
            if any(part.lower().endswith(suffix) for suffix in suff):
                matches[nationality] += 1

    selected_nationality = max(matches, key=matches.get)
    return selected_nationality if matches[selected_nationality] > 0 else Nationality.UNDETERMINED


# Function to remove emojis and special characters
def clean_name(name: str) -> str:
    # Use regex to remove all emojis and special characters
    name_cleaned = re.sub(r'[^\w\s]', '', name)  # Keep only word characters and spaces
    name_cleaned = re.sub(r'\d', '', name_cleaned)  # Optionally, remove numbers if needed
    return name_cleaned.strip()  # Remove leading and trailing whitespace

# Detect nationality based on name
# Updated nationality detection function
def detect_nationality_from_name(name: str) -> Nationality:
    # Step 1: Check for flag emoji indicating nationality
    flag_nationality = detect_nationality_from_flag(name)
    if flag_nationality:
        return flag_nationality

    # Step 2: Clean the name by removing non-flag emojis and special characters
    cleaned_name = clean_name(name)

    # Split the cleaned name into parts
    name_parts = cleaned_name.split()

    # Step 3: Normalize diminutives to formal names
    name_parts = [normalize_diminutive(part) for part in name_parts]

    # Step 4: Filter out non-name parts (like "Ремонт", "Танк", etc.)
    name_parts = [part for part in name_parts if not is_non_name_part(part)]

    # Step 5: Handle first name detection (e.g., "Damir")
    first_name_nationality = detect_nationality_from_first_name(name_parts)
    if first_name_nationality:
        return first_name_nationality

    # Step Check for affectionate nickname
    affectionate_nickname_nationality = detect_nationality_from_affectionate_nickname(
        cleaned_name)
    if affectionate_nickname_nationality:
        return affectionate_nickname_nationality

    # Step 6: Check for vulgar words in the cleaned name
    vulgar_nationality = detect_vulgar_words(cleaned_name)
    if vulgar_nationality:
        return vulgar_nationality

    # Step 7: Check for special '💦' marker for specific classification
    if '💦' in name:
        return Nationality.SHALAVY

    # Step 8: Check for geo-related data in the cleaned name (e.g., locations, countries)
    geo_nationality = detect_nationality_from_geo(cleaned_name)
    if geo_nationality:
        return geo_nationality

    # Step 9: Check for company names indicating nationality
    company_nationality = detect_nationality_from_company_names(cleaned_name)
    if company_nationality:
        return company_nationality

    # Step 10: Check for profession or family relationships
    prof_rel_nationality = detect_nationality_from_professions_family(cleaned_name)
    if prof_rel_nationality:
        # If family relationship is found, still check if first name overrides it
        if first_name_nationality:
            return first_name_nationality
        return prof_rel_nationality

    # Step 11: Check for patronymic-based detection (in the case of full names)
    if len(name_parts) == 3:
        patronymic = name_parts[2]
        patronymic_nationality = detect_nationality_from_patronymic(patronymic)
        if patronymic_nationality:
            return patronymic_nationality

    # Step 12: Check for language-specific letters indicating nationality
    letter_nationality = detect_nationality_from_letters(cleaned_name)
    if letter_nationality:
        return letter_nationality

    # Step 13: Use existing surname detection logic to match the nationality
    return match_nationality(cleaned_name.split())




# Function to extract country code from phone number
def extract_country_code(phone_number, country_codes):
    # Remove '+' or '00' from the beginning
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]
    elif phone_number.startswith('00'):
        phone_number = phone_number[2:]
    # Try to find the longest matching country code
    for code in country_codes:
        if phone_number.startswith(code):
            return code, phone_number[len(code):]
    # If no country code found, return None
    return None, phone_number

# Function to read mobile patterns from CSV file
def read_patterns_from_csv(csv_filename):
    pattern_regions = []
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        for row in reader:
            if len(row) != 4:
                continue  # Skip rows that don't have exactly 4 columns
            code, number_pattern, operator, region = row
            code = code.strip()
            number_pattern = number_pattern.strip()
            operator = operator.strip()
            region = region.strip()

            # Remove 'code-' prefix from number_pattern if present
            if number_pattern.startswith(code + '-'):
                number_pattern = number_pattern[len(code) + 1:]
            # Combine code and number_pattern to get full pattern
            full_pattern = code + number_pattern

            # Replace 'x' with '\d' in regex
            regex_pattern = '^' + full_pattern.replace('x', r'\d') + '$'

            # Compile the regex
            regex = re.compile(regex_pattern)

            # Append to the list
            pattern_regions.append((regex, region))
    return pattern_regions

# Function to read CIS landline and mobile patterns from CSV file
def read_patterns_cis(csv_filename):
    patterns_cis = []
    country_codes_set = set()
    country_code_to_name = {}
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            if len(row) != 4:
                continue  # Skip invalid rows
            country, country_code, city_code, city = row
            country = country.strip()
            country_code = country_code.strip()
            city_code = city_code.strip()
            city = city.strip()
            country_codes_set.add(country_code)
            country_code_to_name[country_code] = country  # Map country code to country name
            # Construct a pattern for the remaining number after country code
            pattern = '^' + city_code + r'\d+$'  # Accept any number of digits after city code
            regex = re.compile(pattern)
            patterns_cis.append((regex, country_code, city))
    # Build ordered list of country codes by length descending
    country_codes = sorted(country_codes_set, key=lambda x: -len(x))
    return patterns_cis, country_codes, country_code_to_name

# Function to read contacts from alldata.txt
def read_contacts(filename, limit=None):
    contacts = []
    with open(filename, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                break
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            parts = line.split(',')
            if len(parts) >= 3:
                phone_number = parts[0].strip().strip('"')
                contact_name = parts[2].strip().strip('"')
                contacts.append((phone_number, contact_name))
    return contacts

# Function to determine the region and nationality of a contact
def process_contact(phone_number, contact_name, pattern_regions, patterns_cis, country_codes, country_code_to_name):
    original_phone_number = phone_number
    if not phone_number or phone_number.lower() == 'none':
        region = "No region found"
        country = "Неизвестная страна"
    else:
        phone_number = phone_number.strip()
        # Remove any '+' or '00' from the beginning
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        elif phone_number.startswith('00'):
            phone_number = phone_number[2:]
        # Handling Kazakhstan numbers
        if phone_number.startswith('77'):
            # Kazakhstan mobile numbers
            region = "Казахстан"
            country = "Казахстан"
        elif phone_number.startswith('7'):
            # Russian numbers
            mobile_number = phone_number[1:]  # Remove '7'
            region_found = False
            for regex, region_match in pattern_regions:
                if regex.match(mobile_number):
                    region = f"Россия, {region_match}"
                    region_found = True
                    break
            if not region_found:
                region = "Россия, Неизвестный регион"
            country = "Россия"
        else:
            # Try to extract country code
            country_code, remaining_number = extract_country_code(phone_number, country_codes)
            if country_code:
                # Try to match the remaining number with patterns_cis
                region = "No region found"
                for regex, pattern_country_code, city in patterns_cis:
                    if country_code == pattern_country_code and regex.match(remaining_number):
                        country = country_code_to_name.get(country_code, "Unknown country")
                        region = f"{country}, {city}"
                        break
                if region == "No region found":
                    country = country_code_to_name.get(country_code, "Unknown country")
                    region = f"{country}, Неизвестный город"
            else:
                region = "No region found"
                country = "Неизвестная страна"

    # Detect nationality from contact name
    if contact_name:
        nationality = detect_nationality_from_name(contact_name)
    else:
        nationality = Nationality.UNDETERMINED

    # If nationality is still undetermined, and country is known, set nationality based on country
    if nationality == Nationality.UNDETERMINED and country in country_to_nationality:
        nationality = country_to_nationality[country]

    return {
        "phone_number": original_phone_number,
        "contact_name": contact_name,
        "region": region,
        "nationality": nationality.value if isinstance(nationality, Nationality) else nationality
    }

def main():
    # Read mobile patterns from mobile_codes.csv
    pattern_regions = read_patterns_from_csv('mobile_codes.csv')

    # Read CIS landline and mobile patterns from city_codes_cis.csv
    patterns_cis, country_codes, country_code_to_name = read_patterns_cis('city_codes_cis.csv')

    # Read contacts from alldata.txt (processing top entries)
    contacts = read_contacts('alldata.txt', limit=1000)

    # Open a CSV file to save the results
    with open('output_results.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Phone Number', 'Region', 'contact_name', 'Nationality'])

        # Process each contact and save the region and nationality
        for phone_number, contact_name in contacts:
            result = process_contact(phone_number, contact_name, pattern_regions, patterns_cis, country_codes, country_code_to_name)
            output_line = [result['phone_number'], result['region'], result['contact_name'], result['nationality']]
            writer.writerow(output_line)

if __name__ == '__main__':
    main()
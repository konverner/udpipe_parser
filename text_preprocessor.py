import re
from morpholog import Morpholog
from nltk import word_tokenize
from separatrice import Separatrice
#nltk.download('punkt')

quest_words = ['кто','что','кого', 'чего','кому', 'чему','кого','как','что','кем', 'чем','где','откуда','отчего','почему','докуда','каков','какой','куда']
abbrev_dict = {'абл': 'аблатив', 'академ': 'академический отпуск', 'абс': 'абсолютный', 'абх': 'абхазский', 'авар': 'аварский', 'авг': 'август', 'австр': 'австрийский', 'австрал': 'австралийский', 'авт': 'автономный', 'адж': 'аджарский', 'адм': 'административный', 'азерб': 'азербайджанский', 'азиат': 'азиатский', 'акк': 'аккузатив', 'акц': 'акционерный', 'алб': 'албанский', 'алг': 'алгебраический', 'алж': 'алжирский', 'алт': 'алтайский', 'алф': 'алфавитный', 'альп': 'альпийский', 'ам': 'аттометр', 'а/м': 'автомашина', 'амер': 'американский', 'анат': 'анатомический', 'англ': 'английский', 'ангол': 'ангольский', 'антич': 'античный', 'а/о': 'акционерное общество', 'ап': 'апостол; апп апостолы', 'а/п': 'аэропорт', 'апр': 'апрель, апрельский', 'араб': 'арабский', 'арам': 'арамейский', 'аргент': 'аргентинский', 'арифм': 'арифметика, арифметический', 'арм': 'армянский', 'арх': 'архитектурный', 'а/т': 'автотранспорт', 'атм': 'атмосферный', 'афг': 'афганский', 'афр': 'африканский', 'б': 'байт', 'быв': 'бывший', 'балк': 'балкарский', 'балт': 'балтийский', 'башк': 'башкирский', 'бельг': 'бельгийский', 'бзн': 'бензин', 'биогр': 'биографический', 'биол': 'биологический', 'б-ка': 'библиотека', 'болг': 'болгарский', 'болив': 'боливийский', 'больн': 'больной', 'бот': 'ботанический', 'браз': 'бразильский', 'брет': 'бретонский', 'брит': 'британский', 'б/у': 'бывший в употреблении', 'буд': 'будущее время', 'бюдж': 'бюджетный', 'вдхр': 'водохранилище', 'венг': 'венгерский', 'вет': 'ветеринарный', 'визант': 'византийский', 'вин': 'винительный падеж', 'вкз': 'вокзал', 'вкл': 'включительно', 'в/с': 'высший сорт', 'вс': 'воскресенье', 'выкл': 'выключение', 'г': 'грамм', 'га': 'гектар', 'Гб': 'гигабайт', 'Гбайт/с': 'гигабайт в секунду', 'Гбит': 'гигабит', 'Гбит/с': 'гигабит в секунду', 'гг': 'годы', 'геогр': 'географический', 'геод': 'геодезический', 'геол': 'геологический', 'геом': 'геометрический', 'герм': 'германский', 'груз': 'грузинский', 'даг': 'дагестанский', 'дат': 'датский', 'дБ': 'децибел', 'действ': 'действительный', 'дек': 'декабрь', 'дер': 'деревня', 'дес': 'л десертная ложка', 'д-з': 'диагноз', 'диал': 'диалектный', 'диам': 'диаметр', 'див': 'дивизия', 'диз': 'дизель', 'дисс': 'диссертация', 'дист': 'дистиллированный', 'дифф': 'дифференциальный', 'д/к': 'Дворец культуры', 'дкг': 'декаграмм', 'дкл': 'декалитр', 'дкм': 'декаметр', 'дл': 'длина', 'дм': 'дециметр', 'долл': 'доллар', 'доп': 'дополнительный', 'доц': 'доцент', 'драм': 'драматический', 'д/с': 'детский сад', 'д/ф': 'документальный фильм', 'евр': 'европейский', 'егип': 'египетский', 'ед': 'единица', 'ежедн': 'ежедневный', 'ежемес': 'ежемесячный', 'еженед': 'еженедельный', 'зав': 'заведующий', 'з/о': 'заочное отделение', 'им': 'имени', 'инд': 'индийский', 'индонез': 'индонезийский', 'инж': 'инженерный', 'иностр': 'иностранный', 'инстр': 'инструментальный', 'инт': 'интегральный', 'ирак': 'иракский', 'иран': 'иранский', 'ирл': 'ирландский', 'ирон': 'иронический', 'иск-во': 'искусство', 'ист': 'исторический', 'исх': 'исходный', 'итал': 'итальянский', 'кил': 'кило', 'кан': 'канадский', 'кг': 'килограмм', 'км/с': 'километр в секунду', 'км/ч': 'километр в час', 'книжн': 'книжное', 'кооп': 'кооперативный', 'кор': 'корейский', 'ко эф ф': 'ко эф фициент', 'к-рый': 'который', 'к/ст': 'киностудия', 'кт': 'килотонна', 'к/т': 'кинотеатр', 'куб': 'кубический', 'к/ф': 'кинофильм', 'кэВ': 'килоэлектронвольт', 'л': 'литр', 'лтш': 'латышский', 'лат': 'латинский', 'мат': 'материальный', 'м': 'метр', 'междунар': 'международный', 'мекс': 'мексиканский', 'мес': 'месяц', 'мех': 'механический', 'мин': 'минимальный', 'мин-во': 'министерство', 'мк': 'микрон', 'мкА': 'микроампер', 'мл': 'миллилитр', 'мм': 'миллиметр', 'наб': 'набережная', 'наг': 'нагорье', 'наз': 'называемый', 'назв': 'название', 'наиб': 'наибольший', 'наим': 'наименьший', 'нар': 'народный', 'нас': 'население', 'наст': 'настоящий', 'науч': 'научный', 'нац': 'национальный', 'негр': 'негритянский', 'нед': 'неделя', 'неизв': 'неизвестный', 'нем': 'немецкий', 'неодуш': 'неодушевленный', 'неперех': 'непереходный', 'нер-во': 'неравенство', 'неск': 'несколько', 'неуд': 'неудовлетворительно', 'нидерл': 'нидерландский', 'нов': 'новый', 'новогреч': 'новогреческий', 'новозел': 'новозеландский', 'норв': 'норвежский', 'норм': 'нормальный', 'нояб': 'ноябрь', 'одуш': 'одушевленный', 'отл': 'отлично', 'офиц': 'официальный', 'оч': 'очень', 'первонач': 'первоначальный', 'перс': 'персидский', 'пищ': 'пищевой', 'пк': 'пиксел', 'пн': 'понедельник', 'полит': 'политика, политический', 'правосл': 'православный', 'прич': 'причастие', 'просп': 'проспект', 'прост': 'просторечный', 'проф': 'профессиональный', 'прош': 'прошедшее время', 'психол': 'психологический', 'пт': 'пятница', 'руб': 'рубль', 'рад': 'радиан', 'т': 'тонна', 'ред': 'редакционный', 'реж': 'режиссер', 'религ': 'религиозный', 'рем': 'ремонтный', 'респ': 'республиканский', 'р-н': 'район', 'росс': 'российский', 'р-р': 'раствор', 'р/с': 'радиостанция', 'рукоп': 'рукопись, рукописный', 'рум': 'румынский', 'рус': 'русский', 'сиб': 'сибирский', 'соц': 'социальный', 'симм': 'симметричный', 'синт': 'синтетический', 'сир': 'сирийский', 'сказ': 'сказуемое', 'сканд': 'скандинавский', 'СПб': 'Санкт-тербург', 'спец': 'специальный', 'спорт': 'спортивный', 'страд': 'страдательный', 'стр-во': 'строительство', 'сут': 'сутки', 'суфф': 'суффикс', 'сущ': 'существительное', 'телеф': 'телефонный', 'теор': 'теоретический', 'техн': 'технический', 'тир': 'тираж', 'т.к': 'так как', 'т.е': 'то есть', 'торг': 'торговый', 'трансп': 'транспортный', 'триг': 'тригонометрический', 'узб': 'узбекский', 'ул': 'улица', 'февр': 'февраль', 'филол': 'филологический', 'филос': 'философский', 'фин': 'финансовый', 'финл': 'финляндский', 'фио': 'фамилия, имя, отчество', 'ф-ла': 'формула', 'флам': 'фламандский', 'хар-ка': 'характеристика', 'хоз-во': 'хозяйство', 'х/ф': 'художественный фильм', 'центр': 'центральный', 'чел': 'человек', 'ч/б': 'черно-белый', 'чт': 'четверг', 'чув': 'чувашский', 'экон': 'экономический', 'тыс': 'тысяч'}
tags = ['Geox', 'Name','Surn','Trad','Orgn','Patr']
punct = ' !"#$%&()*+,-./:;<=>?@^_`{|}~'

# class for text preprocessing : replace word abbreviations, remove stop words and 
# some given words in replace_words, make spelling correction 
class TextPreProcessor:
  def __init__(self, propn_nouns=[], abbrev_dict=abbrev_dict):
    self.abbrev_dict = abbrev_dict
    self.propn_nouns = propn_nouns
    self.splitter = Separatrice()
    self.morph = Morpholog()

  def replace(self,text):
    for propn_noun in self.propn_nouns:
      patterns = [propn_noun.upper(), propn_noun.capitalize(), propn_noun]
      for pattern in patterns:
        if '\\' in propn_noun:
          propn_noun = list(propn_noun)
          propn_noun.remove('\\')
          propn_noun = ''.join(propn_noun)
        text = re.sub('^'+pattern + ' ', " '" + propn_noun+"' " ,text)
        text = re.sub(' ' +pattern + '$', " '" + propn_noun+"'" ,text)
        text = re.sub(' ' + pattern + '[ |!|,|.|?|:|;]', " '" + propn_noun+"' " ,text)

    for key in self.abbrev_dict.keys():
      abbrev = self.abbrev_dict[key]
      text = re.sub('^'+key.upper() + ' ',abbrev.capitalize()+" " ,text)
      text = re.sub('^'+key.capitalize() + ' ',abbrev.capitalize()+" " ,text)
      text = re.sub('^'+key + ' ', abbrev + ' ',text)
      text = re.sub(' ' + key + '$',abbrev + ' ',text)
      text = re.sub(' ' + key + '[ |!|,|.|?|:|;]', " " + abbrev+" " ,text)

    return text


  def run(self,text):

    text = text[0].upper() + text[1:]
    text = ' '.join(text.split())

    if 'ё' in text:
      text = text.replace('ё','е')

    text = re.sub(r'/',' или ', text)

  
    temp = ' '.join([t.capitalize().strip(punct) + ". " for t in self.splitter.into_clauses(text)])
    temp = word_tokenize(temp)
    for i in range(len(temp)):
      if temp[i] in punct and i+1 < len(temp):
        j = 1
        while temp[i+j] in punct:
          temp[i+j] = ''
          j += 1
        temp[i+j] = temp[i+j].capitalize()
      for tag in tags:
        if tag in self.morph.parse(temp[i])[0].tag:
          temp[i] = temp[i].capitalize()

    result = []
    for w in temp:
      if re.findall(r'\d{5}|\d{6}',w) != []:
        w = "'" + w + "'"
      result.append(w)

    result = ' '.join(result)
    result = self.replace(result).strip()
    if result[-1] not in ['.','?','!']:
      result = result + '.'
    return result

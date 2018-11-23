# coding: utf-8
import sys, os, time, math
from datetime import datetime

import re
import random
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import webbrowser



#Имя файла с результатами
outFileName = 'out.csv'

#Колонки таблицы
columns = ['time', 'type', 'position', 'keyword', 'header', 'text', 'path', 'sitelinks']

#Как скрипт будет представляется серверу Яндекса (брать из браузера)
userAgents =  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'

# Время задержки между запросами в сек
sleepTime = 1


def getPage(key, region):
    '''
    Получает первую страницу выдачи яндекса по зананому запросу key в регионе region
    :param key - ключевое слово:
    :param region - регион:
    :return Объект requests :
    '''
    s = requests.Session()
    response = requests.get('https://yandex.ru/search/?text='+key+'&lr='+str(region),
                            headers = {'User-Agent': userAgents},
                            stream = True,
                            cookies=s.cookies)
    return response


def parseInsideSnippet (ad):
    #Селекторы
    position_attr = 'data-cid'
    label_Selector = '.organic__subtitle .label'
    headline_Selector = 'h2 a'
    text_Selector = '.text-container'
    text_seo_short_Selector = '.extended-text__short'
    sitelinks_Selector = '.sitelinks a'
    path_Selector = '.path'

    # Начальные значения
    res = {}

    res['type'] = 'seo'
    res['position'] = ''
    res['header']=''
    res['text'] = ''
    res['path']=''
    res['sitelinks'] = ''

    # Тип сниппета
    try:
        res['type'] = ad.select_one(label_Selector).get_text()
    except:
        res['type'] = 'seo'


    # Позиция сниппета
    try:
        res['position'] = int(ad[position_attr]) + 1
    except:
        res['position'] = ''

    # Получение заголовка
    res['header'] = ad.select_one( headline_Selector ).get_text()

    # Получение текста сниппета в зависимости от типа блока
    try:

        res['text'] =  re.sub('Читать\sещё.*', '', ad.select_one(text_Selector).get_text())

        #if res['type']=="реклама":

        #else:

           # res['text'] =  + ad.select_one(text_seo_short_Selector).get_text()

    except:
        res['text'] = ''

    # Текст быстрых ссылок
    try:
        if res['type'] == "реклама":
            res['sitelinks'] = ad.select(sitelinks_Selector)
            res['sitelinks'] = '||'.join(map(BeautifulSoup.get_text, res['sitelinks']))
    except:
        res['sitelinks']=''

    # Ссылка
    try:
        res['path'] = ad.select_one(path_Selector).get_text()
    except:
        res['path'] = ''
    return res

def parseAds (snippets, key):
    global columns
    df = pd.DataFrame(columns=columns)
    for snippet in snippets:
        snippetList = parseInsideSnippet(snippet)
        snippetList.update({ 'time':datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S") })
        snippetList.update({ 'keyword':key})
        df = df.append (pd.Series(snippetList), ignore_index=True)
    return df
                
def parse(key, region):
    '''
    Получает и парсит содержимое выдачи яндекса
    :param key:         Ключевое слова
    :param region:      Номер региона
    :return Pandas dataFrame:
    '''
    #CSS селектор сниппета
    snippetsSelector = 'li.serp-item'

    tree = getPage(key, region)
    soup = BeautifulSoup(tree.content, "lxml")
    snippets = soup.select(snippetsSelector)

    if (len(snippets)!=0):
        print ('Найдено: %s сниппета' % len(snippets))
        return parseAds(snippets, key)
    else:
        captcha=soup.select_one('img.form__captcha')
        if(captcha):
            form = soup.select_one('form.form__inner')
            form['action']='https://yandex.ru'+form['action']
            file = open('error.html', 'wb')
            file.write(soup.encode('utf-8'))
            file.close()
            print ('Запрос капчи, сделайте запрос позднее')
            webbrowser.open('file://'+os.path.realpath('error.html'))

        print ('ERROR - not finded snippets')
        return None
                


def main():
    global outFileName
    #Проверяем наличие аргументов при выхове
    if len (sys.argv) < 3:
        print ("Пример вызова: getSnippents.py input.txt regionId")
    else:
        if os.path.isfile(sys.argv[1]):
            region = sys.argv[2]
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                #Для каждого ключа парсим выдачу
                for line in f.readlines():
                    print("Запрос: ", line, " Регион: ", region)
                    key=line[:line.find('-')]
                    df = parse(key, region)
                    if os.path.exists(outFileName):
                        headerFlag = False
                    else:
                        headerFlag = True
                    df.to_csv(outFileName, sep='\t', encoding='utf-8', mode="a", header=headerFlag, index=False)
                    time.sleep(sleepTime)
        else:
            print ('Файл не найден')

# def main2():
#
#     global outFileName
#     key = 'реклама в гугл'
#     df =  parse(key, 36 )
#     if os.path.exists(outFileName):
#         headerFlag = False
#     else:
#         headerFlag = True
#     df.to_excel(outFileName,   header=headerFlag, index=False)



main()
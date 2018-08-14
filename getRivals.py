# coding: utf-8
import sys, os, time, math
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
headers = {'user-agent': 'my-app/0.0.1'}
pd.describe_option('display')
df = pd.DataFrame(columns=['keyword', 'header','path', 'sitelinks',
                           'text', 'refinement', 'phone', 'worktime', 'city'])
key = 'натяжные потолки'
region = 36

def getAds(key, region, page=0):
    response = requests.get('https://yandex.ru/search/ads?text='+key+'&lr='+str(region)+'&p='+str(page),
                            headers = headers,
                            stream = True)
    return response


def parseAd (ad):
    res = {}
    serpline =''
    res['header'] = ad.h2.get_text()
    res['text'] = ad.find('div', class_='organic__text').get_text()
    res['sitelinks'] = ad.select('.sitelinks a')
    res['sitelinks'] = ' '.join(map(BeautifulSoup.get_text, res['sitelinks']))
    try:
        res['path'] = ad.select('.path a.link')[0].get_text()
    except:
        res['path'] = ''
    serpline = ad.select('.serp-meta2 .serp-meta2__line')
        
    if len(serpline)==1:
        res['refinement'] = ''
        try:
            res['phone'] = serpline[0].select('.serp-meta2__item')[1].get_text()
        except:
            res['phone'] = ''
        try:    
            res['time'] = serpline[0].select('.serp-meta2__item')[2].get_text()
        except:
            res['time'] = ''
        try:    
            res['city'] = serpline[0].select('.serp-meta2__item')[3].get_text()    
        except:
            res['city'] = ''
    elif len(serpline)==2:
      
        try:
            res['phone'] = serpline[1].select('.serp-meta2__item')[1].get_text()
        except:
            res['phone'] = ''
        try:    
            res['time'] = serpline[1].select('.serp-meta2__item')[2].get_text()
        except:
            res['time'] = ''
        try:    
            res['city'] = serpline[1].select('.serp-meta2__item')[3].get_text()    
        except:
            res['city'] = ''
        try:
            res['refinement'] = serpline[0].select('.serp-meta2__item')
            res['refinement'] = '||'.join(map(BeautifulSoup.get_text, res['refinement']))    
        except:
            res['refinement'] = ''
    
        
    return res

def parseAds (ads, key):
    global df
    for ad in ads:
        parsad = parseAd(ad)
        parsad.update({'keyword':key})
        df = df.append (pd.Series(parsad), ignore_index=True)

                
def parse(key, region):
    global df
    
    tree = getAds(key, region)
    soup = BeautifulSoup(tree.content, 'html.parser')
    try:
        totalAds = soup.find('div', class_='serp-adv__found').string
        totalAds = totalAds.split(' ')[1]
    except:
        print('Строка не найдена')
        totalAds = 0

    print (key, '- total ads: ', totalAds)
    totalAds = int(totalAds)
    if totalAds==0:
        return 0
    else:    
        ads = soup.select('li.serp-adv-item > div')
        print ('ads: ')
        print (len(ads))
        parseAds(ads, key)
        if totalAds>10:
            pages = math.ceil(totalAds/10)+1
            for page in range(1, pages):
                tree = getAds(key, region, page)
                soup = BeautifulSoup(tree.content, 'html.parser')
                ads = soup.select('li.serp-adv-item > div')
                parseAds(ads, key)
        return totalAds
                
      




def main():
    if len (sys.argv) < 3:
        print ("Пример вызова: getRivals.py input.txt regionId")
    else:
        if os.path.isfile(sys.argv[1]):
            outFileName = sys.argv[1].split('.')[0]+'.out.csv'
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    print(line)
                    key=line[:line.find('-')]
                    print(key+";", parse(key, sys.argv[2] ))
            df.to_csv(outFileName, sep='\t', encoding='utf-8')  
            print ('файл %s создан' % outFileName)
        else:
            print ('Файл не найден')
main()

import requests, re, json, sys
from bs4 import BeautifulSoup
import pandas as pd
import time


def progress_bar(name,size):
    
    start_time = time.time()
    def update_progress(new_val):
        progress = float(new_val / size)
        barLength = 40 
        status = ""
        if not isinstance(progress, float):
            progress = 0
            status = "error: progress var must be float\r\n"
        if progress < 0:
            progress = 0
            status = "Halt...\r\n"
        if progress >= 1:
            progress = 1
            status = "Done...\r\n"
        block = int(round(barLength*progress))
        progress = "%0.2f" % (progress*100)
        elapsed_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))
        text = "\r{3}: [{0}] {1}% {2} {4}".format( "#"*block + "-"*(barLength-block), progress, status, name, elapsed_time)
        sys.stdout.write(text)
        sys.stdout.flush()
    return update_progress

class OfferReader():
    def __init__(self,city,wd):
        self.city = city
        self.wd = wd
        self.links = []
        self.main_list = {'Cena ':'price', 
                         'Powierzchnia ':'surface', 
                         'Liczba pokoi ':'rooms',
                         'Piętro ':'floor_num'}


        self.sublist = dict() 
        self.sublist['Rodzaj zabudowy:'] = {'NAME': 'building_type',
                                          'blok':'block',
                                          'kamienica':'tenement',
                                          'dom wolnostojący':'house',
                                          'plomba':'infill',
                                          'szeregowiec':'row_house',
                                          'apartamentowiec':'apartment',
                                          'loft':'loft'}
        
        self.sublist['Materiał budynku:'] = {'NAME':'building_material',
                                           'drewno' : 'wood' ,
                                           'pustak' : 'breezeblock',
                                           'keramzyt' :  'hydroton',
                                           'wielka płyta' : 'concrete_plate',
                                           'beton' : 'concrete', 
                                           'cegła' : 'brick', 
                                           'silikat' : 'silikat',
                                           'beton komórkowy' : 'aerated_concrete', 
                                           'żelbet' : 'reinforced_concrete',
                                           'inne' : 'other'}
                                  
        self.sublist['Forma własności:'] = {'NAME':'ownership',
                                           'spółdzielcze własnościowe' : 'cooperative_ownership',
                                           'spółdzielcze wł. z KW' : 'cooperative_ownership_with_mortgage_register',
                                           'pełna własność' : 'full_ownership',
                                           'udział' : 'share'}
            
        self.sublist['Okna:'] = {'NAME': 'window',
                                  'plastikowe' : 'plastic',
                                  'drewniane' : 'wooden',
                                  'aluminiowe' : 'aluminium'}                  
        
        self.sublist['Ogrzewanie:'] = {'NAME':'heating',
                                     'miejskie' : 'urban',
                                     'gazowe' : 'gas',
                                     'elektryczne' : 'electrical',
                                     'inne' : 'other',
                                     'kotłownia' : 'boiler_room',
                                     'piece kaflowe' : 'tiled_stove'
                                     }  
                           
        self.sublist['Stan wykończenia:'] = {'NAME':'construction_status',
                                            'do zamieszkania' : 'ready_to_use',
                                            'do wykończenia' : 'to_completion',
                                            'do remontu' : 'to_renovation'
                                            }                     
        
        self.sublist['Rynek:'] = {'NAME': 'market',
                                 'pierwotny' : 'primary',
                                 'wtórny' : 'secondary'
                                 }
        
        self.sublist['Stan inwestycji:'] = {'NAME': 'status',
                                       'w budowie' : 'under construction',
                                       'ukończona' : 'finished'
                                      }
        
        self.sublist_other = {'Rok budowy:':'year_of_construction',
                             'Czynsz:':'rent',
                             'Dostępne od:':'available',
                             'Liczba kondygnacji:':'building_floors_num'}
            
        self.extras = {'balkon': 'extras_balcony', 
                      'dwupoziomowe': 'extras_two_storey',
                      'garaż/miejsce parkingowe': 'extras_garage',
                      'klimatyzacja': 'extras_air_conditioning',
                      'meble': 'extras_furniture',
                      'oddzielna kuchnia': 'extras_separate_kitchen',
                      'ogródek': 'extras_garden',
                      'piwnica': 'extras_basement',
                      'pom. użytkowe': 'extras_usable_room',
                      'taras': 'extras_terrace',
                      'tarasy': 'extras_terrace',
                      'winda': 'extras_lift',
                      'garaż': 'extras_garage',
                      'basen': 'extras_swimming_pool',
                      'domofon / wideofon': 'security_entryphone',
                      'drzwi / okna antywłamaniowe': 'security_anti_burglary_door',
                      'monitoring / ochrona': 'security_monitoring',
                      'rolety antywłamaniowe': 'security_roller_shutters',
                      'system alarmowy': 'security_alarm',
                      'teren zamknięty': 'security_closed_area',
                      'ochrona': 'security_security',
                      'internet': 'media_internet',
                      'telefon': 'media_phone',
                      'telewizja kablowa': 'media_cable-television',
                      'kuchenka': 'equipment_stove',
                      'lodówka': 'equipment_fridge',
                      'piekarnik': 'equipment_oven',
                      'pralka': 'equipment_washing_machine',
                      'telewizor': 'equipment_tv',
                      'zmywarka': 'equipment_dishwasher'}   

    def prepareLinks(self, number_pages_to_scrap):
        pb = progress_bar('Reading links',number_pages_to_scrap)
        for i in range(1,number_pages_to_scrap+1): 
            r = requests.get('https://www.otodom.pl/sprzedaz/mieszkanie/' + self.city + '?page=' + str(i) ) 
            soup = BeautifulSoup(r.text,"lxml")
    
            for link in soup.find_all('a',href=True):
                tested_link = (str(link['href']))
                if tested_link.startswith("https://www.otodom.pl/oferta"):
                    pos = tested_link.find('#')
                    if pos > -1:
                        tested_link = tested_link[:pos]
                    self.links.append(tested_link)   
            pb(i)
        self.links = list(set(self.links))
        print('\nRead ', len(self.links), ' links')
                
    def getLinks(self):
        return self.links
                
    def setLinks(self, links):
        self.links = links
    
    def getDescription(self):
        pb = progress_bar('Reading descriptions',len(self.links))
        res = []
        for i,url in enumerate(self.links):
            d = {'Link':url}
            r = requests.get(url) 
            soup = BeautifulSoup(r.text,"lxml")
            for item in soup.find_all('div',{'itemprop': 'description'}):
                d['Desc'] = re.sub('<.*?>','',item.decode_contents()).replace('\n',' ').replace(';',' ').replace('  ',' ').lower()
            for item_list in soup.find_all('div',{'class': 'left'}):
                for item in item_list.find_all('p'):
                    if item.text.startswith('Nr oferty w Otodom: '):
                        d['Id'] = item.text.replace('Nr oferty w Otodom: ','')
            res.append(d)
            pb(i)
        df = pd.DataFrame(res)
        with open(self.wd + self.city + '_desc.csv', 'w', errors='ignore') as f:
            df.to_csv(f, header=True, na_rep='.', sep=';', encoding='utf-8', index=False)
        del df 
       
    def readLinks(self):
        pb = progress_bar('Reading offers',len(self.links))
        lst = []
        correct = 0
        error = 0
        for counter, link in enumerate(self.links): 
            pb(counter+1)            
            try:
                lst.append(self.readLink(link))
                correct = correct + 1
            except:
                error = error + 1

            if counter == 10:
                df = pd.DataFrame(lst)    
                with open(self.wd + self.city + '_raw.csv', 'w') as f:
                    df.to_csv(f,sep=';',header=True,na_rep='.',encoding='utf-8',index=False)
                del df
                lst = []
            elif counter % 500 == 0:
                df = pd.DataFrame(lst)  
                with open(self.wd + self.city + '_raw.csv', 'a') as f:
                    df.to_csv(f, header=False,na_rep='.', sep=';',encoding='utf-8',index=False)
                del df
                lst = []  

        df = pd.DataFrame(lst)  

        with open(self.wd + self.city + '_raw.csv', 'a') as f:
            df.to_csv(f, header=False,na_rep='.', sep=';',encoding='utf-8',index=False)
        del df
        lst = []   
        print('\nRead',correct,'offers',error,'errors') 
         
    def readLink(self,url):
        r = requests.get(url)
        soup = BeautifulSoup(r.text,'lxml')
        found = re.search(r".*window\.ninjaPV\s=\s(?P<json_info>{.*?})", soup.decode('unicode-escape'))
        js = json.loads(found.groupdict()['json_info'])
        if js['business'] == 'sell':       
            offer = {'id':None,'link': url, 'page_views' : None,
                    'address': None, 'district': 'None',
                    'latitude' : None,'longitude' : None,
                    'publicated': None, 'updated': None,
                    'price':None,'price_currency':None,
                    'surface':None,'rooms':None,'market':None,'rent':None, 'available':None,
                    'ownership':None,'building_material':None,'building_type':None,'year_of_construction': None,
                    'construction_status':None,'window':None, 'heating':None,
                    'floor_num':None,
                    #media
                    'media_internet': 0,'media_phone': 0,'media_cable-television': 0,
                    #wyposazenie
                    'equipment_stove': 0,'equipment_fridge': 0,'extras_furniture': 0,
                    'equipment_oven': 0,'equipment_washing_machine': 0,'equipment_tv': 0,'equipment_dishwasher': 0,
                    #zabezpieczenia: 
                    'security_entryphone': 0,'security_anti_burglary_door': 0,'security_monitoring': 0,
                    'security_roller_shutters': 0,'security_alarm': 0,'security_closed_area': 0, 'security_security':0,
                    #inne: 
                    'extras_balcony': 0,'extras_two_storey': 0,'extras_garage': 0,
                    'extras_air_conditioning': 0,'extras_separate_kitchen': 0,'extras_garden': 0,
                    'extras_basement': 0,'extras_usable_room': 0,'extras_terrace': 0,
                    'extras_lift': 0, 'extras_garage' : 0, 'extras_swimming_pool':0
                    }
    
            offer['price'] = js.get('ad_price')   
            offer['price_currency'] = js.get('price_currency')    
            offer['surface'] = js.get('surface')   
            offer['rooms'] = js.get('rooms')
            offer['district'] = js.get('district_name')  
            
            offer['address'] = soup.find_all('address')[0].find_all('p',{'class': 'address-text'})[0].contents[0]
            
            
            geo_cord1 = str(soup.find_all('div',{'id':'adDetailInlineMap'}))
            geo_cord2 = str.replace(str(geo_cord1),"\"",'')
            offer['latitude'] = geo_cord2[geo_cord2.find("data-lat=")+9:geo_cord2.find(" data-lon")]
            offer['longitude'] = geo_cord2[geo_cord2.find("data-lon=")+9:geo_cord2.find(" data-poi-lat")]
            
            
            for item_list in soup.find_all('div',{'class': 'right'}):
                for item in item_list.find_all('p'):
                    if item.text.startswith('Data dodania: '):
                        offer['publicated'] = item.text.replace('Data dodania: ','')
                    if item.text.startswith('Data aktualizacji: '):
                        offer['updated'] = item.text.replace('Data aktualizacji: ','')
                        
            for item_list in soup.find_all('div',{'class': 'left'}):
                for item in item_list.find_all('p'):
                    if item.text.startswith('Nr oferty w Otodom: '):
                        offer['id'] = item.text.replace('Nr oferty w Otodom: ','')
                    if item.text.startswith('Data aktualizacji: '):
                        offer['updated: '] = item.text.replace('Data aktualizacji: ','')
                    if 'Liczba wyświetleń strony: ' in item.text:
                        offer['page_views'] = item.text.replace('Liczba wyświetleń strony: ','').strip()
            
            for list_item in soup.find_all('ul',{'class':'main-list'}):
                for item in list_item.find_all('li'):
                    key = self.main_list[str(item.contents[0])]
                    if not offer.get(key) :
                        offer[key] = item.contents[1].get_text()
                    
            for list_item in soup.find_all('ul',{'class':'sub-list'}):
                for item in list_item.find_all('li'):
                    key = item.contents[0].get_text()
                    value = item.contents[1].lstrip().rstrip()
                    if key in self.sublist:
                        offer[self.sublist[key]['NAME']] = self.sublist[key][value]
                    else:
                        offer[self.sublist_other[key]] = value
                        
            for list_item in soup.find_all('ul',{'class':'dotted-list'}):
                for item in list_item.find_all('li'):
                    offer[self.extras[item.get_text().lstrip()]] = 1
        return offer

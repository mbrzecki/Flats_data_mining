import csv
import sys, os
import pandas as pd

sys.path.append('C:/Users/OEM/data_mining/oto_dom/')
import tools.addressMatching as am

def loadRawFile(file):
    with open( file + ".csv") as f:
        spamreader = csv.reader(f, delimiter=';', quotechar='|')
        lst = []
        col_names = []
        for i,row in enumerate(spamreader):
            if i == 0:
                col_names = row
                continue
            lst.append(dict(zip(col_names,row)))
     
    df = pd.DataFrame(lst)
    return df.set_index('id')

city = 'warszawa'

matched = loadRawFile('C:/Users/OEM/data_mining/oto_dom/utils/matched')

sample = loadRawFile('C:/Users/OEM/data_mining/oto_dom/data/' + city+'_raw')

#
adr_match = am.AddressMatching(city)
ad = adr_match.loadAddresses('C:/Users/OEM/data_mining/oto_dom/utils/warszawa_addresses.csv')
sample = adr_match.stripAddress(sample)

am.addressStats(sample,'raw sample') 

sample['orig_street'] = [False if s == '.' else True  for s in sample['Street']]
#
# Removing rows that do not have any address items
#
sample = sample[(sample['Borough'] != '.') | (sample['Neighbourhood'] != '.') | (sample['Street'] != '.')  \
                | (sample['district'] != '.') | (sample['Unknown'] != '.')]
#
# correcting name of boroughs/neighbourhoods/streets/
#
mapping = {'praga-północ':'praga północ','praga-południe':'praga południe','centrum':'śródmieście','dolny mokotów':'mokotów','górny mokotów':'mokotów'}
sample = adr_match.applyMapping(sample, 'Unknown', 'Borough', mapping)

mapping = {'starówka':'stare miasto','imielin':'stary imielin','stary wilanów':'wilanów wysoki','kawęczyn':'kawęczyn-wygoda' \
           ,'miasteczko wilanów': 'błonia wilanowskie', }
sample = adr_match.applyMapping(sample, 'Unknown', 'Neighbourhood', mapping)

mapping = {'ken':'Komisji Edukacji Narodowej, al.'}
sample = adr_match.applyMapping(sample, 'Unknown', 'street', mapping)

#
# words removed from unknown
#
to_delete_from_address_item = ['ul.', 'al.', 'pokoje','winda kuchnia','windą kuchnią','balkon', 'mieszkanie', 'mieszkania', 'nowoczesnej', \
                               'centrum','kuchnia','kuchnią','górny mokotów','dolny mokotów', 'warszawa', 'metro', 'metra', 'ulica','prowizji']
for item in to_delete_from_address_item:
    sample['Unknown'] = [i.replace(item,'') for i in sample['Unknown']]

# 
# removing rows when unknown address item contains one of the phrase given
#

to_erase = ['mdm', 'nowa inwestycja', 'promocja', 'niska cena']
for item in to_erase:
    sample['Unknown'] = ['to_delete' if item in i else i for i in sample['Unknown']]
temp = sample[sample['Unknown'] == 'to_delete']
del temp
sample['Unknown'] = ['.' if i == 'to_delete' else i for i in sample['Unknown']]

# 
# removing white signs and correcting the inputs
#
sample['Unknown'] = [i.lstrip() for i in sample['Unknown']]
sample['Unknown'] = [i.replace('  ',' ') for i in sample['Unknown']]
sample['Unknown'] = ['.' if i == '' or i == ' ' else i for i in sample['Unknown'] ]

am.addressStats(sample,'cleaned sample') 

#
# filling boroughs and neighbourhoods names basing on the column district
#

sample['district'] = sample['district'].apply(lambda x: x.lower())   
#sample = adr_match.fillBasingOnDistrict(sample, 'Neighbourhood')       
#sample = adr_match.fillBasingOnDistrict(sample, 'Borough')


district_borough_mapping = dict()
for borough in ad['Borough'].unique():
    district_borough_mapping[borough.lower()] = borough.lower()
for borough, neighbourhood in zip(ad['Borough'],ad['Neighbourhood']):
    district_borough_mapping[neighbourhood.lower()] = borough.lower()  

district_borough_mapping['.'] = '.'
district_borough_mapping['annopol'] = 'białołęka'
district_borough_mapping['augustów'] = 'białołęka'
district_borough_mapping['białołęka dworska'] = 'białołęka'
district_borough_mapping['buraków'] = 'bielany'
district_borough_mapping['centrum'] ='śródmieście'
district_borough_mapping['dolny mokotów'] = 'mokotów'
district_borough_mapping['górny mokotów'] ='mokotów'
district_borough_mapping['imielin'] = 'ursynów'
district_borough_mapping['jelonki'] = 'bemowo'
district_borough_mapping['kawęczyn'] = 'rembertów'
district_borough_mapping['kąty grodziskie'] = 'białołęka'
district_borough_mapping['kępa gocławska'] = 'praga południe'
district_borough_mapping['kępa tarchomińska'] = 'białołęka'
district_borough_mapping['królikarnia'] = 'mokotów'
district_borough_mapping['latawiec'] = 'śródmieście'
district_borough_mapping['lewandów'] = 'białołęka'
district_borough_mapping['mariensztat'] = 'śródmieście'
district_borough_mapping['marymont'] = 'bielany'
district_borough_mapping['metro wilanowska'] = 'mokotów'
district_borough_mapping['moczydło'] = 'wola'
district_borough_mapping['nadwilanówka'] = 'wilanów'
district_borough_mapping['nowe bródno'] = 'targówek'
district_borough_mapping['nowe górce'] = 'bemowo'
district_borough_mapping['nowy służewiec'] = 'ursynów'
district_borough_mapping['pola mokotowskie'] = 'mokotów'
district_borough_mapping['praga-południe'] = 'praga południe'
district_borough_mapping['praga-północ'] = 'praga północ'
district_borough_mapping['praga'] = 'praga południe'
district_borough_mapping['przyczółek grochowski'] = 'praga południe'
district_borough_mapping['stokłosy'] = 'ursynów'
district_borough_mapping['witolin'] = 'praga południe'
district_borough_mapping['zielona'] = 'wesoła'

sample = adr_match.applyMapping(sample, 'district', 'Borough', district_borough_mapping,False)

#for item in sample['district'].unique():
#    if not item in district_borough_mapping.keys():
#        print(item)

district_neighbourhood_mapping = dict()
for borough, neighbourhood in zip(ad['Borough'],ad['Neighbourhood']):
    district_neighbourhood_mapping[neighbourhood.lower()] = borough.lower()  
for borough in ad['Borough'].unique():
    district_neighbourhood_mapping[borough.lower()] ='.'

district_neighbourhood_mapping['dolny mokotów'] = '.'
district_neighbourhood_mapping['górny mokotów'] = '.'
district_neighbourhood_mapping['praga'] = '.'
district_neighbourhood_mapping['praga-południe'] = '.'
district_neighbourhood_mapping['praga-północ'] = '.'

district_neighbourhood_mapping['.'] = '.'
district_neighbourhood_mapping['annopol'] = 'żerań' 
district_neighbourhood_mapping['augustów'] = 'grodzisk'
district_neighbourhood_mapping['białołęka dworska'] = 'dworska'
district_neighbourhood_mapping['buraków'] = 'młociny' 
district_neighbourhood_mapping['centrum'] = 'śródmieście północne'
district_neighbourhood_mapping['imielin'] = 'stary imielin'
district_neighbourhood_mapping['jelonki'] = 'jelonki północne'
district_neighbourhood_mapping['kawęczyn'] = 'kawęczyn-wygoda'
district_neighbourhood_mapping['kąty grodziskie'] = 'grodzisk'
district_neighbourhood_mapping['kępa gocławska'] = 'gocław' 
district_neighbourhood_mapping['kępa tarchomińska'] = 'nowodwory'
district_neighbourhood_mapping['królikarnia'] = 'ksawerów'
district_neighbourhood_mapping['latawiec'] = 'śródmieście południowe'
district_neighbourhood_mapping['lewandów'] = 'grodzisk'
district_neighbourhood_mapping['mariensztat'] = 'powiśle'
district_neighbourhood_mapping['marymont'] = 'marymont-kaskada'
district_neighbourhood_mapping['metro wilanowska'] = 'ksawerów'
district_neighbourhood_mapping['moczydło'] = 'koło' 
district_neighbourhood_mapping['nadwilanówka'] = 'powsin'
district_neighbourhood_mapping['nowe bródno'] = 'bródno'
district_neighbourhood_mapping['nowe górce'] = 'górce'  
district_neighbourhood_mapping['nowy służewiec'] = 'wyczółki'
district_neighbourhood_mapping['pola mokotowskie'] = 'stary mokotów'
district_neighbourhood_mapping['przyczółek grochowski'] = 'grochów'
district_neighbourhood_mapping['stokłosy'] = 'ursynów północny'
district_neighbourhood_mapping['witolin'] = 'gocławek'
district_neighbourhood_mapping['zielona'] = 'zielona-grzybowa'


#for item in sample['district'].unique():
#    if not item in district_neighbourhood_mapping.keys():
#        print(item)

sample = adr_match.applyMapping(sample, 'district', 'Neighbourhood', district_neighbourhood_mapping,False)


am.addressStats(sample,'after filling based on district') 

#
# Sometimes the name of borough or neighbourhood was not matched 
# because apart from borough/neighoourhood name there were other words, like "Wola new apartment"
# Here we check if in uknown address item there is a name of borough/neighbourhood
#
sample = adr_match.findInUnkowns('Borough',sample)
sample = adr_match.findInUnkowns('Neighbourhood',sample)

#
# Filling the name of  boroughs based on the name of neighbourhood etc.
#
sample = adr_match.internalFilling(sample,'Neighbourhood','Borough')
sample = adr_match.internalFilling(sample,'Street','Neighbourhood')
sample = adr_match.internalFilling(sample,'Street','Borough')

am.addressStats(sample,'filling based on other address items') 


#
# Filling the name of  boroughs based on the name of neighbourhood etc.
#
mapping  = matched[matched['Item']=='street'].set_index('Key')['Match'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)

mapping  = matched[matched['Item']=='neighbourhood'].set_index('Key')['Match'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Neighbourhood', mapping)


am.addressStats(sample,'after using matched') 
#
# Matching strings. Sometimes the address of the flat couldn't have been recognized because of typo 
# or incomplete name like Mickiewicza instead of Adama Mickiewicza
# Using a sequence matcher we can try to match addresses

#
# Here we try to match the streets names 
# To make algorithm works faster and be less error prone, we try to match street names within the neighbourhood
#
matching = adr_match.matchAddresses(sample, 'Neighbourhood', 'Street', 'full', 20) 
#mapping  = matching[(matching['Score1']>=65)].set_index('Item')['Match1'].to_dict()
#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)

matching = adr_match.matchAddresses(sample, 'Neighbourhood', 'Street', 'sort', 20)
#mapping  = matching[(matching['Score1']>=65)].set_index('Item')['Match1'].to_dict()
#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)

matching = adr_match.matchAddresses(sample, 'Neighbourhood', 'Street', 'partial', 20)
#mapping  = matching[(matching['Score1']>=65)].set_index('Item')['Match1'].to_dict()
#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)

matching = adr_match.matchAddresses(sample, 'Neighbourhood', 'Street', 'set', 20)
#mapping  = matching[(matching['Score1']>=65)].set_index('Item')['Match1'].to_dict()
#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)


#
# We try to match the streets names 
# To make algorithm works faster and be less error prone, we try to match street names within the borough, 
# we compare do not compare strings per se, but sorted tokens
# We select only items with matching score higher than 72%. We manually delete some erroneously assigned streets
# Then we select those with score higher than 61 and when the difference between best match and second best match is larger than 10% 
#
matching = adr_match.matchAddresses(sample, 'Borough', 'Street', 'sort', 50)
mapping  = matching[(matching['Score1']>=65)].set_index('Item')['Match1'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)
#for item in mapping.keys():
#    temp = {"Item":"street"}
#    temp['Key'] = item
#    temp['Match'] = mapping[item]
#    matched = matched.append(temp,ignore_index=True)

#
# We try to match the streets names 
# To make algorithm works faster and be less error prone, we try to match street names within the borough
# We select only items with matching score higher than 79%. 
#

matching = adr_match.matchAddresses(sample, 'Borough', 'Street', 'partial', 50)
mapping  = matching[matching['Score1']>=90].set_index('Item')['Match1'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)


matching = adr_match.matchAddresses(sample, 'Borough', 'Street', 'set', 50)
mapping  = matching[(matching['Score1']>=73) & (matching['Diff_Score1_Score2']>=10)].set_index('Item')['Match1'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)

#for item in mapping.keys():
#    temp = {"Item":"street"}
#    temp['Key'] = item
#    temp['Match'] = mapping[item]
#    matched = matched.append(temp,ignore_index=True)
#    
#
# We try to match the streets names 
# To make algorithm works faster and be less error prone, we try to match street names within the borough
# We select only items with matching score higher than 90%. 
#

matching = adr_match.matchAddresses(sample, 'Borough', 'Street', 'partial', 50)
#mapping  = matching[(matching['Score1']>63)].set_index('Item')['Match1'].to_dict()
#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)


matching = adr_match.matchAddresses(sample, 'Borough', 'Street', 'set', 50)
#mapping  = matching[(matching['Score1']>63)].set_index('Item')['Match1'].to_dict()
#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)


matching = adr_match.matchAddresses(sample, 'Borough', 'Street', 'full', 50)
mapping  = matching[(matching['Score1']>=63)].set_index('Item')['Match1'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)

matching = adr_match.matchAddresses(sample, 'Borough', 'Street', 'sort', 50)
#mapping  = matching[(matching['Score1']>=63)].set_index('Item')['Match1'].to_dict()
#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)

#
# We try to match the neighbourhoods names 
# To make algorithm works faster and be less error prone, we try to match neigbourhood names within the borough
# We select only items with matching score higher than 90%. 
#
matching = adr_match.matchAddresses(sample, 'Borough', 'Neighbourhood', 'full', 50)
mapping  = matching[(matching['Score1']>=60) ].set_index('Item')['Match1'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Neighbourhood', mapping)


matching = adr_match.matchAddresses(sample, 'Borough', 'Neighbourhood', 'partial', 50)
mapping  = matching[(matching['Score1']>76)].set_index('Item')['Match1'].to_dict()
sample = adr_match.applyMapping(sample, 'Unknown', 'Neighbourhood', mapping)

#
# We try to match addresses using not truncated sample as before, but whole list of street/neighbourhood/borough names
#
#matching = adr_match.matchAddresses(sample, None, 'Street', 'sort', 40)
#matching = adr_match.matchAddresses(sample, None, 'Street', 'full', 40)
#matching = adr_match.matchAddresses(sample, None, 'Street', 'partial', 40)
#matching = adr_match.matchAddresses(sample, None, 'Street', 'set', 40)
#
#matching = adr_match.matchAddresses(sample, None, 'Neighbourhood', 'full', 40)
#matching = adr_match.matchAddresses(sample, None, 'Neighbourhood', 'sort', 40)


am.addressStats(sample,'after sequence matching')

#
# Examining the unrecognized address items
#

unknown = sample.groupby(['Unknown']).count()['Street']


#sample = adr_match.applyMapping(sample, 'Unknown', 'Street', mapping)


#for item in mapping.keys():
#    temp = {"Item":"street"}
#    temp['Key'] = item
#    temp['Match'] = mapping[item]
#    matched = matched.append(temp,ignore_index=True)

#
# Filling the name of  boroughs based on the name of neighbourhood etc.
#
sample = adr_match.internalFilling(sample,'Neighbourhood','Borough')
sample = adr_match.internalFilling(sample,'Street','Neighbourhood')
sample = adr_match.internalFilling(sample,'Street','Borough')

sample = sample[(sample['Borough'] != '.') | (sample['Neighbourhood'] != '.')]

am.addressStats(sample,'final')
sample = sample.drop(['Unknown'],axis=1)

#
#  Correcting addreses
# 

mapping = ad.set_index('Neighbourhood')['Borough'].to_dict()
sample['check'] = sample['Neighbourhood'].map(mapping).fillna(".").astype(str)
sample['Borough'] = [c if (b != c) and (c!='.')  else b for b,c in zip(sample['Borough'],sample['check'])]
sample = sample.drop('check',axis=1)
#
#matched['id'] = matched.index
#with open('C:/Users/OEM/data_mining/oto_dom/utils/matched.csv', 'w') as f:
#    matched.to_csv(f, header=True, na_rep='.', sep=';',encoding='utf-8',index=False)

sample['Id'] = sample.index
with open('C:/Users/OEM/data_mining/oto_dom/data/warszawa_addresses.csv', 'w') as f:
    sample.to_csv(f, header=True, na_rep='.', sep=';',encoding='utf-8',index=False)

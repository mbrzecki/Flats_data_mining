import pandas as pd
import csv
import re

from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzprocess

class AddressMatching():
    def __init__(self,city):
        self.city = city
        self.addresses = pd.DataFrame()
        self.address_items = dict()
      
    def loadAddresses(self,addresses_file):
        lst = []
        col = []
        with open(addresses_file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for i,row in enumerate(reader):
                text = row
                if i == 0:
                     col = row   
                     continue
                text = [x.lower() for x in row]
                lst.append(dict(zip(col,text)))
                del row
        self.addresses = pd.DataFrame(lst)         
        self.address_items['Street'] = [x.rstrip() for x in list(set(self.addresses['Street'].tolist()))]    
        self.address_items['Neighbourhood'] = [x.rstrip() for x in list(set(self.addresses['Neighbourhood'].tolist()))]    
        self.address_items['Borough'] = [x.rstrip() for x in list(set(self.addresses['Borough'].tolist()))]    
        return self.addresses
    
    def stripAddress(self,sample):
        address_list = []
        for i, row in sample['address'].iteritems():
            obs = {'Id':None,'City':'.','Borough':'.','Neighbourhood':'.','Street':'.','Unknown':'.'}
            obs['Id'] = i
            items = str(row).split(',') 
            unrecognized = []
            for item in items:
                item = item.lower() #lowercase
                item = item.lstrip() #remove spaces on the left
                temp = re.search('\d+[a-z]', item) #remove number with letter from the end of string, for example Senatorska 10a -> Senatorska
                if not temp is None:         
                    item = item.replace(' ' + temp.group(0),'')
                item = item.rstrip(' 1234567890/()') #remove number from the end of string, for example Senatorska 10 -> Senatorska
                test = item.replace('  ',' ')
                
                if test in [self.city]:
                    obs['City'] = item
                elif test in self.address_items['Borough']:
                    obs['Borough'] = item
                elif test in self.address_items['Neighbourhood']:
                    obs['Neighbourhood'] = item
                elif test in self.address_items['Street']:
                    obs['Street'] = item
                else:
                    unrecognized.append(item)
                     
            obs['Unknown'] = " ".join(unrecognized)
            if obs['Unknown'] == '':
                obs['Unknown'] = '.'
            address_list.append(obs)
            del row
        
        
        
        df = pd.DataFrame.from_dict(address_list)
        df.set_index(keys='Id',inplace=True)
        sample = pd.merge(sample, df, left_index=True, right_index=True)
        return sample.drop('address', 1)   

    def applyMapping(self, sample, base, fill, mapping, drop_unknown=True):
        sample[fill + '_new'] = sample[base].map(mapping).fillna(".").astype(str)
        return replaceNewAdresses(sample, fill, fill + '_new', drop_unknown) 

    def internalFilling(self, sample, base, fill):
        mapping = self.addresses.set_index(base)[fill].to_dict()
        return self.applyMapping(sample, base, fill, mapping)

    def fillBasingOnDistrict(self, sample, base):
        mapping = dict() 
        for item in sample['district'].unique():
            if item == '.':
                continue
            res = fuzzprocess.extract(item, self.address_items[base], scorer=fuzz.ratio, limit=1)
            if res[0][1] == 100:
                mapping[item] = res[0][0]
                print(item, mapping[item] )
        return self.applyMapping(sample, 'district', base, mapping)
    
    def findInUnkowns(self,address_item, sample):
        mapping_pattern = dict()
        items_ = sample[sample[address_item]=='.']['Unknown'].drop_duplicates()        
        for item in items_.iteritems():
            if type(item[1]) == str:
                item = item[1].lower()
                item = ' ' + item
                for pattern in self.address_items[address_item]:
                    if ' ' + pattern + ' ' in item and not item == '.':
                        mapping_pattern[item] = pattern                        
        sample[address_item + '_new'] = sample['Unknown'].map(mapping_pattern).fillna(".").astype(str)
        return replaceNewAdresses(sample, address_item, address_item + '_new',False)  

    def matchAddresses(self, sample, division, address_item, typ, cutoff):
        ret = pd.DataFrame()
        if division == None:
            list_of_patterns =list(set(self.addresses[address_item]))
            df = sample[sample['Unknown'] != '.']['Unknown'].dropna().drop_duplicates() 
            for id_, item in df.iteritems():
                result = []
                
                if typ == 'set':
                    result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.token_set_ratio, limit=3)
                elif typ == 'partial':
                    result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.partial_ratio, limit=3)
                elif typ == 'sort':
                    result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.token_sort_ratio, limit=3)
                elif typ == 'full':
                    result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.ratio)
                if result[0][1] > cutoff:
                    col_names = ['Item','Score1', 'Score2', 'Score3','Match1','Match2','Match3']
                    results = [item] + [x[1] for x in result[:3]] + [x[0] for x in result[:3]]
                    ret = ret.append(dict(zip(col_names,results)),ignore_index=True)            
        else:    
            for div in self.address_items[division]:
                df = sample[(sample[division]==div) & (sample['Unknown'] != '.')]['Unknown'].dropna().drop_duplicates()  
                list_of_patterns =list(set(self.addresses[self.addresses[division]==div][address_item]))
                if df.size == 0:
                    continue
                for id_, item in df.iteritems():
                    result = []
                    if typ == 'set':
                        result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.token_set_ratio, limit=3)
                    elif typ == 'partial':
                        result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.partial_ratio, limit=3)
                    elif typ == 'sort':
                        result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.token_sort_ratio, limit=3)
                    elif typ == 'full':
                        result = fuzzprocess.extract(item, list_of_patterns, scorer=fuzz.ratio)
                    if result[0][1] > cutoff:
                        col_names = ['Item','Score1', 'Score2', 'Score3','Match1','Match2','Match3']
                        results = [item] + [x[1] for x in result[:3]] + [x[0] for x in result[:3]]
                        ret = ret.append(dict(zip(col_names,results)),ignore_index=True)
        if ret.size > 0:
            ret['Diff_Score1_Score2'] = ret['Score1'] - ret['Score2'] 
        return ret

    def getAddresses(self):
        return self.addresses   
    #################################################################################################################################
def replaceNewAdresses(df, col_to_fill, col_with_fill, drop_unknown=True):
    for i, row in df[col_with_fill].iteritems():
        if row != '.' and df.xs(i)[col_to_fill] != '.' and drop_unknown:
            df.ix[df.index == i, 'Unknown'] = '.' 
        if row != '.' and df.xs(i)[col_to_fill] == '.':
            df.ix[df.index == i, col_to_fill] = df.ix[df.index == i, col_with_fill]
            if drop_unknown:
                df.ix[df.index == i, 'Unknown'] = '.'  
    return df.drop(col_with_fill, 1)

def addressStats(df,comment=''):
    print(comment)
    print('Sample', df.shape[0])
    print('Missing Borough\t\t',len(df[df['Borough'] == '.']),'\t',round(100*len(df[df['Borough'] == '.'])/df.shape[0],2),'%')
    print('Missing Neighbourhood:\t',len(df[df['Neighbourhood'] == '.']),'\t',round(100*len(df[df['Neighbourhood'] == '.'])/df.shape[0],2),'%')
    print('Missing Street:\t\t',len(df[df['Street'] == '.']),'\t',round(100*len(df[df['Street'] == '.'])/df.shape[0],2),'%')
    print('Unknown:\t\t',len(df[df['Unknown'] != '.']),'\n\n')
    

  
import sys
import tools.offerReader as ofr

city = 'krakow'
  
reader = ofr.OfferReader(city, wd)
reader.prepareLinks(20)
reader.readLinks()
reader.getDescription()

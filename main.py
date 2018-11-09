# coding: utf8
import codecs
import requests
import json
import re
import time
import settings
from datetime import datetime

from bs4 import *
def id_from_url(url):
    return url.split("?")[0][1:]
####### Memory db

to_visit = []
network = set()
user_data = {}
####### Methods
def add_user(id,name,kwargs):
    global user_data
    user_data[id]={'name':name,**kwargs}
def add_friend(source,target):
    global network
    edge = "{source},{target}".format(source=source,target=target)
    network.add(edge)
def get_all_friends(idlink,keep_to_visit=False):
    global to_visit
    next_url = 'https://m.facebook.com/{idlink}/friends?all=1'.format(idlink=idlink)
    while next_url:
    
        f = session.get(next_url)
        fsoup = BeautifulSoup(f.content,'html5lib') 
        source = fsoup.find('title').string
        add_user(idlink,source,{"type":"friend_of_friend"})
        for friend in fsoup.find_all('a',{"class":re.compile('(cc)|(cf)|(bo)|(bl)')}):
            if "profile.php" not in friend.attrs['href']  \
            and "/friends/" not in friend.attrs['href']  \
            and "accesskey" not in friend.attrs \
            and "/a/" not in friend.attrs['href'] \
            and "logout.php" not in friend.attrs['href'] \
            and "language.php" not in friend.attrs['href'] \
            and "/pages/" not in friend.attrs['href']   \
            and "/bugnub/" not in friend.attrs['href']   :
                if keep_to_visit:
                    to_visit+=[id_from_url(friend.attrs['href'])]
                    
                    add_user(id_from_url(friend.attrs['href']),friend.string,{"type":"friend_of_friend"})    
                else:
                    add_user(id_from_url(friend.attrs['href']),friend.string,{"type":"friend_of_friend"})    
                add_friend(idlink,id_from_url(friend.attrs['href']))
                print(friend.encode('utf-8'))

        next_url = fsoup.find('div',id="m_more_friends")
        
        if next_url:
            next_url = next_url.find('a').attrs['href']
            next_url ='https://m.facebook.com{}'.format(next_url)
        time.sleep(1)

###### Seriousness begin here

# Open a session
session = requests.Session()
req = session.get('https://m.facebook.com')
soup = BeautifulSoup(req.content,'html5lib')

# Get all parameter needed 
data_login = {}
for inp in soup.find_all('input'):
    inpd = inp
    if 'value' in inpd.attrs:
        data_login[inpd.attrs['name']] = inpd['value']
data_login['email'] = settings.EMAIL
data_login['pass']  = settings.PASSWORD
post_url = soup.find('form').attrs['action']

# Should login !
r = session.post(post_url, data=data_login)
rsoup = BeautifulSoup(r.content,"html5lib")

#can't properly guess the user name, that's why it's needed to fill this info by hand
print(settings.URL_NAME)

# First round to get friends and keep them to see in future
get_all_friends(settings.URL_NAME,keep_to_visit=True)

# For all friends, check friends
# Friendception
for ftv in to_visit:
    get_all_friends(ftv)   


for u in to_visit:
    user_data[u]['type'] = "direct_friend"
user_data[settings.URL_NAME]['type'] = "me"
## https://www.youtube.com/watch?v=Y30CYfS080k but it works
output_file_name = "{}-{}.gdf".format(settings.URL_NAME,datetime.today().isoformat().replace(':',''))
with codecs.open(output_file_name, "wb", encoding='utf-8') as file:
    file.write('nodedef>name VARCHAR,label VARCHAR,type VARCHAR\n')
    for u in user_data:
        file.write("{},{},{}\n".format(u,user_data[u]['name'],user_data[u]['type']))
    file.write('edgedef>node1 VARCHAR,node2 VARCHAR\n')
    for n in network:
        file.write("{}\n".format(n))

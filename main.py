# coding: utf8
import codecs
import requests
import json
import re
import time

import getpass
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
    print(next_url)

    while next_url:
    
        f = session.get(next_url)
        fsoup = BeautifulSoup(f.content,'html5lib') 
        source = fsoup.find('title').string
        add_user(idlink,source,{"type":"friend_of_friend"})
        for friend in fsoup.find_all('a'):
            if "fref" in friend.attrs['href'] and "profile.php" not in friend.attrs['href']:
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
if __name__ == "__main__":
    email = input("Email: ")
    url_name = input("Your id (go to your profile page and get https://www.facebook.com/<GET_WHAT_IS_HERE> :")
    password = getpass.getpass(prompt="Password: ",stream=None)
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
    data_login['email'] = email
    data_login['pass']  = password
    post_url = soup.find('form').attrs['action']
    print(post_url)
    # Should login !
    r = session.post('https://m.facebook.com'+post_url, data=data_login)
    rsoup = BeautifulSoup(r.content,"html5lib")
    
    print(r.headers.items())
    print(rsoup.find_all("a"))


    #can't properly guess the user name, that's why it's needed to fill this info by hand
    print(url_name)

    # First round to get friends and keep them to see in future
    get_all_friends(url_name,keep_to_visit=True)

    # For all friends, check friends
    # Friendception
    for ftv in to_visit:
        get_all_friends(ftv)   


    for u in to_visit:
        user_data[u]['type'] = "direct_friend"
    user_data[url_name]['type'] = "me"
    ## https://www.youtube.com/watch?v=Y30CYfS080k but it works
    output_file_name = "{}-{}.gdf".format(url_name,datetime.today().isoformat().replace(':',''))
    with codecs.open(output_file_name, "wb", encoding='utf-8') as file:
        file.write('nodedef>name VARCHAR,label VARCHAR,type VARCHAR\n')
        for u in user_data:
            file.write("{},{},{}\n".format(u,user_data[u]['name'],user_data[u]['type']))
        file.write('edgedef>node1 VARCHAR,node2 VARCHAR\n')
        for n in network:
            file.write("{}\n".format(n))

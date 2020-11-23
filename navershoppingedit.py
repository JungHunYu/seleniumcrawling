from http.server import HTTPServer, BaseHTTPRequestHandler
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

import simplejson
import time
import datetime
import sys
import os.path
import pymssql
import binascii
import platform

global driverlist
driverlist  = []
global temppath
temppath = os.getcwd() + '/temp/'

#--------------------------------------------------------------------------
JS_DROP_FILES = "var c=arguments,b=c[0],k=c[1];c=c[2];for(var d=b.ownerDocument||document,l=0;;){var e=b.getBoundingClientRect(),g=e.left+(k||e.width/2),h=e.top+(c||e.height/2),f=d.elementFromPoint(g,h);if(f&&b.contains(f))break;if(1<++l)throw b=Error('Element not interactable'),b.code=15,b;b.scrollIntoView({behavior:'instant',block:'center',inline:'center'})}var a=d.createElement('INPUT');a.setAttribute('type','file');a.setAttribute('multiple','');a.setAttribute('style','position:fixed;z-index:2147483647;left:0;top:0;');a.onchange=function(b){a.parentElement.removeChild(a);b.stopPropagation();var c={constructor:DataTransfer,effectAllowed:'all',dropEffect:'none',types:['Files'],files:a.files,setData:function(){},getData:function(){},clearData:function(){},setDragImage:function(){}};window.DataTransferItemList&&(c.items=Object.setPrototypeOf(Array.prototype.map.call(a.files,function(a){return{constructor:DataTransferItem,kind:'file',type:a.type,getAsFile:function(){return a},getAsString:function(b){var c=new FileReader;c.onload=function(a){b(a.target.result)};c.readAsText(a)}}}),{constructor:DataTransferItemList,add:function(){},clear:function(){},remove:function(){}}));['dragenter','dragover','drop'].forEach(function(a){var b=d.createEvent('DragEvent');b.initMouseEvent(a,!0,!0,d.defaultView,0,0,0,g,h,!1,!1,!1,!1,0,null);Object.setPrototypeOf(b,null);b.dataTransfer=c;Object.setPrototypeOf(b,DragEvent.prototype);f.dispatchEvent(b)})};d.documentElement.appendChild(a);a.getBoundingClientRect();return a;"

def drop_files(element, files, offsetX=0, offsetY=0):
    driver = element.parent
    isLocal = not driver._is_remote or '127.0.0.1' in driver.command_executor._url
    paths = []
    
    # ensure files are present, and upload to the remote server if session is remote
    for file in (files if isinstance(files, list) else [files]) :
        if not os.path.isfile(file) :
            raise FileNotFoundError(file)
        paths.append(file if isLocal else element._upload(file))
    
    value = '\n'.join(paths)
    elm_input = driver.execute_script(JS_DROP_FILES, element, offsetX, offsetY)
    elm_input._execute('sendKeysToElement', {'value': [value], 'text': value})

WebElement.drop_files = drop_files

#--------------------------------------------------------------------------

def hasxpath(xpath):
    try: 
        driver.find_element_by_xpath(xpath)
        return True
    except:
        return False

#--------------------------------------------------------------------------

def getwebdirver(id, password):
    webdirver = None
    global driverlist
    for item in driverlist:
        if item.id == id and item.password == password and item.status == 'idle':
            webdirver = item
            webdirver.status = 'run'
            webdirver.touchtime = datetime.datetime.now()


    if webdirver == None:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument("--incognito")
        options.add_argument("--disable-notifications")
        options.add_argument('--no-sandbox')
        options.add_argument('--verbose')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        

        if platform.system() == 'Windows':
            webdirver = webdriver.Chrome('.\chromedriver.exe', chrome_options=options)            
        else :
            webdirver = webdriver.Chrome('./chromedriver', chrome_options=options)            

        webdirver.get('https://searchad.naver.com/')

        time.sleep(1.00) 
        webdirver.find_element_by_id('uid').send_keys(id)    
        webdirver.find_element_by_id('upw').send_keys(password)    
        webdirver.find_element_by_id('upw').send_keys(Keys.RETURN)    

        time.sleep(1.00) 
        if len(webdirver.window_handles) > 1 :
            webdirver.switch_to_window(webdirver.window_handles[1])
            webdirver.close()
            webdirver.switch_to_window(webdirver.window_handles[0])
                
        webdirver.id = id
        webdirver.password = password
        webdirver.status = 'run'
        webdirver.touchtime = datetime.datetime.now()

        driverlist.append(webdirver) 

    return webdirver


if __name__ =='__main__':
    if not os.path.isdir(temppath) :
        os.makedirs(temppath)

    conn = pymssql.connect(host="112.216.80.54",user='solution',password='solu0601!@', database='DatNaver', port='14331', charset='EUC-KR', autocommit=True)
    cur = conn.cursor(as_dict=True)
    qry = conn.cursor(as_dict=True)
    
    isrunning = True

    while isrunning:
        cur.execute("SELECT top 1 a.*, isnull(datalength(a.Image) , 0) as imagesize FROM Dat_NavShopEdit a where a.status = 10 and a.Trycount < 40 order by a.num asc")
        # cur.execute("SELECT top 1 * FROM Dat_NavShopEdit order by num asc")
        rows = cur.fetchall()
        if len(rows) > 0 :
            for row in rows:
                seq = str(row['Seq'])
                trycount = row['trycount'] + 1
                
                id = row['ID']
                password = row['Password']
                customerid = row['CustomerId']
                adid = row['AdId']
                title = row['Title']


                try: 
                    qry.execute('update Dat_NavShopEdit set status = 20, Trycount = Trycount + 1 where seq=' + seq)
                    url1 = 'https://manage.searchad.naver.com/customers/' + customerid + '/ads/' + adid
                    webdriver = getwebdirver(id, password)
                    webdriver.get(url1)
                    time.sleep(2.00) 

                    webdriver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div[1]/span/button').click()
                    time.sleep(2.00)                

                    if title != None :
                        webdriver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(Keys.CONTROL + "a")
                        webdriver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(Keys.DELETE)
                        webdriver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(title) 

                    try: 
                        webdriver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[4]/div[2]/div[1]/div[2]/div/div[1]/button').click()
                    except:
                        print('button None')


                    if row['imagesize'] > 0 :
                        dropzone = webdriver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[4]/div[2]/div[1]/div[2]/div/div/div/div[2]/div')
                        imagedata = row['Image']
                        imagepath = temppath + row['ImageName']
                        print('imagepath : ' + imagepath)
                        f = open(imagepath, 'wb')
                        f.write(imagedata)
                        f.close()
                        dropzone.drop_files(imagepath)

                    
                    time.sleep(2.00) 
                    webdriver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[3]/button[1]').click()
                    webdriver.status = 'idle'

                    if row['imagesize'] > 0 :
                        os.remove(imagepath)

                    qry.execute('update Dat_NavShopEdit set status = 30 where seq=' + seq)
                    time.sleep(2.00)             

                except:
                    print('error Seq : ' + seq)
                    webdriver.status = 'idle'
                    qry.execute('update Dat_NavShopEdit set status = 10 where seq=' + seq)
                    if trycount > 3 :
                        qry.execute('update Dat_NavShopEdit set status = 40 where seq=' + seq)


            
        else :
            time.sleep(20.00) 

        
    conn.Close()

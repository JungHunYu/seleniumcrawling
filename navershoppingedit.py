from base64 import encode
from http.server import HTTPServer, BaseHTTPRequestHandler
from logging import exception
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

import simplejson
import time
import datetime
import sys
import os.path
import binascii
import platform
import requests

global driverlist
driverlist  = []
global temppath
temppath = os.getcwd() + '/temp/'

global hosturl
hosturl = "http://112.216.80.54:9001/"

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

global options
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

def setlog(seq, message):
    print("seq = " + seq)
    print("message = " + message)
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    data = {"seq": seq, "message": message}
    res = requests.post(hosturl + "datnaver/setlog", headers=headers, data=simplejson.dumps(data))


def getwebdirver(seq, id, password):
    print('id : ' + id)
    print('password : ' + password)

    driver = None
    global driverlist
    for item in driverlist:
        if item.id == id and item.password == password and item.status == 'idle':
            driver = item
            driver.status = 'run'
            driver.touchtime = datetime.datetime.now()
        else : 
            delta = datetime.datetime.now() - item.touchtime
            if delta.seconds > 60 :
                item.refresh()

            


    if driver == None:
        if platform.system() == 'Windows':
            driver = webdriver.Chrome('.\chromedriver.exe', chrome_options=options)          
        else :
            driver = webdriver.Chrome('./chromedriver', chrome_options=options)            

        
        driver.get('https://searchad.naver.com/')

        time.sleep(1.00) 
        driver.find_element_by_id('uid').send_keys(id)    
        driver.find_element_by_id('upw').send_keys(password)    
        driver.find_element_by_id('upw').send_keys(Keys.RETURN)    

        time.sleep(2.00) 

        try : 
            alert = driver.switch_to_alert()
        except:
            alert = None
        

        if alert == None : 

            time.sleep(1.00) 
            if len(driver.window_handles) > 1 :
                driver.switch_to_window(driver.window_handles[1])
                driver.close()
                driver.switch_to_window(driver.window_handles[0])
                    
            driver.id = id
            driver.password = password
            driver.status = 'run'
            driver.touchtime = datetime.datetime.now()
            driver.refreshcount = 0

            driverlist.append(driver) 

        else : 
            qry.execute("insert into Dat_NavShopEdit_log values (" + seq + ", getdate(), 'login fail')")
            alert.accept()
            driver.quit()
            driver = None


    return driver


if __name__ =='__main__':
    if not os.path.isdir(temppath) :
        os.makedirs(temppath)

    isrunning = True

    while isrunning:
        print('process time : ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        
        try:
            rows = requests.get(hosturl + "datnaver/getwork").json()

            if len(rows) < 1 :
                time.sleep(10.00)         
                for item in driverlist:
                    item.refreshcount = item.refreshcount + 1
                    if item.refreshcount > 20 :
                        item.quit()
                        driverlist.remove(item)
                    else : 
                        item.refresh()   
                        
            for row in rows:
                try :
                    seq = str(row["seq"])
                    print("seq = " + seq)
                    requests.get(hosturl + "datnaver/getwork/" + seq)


                    trycount = row['trycount']
                    id = row['id']
                    password = row['password']
                    customerid = row['customerid']
                    adid = row['adid']
                    title = row['title']
                    imagesize = row['imagesize']
                    

                    if imagesize > 0 :
                        ImageName = row['imagename']
                        imagepath = temppath + ImageName

                    naveradurl = 'https://manage.searchad.naver.com/customers/' + customerid + '/ads/' + adid
                    aresult = True
                    driver = getwebdirver(seq, id, password)
                    try :
                        

                        if (title != None) or (imagesize > 0) :
                            driver.get(naveradurl) 
                            time.sleep(2.00) 

                            try: 

                                errormessage = driver.find_element_by_css_selector('#toast-container > div > div').text
                                if len(errormessage) > 1 :
                                    aresult = False
                                    try : 
                                        setlog(seq, errormessage)
                                    except exception as e :
                                        print(e)
                            except:
                                print('url go')                             
                        
                            driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div[1]/span/button').click()
                            time.sleep(1.00)   


                            if title != None :
                                if len(title) > 25 : 
                                    setlog(seq, "title length over 25")
                                    aresult = False
                                else : 
                                    driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(Keys.CONTROL + "a")
                                    driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(Keys.DELETE)
                                    driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(title) 

                            

                            if imagesize > 0 :
                                print('imagesize = ' + str(imagesize))         
                                try: 
                                    driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[4]/div[2]/div[1]/div[2]/div/div[1]/button').click()
                                except:
                                    print('button None')


                                dropzone = driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[4]/div[2]/div[1]/div[2]/div/div/div/div[2]/div')
                                imagedata = requests.get(hosturl + "datnaver/getimage/" + seq, allow_redirects=True)
                                open(imagepath, 'wb').write(imagedata.content)

                                # f = open(imagepath, 'wb')
                                # f.write(imagedata)
                                # f.close()
                                dropzone.drop_files(imagepath)


                                try: 
                                    errormessage = driver.find_element_by_css_selector('#toast-container > div > div').text
                                    if len(errormessage) > 1 :
                                        aresult = False
                                        try : 
                                            setlog(seq, errormessage)
                                        except exception as e :
                                            print(e)
                                except:
                                    print('drop ok')      

                            time.sleep(1.00)
                            driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[3]/button[1]').click() 

                            if aresult == True : 
                                requests.get(hosturl + "datnaver/setstatus/" + seq + "/30", allow_redirects=True)
                                # qry.execute('update Dat_NavShopEdit set status = 30, Update_DT=getdate() where seq=' + seq)
                            else :

                                if trycount > 3 :    
                                    requests.get(hosturl + "datnaver/setstatus/" + seq + "/40", allow_redirects=True)
                                    # qry.execute('update Dat_NavShopEdit set status = 40, Update_DT=getdate() where seq=' + seq)
                                else : 
                                    requests.get(hosturl + "datnaver/setstatus/" + seq + "/10", allow_redirects=True)
                                    # qry.execute('update Dat_NavShopEdit set status = 10, Update_DT=getdate() where seq=' + seq)


                            driver.status = 'idle'
                            time.sleep(1.00)             

                            if imagesize > 0 :
                                os.remove(imagepath)



                    except :
                        if driver != None : 
                            driver.status = 'idle'
                        
                        if trycount > 3 :
                            requests.get(hosturl + "datnaver/setstatus/" + seq + "/40", allow_redirects=True)
                            # qry.execute('update Dat_NavShopEdit set status = 40, Update_DT=getdate() where seq=' + seq)
                        else :
                            requests.get(hosturl + "datnaver/setstatus/" + seq + "/10", allow_redirects=True)
                            # qry.execute('update Dat_NavShopEdit set status = 10, Update_DT=getdate() where seq=' + seq)


                except exception as e :
                    print("fetch error", e)
        except :
            print("requests error ")

        




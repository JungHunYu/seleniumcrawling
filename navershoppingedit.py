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
import pymssql
# import pyodbc
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

    conn = pymssql.connect(host="112.216.80.54",user='solution',password='solu0601!@', database='DatNaver', port='14331', charset='EUC-KR', autocommit=True)
    cur1 = conn.cursor(as_dict=True)
    cur2 = conn.cursor(as_dict=True)
    qry = conn.cursor(as_dict=True)

    # conn =  pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=112.216.80.54,14331;DATABASE=DatNaver;UID=solution;PWD=solu0601!@')
    # cur1 = conn.cursor()
    # cur2 = conn.cursor()
    # qry = conn.cursor()


    
    isrunning = True

    while isrunning:
        print('process time : ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        
        cur1.execute("SELECT top 1 a.seq FROM Dat_NavShopEdit a where a.status = 10 and a.Trycount < 4 order by a.num asc")
        rows = cur1.fetchall()

        
        if len(rows) > 0 :
            for row in rows:
                seq = str(row['seq'])
                print('into seq : ' + seq)

                qry.execute('update Dat_NavShopEdit set status = 20, Trycount = Trycount + 1, Update_DT=getdate() where seq=' + seq)
                try:
                    cur2.execute("SELECT a.*, isnull(datalength(a.Image) , 0) as imagesize FROM Dat_NavShopEdit a where seq = " + seq)
                    citem = cur2.fetchone()
                        

                    trycount = citem['trycount'] + 1
                    id = citem['ID']
                    password = citem['Password']
                    customerid = citem['CustomerId']
                    adid = citem['AdId']
                    title = citem['Title']
                    imagesize = citem['imagesize']

                    print('into id : ' + id)
                    if title != None:
                        print('into title : ' + title)

                    driver = getwebdirver(seq, id, password)
                    try:
                        aresult = True

                        
                        url1 = 'https://manage.searchad.naver.com/customers/' + customerid + '/ads/' + adid
                        
                        print('url1 : ' + url1)

                        if driver == None :
                            raise NameError('로그인불가')

                        driver.get(url1) 
                        time.sleep(2.00) 


                        try: 
                            errormessage = driver.find_element_by_css_selector('#toast-container > div > div').text
                            if len(errormessage) > 1 :
                                aresult = False
                                try : 
                                    qry.execute("insert into Dat_NavShopEdit_log values (%d, getdate(), %s)", (seq, errormessage.encode('euc-kr')))
                                except exception as e :
                                    print(e)
                        except:
                            print('url go')                          



                        driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div[1]/span/button').click()
                        time.sleep(1.00)   



                        if title != None :
                            if len(title) > 25 : 
                                qry.execute("insert into Dat_NavShopEdit_log values (" + seq + ", getdate(), 'title length over 25')")    
                                aresult = False
                            else : 
                                driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(Keys.CONTROL + "a")
                                driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(Keys.DELETE)
                                driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/input').send_keys(title) 






                        if imagesize > 0 :

                            try: 
                                driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[4]/div[2]/div[1]/div[2]/div/div[1]/button').click()
                            except:
                                print('button None')


                            dropzone = driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[2]/div/div[4]/div[2]/div[1]/div[2]/div/div/div/div[2]/div')
                            imagedata = citem['Image']
                            imagepath = temppath + citem['ImageName']
                            

                            f = open(imagepath, 'wb')
                            f.write(imagedata)
                            f.close()
                            dropzone.drop_files(imagepath)


                            try: 
                                errormessage = driver.find_element_by_css_selector('#toast-container > div > div').text
                                if len(errormessage) > 1 :
                                    aresult = False
                                    try : 
                                        qry.execute("insert into Dat_NavShopEdit_log values (%d, getdate(), %s)", (seq, errormessage.encode('euc-kr')))
                                    except exception as e :
                                        print(e)
                            except:
                                print('drop ok')           


                        time.sleep(1.00)
                        driver.find_element_by_xpath('/html/body/div[4]/div/div[1]/div/div/div[3]/button[1]').click()


                        if aresult == True : 
                            qry.execute('update Dat_NavShopEdit set status = 30, Update_DT=getdate() where seq=' + seq)
                        else :

                            if trycount > 3 :    
                                qry.execute('update Dat_NavShopEdit set status = 40, Update_DT=getdate() where seq=' + seq)
                            else : 
                                qry.execute('update Dat_NavShopEdit set status = 10, Update_DT=getdate() where seq=' + seq)


                        driver.status = 'idle'
                        time.sleep(1.00)             

                        if imagesize > 0 :
                            os.remove(imagepath)

                    except:
                        # print('error Seq : ' + seq)
                        if driver != None : 
                            driver.status = 'idle'
                        
                        if trycount > 3 :
                            qry.execute('update Dat_NavShopEdit set status = 40, Update_DT=getdate() where seq=' + seq)
                        else :
                            qry.execute('update Dat_NavShopEdit set status = 10, Update_DT=getdate() where seq=' + seq)


                except:
                    qry.execute("insert into Dat_NavShopEdit_log values (" + seq + ", getdate(), 'system data fetch parser error')")    

        else :
            time.sleep(10.00)        
            for item in driverlist:
                item.refreshcount = item.refreshcount + 1
                if item.refreshcount > 20 :
                    item.quit()
                    driverlist.remove(item)
                else : 
                    item.refresh()

            time.sleep(10.00)                 

        
    conn.Close()

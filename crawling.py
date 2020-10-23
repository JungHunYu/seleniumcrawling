from http.server import HTTPServer, BaseHTTPRequestHandler
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import simplejson
import time
import sys
import platform

global drivercount

if platform.system() == 'Windows':
    drivercount = 1
else :
    drivercount = 10


global driverlist
driverlist  = []



class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global requestcount
        requestcount = requestcount + 1

        databody = (self.rfile.read(int(self.headers['content-length']))).decode('utf-8')
        print(databody)
        datajson = simplejson.loads(databody)   
        
        index = requestcount%drivercount
        driver = driverlist[index]

        geturl = datajson["URL"]
        timeout = int(datajson["TIMEOUT"])
        response_code = 200
        
        submitoptionfindobject = ''
        submitoptionfindname = ''
        submitoptioninputtext = ''

        completeoptionmode = ''
        completeoptionfindobject = ''
        completeoptionfindname = ''
        completeoptionfindvalue = ''
        

        if 'SUBMITOPTION' in datajson.keys() :
            submitoptionfindobject = datajson["SUBMITOPTION"]["FINDOBJECT"].upper()
            submitoptionfindname = datajson["SUBMITOPTION"]["FINDNAME"]
            submitoptioninputtext = datajson["SUBMITOPTION"]["INPUTTEXT"]


        if 'COMPLETEOPTION' in datajson.keys() :
            completeoptionmode = datajson["COMPLETEOPTION"]["MODE"].upper()
            completeoptionfindobject = datajson["COMPLETEOPTION"]["FINDOBJECT"].upper()
            completeoptionfindname = datajson["COMPLETEOPTION"]["FINDNAME"]            
            completeoptionfindvalue = datajson["COMPLETEOPTION"]["FINDVALUE"]            
            
        print(
            "URL : " + geturl, 
            "TIMEOUT : " + str(timeout), 
            "SUBMITOPTION FINDOBJECT : " + submitoptionfindobject, 
            "SUBMITOPTION FINDNAME : " + submitoptionfindname, 
            "SUBMITOPTION INPUTTEXT : " + submitoptioninputtext, 
            "COMPLETEOPTION MODE : " + completeoptionmode, 
            "COMPLETEOPTION FINDOBJECT : " + completeoptionfindobject, 
            "COMPLETEOPTION FINDNAME : " + completeoptionfindname, 
            "drivercount : " + str(drivercount), 
            "requestcount : " + str(requestcount), 
            "index : " + str(index), sep='\n'
            )


        driver.get(geturl)
        
        if submitoptionfindname != '':
            time.sleep(0.01)    
            if submitoptionfindobject == 'ID':
                wait = WebDriverWait(driver, timeout)
                elem = wait.until(EC.element_to_be_clickable((By.ID, submitoptionfindname))) 
                item = driver.find_element_by_id(submitoptionfindname)
                item.click()

                for word in submitoptioninputtext:
                    item.send_keys(word)    
                    time.sleep(0.01)  

                item.send_keys(Keys.RETURN)    

        
        nowtime = time.time()
        thentime = nowtime + timeout
        if completeoptionmode == 'VISIBLE':

            if completeoptionfindobject == 'CLASSNAME':
                items = driver.find_elements_by_class_name(completeoptionfindname)
                while len(items) < 1:
                    time.sleep(0.01)    
                    thistime = time.time()
                    items = driver.find_elements_by_class_name(completeoptionfindname)
                    print('VISIBLE CLASSNAME nowtime : ' + str(nowtime) + ' thentime : ' + str(thentime) + ' thistime : ' + str(thistime))
                    if thistime > thentime:
                        break

            elif completeoptionfindobject == 'ID':
                wait = WebDriverWait(driver, timeout)
                try:
                    elem = wait.until(EC.element_to_be_clickable((By.ID, completeoptionfindname))) 
                except:
                    response_code = 500
                    print('ID Find fail : ' + completeoptionfindname)
            elif completeoptionfindobject == '':
                time.sleep(timeout)    

        elif completeoptionmode == 'VALUE':
            if completeoptionfindobject == 'ID':
                try:
                    wait = WebDriverWait(driver, timeout)
                    elem = wait.until(EC.element_to_be_clickable((By.ID, completeoptionfindname))) 
                    # item = driver.find_element_by_id(completeoptionfindname)
                    item = driver.find_element_by_xpath("//input[@id='nx_query_btm']")
                    while item.get_attribute('value') != completeoptionfindvalue :
                        time.sleep(0.01)    
                        thistime = time.time()
                        item = driver.find_element_by_xpath("//input[@id='nx_query_btm']")
                        print('VALUE ID nowtime : ' + str(nowtime) + ' thentime : ' + str(thentime) + ' thistime : ' + str(thistime))

                        if thistime > thentime:
                            break      
                except:
                    response_code = 500
                    print('ID Find fail : ' + completeoptionfindname)
                    
        html_source = driver.page_source  

        # print(html_source)  
        print(driver.current_url)
        self.send_response_only(response_code, 'OK')
        self.send_header('Content-Type', 'text/plan')
        self.send_header('current_url', driver.current_url)
        self.end_headers()
        self.wfile.write(html_source.encode("utf-8"))             
if __name__ =='__main__':
    global requestcount
    requestcount = 0
    server = HTTPServer(('', int(sys.argv[1])), MyHandler)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--incognito")
    options.add_argument("--disable-notifications")
    options.add_argument('--no-sandbox')
    options.add_argument('--verbose')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    for i in range(0, drivercount): 
        options.add_argument('window-position=' + str(i*100) + ',' + str(i*100))
        if platform.system() == 'Windows':
            driverlist.append(webdriver.Chrome('.\chromedriver.exe', chrome_options=options)) 
        else :
            driverlist.append(webdriver.Chrome('/web/chromedriver', chrome_options=options)) 


    print('Solution Rending Check Server on port ' + sys.argv[1]  + '...')
    print('Press ^c to quit server')
    server.serve_forever()

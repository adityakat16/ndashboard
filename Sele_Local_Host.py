# sele.py
import selenium
#from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
#from selenium.webdriver.chrome.service import Service
#from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import time
import re
import sys
import string
import os

sys.stdout.reconfigure(encoding='utf-8')


def extract_number(text):
    matches = re.findall(r'[-+]?\d[\d,]*\.?\d*', text)
    if matches:
        num = matches[0].replace(',', '')
        try:
            return float(num)
        except ValueError:
            pass
    return 0.0

def annual_info(driver):
   
    #Periods
    aPeriods=[]
    driver.find_element(By.XPATH,'//*[@id="shareholding"]/div[1]/div[2]/div[1]/button[2]').click() #eps yearly button
    perall=driver.find_elements(By.XPATH,'//*[@id="profit-loss"]/div[2]/table/thead/tr/th')
    perean=driver.find_elements(By.XPATH,'//*[@id="yearly-shp"]/div/table/thead/tr/th')
    ncae=len(perean)
    if len(perall)>2:
        if len(perall) >= len(perean):
            for i in range(1,len(perall)):
                aPeriods.append(perall[i].text)
        else:
            for i in range(1,len(perean)):
                aPeriods.append(perean[i].text)
    else:
        perall=driver.find_elements(By.XPATH,'//*[@id="profit-loss"]/div[3]/table/thead/tr/th')
        if len(perall) >= len(perean):
            for i in range(1,len(perall)):
                aPeriods.append(perall[i].text)
        else:
            for i in range(1,len(perean)):
                aPeriods.append(perean[i].text)
    
    #Annual sales
    sales=[]
    salesa_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[2]/table/tbody/tr[1]/td')
    num_cols = len(salesa_row)
    if num_cols>2:
        nca=num_cols
        if nca<ncae:
            for i in range(ncae-nca):
                sales.append(0)
        for i in range(2, num_cols + 1):
            svalue=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[2]/table/tbody/tr[1]/td[{i}]').text
            salesnum = extract_number(svalue)
            sales.append(int(salesnum))
    else:
        salesa_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[1]/td')
        num_cols=len(salesa_row)
        nca=num_cols
        if nca<ncae:
            for i in range(ncae-nca):
                sales.append(0)
        for i in range(2, num_cols + 1):
            svalue=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[1]/td[{i}]').text
            salesnum = extract_number(svalue)
            sales.append(int(salesnum))

    #Annual other income
    #for banks only
    if driver.find_element(By.XPATH,'//*[@id="peers"]/div[1]/div[1]/p[1]/a[3]').text=='Banks':
        aoincomen=[]
        aoi_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[6]/td')
        num_cols = len(aoi_row)
        ncs=num_cols
        if ncs<nca:
                for i in range(nca-ncs):
                    aoincomen.append(0)
        for i in range(2, num_cols + 1):
            aoivalue=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[6]/td[{i}]').text
            aoinum = extract_number(aoivalue)
            aoincomen.append(int(aoinum))
        ainst = []
        ainrow=driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[2]/td')
        num_cols=len(ainrow)
        if ncs<nca:
                for i in range(nca-ncs):
                    ainst.append(0)
        if num_cols>2:
            for i in range(2, num_cols + 1):
                ainsta=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[2]/td[{i}]').text
                ainum = extract_number(ainsta)
                ainst.append(int(ainum))
        else:
            ainst_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[2]/td')
            num_cols=len(ainst_row)
            for i in range(2, num_cols + 1):
                ainstq=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[2]/td[{i}]').text
                aoinum = extract_number(ainstq)
                ainst.append(int(aoinum))
        oincome=[]
        if ncs<nca:
            for i in range(nca-ncs):
                oincome.append(0)
        for i in range(0, num_cols-1):
            val=aoincomen[i]+ainst[i]
            oincome.append(val)
        
    else:
        oincome=[]
        oia_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[2]/table/tbody/tr[1]/td')
        num_cols = len(oia_row)
        if nca<ncae:
                for i in range(ncae-nca):
                    oincome.append(0)
        if num_cols>2:
            for i in range(2, num_cols + 1):
                oivalue=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[2]/table/tbody/tr[5]/td[{i}]').text
                oinum = extract_number(oivalue)
                oincome.append(int(oinum))
        else:
            oia_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[1]/td')
            num_cols=len(oia_row)
            for i in range(2, num_cols + 1):
                oivalue=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[5]/td[{i}]').text
                oinum = extract_number(oivalue)
                oincome.append(int(oinum))

    #total revenue
    totrev=[]
    for i in range(0, len(oincome)):
        val=oincome[i]+sales[i]
        totrev.append(int(val))

    #revenue growth
    rg=[]
    rg.append(0)
    if nca<ncae:
            for i in range(ncae-nca):
                rg.append(0)
    for i in range(0, len(oincome)-1):
        if totrev[i] == 0 : continue
        val=(totrev[i+1]-totrev[i])*100/totrev[i]
        rounded = round(val, 1)
        valper=str(rounded)+"%"
        rg.append(valper)

    #consolidated net profit
    np=[]
    np_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[2]/table/tbody/tr[10]/td')
    num_cols = len(np_row)
    if nca<ncae:
        for i in range(ncae-nca):
            np.append(0)
    if num_cols>2:
        for i in range(1, num_cols + 1):
            npnum=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[2]/table/tbody/tr[10]/td[{i}]').text
            number_string = re.findall(r'[\d\.]+', npnum)
            if not number_string: continue
            npp = extract_number(npnum)
            np.append(int(npp))
    else:
        np_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[10]/td')
        num_cols=len(np_row)
        for i in range(1, num_cols + 1):
            npnum=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[10]/td[{i}]').text
            number_string = re.findall(r'[\d\.]+', npnum)
            if not number_string: continue
            npp = extract_number(npnum)
            np.append(int(npp))

    #Net profit margin
    npm=[]
    if nca<ncae:
        for i in range(ncae-nca):
            npm.append(0)
    for i in range(0, len(np)):
        if totrev[i] == 0: continue
        val=(np[i]/totrev[i])*100
        rounded = round(val, 1)
        strval=str(rounded)+'%'
        npm.append(strval)

    #EPS
    eps=[]
    if nca<ncae:
        for i in range(ncae-nca):
            eps.append(0)
    eps_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[2]/table/tbody/tr[11]/td')
    num_cols = len(eps_row)
    if num_cols>2:
        for i in range(2, num_cols + 1):
            epsnum=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[2]/table/tbody/tr[11]/td[{i}]').text        
            epsn = extract_number(epsnum)
            eps.append(epsn)
    else:
        eps_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[11]/td')
        num_cols=len(eps_row)
        for i in range(2, num_cols + 1):
            epsnum=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[11]/td[{i}]').text        
            epsn = extract_number(epsnum)
            eps.append(epsn)

    #EPS growth
    epsg=[]
    epsg.append(0)
    if nca<ncae:
        for i in range(ncae-nca):
            epsg.append(0)
    for i in range(0, len(eps)-1):
        if eps[i]==0:continue
        val=(eps[i+1]-eps[i])*100/eps[i]
        rounded = round(val, 1)
        valper=str(rounded)+"%"
        epsg.append(valper)

    #dividend payout
    dp=[]
    if nca<ncae:
            for i in range(ncae-nca):
                dp.append(0)
    div_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[2]/table/tbody/tr[12]/td')
    num_cols = len(div_row)
    if num_cols>2:
        for i in range(1, num_cols + 1):
            dpnum=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[2]/table/tbody/tr[12]/td[{i}]').text
            number_string = re.findall(r'[\d,\.]+', dpnum)
            if number_string:
                dp.append(dpnum)
    else:
        div_row = driver.find_elements(By.XPATH, '//*[@id="profit-loss"]/div[3]/table/tbody/tr[12]/td')
        num_cols=len(div_row)
        for i in range(1, num_cols + 1):
            dpnum=driver.find_element(By.XPATH,f'//*[@id="profit-loss"]/div[3]/table/tbody/tr[12]/td[{i}]').text
            number_string = re.findall(r'[\d,\.]+', dpnum)
            if number_string:
                dp.append(dpnum)

    #promoter annual
    driver.find_element(By.XPATH,'//*[@id="shareholding"]/div[1]/div[2]/div[1]/button[2]').click()
    proan=[]
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="yearly-shp"]/div/table/tbody/tr[1]/td[1]')))
    proan_row = driver.find_elements(By.XPATH, '//*[@id="yearly-shp"]/div/table/tbody/tr[1]/td')
    num_cols = len(proan_row)
    if num_cols<nca :
        for i in range(nca-num_cols):
            proan.append("NA")

    for i in range(1, num_cols + 1):
        pronum=driver.find_element(By.XPATH,f'//*[@id="yearly-shp"]/div/table/tbody/tr[1]/td[{i}]').text
        number_string = re.findall(r'[\d\.]+', pronum)
        if not number_string: continue
        pronumr=extract_number(pronum)
        rounded=round(pronumr,1)
        proan.append(str(rounded)+' %')

    #FII% annual
    fiian=[]
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="yearly-shp"]/div/table/tbody/tr[2]/td[1]')))
    afii_row = driver.find_elements(By.XPATH, '//*[@id="yearly-shp"]/div/table/tbody/tr[2]/td')
    num_cols = len(afii_row)
    if num_cols<nca :
        for i in range(nca-num_cols):
            fiian.append("NA")

    for i in range(1, num_cols + 1):
        fiinum=driver.find_element(By.XPATH,f'//*[@id="yearly-shp"]/div/table/tbody/tr[2]/td[{i}]').text
        number_string = re.findall(r'[\d\.]+', fiinum)
        if not number_string: continue
        fiinumr=extract_number(fiinum)
        rounded=round(fiinumr,1)
        fiian.append(str(rounded)+' %')



    #DII% annual
    diian=[]
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="yearly-shp"]/div/table/tbody/tr[3]/td[1]')))
    adii_row = driver.find_elements(By.XPATH, '//*[@id="yearly-shp"]/div/table/tbody/tr[3]/td')
    num_cols = len(adii_row)
    if num_cols<nca :
        for i in range(nca-num_cols):
            diian.append("NA")

    for i in range(1, num_cols + 1):
        diinum=driver.find_element(By.XPATH,f'//*[@id="yearly-shp"]/div/table/tbody/tr[3]/td[{i}]').text
        number_string = re.findall(r'[\d\.]+', diinum)
        if not number_string: continue
        diinumr=extract_number(diinum)
        rounded=round(diinumr,1)
        diian.append(str(rounded)+' %')
        
    return {
        "asales": sales,
        "aOther_Income": oincome,
        "aTotal_Revenue": totrev,
        "aRevenue_Growth":rg,
        "aNet_Profit":np,
        "aNet_Profit_Margin": npm,
        "aEPS": eps,        
        "aEPS_Growth": epsg,
        "aDividend_Payout": dp,
        "aPromoter": proan,
        "aFII": fiian,
        "aDII": diian,
        "aPeriods":aPeriods
    }
    
    
    
def quaterly_info(driver):
    
    qPeriods=[]
    perall=driver.find_elements(By.XPATH,'//*[@id="quarters"]/div[2]/table/thead/tr/th')
    ncqe=len(perall)
    
    if len(perall)>2:
        for i in range(1,len(perall)):
            qPeriods.append(perall[i].text)
    else:
        perall=driver.find_elements(By.XPATH,'//*[@id="quarters"]/div[3]/table/thead/tr/th')
        for i in range(1,len(perall)):
            qPeriods.append(perall[i].text)
            
    #Quaterly sales
    qsales=[]
    sales_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]/table/tbody/tr[1]/td') 
    perqeps=driver.find_elements(By.XPATH,'//*[@id="quarterly-shp"]/div/table/thead/tr/th')
    num_cols = len(sales_row)
    if num_cols>2:
        nc=num_cols
        if nc<ncqe:
            for i in range(ncqe-nc):
                qsales.append(0)
        for i in range(2, num_cols + 1):
            qsvalue=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[2]/table/tbody/tr[1]/td[{i}]').text
            qsalesnum = extract_number(qsvalue)
            qsales.append(int(qsalesnum))
    else:
        sales_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[1]/td')
        num_cols=len(sales_row)
        nc=num_cols
        if nc<ncqe:
            for i in range(ncqe-nc):
                qsales.append(0)
        for i in range(2, num_cols + 1):
            qsvalue=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[3]/table/tbody/tr[1]/td[{i}]').text
            qsalesnum = extract_number(qsvalue)
            qsales.append(int(qsalesnum))
            

    #Quaterly other income
    #for banks only
    if driver.find_element(By.XPATH,'//*[@id="peers"]/div[1]/div[1]/p[1]/a[3]').text=='Banks':
        qoincomen=[]
        qoi_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]/table/tbody/tr[6]/td')
        num_cols = len(qoi_row)
        if nc<ncqe:
                for i in range(ncqe-nc):
                    qoincomen.append(0)
        if num_cols>2:
            for i in range(2, num_cols + 1):
                qoivalue=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[2]/table/tbody/tr[6]/td[{i}]').text
                qoinum = extract_number(qoivalue)
                qoincomen.append(int(qoinum))
        else:
            qoi_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[6]/td')
            num_cols=len(qoi_row)
            for i in range(2, num_cols + 1):
                qoivalue=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[3]/table/tbody/tr[6]/td[{i}]').text
                qoinum = extract_number(qoivalue)
                qoincomen.append(int(qoinum))
        qinst=[]
        qinrow=driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]/table/tbody/tr[2]/td')
        num_cols=len(qinrow)
        if nc<ncqe:
                for i in range(ncqe-nc):
                    qinst.append(0)
        if num_cols>2:
            for i in range(2, num_cols + 1):
                qinst=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[2]/table/tbody/tr[2]/td[{i}]').text
                qinum = extract_number(qinst)
                qinst.append(int(qinum))
        else:
            qinst_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[2]/td')
            num_cols=len(qinst_row)
            for i in range(2, num_cols + 1):
                qinstq=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[3]/table/tbody/tr[2]/td[{i}]').text
                qoinum = extract_number(qinstq)
                qinst.append(int(qoinum))
        qoincome=[]
        if nc<ncqe:
            for i in range(ncqe-nc):
                qoincome.append(0)
        for i in range(0, num_cols-1):
            val=qoincomen[i]+qinst[i]
            qoincome.append(val)
        
    #other than banks
    else:
        qoincome=[]
        qoi_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]/table/tbody/tr[5]/td')
        num_cols = len(qoi_row)
        if nc<ncqe:
                for i in range(ncqe-nc):
                    qoincome.append(0)
        if num_cols>2:
            for i in range(2, num_cols + 1):
                qoivalue=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[2]/table/tbody/tr[5]/td[{i}]').text
                qoinum = extract_number(qoivalue)
                qoincome.append(int(qoinum))
        else:
            qoi_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[5]/td')
            num_cols=len(qoi_row)
            for i in range(2, num_cols + 1):
                qoivalue=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[3]/table/tbody/tr[5]/td[{i}]').text
                qoinum = extract_number(qoivalue)
                qoincome.append(int(qoinum))

    #total revenue quaterly
    qtotrev=[]
    if nc<ncqe:
        for i in range(ncqe-nc):
            qtotrev.append(0)
    for i in range(0, num_cols-1):
        val=qoincome[i]+qsales[i]
        qtotrev.append(val)
    
    #revenue growth quaterly
    rgq=[]
    rgq.append('0')
    if nc<ncqe:
        for i in range(ncqe-nc):
            rgq.append(0)
    for i in range(0, num_cols - 2):
        if qtotrev[i]==0: continue
        val=(qtotrev[i+1]-qtotrev[i])*100/qtotrev[i]
        rounded = round(val, 1)
        valper=str(rounded)+"%"
        rgq.append(valper)

    #consolidated net profit quaterly
    npq=[]
    npq_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]/table/tbody/tr[1]/td')
    num_cols = len(npq_row)
    if nc<ncqe:
            for i in range(ncqe-nc):
                npq.append(0)
    if num_cols>2:
        for i in range(1, num_cols + 1):
            npqnum=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[2]/table/tbody/tr[10]/td[{i}]').text
            number_string = re.findall(r'[\d\.]+', npqnum)
            if not number_string: continue
            nppq = extract_number(npqnum)
            npq.append(int(nppq))
    else:
        npq_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[1]/td')
        num_cols=len(npq_row)
        for i in range(1, num_cols + 1):
            npqnum=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[3]/table/tbody/tr[10]/td[{i}]').text
            number_string = re.findall(r'[\d\.]+', npqnum)
            if not number_string: continue
            nppq = extract_number(npqnum)
            npq.append(int(nppq))
            

    #Net profit margin
    npqm=[]
    if nc<ncqe:
        for i in range(ncqe-nc):
            npqm.append(0)
    for i in range(0, num_cols - 1):
        if qtotrev[i]==0: continue
        val=(npq[i]/qtotrev[i])*100
        rounded = round(val, 1)
        strval=str(rounded)+'%'
        npqm.append(strval)

    #EPS quaterly
    epsq=[]
    if ncqe<nc:
            for i in range(ncqe-nc):
                epsgq.append(0)
    epsq_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[2]/table/tbody/tr[11]/td')
    num_cols = len(epsq_row)
    if num_cols > 2:
        for i in range(2, num_cols + 1):
            epsqnum=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[2]/table/tbody/tr[11]/td[{i}]').text
            epsqn = extract_number(epsqnum)
            epsq.append(epsqn)
    else:
        epsq_row = driver.find_elements(By.XPATH, '//*[@id="quarters"]/div[3]/table/tbody/tr[11]/td')
        num_cols=len(epsq_row)
        for i in range(2, num_cols + 1):
            epsqnum=driver.find_element(By.XPATH,f'//*[@id="quarters"]/div[3]/table/tbody/tr[11]/td[{i}]').text
            epsqn = extract_number(epsqnum)
            epsq.append(epsqn)

    #EPS growth quaterly
    epsgq=[]
    epsgq.append('0')
    if ncqe<nc:
        for i in range(ncqe-nc):
            epsgq.append(0)
    for i in range(0, num_cols - 2):
        if epsq[i] == 0: continue
        val=(epsq[i+1]-epsq[i])*100/epsq[i]
        rounded = round(val, 1)
        valper=str(rounded)+"%"
        epsgq.append(valper)

    #promoter quaterly
    qpro=[]
    qpro_row = driver.find_elements(By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[1]/td')
    num_cols = len(qpro_row)
    if num_cols<nc :
        for i in range(nc-num_cols):
            qpro.append("NA")

    for i in range(1, num_cols + 1):
        qpronum=driver.find_element(By.XPATH,f'//*[@id="quarterly-shp"]/div/table/tbody/tr[1]/td[{i}]').text
        number_string = re.findall(r'[\d\.]+', qpronum)
        if not number_string: continue
        qpronumr=extract_number(qpronum)
        rounded=round(qpronumr,1)
        qpro.append(str(rounded)+' %')

    #FII% quaterly
    qfii=[]
    qfii_row = driver.find_elements(By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[1]/td')
    num_cols = len(qfii_row)
    if num_cols<nc :
        for i in range(nc-num_cols):
            qfii.append("NA")

    for i in range(1, num_cols + 1):
        qfiinum=driver.find_element(By.XPATH,f'//*[@id="quarterly-shp"]/div/table/tbody/tr[2]/td[{i}]').text
        number_string = re.findall(r'[\d\.]+', qfiinum)
        if not number_string: continue
        qfiinumr=extract_number(qpronum)
        rounded=round(qfiinumr,1)
        qfii.append(str(rounded)+' %')

    #DII% quaterly
    qdii=[]
    qdii_row = driver.find_elements(By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[1]/td')
    num_cols = len(qdii_row)
    if num_cols<nc :
        for i in range(nc-num_cols):
            qdii.append("NA")

    for i in range(1, num_cols + 1):
        qdiinum=driver.find_element(By.XPATH,f'//*[@id="quarterly-shp"]/div/table/tbody/tr[3]/td[{i}]').text
        number_string = re.findall(r'[\d\.]+', qdiinum)
        if not number_string: continue
        qdiinumr=extract_number(qdiinum)
        rounded=round(qdiinumr,1)
        qdii.append(str(rounded)+' %')
        
    return {
        "qsales": qsales,
        "qOther_Income": qoincome,
        "qTotal_Revenue": qtotrev,
        "qRevenue_Growth":rgq,
        "qNet_Profit":npq,
        "qNet_Profit_Margin": npqm,
        "qEPS": epsq,        
        "qEPS_Growth": epsgq,
        "qPromoter": qpro,
        "qFII": qfii,
        "qDII": qdii,
        "qPeriods":qPeriods
    }


    #Quaterly info ends here   

    
    
    
def run_scraper(stock):
    # Set Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    
    chrome_binary_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe" # Example: r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.binary_location = chrome_binary_path
    driver = uc.Chrome(options=options)

    #navigate to screener.com
    driver.get("https://www.screener.in/")
    #driver.maximize_window()
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div[2]/div/div/div/input')))
    driver.find_element(By.XPATH, "/html/body/main/div[2]/div/div/div/input").send_keys(stock)
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div[2]/div/div/div/ul/li[1]')))
    driver.find_element(By.XPATH, "/html/body/main/div[2]/div/div/div/ul/li[1]").click()
    
    
    #shareholding patterns
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="top"]/div[1]/div/h1')))
    STOCK=driver.find_element(By.XPATH,'//*[@id="top"]/div[1]/div/h1').text
    PROMOTERS = driver.find_element(By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[1]/td[13]').text
    MCAP=driver.find_element(By.XPATH,'//*[@id="top-ratios"]/li[1]/span[2]/span').text
    FII = driver.find_element(By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[2]/td[13]').text
    DII = driver.find_element(By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[3]/td[13]').text
    PUBLIC = driver.find_element(By.XPATH, '//*[@id="quarterly-shp"]/div/table/tbody/tr[5]/td[13]').text
    CMP = driver.find_element(By.XPATH, '//*[@id="top-ratios"]/li[2]/span[2]/span').text
    F_HIGH = driver.find_element(By.XPATH, '//*[@id="top-ratios"]/li[3]/span[2]/span[1]').text
    F_LOW = driver.find_element(By.XPATH, '//*[@id="top-ratios"]/li[3]/span[2]/span[2]').text
    cmpn=extract_number(CMP)
    fln=extract_number(F_LOW)
    fhn=extract_number(F_HIGH)
    HLP=((cmpn-fln)*100)/(fhn-fln)
    roundedh = round(HLP, 2)
    hlper=str(roundedh)+"%"
    BV = driver.find_element(By.XPATH, '//*[@id="top-ratios"]/li[5]/span[2]').text
    BVn=extract_number(BV)
    PB=round(cmpn/BVn,1)
    time.sleep(3)
    
# Scroll into view to avoid intercept
    time.sleep(3)
    #pe3yr
    driver.find_element(By.XPATH, '//*[@id="company-chart-metrics"]/button[2]').click()
    #time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id="company-chart-metrics"]/button[2]').click()
    time.sleep(2)
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/section[1]/div[3]/label[2]/span')))
    pe_3yr_f = driver.find_element(By.XPATH, '/html/body/main/section[1]/div[3]/label[2]/span').text
    pe3l = pe_3yr_f.split()
    pe_3yr = pe3l[3]

    #pe5yr
    time.sleep(1)
    driver.find_element(By.XPATH,'//*[@id="company-chart-days"]/button[5]').click()
    time.sleep(2)
    pe_5yr_f = driver.find_element(By.XPATH, '//*[@id="chart-legend"]/label[2]/span').text
    pe5l = pe_5yr_f.split()
    pe_5yr = pe5l[3]  
    
    #pe current
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/section[1]/div[3]/label[2]/span')))
    peCur = driver.find_element(By.XPATH,'//*[@id="top-ratios"]/li[4]/span[2]/span').text
    
    #pe10yr
    driver.find_element(By.XPATH, '//*[@id="company-chart-days"]/button[6]').click()
    time.sleep(2)
    w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="chart-legend"]/label[2]/span')))
    pe_10yr_f = driver.find_element(By.XPATH, '//*[@id="chart-legend"]/label[2]/span').text
    pe10l = pe_10yr_f.split()
    pe_10yr = pe10l[3]

    #DY
    DYn = driver.find_element(By.XPATH, '//*[@id="top-ratios"]/li[6]/span[2]/span').text
    DY=str(DYn)+' %'
    time.sleep(3)
    try:
        #switch to consolidated:
        w=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="quarters"]/div[1]/div[1]/p/a')))
        driver.find_element(By.LINK_TEXT,'View Consolidated').click()
        time.sleep(2) 
    except:
        pass
    
    
    #Run the two functions
    quaterly_data=quaterly_info(driver)
    annual_data = annual_info(driver)
    
    #sales last mar
    saleslen=len(annual_data["asales"])
    sales=annual_data["asales"][saleslen-1]
    
    #MCAP/SALES
    msur=float(extract_number(MCAP))/float(sales)
    ms=round(msur,2)
    
    #Projections functions:
    s=0
    j=0
    neps=len(quaterly_data["qEPS_Growth"])
    if neps > 8:
        for i in range(neps-8,neps):
            #if float(extract_number(quaterly_data["qEPS_Growth"][i])) == 0.0: continue
            s=s+extract_number(quaterly_data["qEPS_Growth"][i])
            j+=1
        aveps=round(s/j,2)
    else:
        for i in range(0,neps):
            #if float(extract_number(quaterly_data["qEPS_Growth"][i])) == 0.0: continue
            s=s+extract_number(quaterly_data["qEPS_Growth"][i])
            j+=1
        aveps=round(s/j,2)
    avper=1+aveps/100
    yrepsur = aveps * (1 + avper + (avper**2) + (avper**3))
    yreps=round(yrepsur,2)
    yrper=1+yreps/100
    #Projected EPS
    aeps_len=len(annual_data["aEPS"])
    aeps=annual_data["aEPS"][aeps_len-1]
    aeps_prour=float(aeps) * (1+(yreps/100))
    aeps_pro=round(aeps_prour,2)
    
    # PE Calculation
    if pe_10yr<peCur:
        PEcal=float(pe_10yr)
    else:
        PEcal=float(peCur)
    
    #Projected stock price nyr
    propriur=PEcal * aeps_pro
    propri=round(propriur,0)
    
    #projected stock prive nnyr
    proprinnyur=yrper * propri
    proprinny=round(proprinnyur,0)
    # At the end, close driver:
    driver.quit()
    
    # RETURN collected data as a dict:
    return {
        
        "STOCK":STOCK,
        "PROMOTERS": PROMOTERS,
        "FII": FII,
        "DII": DII,
        "PUBLIC": PUBLIC,
        "CMP": CMP,
        "F_HIGH": F_HIGH,
        "F_LOW": F_LOW,
        "HiLoPer":hlper,
        "PB": PB,
        "peCur": peCur,
        "pe_3yr": pe_3yr,
        "pe_5yr": pe_5yr,
        "pe_10yr": pe_10yr,
        "DY": DY,
        "AvgEPSG":aveps,
        "YrEPSG":yreps,
        "EPSnyr":aeps_pro,
        "PEcal":PEcal,
        "Pro_Priceny":propri,
        "Pro_Pricenny":proprinny,
        "McapSales":ms,
        **quaterly_data,
        **annual_data
    }

# Allow standalone use:
if __name__ == "__main__":
    stock_symbol = 'icici'
    result = run_scraper(stock_symbol)
    print(result)

import requests
import argparse
from bs4 import BeautifulSoup
import json,sys, time, csv, os

BASE_URL = "https://search.ipaustralia.gov.au/trademarks/search/view/"

start = time.time()
isHeader = True
session = requests.session()

fieldnames = [    'ID',
                  'Words',
                  'IR number',
                  'IR notification',
                  'Kind',
                  'Class',
                  'Filing Date',
                  'First report Date',
                  'Registered From Date',
                  'Registration Advertised Date',
                  'Acception Advertised Date',
                  'Acception Date',
                  'Image',
                  'Image description',
                  'Priority Date',
                  'Renewal Due Date',
                  'Status',
                  'Owner',
                  'Address for service',
                  'IR Contact',
                  'History',
                  'Goods and services',
                  'Indexing constituents image',
                  'Indexing constituents word',
                  'Convention date',
                  'Convention number',
                  'Convention country'
              ]

def elapsed():
    return time.time() - start

def returnValue(key, dict):
    return dict[key] if key in dict else ''

def AdjustData(dict):
    rowdict = {}
    rowdict['ID'] =  returnValue('ID', dict)
    rowdict['Words'] = returnValue('Words', dict)
    rowdict['IR number'] = returnValue('IR number', dict)
    rowdict['IR notification'] = returnValue('IR notification', dict)
    rowdict['Kind'] = returnValue('Kind', dict)
    rowdict['Class'] = dict['Class'] if 'Class' in dict else dict['Classes']
    rowdict['Filing Date'] = returnValue('Filing', dict)
    rowdict['First report Date'] = returnValue('First report', dict)
    rowdict['Registered From Date'] = returnValue('Registered from', dict)
    rowdict['Registration Advertised Date'] = returnValue('Registration advertised', dict)
    rowdict['Acception Advertised Date'] = returnValue('Acceptance advertised', dict)
    rowdict['Acception Date'] = returnValue('Acceptance', dict)
    rowdict['Image'] = returnValue('Image', dict)
    rowdict['Image description'] = returnValue('Image description', dict)
    rowdict['Priority Date'] = returnValue('Priority date', dict)
    rowdict['Renewal Due Date'] = returnValue('Renewal due', dict)
    rowdict['Status'] = returnValue('Status', dict)
    rowdict['Owner'] = returnValue('Owner', dict)
    rowdict['Address for service'] = returnValue('Address for service', dict)
    rowdict['IR Contact'] = returnValue('IR Contact', dict)
    rowdict['History'] = returnValue('History', dict)
    rowdict['Goods and services'] = returnValue('Goods and services', dict)
    rowdict['Indexing constituents image'] = returnValue('Indexing constituents image', dict)
    rowdict['Indexing constituents word'] = returnValue('Indexing constituents word', dict)
    if 'Convention details' in dict:
        rowdict['Convention date'] = returnValue('Date', dict['Convention details'])
        rowdict['Convention number'] = returnValue('Number', dict['Convention details'])
        rowdict['Convention country'] = returnValue('Country', dict['Convention details'])
    else:
        rowdict['Convention date'] = ''
        rowdict['Convention number'] = ''
        rowdict['Convention country'] = ''

    return rowdict

def ouputCSV(dict, filename, mode):
    global isHeader
    with open(filename, mode, newline='\n') as file:
        csvWriter = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        if isHeader:
            csvWriter.writeheader()
            isHeader = False
        csvWriter.writerow(dict)

def argsParse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', required=True, choices=['file', 'id'], help='verbose : format ; file or id')
    parser.add_argument('--trademark', required=True, help='trademark number or file with trademark list')
    parser.add_argument('--csv', help="output csv file name; format: result.csv")
    parser.add_argument('--json', help="output json format", default=True)
    return vars(parser.parse_args())

def scrap_Unit(trademark, filename):
    print(trademark)
    url = BASE_URL + trademark + "/details??a=1&h=1"
    res = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    divs = soup.find_all('div', {'class': 'box-with-shadow'})
    extracted_data = {'ID' : trademark}

    """ Step 1. Retrieve First table in first Div:  Words, Image, Image description, Status, Priority date, Class(Classes), Kind"""
    table_bodys = divs[0].find_all('table')
    trs = table_bodys[1].find_all('tr')

    for tr in trs:
        key = tr.find('th').text.replace('\n', '')
        value = tr.find('td').text.replace('\n', ' ')
        if key == '': continue
        extracted_data[key] = value
    ## especially get image url
    imagetags = table_bodys[1].find_all('img')
    iamge_urls = []
    for image in imagetags:
        iamge_urls.append(image.get('src').replace('\n', ' '))
    ## especially get video url
    images = table_bodys[1].find_all('video')
    for image in images:
        iamge_urls.append(image.get('src').replace('\n', ' '))
    extracted_data['Image'] = "||" .join(iamge_urls)

    """ Step 2.  Retrieve Second table in first Div: Dates
    {
        Renewal due, Registration advertised, Entered on Register, Acceptance advertised, Acceptance, Filing, Registered from
    }
    """
    trs = table_bodys[2].find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) == 1: continue
        key = tds[0].text.replace('\n', '')
        value = tds[1].text.replace('\n', ' ')
        if key == '': continue
        extracted_data[key] = value

    """ Step 3. Retrieve in Second Div : Owner, Address for service """
    tds = divs[1].find_all('td')
    Owner = tds[0].text.replace('\n', ' ')
    Address = tds[1].text.replace('\n', ' ')
    extracted_data['Owner'] = Owner
    extracted_data['Address for service'] = Address

    """ Step 4. Retreive Third Div : Goods & Services"""
    goods_services = soup.find_all("div", {'class': 'box-with-shadow long-content-container'})[0]\
                         .find_all('div', {'class': 'goods-service'})
    values = []
    for services in goods_services:
        values.append(services.text.replace('\n', ' '))
    extracted_data['Goods and services'] = "||".join(values)

    """ Step 5. Extract IR Contact """
    if len(divs[2].get('class'))==1:
        trs = divs[2].find_all('tr')
        if len(trs) > 1:
            extracted_data['IR Contact'] = trs[1].text.replace('\n',' ')

    """
        Step 6.
        get all data of div with class name  'box-with-shadow'
    """
    for i in range(3, len(divs)):
        if len(divs[i].get('class')) == 1:
            trs = divs[i].find_all('tr')
            if len(trs)>0:
                key_dict = trs[0].find('th').text.replace('\n', '')
                value_dicts = {}
                for tr in trs:
                    tds = tr.find_all('td')
                    if len(tds) == 1: continue
                    key = tds[0].text.replace('\n', '')
                    value = tds[1].text.replace('\n', ' ').replace('"',"'")
                    value_dicts[key] = value
                extracted_data[key_dict] = value_dicts

    """ Step 7. History and publication details """
    tbodys = soup.find('div', id='toggleHistoryTable').find_all('tbody')
    history = []
    for tbody in tbodys:
        trs = tbody.find_all('tr')
        tds = tbody.find_all('td')
        if len(tds) == 0: continue
        key = tds[0].text.replace('\n', '')
        value = tds[1].text.replace('\n', ' ')
        history.append('-'.join([key, value]))

        if len(trs) > 1:
            ps = trs[1].find_all('p')
            pubvalue = ""
            for p in ps:
                pubval = p.text.replace('\n',' ')
                pubvalue = pubvalue + pubval
            history.append(pubvalue)
    extracted_data['History'] = '||'.join(history)

    """ Step 8. Get Indexing constituents """
    tables = soup.find('div',{'class':'box-with-shadow row cf'}).find_all('table')
    if len(tables) > 1:
        ## get Words
        words = []
        trs = tables[0].find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) > 1:
                snippet = ":".join([tds[0].text.replace('\n', ' '),tds[1].text.replace('\n', ' ')])
            else:
                snippet = ":".join([tds[0].text.replace('\n', ' ')])
            words.append(snippet)
        ## get Image
        images = []
        trs = tables[1].find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) > 1:
                snippet = "-".join([tds[0].text.replace('\n', ' '), tds[1].text.replace('\n', ' ')])
            else:
                snippet = "-".join([tds[0].text.replace('\n', ' ')])
            images.append(snippet)
        extracted_data['Indexing constituents image'] = "||".join(images)
        extracted_data['Indexing constituents word'] = "||".join(words)

    """ create dict from extracted_data """
    rowdict = AdjustData(extracted_data)

    """ Output as csv or json """
    if filename:
        ouputCSV(rowdict,filename, 'a')
    else:
        print(json.dumps(rowdict))

if __name__ == "__main__":
    args = argsParse()

    """
    # args for test
    args = {
        'csv' : 'outut.csv',
        'trademark' : '1594492',
        'verbose' : 'id'
    }
    """
    if args['csv'] == None and args['json']==None:
        print("--csv or --json required")
        sys.exit()
    print("start scraping")
    if args['verbose'] == 'file':
        file = open(args['trademark'], 'r')
        for line in file.readlines():
            scrap_Unit(line.strip(), args['csv'])
    else:
        scrap_Unit(args['trademark'], args['csv'])

    print("Finish %.3fs" % (elapsed()))

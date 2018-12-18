import requests
import argparse
from bs4 import BeautifulSoup
import json,sys, time, csv, os

BASE_URL = "https://search.ipaustralia.gov.au/trademarks/search/view/"

start = time.time()
isHeader = True

def elapsed():
    return time.time() - start

def ouputCSV(dict, filename):
    global isHeader
    fieldnames = [  'ID',
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
                    'IR contact',
                    'History',
                    'Goods and services',
                    'Indexing constituents image',
                    'Indexing constituents word',
                    'Convention date',
                    'Convention number',
                    'Convention country'
                ]
    rowdict = {}
    rowdict['ID'] = dict['ID'] if dict['ID'] else ''
    rowdict['Words'] = dict['Words'] if dict['Words'] else ''
    rowdict['IR number'] = dict['IR number'] if 'IR number' in dict else ''
    rowdict['IR notification'] = dict['IR notification'] if 'IR notification' in dict else ''
    rowdict['Kind'] = dict['Kind'] if 'Kind' in dict else ''
    rowdict['Class'] = dict['Class'] if 'Class' in dict else ''
    rowdict['Filing Date'] = dict['Filing'] if 'Filing' in dict else ''
    rowdict['First report Date'] = dict['First report Date'] if 'First report Date' in dict else ''
    rowdict['Registered From Date'] = dict['Registered from'] if 'Registered from' in dict else ''
    rowdict['Registration Advertised Date'] = dict['Registration advertised'] if 'Registration advertised' in dict else ''
    rowdict['Acception Advertised Date'] = dict['Acceptance advertised'] if 'Acceptance advertised' in dict else ''
    rowdict['Acception Date'] = dict['Acceptance'] if 'Acceptance' in dict else ''
    rowdict['Image'] = dict['Image'] if 'Image' in dict else ''
    rowdict['Image description'] = dict['Image description'] if 'Image description' in dict else ''
    rowdict['Priority Date'] = dict['Priority date'] if 'Priority date' in dict else ''
    rowdict['Renewal Due Date'] = dict['Renewal due'] if 'Renewal due' in dict else ''
    rowdict['Status'] = dict['Status'] if 'Status' in dict else ''
    rowdict['Owner'] = dict['Owner'] if 'Owner' in dict else ''
    rowdict['Address for service'] = dict['Address for service'] if 'Address for service' in dict else ''
    rowdict['IR contact'] = dict['IR contact'] if 'IR contact' in dict else ''
    rowdict['Goods and services'] = dict['Goods and services'] if 'Goods and services' in dict else ''
    rowdict['Indexing constituents image'] = dict['Indexing constituents image'] if 'Indexing constituents image' in dict else ''
    rowdict['Indexing constituents word'] = dict['Indexing constituents word'] if 'Indexing constituents word' in dict else ''
    rowdict['Convention date'] = dict['Convention details']['Date'] if 'Convention details' in dict else ''
    rowdict['Convention number'] = dict['Convention details']['Number'] if 'Convention details' in dict else ''
    rowdict['Convention country'] = dict['Convention details']['Country'] if 'Convention details' in dict else ''

    with open(filename, "a", newline='') as file:
        csvWriter = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        if isHeader:
            csvWriter.writeheader()
            isHeader = False
        csvWriter.writerow(rowdict)

def argsParse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', required=True, choices=['file', 'id'], help='verbose : format ; file or id')
    parser.add_argument('--trademark', required=True, help='trademark number or file with trademark list')
    parser.add_argument('--csv', help="output csv file name; format: result.csv")
    parser.add_argument('--json', help="output json format", default=True)
    return vars(parser.parse_args())


def scrap_Unit(trademark, filename):
    url = BASE_URL + trademark + "/details??a=1&h=1"
    print(url)
    session = requests.session()
    res = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    divs = soup.find_all('div', {'class': 'box-with-shadow'})
    extracted_data = {'ID' : trademark}

    """ Retrieve First table in first Div:  Words, Image, Image description, Status, Priority date, Class(Classes), Kind"""
    table_body = divs[0].find_all('table')
    trs = table_body[1].find_all('tr')

    for tr in trs:
        key = tr.find('th').text.replace('\n', '')
        value = tr.find('td').text.replace('\n', ' ')
        if key == '': continue
        extracted_data[key] = value
    ## especially get image url
    images = table_body[1].find_all('img')
    iamge_urls = []
    for image in images:
        iamge_urls.append(image.get('src'))
    extracted_data['Image'] = iamge_urls

    """ Retrieve Second table in first Div: Dates
    {
        Renewal due,
        Registration advertised,
        Entered on Register,
        Acceptance advertised,
        Acceptance,
        Filing,
        Registered from
    }
    """
    trs = table_body[2].find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) == 1: continue
        key = tds[0].text.replace('\n', '')
        value = tds[1].text.replace('\n', ' ')
        if key == '': continue
        extracted_data[key] = value

    """ Retrieve in Second Div : Owner, Address for service """
    tds = divs[1].find_all('td')
    Owner = tds[0].text.replace('\n', ' ')
    Address = tds[1].text.replace('\n', ' ')
    extracted_data['Owner'] = Owner
    extracted_data['Address for service'] = Address

    """ Retreive Third Div : Goods & Services"""
    goods_services = soup.find_all("div", {'class': 'box-with-shadow long-content-container'})[0]\
                         .find_all('div', {'class': 'goods-service'})
    values = []
    for services in goods_services:
        values.append(services.text.replace('\n', ' '))
    extracted_data['Goods and services'] = values

    """
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
                    value = tds[1].text.replace('\n', ' ')
                    value_dicts[key] = value
                extracted_data[key_dict] = value_dicts

    """ History and publication details """
    tbodys = soup.find('div', id='toggleHistoryTable').find_all('tbody')
    history = []
    for tbody in tbodys:
        trs = tbody.find_all('tr')
        tds = tbody.find_all('td')
        if len(tds) == 0: continue
        key = tds[0].text.replace('\n', '')
        value = tds[1].text.replace('\n', ' ')
        vals = {}
        vals['date'] = key
        vals['description'] = value

        if len(trs) > 1:
            eventval = {}
            ps = trs[1].find_all('p')
            for p in ps:
                pubvalues = p.text.split('\n\n')
                key = pubvalues[0].replace('\n', '')
                pubvalue = '' if len(pubvalues) == 1 else pubvalues[1]
                pubvalue = pubvalue.replace('\n', ' ')
                eventval[key] = pubvalue
            vals['detail'] = eventval
        history.append(vals)
    extracted_data['History'] = history

    """ Get Indexing constituents """
    tables = soup.find('div',{'class':'box-with-shadow row cf'}).find_all('table')
    if len(tables) > 1:
        ## get Words
        words = []
        trs = tables[0].find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) > 1:
                snippet = ":".join([tds[0].text,tds[1].text])
            else:
                snippet = ":".join([tds[0].text])
            words.append(snippet)
        ## get Image
        images = []
        trs = tables[1].find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) > 1:
                snippet = ":".join([tds[0].text, tds[1].text])
            else:
                snippet = ":".join([tds[0].text])
            images.append(snippet)
        extracted_data['Indexing constituents image'] = images
        extracted_data['Indexing constituents word'] = words

    if filename:
        ouputCSV(extracted_data,filename)
    # print(json.dumps(extracted_data))


if __name__ == "__main__":
    args = argsParse()

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

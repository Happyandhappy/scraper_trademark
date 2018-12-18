import requests
import argparse
from bs4 import BeautifulSoup
import json,sys


BASE_URL = "https://search.ipaustralia.gov.au/trademarks/search/view/"

def Parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', required=True, help='verbose')
    parser.add_argument('--trademark', required=True, help='trademark number')
    parser.add_argument('--csv', help="output csv file name; format: result.csv")
    parser.add_argument('--json', help="output json format", default=True)
    return vars(parser.parse_args())

if __name__ == "__main__":
    args = Parse()
    print(args)
    if args['csv'] == None and args['json']==None:
        print("--csv or --json required")
        sys.exit()
    elif args['csv'] != None:
        print("--json only required now")
        sys.exit()
    url = BASE_URL + args['trademark'] + "/details??a=1&h=1&e=1"
    session = requests.session()
    res = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    divs = soup.find_all('div', {'class' : 'box-with-shadow'})
    extracted_data = {}

    """ Retrieve First table in first Div:  Words, Image, Image description, Status, Priority date, Class(Classes), Kind"""
    table_body = divs[0].find_all('table')
    trs = table_body[1].find_all('tr')

    for tr in trs:
        key = tr.find('th').text.replace('\n','')
        value = tr.find('td').text.replace('\n',' ')
        if key=='': continue
        extracted_data[key] = value
    ## especially get image url
    try:
        extracted_data['Image'] = table_body[1].find('img').get('src')
    except:
        extracted_data['Image'] = ''


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
        if len(tds)==1: continue
        key = tds[0].text.replace('\n','')
        value = tds[1].text.replace('\n',' ')
        if key == '': continue
        extracted_data[key] = value

    """ Retrieve in Second Div : Owner, Address for service """
    tds = divs[1].find_all('td')
    Owner = tds[0].text.replace('\n',' ')
    Address = tds[1].text.replace('\n',' ')
    extracted_data['Owner'] = Owner
    extracted_data['Address'] = Address


    """ Retreive Third Div : Goods & Services"""
    goods_services = soup.find_all("div",{'class' : 'box-with-shadow long-content-container'})[0].find_all('div',{'class':'goods-service'})
    values = []
    for services in goods_services:
        values.append(services.text.replace('\n',' '))
    extracted_data['Goods_Services'] = values


    """
        get all data of div with class name  'box-with-shadow'
    """
    for i in range(3, len(divs)):
        if len(divs[i].get('class')) == 1:
            trs = divs[i].find_all('tr')
            key_dict = trs[0].find('th').text.replace('\n','')
            value_dicts = {}
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) == 1 : continue
                key = tds[0].text.replace('\n','')
                value = tds[1].text.replace('\n',' ')
                value_dicts[key] = value
            extracted_data[key_dict] = value_dicts

    """ History and publication details """
    tbodys = soup.find('div', id='toggleHistoryTable').find_all('tbody')
    history = []
    for tbody in tbodys:
        trs = tbody.find_all('tr')
        tds = tbody.find_all('td')
        if len(tds) == 0:continue
        key = tds[0].text.replace('\n','')
        value = tds[1].text.replace('\n',' ')
        vals = {}
        vals['date'] = key
        vals['description'] = value

        if len(trs) > 1:
            eventval = {}
            ps = trs[1].find_all('p')
            for p in ps:
                pubvalues = p.text.split('\n\n')
                key = pubvalues[0].replace('\n','')
                pubvalue = '' if len(pubvalues) == 1 else pubvalues[1]
                pubvalue = pubvalue.replace('\n',' ')
                eventval[key] = pubvalue
            vals['detail'] = eventval
        history.append(vals)
    extracted_data['history'] = history

    print(json.dumps(extracted_data))
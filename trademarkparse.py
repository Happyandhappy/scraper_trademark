import requests
import argparse
from bs4 import BeautifulSoup
import json,sys, datetime, csv
from importDB import TradeDB

class TradeMarks():
    BASE_URL = "https://search.ipaustralia.gov.au/trademarks/search/view/"
    isHeader = True
    session = requests.session()
    fieldnames = ['ID','Words','IR number','IR notification','Kind','Class','Filing Date','First report Date','Registered From Date',
                  'Registration Advertised Date','Acception Advertised Date','Acception Date','Image','Image description','Priority Date',
                  'Renewal Due Date','Status','Owner','Address for service','IR Contact','History','Goods and services',
                  'Indexing constituents image','Indexing constituents word','Convention date','Convention number','Convention country',
                  ### added newly
                  'OwnerAddress1','OwnerAddress2','OwnerCity','OwnerState','OwnerPostcode','OwnerCountry',
                  'ServiceAddress1','ServiceAddress2','ServiceCity','ServiceState','ServicePostcode','ServiceCountry',
                  'Endorsements'
                  ]
    trademark = ""
    filename = ""
    isJson = False

    def __init__(self, filename, isJson):
        self.filename = filename
        self.isJson = isJson

    def convertDate(self, date):
        words = date.split(' ')
        date = datetime.datetime.strptime(" ".join(words[:3]) , '%d %b %Y').strftime('%Y-%m-%d') if len(words) > 2 else ""
        return date

    def setTrademark(self, trademark):
        self.trademark = trademark

    def returnValue(self, key, dict):
        return dict[key].encode('ascii','ignore') if key in dict else ''

    """ def for parse of addresses """
    def addressParse(self, address):
        words = address.split(',')
        addresses = {
            "address1" : "","address2" : "",
            "city" : "","state" : "",
            "postcode" : "","country" : ""
        }
        cnt = len(words)
        if cnt < 5 :
            addresses['address1'] = address
            return addresses

        addresses['city'] = words[cnt-4]
        addresses['state'] = words[cnt-3]
        addresses['postcode'] = words[cnt-2]
        addresses['country'] = words[cnt-1]

        if cnt == 6:
            addresses['address1'] = words[0]
            addresses['address2'] = words[1]
        elif cnt == 5:
            addresses['address1'] = words[0]
        else:
            addresses['address1'] = " ".join(words[0:cnt-6])
            addresses['address2'] = words[cnt-5]
        return addresses

    """ Create Dict from retrieve data """
    def AdjustData(self, dict):
        rowdict = {}
        rowdict['ID'] =  self.returnValue('ID', dict).lstrip().rstrip()
        rowdict['Words'] =  self.returnValue('Words', dict).lstrip().rstrip()
        rowdict['IR number'] =  self.returnValue('IR number', dict).lstrip().rstrip()
        rowdict['IR notification'] =  self.returnValue('IR notification', dict).lstrip().rstrip()
        rowdict['Kind'] =  self.returnValue('Kind', dict).lstrip().rstrip()
        rowdict['Class'] = dict['Class'].lstrip().rstrip().encode('ascii','ignore') if 'Class' in dict else dict['Classes'].lstrip().rstrip().encode('ascii','ignore')
        rowdict['Filing Date'] =  self.convertDate(self.returnValue('Filing', dict).lstrip().rstrip())
        rowdict['First report Date'] =  self.convertDate(self.returnValue('First report', dict).lstrip().rstrip())
        rowdict['Registered From Date'] =  self.convertDate(self.returnValue('Registered from', dict).lstrip().rstrip())
        rowdict['Registration Advertised Date'] =  self.convertDate(self.returnValue('Registration advertised', dict).lstrip().rstrip())
        rowdict['Acception Advertised Date'] =  self.convertDate(self.returnValue('Acceptance advertised', dict).lstrip().rstrip())
        rowdict['Acception Date'] =  self.convertDate(self.returnValue('Acceptance', dict).lstrip().rstrip())
        rowdict['Image'] =  self.returnValue('Image', dict).lstrip().rstrip().replace('MEDIUM','LARGE')
        rowdict['Image description'] =  self.returnValue('Image description', dict).lstrip().rstrip()
        rowdict['Priority Date'] = self.convertDate(self.returnValue('Priority date', dict).lstrip().rstrip())
        rowdict['Renewal Due Date'] =  self.convertDate(self.returnValue('Renewal due', dict).lstrip().rstrip())
        rowdict['Status'] =  self.returnValue('Status', dict).lstrip().rstrip()
        rowdict['Owner'] =  self.returnValue('Owner', dict).lstrip().rstrip()
        rowdict['Address for service'] =  self.returnValue('Address for service', dict).lstrip().rstrip()
        rowdict['IR Contact'] =  self.returnValue('IR Contact', dict).lstrip().rstrip()
        rowdict['History'] =  self.returnValue('History', dict).lstrip().rstrip()
        rowdict['Goods and services'] =  self.returnValue('Goods and services', dict).lstrip().rstrip()
        rowdict['Indexing constituents image'] =  self.returnValue('Indexing constituents image', dict).lstrip().rstrip()
        rowdict['Indexing constituents word'] =  self.returnValue('Indexing constituents word', dict).lstrip().rstrip()
        if 'Convention details' in dict:
            rowdict['Convention date'] =  self.convertDate(self.returnValue('Date', dict['Convention details']).lstrip().rstrip())
            rowdict['Convention number'] =  self.returnValue('Number', dict['Convention details']).lstrip().rstrip()
            rowdict['Convention country'] =  self.returnValue('Country', dict['Convention details']).lstrip().rstrip()
        else:
            rowdict['Convention date'] = ''
            rowdict['Convention number'] = ''
            rowdict['Convention country'] = ''

        ### added newly
        rowdict['OwnerAddress1'] = dict['OwnerAddresses']['address1'].encode('ascii','ignore')
        rowdict['OwnerAddress2'] = dict['OwnerAddresses']['address2'].encode('ascii','ignore')
        rowdict['OwnerCity'] = dict['OwnerAddresses']['city'].encode('ascii','ignore')
        rowdict['OwnerState'] = dict['OwnerAddresses']['state'].encode('ascii','ignore')
        rowdict['OwnerPostcode'] = dict['OwnerAddresses']['postcode'].encode('ascii','ignore')
        rowdict['OwnerCountry'] = dict['OwnerAddresses']['country'].encode('ascii','ignore')

        rowdict['ServiceAddress1'] = dict['ServiceAddress']['address1'].encode('ascii','ignore')
        rowdict['ServiceAddress2'] = dict['ServiceAddress']['address2'].encode('ascii','ignore')
        rowdict['ServiceCity'] = dict['ServiceAddress']['city'].encode('ascii','ignore')
        rowdict['ServiceState'] = dict['ServiceAddress']['state'].encode('ascii','ignore')
        rowdict['ServicePostcode'] = dict['ServiceAddress']['postcode'].encode('ascii','ignore')
        rowdict['ServiceCountry'] = dict['ServiceAddress']['country'].encode('ascii','ignore')

        rowdict['Endorsements'] = self.returnValue('Endorsements', dict).lstrip().rstrip()
        return rowdict

    def scrap(self):
        print(self.trademark)
        url = self.BASE_URL + self.trademark + "/details??a=1&h=1&e=1"
        res = self.session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        divs = soup.find_all('div', {'class': 'box-with-shadow'})
        extracted_data = {'ID': self.trademark}

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
        extracted_data['Image'] = "||".join(iamge_urls)

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
        OwnerName = tds[0].find('span', {'class': 'party-name'}).text.replace('\n', ' ')
        OwnerAddress = tds[0].find('div', {'class' : 'js-address'}).text.replace('\n',',').replace(',,',',').lstrip(',').rstrip(',') #.replace('\n',' ')
        Owner = OwnerName + "/" + OwnerAddress
        extracted_data['Owner'] = Owner
        extracted_data['OwnerAddresses'] = self.addressParse(OwnerAddress)

        try:
            AddressforServiceName = tds[1].find('span', {'class': 'party-name'}).text.replace('\n','')
            AddressforServiceAddress = tds[1].find('div', {'class': 'js-address'}).text.replace('\n', ',').replace(',,',',').lstrip(',').rstrip(',')
        except:
            AddressforServiceName = ""
            AddressforServiceAddress = ""

        extracted_data['Address for service'] = AddressforServiceName + "/" + AddressforServiceAddress
        extracted_data['ServiceAddress'] = self.addressParse(AddressforServiceAddress)

        """ Step 4. Retreive Third Div : Goods & Services"""
        goods_services = soup.find_all("div", {'class': 'box-with-shadow long-content-container'})[0].find_all('div', {'class': 'goods-service'})
        values = []
        for services in goods_services:
            values.append(services.text.replace('\n', ' '))
        extracted_data['Goods and services'] = "||".join(values)

        """ Step 5. Extract IR Contact """
        if len(divs[2].get('class')) == 1:
            trs = divs[2].find_all('tr')
            if len(trs) > 1:
                extracted_data['IR Contact'] = trs[1].text.replace('\n', ' ')

        """ Step 6. get all data of div with class name  'box-with-shadow' """
        for i in range(3, len(divs)):
            if len(divs[i].get('class')) == 1:
                trs = divs[i].find_all('tr')
                if len(trs) > 0:
                    key_dict = trs[0].find('th').text.replace('\n', '')
                    value_dicts = {}
                    for tr in trs:
                        tds = tr.find_all('td')
                        if len(tds) == 1: continue
                        key = tds[0].text.replace('\n', '')
                        value = tds[1].text.replace('\n', ' ').replace('"', "'")
                        value_dicts[key] = value
                    extracted_data[key_dict] = value_dicts

        """ Get Convention details	 """
        for i in range(3, len(divs)):
            if 'Endorsements' in divs[i].text:
                values = ""
                trs = divs[i].find_all('tr')
                for j in range(1, len(trs)):
                    title = trs[j].find("th").text.replace('\n', '')
                    value = trs[j].find('td').text.replace('\n', '')
                    values += title + " - " + value + ','
                extracted_data['Endorsements'] = values
            else:
                extracted_data['Endorsements'] = ""

        """ Step 7. History and publication details """
        tbodys = soup.find('div', id='toggleHistoryTable').find_all('tbody')
        history = []
        for tbody in tbodys:
            trs = tbody.find_all('tr')
            tds = tbody.find_all('td')
            if len(tds) == 0: continue
            key = self.convertDate(tds[0].text.replace('\n', ''))
            value = tds[1].text.replace('\n', ' ')
            history.append(' - '.join([key, value]))

            if len(trs) > 1:
                ps = trs[1].find_all('p')
                pubvalue = ""
                for p in ps:
                    pubval = p.text.replace('\n', ' ')
                    pubvalue = pubvalue + pubval
                history.append(pubvalue)
        extracted_data['History'] = '||'.join(history)

        """ Step 8. Get Indexing constituents """
        tables = soup.find('div', {'class': 'box-with-shadow row cf'}).find_all('table')
        if len(tables) > 1:
            ## get Words
            words = []
            trs = tables[0].find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) > 1:
                    snippet = ":".join([tds[0].text.replace('\n', ' '), tds[1].text.replace('\n', ' ')])
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
        rowdict = self.AdjustData(extracted_data)

        if self.isJson:
            print(json.dumps(rowdict))
        else:
            self.ouputCSV(rowdict)
        return rowdict

    def ouputCSV(self, dict):
        if self.isHeader:
            mode = 'w'
        else:
            mode = 'a'
        with open(self.filename, mode) as file:
            csvWriter = csv.DictWriter(file, fieldnames=self.fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            if self.isHeader:
                csvWriter.writeheader()
                self.isHeader = False
            csvWriter.writerow(dict)

def argsParse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', required=True, choices=['file', 'id'], help='verbose : format ; file or id')
    parser.add_argument('--trademark', required=True, help='trademark number or file with trademark list')
    parser.add_argument('--csv', help="output csv file name; format: result.csv")
    parser.add_argument('--json', help="output json format", default=True)
    return vars(parser.parse_args())


if __name__ == "__main__":
    args = argsParse()

    """
    # args for test
    args = {
        'csv' : "out.csv",
        'trademark' : '1805224',
        'verbose' : 'id',
        'json' : False
    }
    """
    if args['csv'] == None and args['json']==None:
        print("--csv or --json required")
        sys.exit()

    print("start scraping")

    if args['csv'] != None:
        trades = TradeMarks(filename=args['csv'], isJson=False)
    else:
        trades = TradeMarks(filename=args['csv'], isJson=True)

    if args['verbose'] == 'file':
        file = open(args['trademark'], 'r')
        for line in file.readlines():
            trades.setTrademark(line.strip())
            trades.scrap()
    else:
        trades.setTrademark(args['trademark'])
        trades.scrap()

    if args['csv']:
        trade = TradeDB(args['csv'])
        trade.creatTables()
        trade.importCSV()
        trade.storeImagetoDB()

    print("Finish ...")


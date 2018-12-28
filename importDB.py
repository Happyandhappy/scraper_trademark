from config import *
import base64, pymysql, csv, requests
import warnings
warnings.filterwarnings("ignore")


class TradeDB():
    def __init__(self, csv):
        self.csvName = csv
        self.Dbcon = pymysql.connect(user=MYSQL_USER, password=MYSQL_PASS, host=MYSQL_HOST)
        self.createDB()

    def runQuery(self, query):
        dbcur = self.Dbcon.cursor()
        try:
            dbcur.execute(query)
            self.Dbcon.commit()
        except:
            self.Dbcon.rollback()
            print(query)
            print("Sql statement Error!")
        dbcur.close()

    def storeImagetoDB(self):
        with open(self.csvName, 'r') as csvfile:
            firstLine = True
            lines = csv.reader(csvfile, delimiter=',')
            for line in lines:
                url = line[12].replace('MEDIUM','LARGE')
                ID = line[0]
                if not url or url == '' or firstLine:
                    firstLine = False
                    continue
                r = requests.get(url=url, stream=True)
                if r.status_code == 200:
                    with open("image_name.jpg", 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                else:
                    continue

                with open('image_name.jpg', 'rb') as f:
                    photo = f.read()
                    encodestring = base64.b64encode(photo)
                    mycursor = self.Dbcon.cursor()
                    sql = "insert ignore into `images` (`ID`,`url`, `content`) values(%s, %s, %s)"
                    mycursor.execute(sql, (ID, url, encodestring,))
                    self.Dbcon.commit()
                    mycursor.close()

    """ Prototype function to retrieve image from database """
    def retriveImagefromDB(self):
        query = "select * from `images`"
        cursor = self.Dbcon.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        imagestring = data[0][0]
        imagedata = base64.b64decode(imagestring)
        with open("out.jpg", 'wb') as f:
            f.write(imagedata)

    def createDB(self):
        query = """CREATE DATABASE IF NOT EXISTS `%s`;""" % (MYSQL_DBNAME)
        dbcur = self.Dbcon.cursor()
        try:
            dbcur.execute(query)
            self.Dbcon.commit()
            print("Database %s was created." % (MYSQL_DBNAME))
            self.Dbcon = pymysql.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DBNAME, local_infile=True)
        except:
            self.Dbcon.rollback()
            print(query)
            print("SQL statement Error")
        dbcur.close()

    def checkTableExists(self,tablename):
        dbcur = self.Dbcon.cursor()
        dbcur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name = '{0}'
                """.format(tablename.replace('\'', '\'\'')))
        if dbcur.fetchone()[0] == 1:
            dbcur.close()
            return True
        dbcur.close()
        return False

    def creatTables(self):
        if not self.checkTableExists('Trademarks'):
            query = """
                    create table `Trademarks` (
                        `ID` int(10) NOT NULL, 
                        `Words` VARCHAR(50) , 
                        `IR number` VARCHAR(200), 
                        `IR notification` VARCHAR(200),
                        `Kind` VARCHAR(100),
                        `Class` VARCHAR(200),
                        `Filing Date` DATE,
                        `First report Date` DATE,
                        `Registered From Date` DATE,
                        `Registration Advertised Date` DATE,
                        `Acception Advertised Date` DATE,
                        `Acception Date` DATE,
                        `Image` TEXT,
                        `Image description` TEXT,
                        `Priority Date` DATE,
                        `Renewal Due Date` DATE,
                        `Status` VARCHAR(200),
                        `Owner` VARCHAR(200),
                        `Address for service` TEXT,
                        `IR Contact` TEXT,
                        `History` TEXT,
                        `Goods and services` TEXT,
                        `Indexing constituents image` TEXT,
                        `Indexing constituents word` TEXT,
                        `Convention date` DATE,
                        `Convention number` TEXT,
                        `Convention country` TEXT,
                        `OwnerName` TEXT,
                        `OwnerAddress1` TEXT,
                        `OwnerAddress2` TEXT,
                        `OwnerCity` TEXT,
                        `OwnerState` TEXT,
                        `OwnerPostcode` TEXT,
                        `OwnerCountry` TEXT,
                        `ServiceName` TEXT,
                        `ServiceAddress1` TEXT,
                        `ServiceAddress2` TEXT,
                        `ServiceCity` TEXT,
                        `ServiceState` TEXT,
                        `ServicePostcode` TEXT,
                        `ServiceCountry` TEXT,
                        `Endorsements` TEXT , PRIMARY KEY (`ID`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
                    """
            self.runQuery(query)

        if not self.checkTableExists('images'):
            query = """create table `images` (
                    `ID` INT(10) NOT NULL,
                    `url` varchar(200),
                    `content` LONGBLOB, PRIMARY KEY (`ID`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
                    """
            self.runQuery(query)
        self.runQuery("set sql_mode='';")

    def importCSV(self):
        query = """LOAD DATA LOCAL INFILE '%s' REPLACE INTO TABLE `Trademarks` FIELDS TERMINATED BY ','  enclosed by '"'  LINES TERMINATED BY '\r\n' IGNORE 1 LINES;""" % (self.csvName);
        self.runQuery(query)


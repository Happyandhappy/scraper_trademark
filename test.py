import pymysql
import base64
import io, requests

r = requests.get("https://images.pexels.com/photos/67636/rose-blue-flower-rose-blooms-67636.jpeg?auto=compress&cs=tinysrgb&h=650&w=940.jpg", stream=True)
if r.status_code == 200:
    with open("image_name.jpg", 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

with open('image_name.jpg', 'rb') as f:
    photo = f.read()
encodestring = base64.b64encode(photo)
db= pymysql.connect(user="root",password="",host="localhost",database="csv_table")
mycursor=db.cursor()
sql = "insert into sample values(%s)"
mycursor.execute(sql,(encodestring,))
db.commit()

# sql1="select * from sample"
# mycursor.execute(sql1)
# data = mycursor.fetchall()
# baseString = data[0][0]
# data1=base64.b64decode(baseString)
# with open('some_image.jpg', 'wb') as f:
#     f.write(data1)

db.close()
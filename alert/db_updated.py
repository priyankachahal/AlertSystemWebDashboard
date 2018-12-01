import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import pymysql

conn = pymysql.connect(host="localhost", user="root", passwd= "root", db= "data")

myCursor = conn.cursor()

# Set Date of 3 days ago to get logs
set_date = str((date.today() - timedelta(10)))
# print (set_date)

log_url = "https://spotcrime.com/ca/san+jose/daily-blotter/" + set_date
# print (log_url)

# Get entire data from URL request
r = requests.get(log_url)

# Soup object to store data after parsing
soup = BeautifulSoup(r.content, "html.parser")

for g_data in soup.find_all("div", {"class": "main-content-column"}):
    tds = g_data.find_all('td')
    # print(tds[0].text, "---", tds[1].text, "---", tds[2].text, "---",
    #       tds[3].text, "---", tds[4].text, "---", tds[5].text, "---", tds[6].text, "---", tds[7].text)
    # print (tds[300].text,"---",tds[301].text,"---", tds[302].text, "---",
    #        tds[303].text, "---", tds[304].text, "---", tds[305].text, "---", tds[306].text, "---", tds[307].text )

i=0
while (i < 200):
    if (((i + 1) % 5) != 0):
        Type =(tds[i + 1].text)
        dt =(tds[i + 2].text)
        dt_slice = dt[0:8]
        day = dt_slice[3:5]
        month = dt_slice[0:2]
        year = "20"+dt_slice[6:8]
        date = year+"-"+month+"-"+day

        #Datetime type code
        # # date = '29/12/2017'  # The date - 29 Dec 2017
        # format_str = '%d-%m-%Y'  # The format
        # datetime_obj = datetime.datetime.strptime(date_str, format_str)
        #
        # a=(datetime_obj.date())
        # type(a)

        var =(tds[i + 3].text)
        address = var.title()

        for td in tds[i + 4]:
            link = ("https://spotcrime.com" + td["href"])
            myCursor.execute('INSERT INTO pastreport (Type, Date, address, Link) VALUES (\'%s\',\'%s\',\'%s\',\'%s\')' % (Type, date, address, link))

        i += 5




conn.commit()

conn.close()
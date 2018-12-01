import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import pymysql

conn = pymysql.connect(host="localhost", user="root", passwd= "", db= "crimereportdb")

myCursor = conn.cursor()

# Set Date of 3 days ago to get logs
set_date = str((date.today() - timedelta(10)))

log_url = "https://spotcrime.com/ca/san+jose/daily-blotter/" + set_date

# Get entire data from URL request
r = requests.get(log_url)

# Soup object to store data after parsing
soup = BeautifulSoup(r.content, "html.parser")

for g_data in soup.find_all("div", {"class": "main-content-column"}):
    tds = g_data.find_all('td')

i=0
while (i < 200):
    if (((i + 1) % 5) != 0):
        type =(tds[i + 1].text)
        dt =(tds[i + 2].text)
        dt_slice = dt[0:8]
        day = dt_slice[3:5]
        month = dt_slice[0:2]
        year = "20"+dt_slice[6:8]
        date = day+"-"+month+"-"+year

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
            myCursor.execute('INSERT INTO crimelogs (Type, Date, Location, Link) VALUES (\'%s\',\'%s\',\'%s\',\'%s\')' % (type, date, address, link))

        i += 5

# Checking DB
myCursor.execute("SELECT * FROM crimelogs;") # WHERE type = 'Assault';")
print(myCursor.fetchall(), end='\n')

# Commit to confirm changes
conn.commit()
# Close connection
conn.close()
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import pymysql

conn = pymysql.connect(host="localhost", user="root", passwd= "", db= "crimereportdb")

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
while (i < 2000):
    if (((i + 1) % 5) != 0):
        # print("a", tds[i + 0].text)
        var1=(tds[i + 1].text)
        dt =(tds[i + 2].text)
        var2 = dt[0:8]
        varr =(tds[i + 3].text)
        var3 = varr.title()
        print(var3)
        # print("e", tds[i + 4].text)
        for link in tds[i + 4]:
            var4 = ("https://spotcrime.com" + link["href"])


         myCursor.execute('INSERT INTO crimelogs (Type, Date, Location, Link) VALUES (\'%s\',\'%s\',\'%s\',\'%s\')' % (
         var1, var2, var3, var4))

        i += 5

myCursor.execute("SELECT * FROM crimelogs;")
print(myCursor.fetchall(), end='\n')

conn.commit()

conn.close()
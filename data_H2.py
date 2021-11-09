import threading
import mysql.connector as mc
import requests
import pandas as pd
import numpy as np
from datetime import datetime

mydb = mc.connect(
    host="localhost",
    user="root",
    password="",
    database="webta"
)

def get_last_date_api():
    cur = mydb.cursor()
    cur.execute('SELECT date FROM monitor WHERE id_gedung = 5 ORDER BY id DESC LIMIT 1')
    last_date = cur.fetchall()
    # print(last_date[0][0])
    cur.close()
    if (len(last_date)==1):
        return last_date[0][0]
    else :
        return datetime.strptime("2020-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')

def Get_Data():
    base_url = "http://213.190.4.40/iems/iems-api/index.php"
    device_token = "5034e836792df04c0794f4c2a6beb6a7"
    page = 0
    batas = False

    api_data_lisrik = []
    api_data_device = []
    api_data_date = []
    api_data_time = []

    while (batas == False) :
        pull = requests.get(base_url + "/public/devices/pull?device_token=" + device_token + "&page=" + str(page)).json()
        page += 1
        if (len(pull["data"])) != 0:
            for i in range(len(pull['data'])): 
                # print(pull['data'][i]['date'])
                try:
                    a = pull['data'][i]['date'] + ' ' + pull['data'][i]['time']
                    a = datetime.strptime(a,'%Y-%m-%d %H:%M:%S')
                    res = bool(a)
                except ValueError:
                    res = False
                if (res==True):
                    api_date = pull['data'][i]['date'] + ' ' + pull['data'][i]['time']
                    print (api_date)
                    api_date = datetime.strptime(api_date,'%Y-%m-%d %H:%M:%S')
                    # print(api_date)
                    db_date = get_last_date_api()
                    # print(api_date, db_date)
                    # print(api_date > db_date)
                    if  api_date > db_date:
                        api_data_lisrik.insert(0,float(pull["data"][i]["kwh"]))
                        api_data_device.insert(0,pull["data"][i]["id_m_devices"])
                        api_data_date.insert(0,pull["data"][i]["date"])
                        api_data_time.insert(0,pull["data"][i]["time"])
                    else:
                        batas = True
                        break
        else:  
            batas = True

    # print(api_data_date)
    dataset = pd.DataFrame({'Date': api_data_date, 'Time': api_data_time,'Device': api_data_device, 'Kwh': api_data_lisrik  })
    if len(dataset) == 0:
        return []
    # dataset.drop(['Unnamed: 0'], axis=1, inplace=True)
    Daya = dataset["Kwh"]
    Data_pisah_Datetime = dataset['Date'].str.cat(dataset['Time'], sep=' ')
    Data_Pisah_id = dataset["Device"]
    Data_filter = pd.concat([Data_Pisah_id, Data_pisah_Datetime, Daya], axis=1)
    Data_Benar = Data_filter
    Data_dateBenar = pd.to_datetime(Data_Benar["Date"], format="%Y-%m-%d", errors='coerce')
    Data_Benar = pd.concat([dataset["Device"], Data_dateBenar, Data_Benar["Kwh"]], axis=1)
    Data_Benar.dropna(inplace=True)
    Data_benar = Data_Benar.loc[(Data_Benar["Kwh"] > 0.0)]
    format = '%Y-%m-%d %H:%M:%S'
    Data_benar['Datetime'] = pd.to_datetime(Data_benar['Date'], format=format)
    Data_benar = Data_benar.set_index(pd.DatetimeIndex(Data_benar['Datetime']))
    Data_benar.drop(['Date'], axis=1, inplace=True)
    Data_benar.drop(['Datetime'], axis=1, inplace=True)
    Data_benar.drop(['Device'], axis=1, inplace=True)
    df_hour = Data_benar.resample('15min').max()
    df_hour = df_hour.resample('h').min()
    # df_interpolate_lin = df_hour.interpolate(method='linear', axis=0)
    # df_pakai = df_interpolate_lin
    # df_pakai = df_pakai.iloc[int(np.ceil(len(df_pakai.values)*.20)):]

    df_hour['datetime'] = df_hour.index
    df=df_hour.dropna()

    return df


# import sched, time
# s = sched.scheduler(time.time, time.sleep)
# def do_something(sc): 
#     print("Doing stuff...")
#     print("get data API ...")
#     dataset = Get_Data()

#     print("read API data completed.")
#     if (len(dataset)==0):
#         return True
#     data_list = dataset.values.tolist()
#     cur = mydb.cursor()

#     for data in data_list:
#         sql = "INSERT INTO `monitor`(id_gedung, kwh, date) VALUES(%s,%s,%s)"
#         print(data)
#         val = (0, str(data[0]), str(data[1]))
#         cur.execute(sql, val)
#         mydb.commit()
#     cur.close()
#     s.enter(5, 5, do_something, (sc,))

# s.enter(5, 5, do_something, (s,))
# s.run()

def import_data():
    threading.Timer(1800, import_data).start()
    dataset = Get_Data()
    print("read API data completed.")
    if (len(dataset)==0):
        return True
    data_list = dataset.values.tolist()
    cur = mydb.cursor()
    for data in data_list:
        sql = "INSERT INTO `monitor`(id_gedung, kwh, date) VALUES(%s,%s,%s)"
        print(data)
        val = (5, str(data[0]), str(data[1]))
        cur.execute(sql, val)
        mydb.commit()
    cur.close()

import_data()
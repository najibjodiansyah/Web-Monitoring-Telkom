# bikin data random dari bulan april sampai juli, sehari ada data kwh perjam,

# bikin data realtime dikirim setiap jam data terbaru dimulai detik dan jam yang sangat terbaru

# kenaikannya random naik dianka 0,1,2,3,dan 4, gaboleh turun

# semuanya generate buat setiap gedung yang ada di data base yang aktif

# semua data di kirim dan di simpan di database local "webta" di tabel monitor

#mulai setiap jam di menit 00:00 


import threading
import mysql.connector as mc
import random
from datetime import datetime
from time import time

mydb = mc.connect(
    host="localhost",
    user="root",
    password="",
    database="webta"
)

def connect_sensor():
    print("connect_sensor")
    threading.Timer(20, connect_sensor).start()
    print('lakukan .. !! ')

    now = datetime.now()

    current_time = now.strftime("%M:%S")
    
    # jam 22.17
    # if current_time == '00:00' :
    if current_time == current_time :
        print("jalan ========= ")
        print("Current Time =", current_time)
        cur = mydb.cursor()

        sql = "SELECT * FROM `gedung`"
        cur.execute(sql)
        data_gedung = cur.fetchall()

        kwh_gedung = []

        for gedung in data_gedung:
            
            if gedung[0]==0:
                continue

            sql = "SELECT * FROM monitor WHERE id_gedung=%s ORDER BY id DESC LIMIT 1" % gedung[0]
            cur.execute(sql)
            _gedung = cur.fetchall()
            
            if len(_gedung) != 0:
                
                kwh_gdg = _gedung[0][2]

            else:
                kwh_gdg = 450

        
            kwh_gedung.append(kwh_gdg)

        # while True:
            # print(gedung)
            deleted = check_deleted_gedung(gedung[0])
            # print(status)
            if int(deleted) == 0:
                kwh = (kwh_gdg + random.uniform(0.0, 4.0))

                sql = "INSERT INTO `monitor`(id_gedung, kwh, date) VALUES(%s,%s,%s)"
                val = (gedung[0], int(kwh), datetime.now())

                cur.execute(sql, val)
                mydb.commit()

                print(cur.rowcount, "Record inserted.", datetime.now())

        cur.close()

def check_deleted_gedung(id_gedung):
    cur = mydb.cursor()

    sql = "SELECT deleted FROM `gedung` WHERE id=%s" % id_gedung
    cur.execute(sql)
    gedung = cur.fetchall()
    cur.close()
    return gedung[0][0]

print("start")
connect_sensor()
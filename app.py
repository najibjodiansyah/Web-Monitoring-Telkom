from datetime import datetime
import time
import datetime
import random
import json
import threading
import hashlib
import requests
from flask import Flask, Response, render_template, request, jsonify, session, redirect
from flask_mysqldb import MySQL
from numpy import unique, where

from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans

import numpy as np
import mysql.connector as mc

import matplotlib.pyplot as plt
import matplotlib

import pandas as pd

matplotlib.use('Agg')


app = Flask(__name__, static_url_path='/static')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'webta'

mydb = mc.connect(
    host="localhost",
    user="root",
    password="",
    database="webta"
)

mysql = MySQL(app)

do_background = False

@app.route("/do_login", methods=["GET", "POST"])
def do_login():

    if request.method == "GET":
        return login()

    cur = mysql.connection.cursor()
    data = request.form

    username = data["username"]
    password = hashlib.md5(data["password"].encode())

    sql = 'SELECT * FROM `user` where username = "%s"' % username
    cur.execute(sql)
    user_data = cur.fetchall()
    cur.close()
    if user_data:
        user_data = user_data[0]
        if password.hexdigest() == user_data[1]:
            session["username"] = user_data[0]
            return dashboard()
        else:
            return login(1)  # password tidak sesuai
    else:
        return login(2)  # username tidak terdaftar
    # return login(False)


@app.route("/sign_out")
def sign_out():
    session.clear()
    return redirect("login")


@app.route("/login")
def login(code=0):

    message = ["Benar", "Password tidak sesuai!", "Username tidak terdaftar!"]
    print(message[code])
    return render_template('login.html', message=message[code])


@app.route("/users/change_password", methods=["POST"])
def change_password():

    cur = mysql.connection.cursor()
    data = request.form

    username = data["username"]
    password = hashlib.md5(data["password"].encode())
    password = password.hexdigest()

    sql = 'UPDATE `user` SET `password` = "'+password + \
        '" WHERE `user`.`username` = "'+username+'"'
    cur.execute(sql)

    mysql.connection.commit()
    cur.close()
    return redirect("/setting")


@app.route("/users/delete_user", methods=["POST"])
def delete_user():

    cur = mysql.connection.cursor()
    data = request.form

    username = data["username"]

    sql = 'DELETE FROM `user` WHERE `user`.`username` = "'+username+'"'
    cur.execute(sql)

    mysql.connection.commit()
    cur.close()
    return redirect("/setting")


@app.route("/users/create_user", methods=["POST"])
def create_user():

    cur = mysql.connection.cursor()
    data = request.form

    username = data["username"]
    password = hashlib.md5(data["password"].encode())
    password = password.hexdigest()
    name = data["name"]
    phone = data["phone"]

    sql = 'INSERT INTO `user` (`username`, `password`, `name`, `phone`) VALUES (%s, %s, %s, %s);'
    val = (username, password, name, phone)
    cur.execute(sql, val)

    mysql.connection.commit()
    cur.close()
    return redirect("/setting")


@app.route("/")
def dashboard():

    if session.get("username") == None:
        return redirect("login")

    cur = mysql.connection.cursor()
    sql = 'SELECT gedung.id, gedung.nama, gedung.pj FROM `gedung` JOIN user ON user.username = gedung.pj WHERE gedung.deleted != 1'

    cur.execute(sql)
    data_dashboard = cur.fetchall()

    data_show = []
    for data in data_dashboard:
        if not data_show.extend(str(data[0])):
            data_show.append(data)

    sql = "SELECT * FROM gedung WHERE deleted != 1"
    cur.execute(sql)
    mysql.connection.commit()

    data_gedung = cur.fetchall()
    cur.close()

    return render_template('dashboard.html', data_show=data_show, data_gedung=data_gedung, session=session, id=id)


@app.route("/tambah_gedung", methods=['POST'])
def tambah_gedung():
    if session.get("username") == None:
        return redirect("login")

    cur = mysql.connection.cursor()
    data = request.form

    sql = "INSERT INTO gedung( pj, nama, lokasi, deleted) VALUES ( %s, %s, %s,%s)"
    val = (session['username'], data['nama'], data['lokasi'], 0)

    cur.execute(sql, val)
    mysql.connection.commit()

    cur = mysql.connection.cursor()
    sql = "SELECT id FROM gedung ORDER BY id DESC LIMIT 1"
    cur.execute(sql)

    data_gedung = cur.fetchall()

    cur.close()
    return formgd()


@app.route('/get_opt_date/<id_gedung>')
def get_opt_date(id_gedung):
    cur = mysql.connection.cursor()
    sql = "SELECT DISTINCT MONTH(date),YEAR(date) FROM `monitor` JOIN gedung WHERE monitor.id_gedung= %s " % id_gedung
    cur.execute(sql)
    data_date = cur.fetchall()
    months = []
    years = []
    for date_ in data_date:
        months.append(date_[0])
        years.append(date_[1])

    data = {
        "bulan": list(set(months)),
        "tahun": list(set(years)),
        "completed": data_date
    }

    cur.close()

    return jsonify({"data": data})


@app.route('/get_opt_day/<id_gedung>/<year>/<month>')
def get_opt_day(id_gedung, year, month):
    cur = mysql.connection.cursor()
    if int(year) == -1:
        sql = "SELECT DISTINCT MONTH(date),YEAR(date),DAY(date) FROM `monitor` JOIN gedung WHERE monitor.id_gedung= %s " % id_gedung
    elif int(month) == -1:
        sql = "SELECT DISTINCT MONTH(date),YEAR(date),DAY(date) FROM `monitor` JOIN gedung WHERE monitor.id_gedung= " + \
            id_gedung + " and year(date) ="+year
    else:
        sql = "SELECT DISTINCT MONTH(date),YEAR(date),DAY(date) FROM `monitor` JOIN gedung WHERE monitor.id_gedung= " + \
            id_gedung + " and year(date) ="+year + " and Month(date) ="+month
    cur.execute(sql)
    data_date = cur.fetchall()
    months = []
    years = []
    days = []
    for date_ in data_date:
        months.append(date_[0])
        years.append(date_[1])
        days.append(date_[2])

    data = {

        "bulan": list(set(months)),
        "tahun": list(set(years)),
        "hari": list(set(days)),
        "completed": data_date
    }

    print(data["hari"])
    print(data)

    cur.close()

    return jsonify({"data": data})


@app.route("/get_dash_data")
def get_dash_data():
    mydb = mc.connect(
        host="localhost",
        user="root",
        password="",
        database="webta"
    )
    # print("getting blok data")
    cur1 = mysql.connection.cursor()
    sql = 'select * from gedung where deleted=0'
    cur1.execute(sql)
    data_gedung = cur1.fetchall()
    print("cek data_gedung")
    print(data_gedung)

    collect_dg = []
    null_kwh = []
    datajam1=[]
    datajam2=[]
    for idx, gedung in enumerate(data_gedung):
        cur2 = mysql.connection.cursor()
        date_now = datetime.datetime.now()-datetime.timedelta(hours=1)
        dt_string = date_now.strftime("%Y-%m-%d %H") + ':00:00'
        date_now2 = datetime.datetime.now()-datetime.timedelta(hours=2)
        dt_string2 = date_now2.strftime("%Y-%m-%d %H") + ':00:00'
        print("2 jam sebelum", dt_string2)
        print("1 jam sebelum", dt_string)
        print(gedung[0])
        # dt_string = '2021-08-17 11:00:00' 
        # dt_string2 = '2021-08-17 10:00:00' 
        sql = "SELECT kwh FROM monitor WHERE id_gedung= "+str(gedung[0])+" AND date='"+dt_string+"' ORDER BY id DESC LIMIT 1 "
        # sql = "SELECT kwh FROM monitor WHERE id_gedung= " + \
        #     str(gedung[0])+" ORDER BY id DESC LIMIT 1 "
        cur2.execute(sql)
        kwh_gedung = cur2.fetchall()
        sql2 = "SELECT kwh FROM monitor WHERE id_gedung= "+str(gedung[0])+" AND date='"+dt_string2+"' ORDER BY id DESC LIMIT 1 "
        # sql2 = "SELECT kwh from (select * from monitor where id_gedung = "+str(
        #     gedung[0])+" ORDER BY id DESC LIMIT 2) table_alias ORDER BY id LIMIT 1"
        cur2.execute(sql2)
        kwh_gedung2 = cur2.fetchall()
        # kondisi default untuk gedung yang kosong
        print("kwh gedung adalah =")
        print(len(kwh_gedung))
        print("kwh gedung adalah 2 =")
        print(len(kwh_gedung2))
        # tup=((-1.0,),)
        if len(kwh_gedung) == 0 or len(kwh_gedung2) == 0:
            null_kwh.append(idx)
        else:
            
            delta_kwh = kwh_gedung[0][0]-kwh_gedung2[0][0]
            print("ini delta kwh")
            print(delta_kwh)
            collect_dg.append([delta_kwh, delta_kwh])
        if len(kwh_gedung)!=0:
            datajam1.append([kwh_gedung[0][0],idx])
        if len(kwh_gedung2)!=0:
            datajam2.append([kwh_gedung2[0][0],idx])
            
        
    print("ini data jam 1",datajam1)
    print("ini data jam 2",datajam2)
    print(null_kwh, collect_dg)
    collect_cl = []
    labels_ = []
    if len(collect_dg) >= 3:
        # if collect_dg[0][0] != 0:
        # if a[0]!=0:
        # proses Clustering
        # konversi dari list ke numpy array
        collect_cl = np.array(collect_dg)
        # buat model KMeans
        model = KMeans(n_clusters=3, init='k-means++')
        #menghitung execute time
        start_time = time.time()    
        # fit the model
        model.fit(collect_cl)
        # assign a cluster to each example
        labels_ = model.fit_predict(collect_cl)
        labels_ = labels_.tolist()
        collect_cl = collect_cl.tolist()
        print(labels_)
        # from sklearn import metrics
        # from sklearn.metrics import silhouette_score
        # global_silhouette = metrics.silhouette_score(
        #     collect_cl, labels=labels_)
        # print("silhouette score: ", global_silhouette)
        
        # pengelompokan data cluster
        sub_1 = []
        sub_2 = []
        sub_3 = []

        for num, monitor in enumerate(collect_dg):
            if labels_[num] == 0:
                sub_1.append(monitor[0])
            elif labels_[num] == 1:
                sub_2.append(monitor[0])
            elif labels_[num] == 2:
                sub_3.append(monitor[0])

        mean_1 = mean_2 = mean_3 = 2
        if len(sub_1) != 0:
            mean_1 = sum(sub_1)/len(sub_1)  # rerata cluster 0
        if len(sub_2) != 0:
            mean_2 = sum(sub_2)/len(sub_2)  # rerata cluster 1
        if len(sub_3) != 0:
            mean_3 = sum(sub_3)/len(sub_3)  # rerata cluster

        kelas = [0, 0, 0]
        means = [mean_1, mean_2, mean_3]
        print("old means",means)
        means.sort(reverse=True)
        print("ini means",means)
        for index, mean in enumerate(means):
            print("index",index, mean_1, mean_2, mean_3)
            if mean == mean_1:
                kelas[index] = 0
            elif mean == mean_2:
                kelas[index] = 1
            elif mean == mean_3:
                kelas[index] = 2
            print(kelas)
        print(kelas)
        sub_1.sort()
        sub_2.sort()
        sub_3.sort()
        # print("min : ", kelas[0], sub_1[0:5])
        # print("min : ", kelas[1], sub_2[0:5])
        # print("min : ", kelas[2], sub_3[0:5])

        # sub_1.sort(reverse=True)
        # sub_2.sort(reverse=True)
        # sub_3.sort(reverse=True)
        # print("max : ", kelas[0], sub_1[0:5])
        # print("max : ", kelas[1], sub_2[0:5])
        # print("max : ", kelas[2], sub_3[0:5])

        # print("avg_per_class")
        # print("mean_1 kelas  : ", kelas[0],  mean_1)
        # print("mean_2 kelas  : ", kelas[1],  mean_2)
        # print("mean_3 kelas  : ", kelas[2],  mean_3)

        res_class = []

        count_data = [0, 0, 0]

        # for num, monitor in enumerate(collect_dg):
        #     if labels_[num] == 0:
        #         res_class.append(kelas[0])
        #         count_data[kelas[0]] += 1
        #     elif labels_[num] == 1:
        #         res_class.append(kelas[1])
        #         count_data[kelas[1]] += 1
        #     elif labels_[num] == 2:
        #         res_class.append(kelas[2])
        #         count_data[kelas[2]] += 1

        # print(collect_dg[11], res_class[11])
        # print("count_data", count_data)
        print("--- %s seconds ---" % (time.time() - start_time))

    idx_collect = 0
    coll = []
    lab = []
    index_dg = 0
    print(labels_)
    for idx in range(len(data_gedung)):
        if idx in null_kwh:
            coll.append(-1)
            lab.append(-1)
        else:
            if len(collect_cl) != 0:
                coll.append(collect_cl[idx_collect][0])
                level = 0
                if labels_[idx_collect] == kelas[1]:
                    level = 1
                elif labels_[idx_collect] == kelas[2]:
                    level = 2

                lab.append(level)
                idx_collect += 1
            else:
                coll.append(collect_dg[index_dg][0])
                index_dg+=1
                lab.append(-2)
    
    print(coll)
    print(lab)

    return jsonify({"data": lab, "kwh": coll,"datasatu":datajam1,"datadua":datajam2})


@app.route("/hapus_gedung/<id_gedung>", methods=['POST'])
def hapus_gedung(id_gedung):
    cur = mysql.connection.cursor()

    sql = "UPDATE `gedung` SET `deleted` = '1' WHERE `gedung`.`id` = %s;" % id_gedung

    cur.execute(sql)
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': 200})


@app.route("/get_gd")
def get_gd():
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM gedung WHERE deleted != 1 ORDER BY id ASC"
    cur.execute(sql)

    data_gedung = cur.fetchall()
    cur.close()
    return jsonify({"data": data_gedung})


@app.route("/get_gd_history")
def get_gd_history():
    cur = mysql.connection.cursor()
    sql = 'SELECT DISTINCT(monitor.id_gedung) FROM gedung JOIN monitor ON gedung.id = monitor.id_gedung WHERE gedung.deleted != 1 ORDER BY gedung.id ASC'
    cur.execute(sql)

    data_gedung = cur.fetchall()
    cur.close()
    return jsonify({"data": data_gedung})


@app.route("/history")
def history():
    if session.get("username") == None:
        return redirect("login")
    return render_template('history.html', data=[], session=session)


@app.route("/formgd")
def formgd():
    if session.get("username") == None:
        return redirect("login")
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM gedung WHERE deleted != 1"
    cur.execute(sql)

    data_gedung = cur.fetchall()
    cur.close()
    return render_template('formgd.html', data_gedung=data_gedung, session=session)


@app.route("/setting")
def setting():
    if session.get("username") == None:
        return redirect("login")

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user")

    get_data = cur.fetchall()

    users_data = []
    for user in get_data:
        user = {
            "username": user[0],
            "name": user[2],
            "phone": user[3]
        }
        users_data.append(user)
    return render_template('pengaturan.html', session=session, users_data=users_data)


@app.route('/chart-data')
def chart_data():
    def generate_random_data():
        while True:
            cur = mysql.connection.cursor()
            sql = "SELECT * FROM gedung WHERE deleted != 1"
            cur.execute(sql)
            cur.close()

            json_data = json.dumps(
                {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 'value': [random.random() * 100, random.random() * 100, random.random() * 100]})
            yield f"data:{json_data}\n\n"
            time.sleep(5)

    return Response(generate_random_data(), mimetype='text/event-stream')


@app.route('/reset_monitor/')
def reset_monitor():
    mydb = mc.connect(
        host="localhost",
        user="root",
        password="",
        database="webta"
    )

    cur = mydb.cursor()

    sql = "SELECT * FROM monitor"
    cur.execute(sql)
    data_monitor = cur.fetchall()

    for monitor in data_monitor:
        sql = "DELETE FROM `monitor` WHERE `monitor`.`id` = %s" % monitor[0]
        cur.execute(sql)
        mydb.commit()
        print("delete data id: ", monitor[0])

    sql = "ALTER TABLE monitor AUTO_INCREMENT = 1"
    cur.execute(sql)
    mydb.commit()
    cur.close()
    return "Reset Completed"


@app.route('/kmeansplus')
def kmeansplus():
    if session.get("username") == None:
        return redirect("login")

    cur1 = mydb.cursor()
    sql = "SELECT DISTINCT gedung.id, gedung.nama FROM `monitor` JOIN gedung ON gedung.id = monitor.id_gedung WHERE gedung.deleted != 1"
    cur1.execute(sql)
    data_gedung = cur1.fetchall()

    cur1.close()

    return render_template('kmeansplus.html', data_gedung=data_gedung, session=session)


@app.route("/result_kmeansplus/<bulan>/<tahun>/<gedung>/<page>")
# kondisi jika labels/data cluster tidak sama dengan 3
def result_kmeansplus(bulan, tahun, gedung, page=0):
    if session.get("username") == None:
        return redirect("login")
    bulan = int(bulan)
    tahun = int(tahun)
    gedung = int(gedung)
    page = int(page)

    cur1 = mydb.cursor()

    # ambil data monitor sesuai dengan bulan, tahun dan gedung yang dipilih
    sql = "select gedung.id, monitor.date, gedung.nama, monitor.kwh from monitor JOIN gedung on monitor.id_gedung=gedung.id where gedung.id=" + \
        str(gedung)+" AND MONTH(date)=" + str(bulan) + \
        " AND YEAR(date)=" + str(tahun) + " ORDER BY gedung.id ASC"
    cur1.execute(sql)
    data_monitor = cur1.fetchall()

    # proses mencari delta
    old_kwh = []
    old_kwh.append(0.0)
    for data in data_monitor:
        old_kwh.append(data[3])
    old_kwh.pop()
    print("ini old kwh")
    # print(old_kwh)

    kwh = []
    print('ini kwh asli')
    for data in data_monitor:
        kwh.append(data[3])
    # print(kwh)

    delta_kwh = []
    for i, delta in enumerate(kwh):
        delta_kwh.append(delta-old_kwh[i])
    delta_kwh[0] = 0

    print("ini delta kwh")
    # print(delta_kwh)
    # kalo data x lebih = dari 3 jalan kan
    data_X = []
    for monitor in delta_kwh:
        data_X.append([monitor, monitor])

    # print(data_X)

    # proses Clustering
    # konversi dari list ke numpy array
    data_X = np.array(data_X)
    # buat model
    model = KMeans(n_clusters=3, init='k-means++', random_state=42)
    # menghitung waktu execute fit kmeans
    start_time = time.time()
    # fit the model
    model.fit_predict(data_X)
    # assign a cluster to each example
    labels_ = model.fit_predict(data_X)
    print ("ini delta kwh", len(delta_kwh))
    i = 0
    while labels_[i] == 0:
        global_silhouette = -1
        i += 1
        print(i)
        if len(delta_kwh) == i:
            break  # This is the same as count = count + 1
    else:
        # gadipake karna hasil labels != n_cluster - 1
        from sklearn import metrics
        from sklearn.metrics import silhouette_score
        global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
        print("silhouette score: ", global_silhouette)

    # buat gambar koordinat hasil clustering data_X
    clusters = unique(labels_)
    print(clusters)
    # create scatter plot for samples from each cluster
    for cluster in clusters:
        # get row indexes for samples with this cluster
        row_ix = where(labels_ == cluster)
        # create scatter of these samples
        plt.scatter(data_X[row_ix, 0], data_X[row_ix, 1])
    # show the plot
    plt.savefig('result.png')
    plt.close()
    print("sum_per_class")

    # pengelompokan data cluster
    sub_1 = []
    sub_2 = []
    sub_3 = []

    for num, monitor in enumerate(delta_kwh):
        if labels_[num] == 0:
            sub_1.append(monitor)
        elif labels_[num] == 1:
            sub_2.append(monitor)
        elif labels_[num] == 2:
            sub_3.append(monitor)

    # level = ["tinggi", "sedang", "rendah"]
    # menentukan level setiap cluster

    mean_1 = mean_2 = mean_3 = 2
    if len(sub_1) != 0:
        mean_1 = sum(sub_1)/len(sub_1)  # rerata cluster 0
    if len(sub_2) != 0:
        mean_2 = sum(sub_2)/len(sub_2)  # rerata cluster 1
    if len(sub_3) != 0:
        mean_3 = sum(sub_3)/len(sub_3)  # rerata cluster 2

    kelas = [0, 0, 0]
    means = [mean_1, mean_2, mean_3]
    means.sort(reverse=True)

    # mencari urutan level setiap cluster
    for index, mean in enumerate(means):
        if mean == mean_1:
            kelas[0] = index
        elif mean == mean_2:
            kelas[1] = index
        elif mean == mean_3:
            kelas[2] = index

    sub_1.sort()
    sub_2.sort()
    sub_3.sort()
    print("min : ", kelas[0], sub_1[0:5])
    print("min : ", kelas[1], sub_2[0:5])
    print("min : ", kelas[2], sub_3[0:5])

    sub_1.sort(reverse=True)
    sub_2.sort(reverse=True)
    sub_3.sort(reverse=True)
    print("max : ", kelas[0], sub_1[0:5])
    print("max : ", kelas[1], sub_2[0:5])
    print("max : ", kelas[2], sub_3[0:5])

    print("avg_per_class")
    print("mean_1 kelas  : ", kelas[0],  mean_1)
    print("mean_2 kelas  : ", kelas[1],  mean_2)
    print("mean_3 kelas  : ", kelas[2],  mean_3)

    # mencari hasil urutan level cluster
    res_class = []

    count_data = [0, 0, 0]

    for num, monitor in enumerate(data_monitor):
        if labels_[num] == 0:
            res_class.append(kelas[0])
            count_data[kelas[0]] += 1
        elif labels_[num] == 1:
            res_class.append(kelas[1])
            count_data[kelas[1]] += 1
        elif labels_[num] == 2:
            res_class.append(kelas[2])
            count_data[kelas[2]] += 1

    print(data_monitor[11], res_class[11])
    print("count_data", count_data)

    start1 = int(page)*20
    end1 = start1 + 10

    start2 = end1
    end2 = start2 + 10

    page_numbers = int(len(data_monitor) / 20)
    if len(data_monitor) % 20 != 0:
        page_numbers = int(page_numbers) + 1

    print("page_numbers :", page_numbers)
    split_data1 = data_monitor[start1: end1]
    split_data2 = data_monitor[start2: end2]
    print(split_data1)
    print(split_data2)

    res_class1 = res_class[start1: end1]
    res_class2 = res_class[start2: end2]
    print(res_class1)
    print(res_class2)

    delta_kwh1 = delta_kwh[start1: end1]
    delta_kwh2 = delta_kwh[start2: end2]
    print("--- %s seconds ---" % (time.time() - start_time))

    cur1.close()

    # from sklearn import metrics
    # from sklearn.metrics import silhouette_score
    # global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
    # print("silhouette score: ", global_silhouette)

    return render_template('result_kmeansplus.html',
                           delta_kwh1=delta_kwh1,
                           delta_kwh2=delta_kwh2,
                           data_monitor1=split_data1,
                           data_monitor2=split_data2,
                           res_class1=res_class1,
                           res_class2=res_class2,
                           count_data=count_data,
                           page_numbers=page_numbers,
                           page=page,
                           bulan=bulan,
                           tahun=tahun,
                           gedung=gedung,
                           global_silhouette=global_silhouette,
                           session=session)


@app.route("/result_kmeansday/<hari>/<bulan>/<tahun>/<gedung>/<page>")
# kondisi jika labels/data cluster tidak sama dengan 3
def result_kmeansday(hari, bulan, tahun, gedung, page=0):
    if session.get("username") == None:
        return redirect("login")
    hari = int(hari)
    bulan = int(bulan)
    tahun = int(tahun)
    gedung = int(gedung)
    page = int(page)

    cur1 = mydb.cursor()

    # ambil data monitor sesuai dengan bulan, tahun dan gedung yang dipilih
    sql = "select gedung.id, monitor.date, gedung.nama, monitor.kwh from monitor JOIN gedung on monitor.id_gedung=gedung.id where gedung.id=" + \
        str(gedung)+" AND DAY(date)=" + str(hari) + " AND MONTH(date)=" + str(bulan) + \
        " AND YEAR(date)=" + str(tahun) + " ORDER BY gedung.id ASC"
    cur1.execute(sql)
    data_monitor = cur1.fetchall()

    # proses mencari delta
    old_kwh = []
    old_kwh.append(0.0)
    for data in data_monitor:
        old_kwh.append(data[3])
    old_kwh.pop()
    print("ini old kwh")
    print(old_kwh)

    kwh = []
    print('ini kwh asli')
    for data in data_monitor:
        kwh.append(data[3])
    print(kwh)

    delta_kwh = []
    for i, delta in enumerate(kwh):
        delta_kwh.append(delta-old_kwh[i])
    delta_kwh[0] = 0

    print("ini delta kwh")
    print(delta_kwh)

    data_X = []
    for monitor in delta_kwh:
        data_X.append([monitor, monitor])

    print(data_X)

    # proses Clustering
    # konversi dari list ke numpy array
    data_X = np.array(data_X)
    # buat model Birch
    model = KMeans(n_clusters=3, init='k-means++', random_state=42)
    # menghitung execute time
    start_time = time.time() 
    # fit the model
    model.fit_predict(data_X)
    # assign a cluster to each example
    labels_ = model.fit_predict(data_X)
    labels_ = labels_
    print("labelsnya:", labels_)
    i = 0
    print(delta_kwh)
    while labels_[i] == 0:
        global_silhouette = -1
        i += 1
        if len(delta_kwh) == i:
            break  # This is the same as count = count + 1
    else:
        # gadipake karna hasil labels != n_cluster - 1
        from sklearn import metrics
        from sklearn.metrics import silhouette_score
        global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
        print("silhouette score: ", global_silhouette)

    # buat gambar koordinat hasil clustering data_X
    clusters = unique(labels_)
    print(clusters)
    # create scatter plot for samples from each cluster
    for cluster in clusters:
        # get row indexes for samples with this cluster
        row_ix = where(labels_ == cluster)
        # create scatter of these samples
        plt.scatter(data_X[row_ix, 0], data_X[row_ix, 1])
    # show the plot
    plt.savefig('result.png')
    plt.close()
    print("sum_per_class")

    # pengelompokan data cluster
    sub_1 = []
    sub_2 = []
    sub_3 = []

    for num, monitor in enumerate(delta_kwh):
        if labels_[num] == 0:
            sub_1.append(monitor)
        elif labels_[num] == 1:
            sub_2.append(monitor)
        elif labels_[num] == 2:
            sub_3.append(monitor)

    print("ini monitor")
    print(monitor)
    print("ini nilai delta kwh")
    print(delta_kwh)

    # level = ["tinggi", "sedang", "rendah"]
    # menentukan level setiap cluster

    print(sub_1)
    print(sub_2)
    print(sub_3)

    # cari nilai rata-rata setiap cluster
    mean_1 = mean_2 = mean_3 = 2
    if len(sub_1) != 0:
        mean_1 = sum(sub_1)/len(sub_1)  # rerata cluster 0
    if len(sub_2) != 0:
        mean_2 = sum(sub_2)/len(sub_2)  # rerata cluster 1
    if len(sub_3) != 0:
        mean_3 = sum(sub_3)/len(sub_3)  # rerata cluster 2

    kelas = [0, 0, 0]
    means = [mean_1, mean_2, mean_3]
    means.sort(reverse=True)

    # mencari urutan level setiap cluster
    for index, mean in enumerate(means):
        if mean == mean_1:
            kelas[0] = index
        elif mean == mean_2:
            kelas[1] = index
        elif mean == mean_3:
            kelas[2] = index

    sub_1.sort()
    sub_2.sort()
    sub_3.sort()
    print("min : ", kelas[0], sub_1[0:5])
    print("min : ", kelas[1], sub_2[0:5])
    print("min : ", kelas[2], sub_3[0:5])

    sub_1.sort(reverse=True)
    sub_2.sort(reverse=True)
    sub_3.sort(reverse=True)
    print("max : ", kelas[0], sub_1[0:5])
    print("max : ", kelas[1], sub_2[0:5])
    print("max : ", kelas[2], sub_3[0:5])

    print("avg_per_class")
    print("mean_1 kelas  : ", kelas[0],  mean_1)
    print("mean_2 kelas  : ", kelas[1],  mean_2)
    print("mean_3 kelas  : ", kelas[2],  mean_3)

    # mencari hasil urutan level cluster
    res_class = []

    count_data = [0, 0, 0]

    for num, monitor in enumerate(data_monitor):
        if labels_[num] == 0:
            res_class.append(kelas[0])
            count_data[kelas[0]] += 1
        elif labels_[num] == 1:
            res_class.append(kelas[1])
            count_data[kelas[1]] += 1
        elif labels_[num] == 2:
            res_class.append(kelas[2])
            count_data[kelas[2]] += 1

    # print(data_monitor[11], res_class[11])
    print("count_data", count_data)

    start1 = int(page)*20
    end1 = start1 + 10

    start2 = end1
    end2 = start2 + 10

    page_numbers = int(len(data_X) / 20)
    if len(data_monitor) % 20 != 0:
        page_numbers = int(page_numbers) + 1

    print("page_numbers :", page_numbers)
    split_data1 = data_monitor[start1: end1]
    split_data2 = data_monitor[start2: end2]
    print(split_data1)
    print(split_data2)

    res_class1 = res_class[start1: end1]
    res_class2 = res_class[start2: end2]
    print(res_class1)
    print(res_class2)

    delta_kwh1 = delta_kwh[start1: end1]
    delta_kwh2 = delta_kwh[start2: end2]
    print("--- %s seconds ---" % (time.time() - start_time))

    cur1.close()

    return render_template('result_kmeansday.html',
                           delta_kwh1=delta_kwh1,
                           delta_kwh2=delta_kwh2,
                           data_monitor1=split_data1,
                           data_monitor2=split_data2,
                           res_class1=res_class1,
                           res_class2=res_class2,
                           count_data=count_data,
                           page_numbers=page_numbers,
                           page=page,
                           hari=hari,
                           bulan=bulan,
                           tahun=tahun,
                           gedung=gedung,
                           global_silhouette=global_silhouette,
                           session=session)


@app.route('/ahc')
def ahc():
    if session.get("username") == None:
        return redirect("login")
    bulan_collection = ['Januari', 'Februari', 'Maret', 'April', 'Mei',
                        'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    cur1 = mydb.cursor()
    sql = "SELECT DISTINCT MONTH(date),YEAR(date) FROM `monitor`"
    cur1.execute(sql)
    data_bulan = cur1.fetchall()

    cur1 = mydb.cursor()
    sql = "SELECT DISTINCT gedung.id, gedung.nama FROM `monitor` JOIN gedung ON gedung.id = monitor.id_gedung WHERE gedung.deleted != 1"
    cur1.execute(sql)
    data_gedung = cur1.fetchall()

    cur1.close()

    return render_template('ahc.html', data_gedung=data_gedung, session=session)


@app.route("/result_ahc/<bulan>/<tahun>/<gedung>/<page>")
def result_ahc(bulan, tahun, gedung, page=0):
    if session.get("username") == None:
        return redirect("login")
    bulan = int(bulan)
    tahun = int(tahun)
    gedung = int(gedung)
    page = int(page)

    cur1 = mydb.cursor()

    # ambil data monitor sesuai dengan bulan, tahun dan gedung yang dipilih
    sql = "select gedung.id, monitor.date, gedung.nama, monitor.kwh from monitor JOIN gedung on monitor.id_gedung=gedung.id where gedung.id=" + \
        str(gedung)+" AND MONTH(date)=" + str(bulan) + \
        " AND YEAR(date)=" + str(tahun) + " ORDER BY gedung.id ASC"
    cur1.execute(sql)
    data_monitor = cur1.fetchall()

    # proses mencari delta
    old_kwh = []
    old_kwh.append(0.0)
    for data in data_monitor:
        old_kwh.append(data[3])
    old_kwh.pop()
    print("ini old kwh")
    print(old_kwh)

    kwh = []
    print('ini kwh asli')
    for data in data_monitor:
        kwh.append(data[3])
    print(kwh)

    delta_kwh = []
    for i, delta in enumerate(kwh):
        delta_kwh.append(delta-old_kwh[i])
    delta_kwh[0] = 0

    print("ini delta kwh")
    print(delta_kwh)

    data_X = []
    for monitor in delta_kwh:
        data_X.append([monitor, monitor])

    # proses Clustering
    # konversi dari list ke numpy array
    data_X = np.array(data_X)
    # buat model Birch
    model = AgglomerativeClustering(n_clusters=3, affinity='euclidean', linkage='complete')
    #menghitung execute time
    start_time = time.time() 
    # fit the model
    model.fit(data_X)
    # assign a cluster to each example
    labels_ = model.fit_predict(data_X)
    i = 0
    print(delta_kwh)
    while labels_[i] == 0:
        global_silhouette = -1
        i += 1
        if len(delta_kwh) == i:
            break  # This is the same as count = count + 1
    else:
        # gadipake karna hasil labels != n_cluster - 1
        from sklearn import metrics
        from sklearn.metrics import silhouette_score
        global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
        print("silhouette score: ", global_silhouette)

    # buat gambar koordinat hasil clustering data_X
    clusters = unique(labels_)
    print(clusters)
    # create scatter plot for samples from each cluster
    for cluster in clusters:
        # get row indexes for samples with this cluster
        row_ix = where(labels_ == cluster)
        # create scatter of these samples
        plt.scatter(data_X[row_ix, 0], data_X[row_ix, 1])
    # show the plot
    plt.savefig('result.png')
    plt.close()
    print("sum_per_class")

    # pengelompokan data cluster
    sub_1 = []
    sub_2 = []
    sub_3 = []

    for num, monitor in enumerate(delta_kwh):
        if labels_[num] == 0:
            sub_1.append(monitor)
        elif labels_[num] == 1:
            sub_2.append(monitor)
        elif labels_[num] == 2:
            sub_3.append(monitor)

    # level = ["tinggi", "sedang", "rendah"]
    # menentukan level setiap cluster

    mean_1 = mean_2 = mean_3 = 2
    if len(sub_1) != 0:
        mean_1 = sum(sub_1)/len(sub_1)  # rerata cluster 0
    if len(sub_2) != 0:
        mean_2 = sum(sub_2)/len(sub_2)  # rerata cluster 1
    if len(sub_3) != 0:
        mean_3 = sum(sub_3)/len(sub_3)  # rerata cluster 2

    kelas = [0, 0, 0]
    means = [mean_1, mean_2, mean_3]
    means.sort(reverse=True)

    # mencari urutan level setiap cluster
    for index, mean in enumerate(means):
        if mean == mean_1:
            kelas[0] = index
        elif mean == mean_2:
            kelas[1] = index
        elif mean == mean_3:
            kelas[2] = index

    sub_1.sort()
    sub_2.sort()
    sub_3.sort()
    print("min : ", kelas[0], sub_1[0:5])
    print("min : ", kelas[1], sub_2[0:5])
    print("min : ", kelas[2], sub_3[0:5])

    sub_1.sort(reverse=True)
    sub_2.sort(reverse=True)
    sub_3.sort(reverse=True)
    print("max : ", kelas[0], sub_1[0:5])
    print("max : ", kelas[1], sub_2[0:5])
    print("max : ", kelas[2], sub_3[0:5])

    print("avg_per_class")
    print("mean_1 kelas  : ", kelas[0],  mean_1)
    print("mean_2 kelas  : ", kelas[1],  mean_2)
    print("mean_3 kelas  : ", kelas[2],  mean_3)

    # mencari hasil urutan level cluster
    res_class = []

    count_data = [0, 0, 0]

    for num, monitor in enumerate(data_monitor):
        if labels_[num] == 0:
            res_class.append(kelas[0])
            count_data[kelas[0]] += 1
        elif labels_[num] == 1:
            res_class.append(kelas[1])
            count_data[kelas[1]] += 1
        elif labels_[num] == 2:
            res_class.append(kelas[2])
            count_data[kelas[2]] += 1

    print(data_monitor[11], res_class[11])
    print("count_data", count_data)

    start1 = int(page)*20
    end1 = start1 + 10

    start2 = end1
    end2 = start2 + 10

    page_numbers = int(len(data_monitor) / 20)
    if len(data_monitor) % 20 != 0:
        page_numbers = int(page_numbers) + 1

    print("page_numbers :", page_numbers)
    split_data1 = data_monitor[start1: end1]
    split_data2 = data_monitor[start2: end2]

    res_class1 = res_class[start1: end1]
    res_class2 = res_class[start2: end2]

    delta_kwh1 = delta_kwh[start1: end1]
    delta_kwh2 = delta_kwh[start2: end2]
    print("--- %s seconds ---" % (time.time() - start_time))

    cur1.close()

    # from sklearn import metrics
    # from sklearn.metrics import silhouette_score
    # global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
    # print("silhouette score: ", global_silhouette)

    return render_template('result_ahc.html',
                           delta_kwh1=delta_kwh1,
                           delta_kwh2=delta_kwh2,
                           data_monitor1=split_data1,
                           data_monitor2=split_data2,
                           res_class1=res_class1,
                           res_class2=res_class2,
                           count_data=count_data,
                           page_numbers=page_numbers,
                           page=page,
                           bulan=bulan,
                           tahun=tahun,
                           gedung=gedung,
                           global_silhouette=global_silhouette,
                           session=session)


@app.route("/result_ahcday/<hari>/<bulan>/<tahun>/<gedung>/<page>")
def result_ahcday(hari, bulan, tahun, gedung, page=0):
    if session.get("username") == None:
        return redirect("login")
    hari = int(hari)
    bulan = int(bulan)
    tahun = int(tahun)
    gedung = int(gedung)
    page = int(page)

    cur1 = mydb.cursor()

    # ambil data monitor sesuai dengan bulan, tahun dan gedung yang dipilih
    sql = "select gedung.id, monitor.date, gedung.nama, monitor.kwh from monitor JOIN gedung on monitor.id_gedung=gedung.id where gedung.id=" + \
        str(gedung)+" AND DAY(date)=" + str(hari) + " AND MONTH(date)=" + str(bulan) + \
        " AND YEAR(date)=" + str(tahun) + " ORDER BY gedung.id ASC"
    cur1.execute(sql)
    data_monitor = cur1.fetchall()

    # proses mencari delta
    old_kwh = []
    old_kwh.append(0.0)
    for data in data_monitor:
        old_kwh.append(data[3])
    old_kwh.pop()
    print("ini old kwh")
    print(old_kwh)

    kwh = []
    print('ini kwh asli')
    for data in data_monitor:
        kwh.append(data[3])
    print(kwh)

    delta_kwh = []
    for i, delta in enumerate(kwh):
        delta_kwh.append(delta-old_kwh[i])
    delta_kwh[0] = 0

    print("ini delta kwh")
    print(delta_kwh)

    data_X = []
    for monitor in delta_kwh:
        data_X.append([monitor, monitor])

    print(data_X)

   # proses Clustering
    # konversi dari list ke numpy array
    data_X = np.array(data_X)
    # buat model Birch
    model = AgglomerativeClustering(
        n_clusters=3, affinity='euclidean', linkage='complete')
    #menghitung execute time
    start_time = time.time() 
    # fit the model
    model.fit(data_X)
    # assign a cluster to each example
    labels_ = model.fit_predict(data_X)
    labels_ = labels_
    print("labelsnya:", labels_)
    # i = 0
    i = 0
    print(delta_kwh)
    print(labels_)
    while labels_[i] == 0:
        global_silhouette = -1
        i += 1
        if len(delta_kwh) == i:
            break  # This is the same as count = count + 1
    else:
        # gadipake karna hasil labels != n_cluster - 1
        from sklearn import metrics
        from sklearn.metrics import silhouette_score
        global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
        print("silhouette score: ", global_silhouette)

    # buat gambar koordinat hasil clustering data_X
    clusters = unique(labels_)
    print(clusters)
    # create scatter plot for samples from each cluster
    for cluster in clusters:
        # get row indexes for samples with this cluster
        row_ix = where(labels_ == cluster)
        # create scatter of these samples
        plt.scatter(data_X[row_ix, 0], data_X[row_ix, 1])
    # show the plot
    plt.savefig('result.png')
    plt.close()
    print("sum_per_class")

    # pengelompokan data cluster
    sub_1 = []
    sub_2 = []
    sub_3 = []

    for num, monitor in enumerate(delta_kwh):
        if labels_[num] == 0:
            sub_1.append(monitor)
        elif labels_[num] == 1:
            sub_2.append(monitor)
        elif labels_[num] == 2:
            sub_3.append(monitor)

    print("ini monitor")
    print(monitor)
    print("ini nilai delta kwh")
    print(delta_kwh)

    # level = ["tinggi", "sedang", "rendah"]
    # menentukan level setiap cluster

    print(sub_1)
    print(sub_2)
    print(sub_3)

    # cari nilai rata-rata setiap cluster
    mean_1 = mean_2 = mean_3 = 2
    if len(sub_1) != 0:
        mean_1 = sum(sub_1)/len(sub_1)  # rerata cluster 0
    if len(sub_2) != 0:
        mean_2 = sum(sub_2)/len(sub_2)  # rerata cluster 1
    if len(sub_3) != 0:
        mean_3 = sum(sub_3)/len(sub_3)  # rerata cluster 2

    kelas = [0, 0, 0]
    means = [mean_1, mean_2, mean_3]
    means.sort(reverse=True)

    # mencari urutan level setiap cluster
    for index, mean in enumerate(means):
        if mean == mean_1:
            kelas[0] = index
        elif mean == mean_2:
            kelas[1] = index
        elif mean == mean_3:
            kelas[2] = index

    sub_1.sort()
    sub_2.sort()
    sub_3.sort()
    print("min : ", kelas[0], sub_1[0:5])
    print("min : ", kelas[1], sub_2[0:5])
    print("min : ", kelas[2], sub_3[0:5])

    sub_1.sort(reverse=True)
    sub_2.sort(reverse=True)
    sub_3.sort(reverse=True)
    print("max : ", kelas[0], sub_1[0:5])
    print("max : ", kelas[1], sub_2[0:5])
    print("max : ", kelas[2], sub_3[0:5])

    print("avg_per_class")
    print("mean_1 kelas  : ", kelas[0],  mean_1)
    print("mean_2 kelas  : ", kelas[1],  mean_2)
    print("mean_3 kelas  : ", kelas[2],  mean_3)

    # mencari hasil urutan level cluster
    res_class = []

    count_data = [0, 0, 0]

    for num, monitor in enumerate(data_monitor):
        if labels_[num] == 0:
            res_class.append(kelas[0])
            count_data[kelas[0]] += 1
        elif labels_[num] == 1:
            res_class.append(kelas[1])
            count_data[kelas[1]] += 1
        elif labels_[num] == 2:
            res_class.append(kelas[2])
            count_data[kelas[2]] += 1

    # print(data_monitor[11], res_class[11])
    print("count_data", count_data)

    start1 = int(page)*20
    end1 = start1 + 10

    start2 = end1
    end2 = start2 + 10

    page_numbers = int(len(data_X) / 20)
    if len(data_monitor) % 20 != 0:
        page_numbers = int(page_numbers) + 1

    print("page_numbers :", page_numbers)
    split_data1 = data_monitor[start1: end1]
    split_data2 = data_monitor[start2: end2]
    print(split_data1)
    print(split_data2)

    res_class1 = res_class[start1: end1]
    res_class2 = res_class[start2: end2]
    print(res_class1)
    print(res_class2)

    delta_kwh1 = delta_kwh[start1: end1]
    delta_kwh2 = delta_kwh[start2: end2]
    print("--- %s seconds ---" % (time.time() - start_time))

    cur1.close()

    return render_template('result_ahcday.html',
                           delta_kwh1=delta_kwh1,
                           delta_kwh2=delta_kwh2,
                           data_monitor1=split_data1,
                           data_monitor2=split_data2,
                           res_class1=res_class1,
                           res_class2=res_class2,
                           count_data=count_data,
                           page_numbers=page_numbers,
                           page=page,
                           hari=hari,
                           bulan=bulan,
                           tahun=tahun,
                           gedung=gedung,
                           global_silhouette=global_silhouette,
                           session=session)


@app.route('/dbscan')
def dbscan():
    if session.get("username") == None:
        return redirect("login")
    bulan_collection = ['Januari', 'Februari', 'Maret', 'April', 'Mei',
                        'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    cur1 = mydb.cursor()
    sql = "SELECT DISTINCT MONTH(date),YEAR(date) FROM `monitor`"
    cur1.execute(sql)
    data_bulan = cur1.fetchall()

    cur1 = mydb.cursor()
    sql = "SELECT DISTINCT gedung.id, gedung.nama FROM `monitor` JOIN gedung ON gedung.id = monitor.id_gedung WHERE gedung.deleted != 1"
    cur1.execute(sql)
    data_gedung = cur1.fetchall()

    cur1.close()

    return render_template('dbscan.html', data_gedung=data_gedung, session=session)


@app.route("/result_dbscan/<bulan>/<tahun>/<gedung>/<page>")
def result_dbscan(bulan, tahun, gedung, page=0):
    if session.get("username") == None:
        return redirect("login")
    bulan = int(bulan)
    tahun = int(tahun)
    gedung = int(gedung)
    page = int(page)

    cur1 = mydb.cursor()

    # ambil data monitor sesuai dengan bulan, tahun dan gedung yang dipilih
    sql = "select gedung.id, monitor.date, gedung.nama, monitor.kwh from monitor JOIN gedung on monitor.id_gedung=gedung.id where gedung.id=" + \
        str(gedung)+" AND MONTH(date)=" + str(bulan) + \
        " AND YEAR(date)=" + str(tahun) + " ORDER BY gedung.id ASC"
    cur1.execute(sql)
    data_monitor = cur1.fetchall()

    # proses mencari delta
    old_kwh = []
    old_kwh.append(0.0)
    for data in data_monitor:
        old_kwh.append(data[3])
    old_kwh.pop()
    print("ini old kwh")
    print(old_kwh)

    kwh = []
    print('ini kwh asli')
    for data in data_monitor:
        kwh.append(data[3])
    print(kwh)

    delta_kwh = []
    for i, delta in enumerate(kwh):
        delta_kwh.append(delta-old_kwh[i])
    delta_kwh[0] = 0

    print("ini delta kwh")
    print(delta_kwh)

    data_X = []
    for monitor in delta_kwh:
        data_X.append([monitor, monitor])

    print(data_X)

    #data_X = []
    # for monitor in data_monitor:
    # data_X.append([monitor[4], monitor[4]])

    # proses Clustering
    # konversi dari list ke numpy array
    data_X = np.array(data_X)
    # buat model Birch
    model = DBSCAN(eps=1.3, min_samples=2, metric='euclidean')
    #menghitung execute time
    start_time = time.time() 
    # fit the model
    model.fit(data_X)
    # assign a cluster to each example
    labels_ = model.fit_predict(data_X)
    i = 0
    
    while labels_[i] == 0:
        global_silhouette = -1
        i += 1
        print(labels_)
        if len(delta_kwh) == i:
            break  # This is the same as count = count + 1
        print("default")
    else:
        # gadipake karna hasil labels != n_cluster - 1
        from sklearn import metrics
        from sklearn.metrics import silhouette_score
        global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
        print("hasil dari library silhouette score: ", global_silhouette)
    # buat gambar koordinat hasil clustering data_X
    clusters = unique(labels_)
    print(clusters)
    # create scatter plot for samples from each cluster
    for cluster in clusters:
        # get row indexes for samples with this cluster
        row_ix = where(labels_ == cluster)
        # create scatter of these samples
        plt.scatter(data_X[row_ix, 0], data_X[row_ix, 1])
    # show the plot
    plt.savefig('result.png')
    plt.close()
    print("sum_per_class")

    # pengelompokan data cluster
    sub_1 = []
    sub_2 = []
    sub_3 = []

    for num, monitor in enumerate(delta_kwh):
        if labels_[num] == 0:
            sub_1.append(monitor)
        elif labels_[num] == 1:
            sub_2.append(monitor)
        elif labels_[num] == 2:
            sub_3.append(monitor)

    # level = ["tinggi", "sedang", "rendah"]
    # menentukan level setiap cluster

    mean_1 = mean_2 = mean_3 = 2
    if len(sub_1) != 0:
        mean_1 = sum(sub_1)/len(sub_1)  # rerata cluster 0
    if len(sub_2) != 0:
        mean_2 = sum(sub_2)/len(sub_2)  # rerata cluster 1
    if len(sub_3) != 0:
        mean_3 = sum(sub_3)/len(sub_3)  # rerata cluster 2

    kelas = [0, 0, 0]
    means = [mean_1, mean_2, mean_3]
    means.sort(reverse=True)

    # mencari urutan level setiap cluster
    for index, mean in enumerate(means):
        if mean == mean_1:
            kelas[0] = index
        elif mean == mean_2:
            kelas[1] = index
        elif mean == mean_3:
            kelas[2] = index

    sub_1.sort()
    sub_2.sort()
    sub_3.sort()
    print("min : ", kelas[0], sub_1[0:5])
    print("min : ", kelas[1], sub_2[0:5])
    print("min : ", kelas[2], sub_3[0:5])

    sub_1.sort(reverse=True)
    sub_2.sort(reverse=True)
    sub_3.sort(reverse=True)
    print("max : ", kelas[0], sub_1[0:5])
    print("max : ", kelas[1], sub_2[0:5])
    print("max : ", kelas[2], sub_3[0:5])

    print("avg_per_class")
    print("mean_1 kelas  : ", kelas[0],  mean_1)
    print("mean_2 kelas  : ", kelas[1],  mean_2)
    print("mean_3 kelas  : ", kelas[2],  mean_3)

    # mencari hasil urutan level cluster
    res_class = []

    count_data = [0, 0, 0]

    for num, monitor in enumerate(data_monitor):
        if labels_[num] == 0:
            res_class.append(kelas[0])
            count_data[kelas[0]] += 1
        elif labels_[num] == 1:
            res_class.append(kelas[1])
            count_data[kelas[1]] += 1
        elif labels_[num] == 2:
            res_class.append(kelas[2])
            count_data[kelas[2]] += 1

    print(data_monitor[11], res_class[11])
    print("count_data", count_data)

    start1 = int(page)*20
    end1 = start1 + 10

    start2 = end1
    end2 = start2 + 10

    page_numbers = int(len(data_monitor) / 20)
    if len(data_monitor) % 20 != 0:
        page_numbers = int(page_numbers) + 1

    print("page_numbers :", page_numbers)
    split_data1 = data_monitor[start1: end1]
    split_data2 = data_monitor[start2: end2]
    print(split_data1)
    print(split_data2)

    res_class1 = res_class[start1: end1]
    res_class2 = res_class[start2: end2]
    print(res_class1)
    print(res_class2)

    delta_kwh1 = delta_kwh[start1: end1]
    delta_kwh2 = delta_kwh[start2: end2]
    print("--- %s seconds ---" % (time.time() - start_time))

    cur1.close()

    # from sklearn import metrics
    # from sklearn.metrics import silhouette_score
    # global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
    # print("silhouette score: ", global_silhouette)

    return render_template('result_dbscan.html',
                           delta_kwh1=delta_kwh1,
                           delta_kwh2=delta_kwh2,
                           data_monitor1=split_data1,
                           data_monitor2=split_data2,
                           res_class1=res_class1,
                           res_class2=res_class2,
                           count_data=count_data,
                           page_numbers=page_numbers,
                           page=page,
                           bulan=bulan,
                           tahun=tahun,
                           gedung=gedung,
                           global_silhouette=global_silhouette,
                           session=session)


@app.route("/result_dbscanday/<hari>/<bulan>/<tahun>/<gedung>/<page>")
def result_dbscanday(hari, bulan, tahun, gedung, page=0):
    if session.get("username") == None:
        return redirect("login")
    hari = int(hari)
    bulan = int(bulan)
    tahun = int(tahun)
    gedung = int(gedung)
    page = int(page)

    cur1 = mydb.cursor()

    # ambil data monitor sesuai dengan bulan, tahun dan gedung yang dipilih
    sql = "select gedung.id, monitor.date, gedung.nama, monitor.kwh from monitor JOIN gedung on monitor.id_gedung=gedung.id where gedung.id=" + \
        str(gedung)+" AND DAY(date)=" + str(hari) + " AND MONTH(date)=" + str(bulan) + \
        " AND YEAR(date)=" + str(tahun) + " ORDER BY gedung.id ASC"
    cur1.execute(sql)
    data_monitor = cur1.fetchall()

    # proses mencari delta
    old_kwh = []
    old_kwh.append(0.0)
    for data in data_monitor:
        old_kwh.append(data[3])
    old_kwh.pop()
    print("ini old kwh")
    print(old_kwh)

    kwh = []
    print('ini kwh asli')
    for data in data_monitor:
        kwh.append(data[3])
    print(kwh)

    delta_kwh = []
    for i, delta in enumerate(kwh):
        delta_kwh.append(delta-old_kwh[i])
    delta_kwh[0] = 0

    print("ini delta kwh")
    print(delta_kwh)

    data_X = []
    for monitor in delta_kwh:
        data_X.append([monitor, monitor])

    print(data_X)

# proses Clustering
    # konversi dari list ke numpy array
    data_X = np.array(data_X)
    # buat model Birch
    model = DBSCAN(eps=0.4, min_samples=3, metric='euclidean')
    start_time = time.time() 
    # fit the model
    model.fit(data_X)
    # assign a cluster to each example
    labels_ = model.fit_predict(data_X)
    labels_ = labels_
    print("labelsnya:", labels_)
    # i = 0
    i = 0
    print(delta_kwh)
    while labels_[i] == 0:
        global_silhouette = -1
        i += 1
        if len(delta_kwh) == i:
            break  # This is the same as count = count + 1
        print("default")
    else:
        # gadipake karna hasil labels != n_cluster - 1
        from sklearn import metrics
        from sklearn.metrics import silhouette_score
        global_silhouette = metrics.silhouette_score(data_X, labels=labels_)
        print("hasil dari library silhouette score: ", global_silhouette)

    # buat gambar koordinat hasil clustering data_X
    clusters = unique(labels_)
    print(clusters)
    # create scatter plot for samples from each cluster
    for cluster in clusters:
        # get row indexes for samples with this cluster
        row_ix = where(labels_ == cluster)
        # create scatter of these samples
        plt.scatter(data_X[row_ix, 0], data_X[row_ix, 1])
    # show the plot
    plt.savefig('result.png')
    plt.close()
    print("sum_per_class")

    # pengelompokan data cluster
    sub_1 = []
    sub_2 = []
    sub_3 = []

    for num, monitor in enumerate(delta_kwh):
        if labels_[num] == 0:
            sub_1.append(monitor)
        elif labels_[num] == 1:
            sub_2.append(monitor)
        elif labels_[num] == 2:
            sub_3.append(monitor)

    print("ini monitor")
    print(monitor)
    print("ini nilai delta kwh")
    print(delta_kwh)

    # level = ["tinggi", "sedang", "rendah"]
    # menentukan level setiap cluster

    print(sub_1)
    print(sub_2)
    print(sub_3)

    # cari nilai rata-rata setiap cluster
    mean_1 = mean_2 = mean_3 = 2
    if len(sub_1) != 0:
        mean_1 = sum(sub_1)/len(sub_1)  # rerata cluster 0
    if len(sub_2) != 0:
        mean_2 = sum(sub_2)/len(sub_2)  # rerata cluster 1
    if len(sub_3) != 0:
        mean_3 = sum(sub_3)/len(sub_3)  # rerata cluster 2

    kelas = [0, 0, 0]
    means = [mean_1, mean_2, mean_3]
    means.sort(reverse=True)

    # mencari urutan level setiap cluster
    for index, mean in enumerate(means):
        if mean == mean_1:
            kelas[0] = index
        elif mean == mean_2:
            kelas[1] = index
        elif mean == mean_3:
            kelas[2] = index

    sub_1.sort()
    sub_2.sort()
    sub_3.sort()
    print("min : ", kelas[0], sub_1[0:5])
    print("min : ", kelas[1], sub_2[0:5])
    print("min : ", kelas[2], sub_3[0:5])

    sub_1.sort(reverse=True)
    sub_2.sort(reverse=True)
    sub_3.sort(reverse=True)
    print("max : ", kelas[0], sub_1[0:5])
    print("max : ", kelas[1], sub_2[0:5])
    print("max : ", kelas[2], sub_3[0:5])

    print("avg_per_class")
    print("mean_1 kelas  : ", kelas[0],  mean_1)
    print("mean_2 kelas  : ", kelas[1],  mean_2)
    print("mean_3 kelas  : ", kelas[2],  mean_3)

    # mencari hasil urutan level cluster
    res_class = []

    count_data = [0, 0, 0]

    for num, monitor in enumerate(data_monitor):
        if labels_[num] == 0:
            res_class.append(kelas[0])
            count_data[kelas[0]] += 1
        elif labels_[num] == 1:
            res_class.append(kelas[1])
            count_data[kelas[1]] += 1
        elif labels_[num] == 2:
            res_class.append(kelas[2])
            count_data[kelas[2]] += 1

    # print(data_monitor[11], res_class[11])
    print("count_data", count_data)

    start1 = int(page)*20
    end1 = start1 + 10

    start2 = end1
    end2 = start2 + 10

    page_numbers = int(len(data_X) / 20)
    if len(data_monitor) % 20 != 0:
        page_numbers = int(page_numbers) + 1

    print("page_numbers :", page_numbers)
    split_data1 = data_monitor[start1: end1]
    split_data2 = data_monitor[start2: end2]
    print(split_data1)
    print(split_data2)

    res_class1 = res_class[start1: end1]
    res_class2 = res_class[start2: end2]
    print(res_class1)
    print(res_class2)

    delta_kwh1 = delta_kwh[start1: end1]
    delta_kwh2 = delta_kwh[start2: end2]
    print("--- %s seconds ---" % (time.time() - start_time))

    cur1.close()

    return render_template('result_dbscanday.html',
                           delta_kwh1=delta_kwh1,
                           delta_kwh2=delta_kwh2,
                           data_monitor1=split_data1,
                           data_monitor2=split_data2,
                           res_class1=res_class1,
                           res_class2=res_class2,
                           count_data=count_data,
                           page_numbers=page_numbers,
                           page=page,
                           bulan=bulan,
                           hari=hari,
                           tahun=tahun,
                           gedung=gedung,
                           global_silhouette=global_silhouette,
                           session=session)

if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.run(host='127.0.0.1', port=4321, debug=True, use_reloader=True)

"""ก๋วยเตี๋ยวร่มลื่น"""
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import json
import random
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
print('>>>', DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)

app = Flask(__name__)
connection = mysql.connector.connect(
    host=DB_HOST,
    port=3306,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_DATABASE
)

curs = connection.cursor()
myname = ''
myid = ''
pick = ''

@app.route('/')
def firstpage():
    '''หน้าแรกของ web ฝั่ง user'''
    return render_template('firstpage.html')

@app.route('/table')
def table():
    '''เลือกหมายเลขโต๊ะสำหรับนั่งทานที่ร้าน'''
    return render_template('table.html')

@app.route('/name')
def name():
    '''สั่งกลับบ้าน กรอกชื่อ'''
    return render_template('takehome.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        global myname
        global myid
        myname = request.form['name']
        myid = random.randrange(0, 1000000)
        print('=====================')
        print(myname, myid)
        print('=====================')
        sql = 'INSERT INTO users (id, name, menus) VALUES (%s, %s, %s)'
        curs.execute(sql, (myid, myname, '[]'))
        connection.commit()
    return render_template('home.html', myname=myname, myid=myid)

@app.route('/menus', methods=['GET', 'POST'])
def menus():
    ''' ดึงเมนูมาแสดง '''
    curs.execute('SELECT * FROM menus')
    menu = curs.fetchall()
    curs.execute('SELECT type FROM options')
    options = [i[0] for i in curs.fetchall()]
    all_picked_options = []
    sql = ('SELECT price FROM menus WHERE name = %s')
    curs.execute(sql, (pick, ))
    main_price = curs.fetchall()
    for i in main_price:
        main_price = i[0]
    if request.method == 'POST':
        for group in options:
            all_picked_options += request.form.getlist(group)
        all_picked_options = str(all_picked_options)
        print(pick, all_picked_options, myname, myid)
        sql = 'INSERT INTO orderuser (iduser, tableuser, menu, orderoption, special, num, price) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        curs.execute(sql, (myid, myname, pick, all_picked_options, '1', '1', main_price))
        connection.commit()
    return render_template('menu.html', datas=menu)

@app.route('/options', methods=['GET', 'POST'])
def options():
    ''' option ของแต่ละเมนู '''
    if request.method == 'POST':
        global pick
        pick = request.form['pick']
        sql = 'SELECT price FROM menus WHERE name = %s'
        curs.execute(sql, (pick, ))
        main_price = curs.fetchall()[0][0]
        if 'ก๋วยเตี๋ยว' in pick:
            curs.execute('SELECT * FROM options')
        if 'เกาเหลา' in pick:
            curs.execute('SELECT * FROM options WHERE name = "เกาเหลา"')
        option_menu = curs.fetchall()
        items = {}
        for i in option_menu:
            yea = json.loads(i[3].replace("'", '"'))
            items[i[2]] = yea
    return render_template('option.html', datas=option_menu, items=items, pick=pick)

@app.route('/ordersummary', methods=['GET', 'POST'])
def order_summary():
    ''' รายการอาหารที่ลูกค้าสั่ง '''
    sql = 'SELECT iduser, tableuser FROM orderuser WHERE iduser = %s'
    curs.execute(sql, (myid, ))
    id_table = curs.fetchall()
    print(id_table)

    sql = 'SELECT menu, num, price FROM orderuser WHERE iduser = %s'
    curs.execute(sql, (myid, ))
    user_get = curs.fetchall()
    print(user_get)

    sql = 'SELECT price FROM orderuser WHERE iduser = %s'
    curs.execute(sql, (myid, ))
    price = curs.fetchall()
    cost = 0
    for i in price:
        cost += float(i[0])
    print('ราคาาาาาาาาาาาาาาาาาา', price, cost)

    optionuser = 'SELECT orderoption FROM orderuser WHERE iduser = %s'
    curs.execute(optionuser, (myid, ))
    get_option = curs.fetchall()
    print(get_option)
    options = []
    for item in get_option:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', item)
        options += [json.loads(item[0].replace("'", '"'))]
    print(options)
    datas = zip(user_get, options)
    return render_template('ordersummary.html', id=id_table, datas=datas, price=cost)

@app.route('/complete')
def complete():
    return render_template('complete.html')

if __name__ == '__main__':
    app.run(debug=True)

"""ก๋วยเตี๋ยวร่มลื่น"""
from flask import Flask, render_template, request, redirect, url_for
from flask.scaffold import F
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
# print('>>>', DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)

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
    num_table = [i for i in range(1, 11)]
    return render_template('table.html', datas=num_table)

@app.route('/name')
def name():
    '''สั่งกลับบ้าน กรอกชื่อ'''
    return render_template('takehome.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        global myname
        global myid
        try:
            myname = request.form['name']
        except:
            myname = request.form['table']
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
            item = request.form.getlist(group)
            all_picked_options += item
            if item == ['พิเศษ']:
                main_price += 10
        all_picked_options = str(all_picked_options)
        num = request.form['num']
        main_price *= int(num)
        print(pick, all_picked_options, myname, myid)
        sql = 'INSERT INTO orderuser (iduser, tableuser, menu, orderoption, num, price) VALUES (%s, %s, %s, %s, %s, %s)'
        curs.execute(sql, (myid, myname, pick, all_picked_options, num, main_price))
        connection.commit()
    return render_template('menu.html', datas=menu)

@app.route('/options', methods=['GET', 'POST'])
def options():
    ''' option ของแต่ละเมนู '''
    if request.method == 'POST':
        global pick
        pick = request.form['pick']
        sql = 'SELECT price, next FROM menus WHERE name = %s'
        curs.execute(sql, (pick, ))
        price_next = curs.fetchall()
        for item in price_next:
            main_price = item[0]
            next_option = item[1]
            print(main_price, next_option)
        sql = 'SELECT * FROM options WHERE name = %s'
        curs.execute(sql, (next_option, ))
        option_menu = curs.fetchall()
        items = {}
        for i in option_menu:
            yea = json.loads(i[3].replace("'", '"'))
            items[i[2]] = yea
        num = [i for i in range(1,11)]
    return render_template('option.html', datas=option_menu, items=items, pick=pick, num=num)

@app.route('/ordersummary', methods=['GET', 'POST'])
def order_summary():
    ''' รายการอาหารที่ลูกค้าสั่ง '''
    if request.method == 'POST':
        lob = request.form['delete']
        print('LOB >>>>>>>>>>>>>>', lob, list(lob), type(lob))
        if lob == 'all':
            sql = 'DELETE FROM orderuser WHERE iduser = %s'
            vals = (myid, )
        else:
            sql = 'DELETE FROM orderuser WHERE (id, iduser) = (%s, %s)'
            vals = (lob, myid, )
        curs.execute(sql, vals)
        connection.commit()
    sql = 'SELECT iduser, tableuser FROM orderuser WHERE iduser = %s'
    curs.execute(sql, (myid, ))
    id_table = curs.fetchall()
    print('id_table >>>>>>>>>>', id_table)

    sql = 'SELECT menu, num, price FROM orderuser WHERE iduser = %s'
    curs.execute(sql, (myid, ))
    user_get = curs.fetchall()
    print('user_get >>>>>>>>>>', user_get)

    sql = 'SELECT price FROM orderuser WHERE iduser = %s'
    curs.execute(sql, (myid, ))
    price = curs.fetchall()
    cost = sum(float(i[0]) for i in price)
    print('ราคาาาาาาาาาาาาาาาาาาา', price, cost)

    sql = 'SELECT id FROM orderuser WHERE iduser = %s'
    curs.execute(sql, (myid, ))
    menu_id = curs.fetchall()
    menu_id = [i[0] for i in menu_id]
    print('menu_id >>>>>>>>>>>>', menu_id)

    optionuser = 'SELECT orderoption FROM orderuser WHERE iduser = %s'
    curs.execute(optionuser, (myid, ))
    get_option = curs.fetchall()
    print(get_option)
    options = []
    for item in get_option:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', item)
        options += [json.loads(item[0].replace("'", '"'))]
    print(options)

    datas = zip(user_get, options, menu_id)
    print('datas >>>>>>>>>>>>>', datas)
    return render_template('ordersummary.html', id=id_table, datas=datas, price=cost)

@app.route('/complete', methods=['GET', 'POST'])
def complete():
    sql = 'INSERT INTO queue_user (iduser, tableuser) VALUES (%s, %s)'
    curs.execute(sql, (myid, myname))
    connection.commit()
    curs.execute('SELECT COUNT(*) FROM queue_user')
    queue = curs.fetchall()
    #print('queue >>>>>>>>>', queue)
    return render_template('complete.html', queue=queue[0][0])

@app.route('/admin_menu', methods=['GET', 'POST'])
def admin_menu():
    curs.execute('SELECT * FROM queue_user')
    order_admin = curs.fetchall()
    order_list = []
    order_option = []
    for item in order_admin:
        sql = 'SELECT * FROM orderuser WHERE (iduser, tableuser) = (%s, %s)'
        curs.execute(sql, (item[1], item[2]))
        orderr = curs.fetchall()
        print(item[0], end='\n')
        # for item_menu in orderr:
        #     print(item_menu)
        # print('----------------------------------------------------------------------')
        orderr = [list(i) for i in orderr]
        for menu in orderr:
            menu[4] = json.loads(menu[4].replace("'", '"'))
        order_list += [orderr]
    print('*************** order_list *******************************************************')
    print(*order_list, sep='\n')
    print('**********************************************************************************')
    return render_template('admin_menu.html', datas=order_list)

@app.route('/money')
def money():
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
    cost = sum(float(i[0]) for i in price)
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
    return render_template('money.html', id=id_table, datas=datas, price=cost)

@app.route('/admin_home', methods=['GET', 'POST'])
def admin_home():
    return render_template('admin_home.html')

@app.route('/admin_account', methods=['GET', 'POST'])
def admin_account():
    return render_template('admin_account.html')

@app.route('/admin_menu_success', methods=['GET', 'POST'])
def admin_menu_success():
    return render_template('admin_menu_success.html')

if __name__ == '__main__':
    app.run(debug=True)

"""ก๋วยเตี๋ยวร่มลื่น"""
from weakref import ProxyTypes
from flask import Flask, render_template, request, redirect, url_for
from flask.scaffold import F
import mysql.connector
import json
import random
from dotenv import load_dotenv
import os
from datetime import datetime, date

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
print('>>>', DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)
app = Flask(__name__)
# connection = mysql.connector.connect(
#     host=DB_HOST,
#     port=3306,
#     user=DB_USER,
#     password=DB_PASSWORD,
#     database=DB_DATABASE
# )

# curs = connection.cursor()
myname = ''
myid = ''
pick = ''
order_id = ''

class DB:
    conn = None # connection
    curs = None # cursor

    def connect(self):
        print('DATABASE: Connecting...')
        self.conn = mysql.connector.connect(
            host=DB_HOST,
            port=3306,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        self.curs = self.conn.cursor()
        print('DATABASE: Connected.')

    def query(self, sql, values):
        try:
            print('DATABASE: Querying...:', sql, 'values:', values)
            self.curs.execute(sql, values)
        except: # reconnect when timeout
            print('DATABASE: Error, reconnecting...')
            self.connect()
            print('DATABASE: Querying...:', sql, 'values:', values)
            self.curs.execute(sql, values)
        finally:
            print('DATABASE: Query finished.')
        return self.curs

    def save(self):
        print('DATABASE: Committing changes...')
        self.conn.commit()
        print('DATABASE: Committed.')

    def fetch(self):
        print('DATABASE: Fetching data...')
        yea = self.curs.fetchall()
        print('DATABASE: Fetched.')
        return yea

database = DB()
database.connect()

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
        global myname, myid
        try:
            myname = request.form['name']
        except:
            myname = request.form['table']
        myid = random.randrange(0, 1000000)
        print('=====================')
        print(myname, myid)
        print('=====================')
        sql = 'INSERT INTO users (id, name, menus) VALUES (%s, %s, %s)'
        database.query(sql, (myid, myname, '[]'))
        database.save()
    return render_template('home.html', myname=myname, myid=myid)

@app.route('/menus', methods=['GET', 'POST'])
def menus():
    ''' ดึงเมนูมาแสดง '''
    database.query('SELECT * FROM menus', ())
    menu = database.fetch()
    database.query('SELECT type FROM options', ())
    options = list(set([i[0] for i in database.fetch()]))
    all_picked_options = []
    sql = ('SELECT price FROM menus WHERE name = %s')
    database.query(sql, (pick, ))
    main_price = database.fetch()
    for i in main_price:
        main_price = i[0]
    if request.method == 'GET':
        global order_id
        order_id = random.randrange(0, 1000000)
        print(order_id)
    if request.method == 'POST':
        print('options >>>', options)
        for group in options:
            print('group >>>>>', group)
            item = request.form.getlist(group)
            all_picked_options += item
            if item == ['พิเศษ']:
                main_price += 10
        all_picked_options = str(all_picked_options)
        num = request.form['num']
        main_price *= int(num)
        print(pick, all_picked_options, myname, myid)
        sql = 'INSERT INTO orderuser (iduser, tableuser, menu, orderoption, num, price, orderid) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        database.query(sql, (myid, myname, pick, all_picked_options, num, main_price, order_id))
        database.save()
    return render_template('menu.html', datas=menu)

@app.route('/options', methods=['GET', 'POST'])
def options():
    ''' option ของแต่ละเมนู '''
    if request.method == 'POST':
        global pick
        pick = request.form['pick']
        sql = 'SELECT price, next FROM menus WHERE name = %s'
        database.query(sql, (pick, ))
        price_next = database.fetch()
        for item in price_next:
            main_price = item[0]
            next_option = item[1]
            print(main_price, next_option)
        sql = 'SELECT * FROM options WHERE name = %s'
        database.query(sql, (next_option, ))
        option_menu = database.fetch()
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
            sql = 'DELETE FROM orderuser WHERE orderid = %s'
            vals = (order_id, )
        else:
            sql = 'DELETE FROM orderuser WHERE (id, iduser, orderid) = (%s, %s, %s)'
            vals = (lob, myid, order_id, )
        database.query(sql, vals)
        database.save()
    sql = 'SELECT iduser, tableuser FROM orderuser WHERE orderid = %s'
    database.query(sql, (order_id, ))
    id_table = database.fetch()
    print('id_table >>>>>>>>>>', id_table)

    sql = 'SELECT menu, num, price FROM orderuser WHERE orderid = %s'
    database.query(sql, (order_id, ))
    user_get = database.fetch()
    print('user_get >>>>>>>>>>', user_get)

    sql = 'SELECT price FROM orderuser WHERE orderid = %s'
    database.query(sql, (order_id, ))
    price = database.fetch()
    cost = sum(float(i[0]) for i in price)
    print('ราคาาาาาาาาาาาาาาาาาาา', price, cost)

    sql = 'SELECT id FROM orderuser WHERE orderid = %s'
    database.query(sql, (order_id, ))
    menu_id = database.fetch()
    menu_id = [i[0] for i in menu_id]
    print('menu_id >>>>>>>>>>>>', menu_id)

    optionuser = 'SELECT orderoption FROM orderuser WHERE orderid = %s'
    database.query(optionuser, (order_id, ))
    get_option = database.fetch()
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
    '''คิว'''
    sql = 'SELECT price FROM orderuser WHERE iduser = %s'
    database.query(sql, (myid, ))
    price = database.fetch()
    cost = sum(float(i[0]) for i in price)
    sql = 'INSERT INTO queue_user (iduser, tableuser, totalprice, ordertime, orderid) VALUES (%s, %s, %s, %s, %s)'
    database.query(sql, (myid, myname, cost, str(datetime.now()), order_id))
    database.save()
    database.query('SELECT COUNT(*) FROM queue_user', ())
    queue = database.fetch()
    #print('queue >>>>>>>>>', queue)
    return render_template('complete.html', queue=queue[0][0])

@app.route('/admin_menu', methods=['GET', 'POST'])
def admin_menu():
    '''หน้าเว็บฝั่งแม่ค้า'''
    cook = 'กำลังปรุง'
    if request.method == 'POST':
        # try:
        orderiduser = request.form
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', orderiduser)
        orderiduser_id = dict(orderiduser)
        orderiduser_id = next(iter((orderiduser_id.items())) )
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ไหมอยากเห็นนนนนนนนนนน', orderiduser_id)
        if orderiduser_id[0] == 'cooking':
            sql = "UPDATE queue_user SET status = 'กำลังปรุง' WHERE orderid = %s"
            database.query(sql, (orderiduser_id[1], ))
            database.save()
        elif orderiduser_id[0] == 'complete':
            sql = "SELECT iduser, tableuser, totalprice, orderid FROM queue_user WHERE orderid = %s"
            database.query(sql, (orderiduser_id[1], ))
            user_data = database.fetch()
            for data in user_data:
                user_data = data
            print('user_data >>>>>>>>>>>>>>>>>>>>>>>>', user_data)
            sql = "INSERT INTO complete_user (iduser, tableuser, totalprice, orderid) VALUES (%s, %s, %s, %s)"
            database.query(sql, user_data)
            sql = "DELETE FROM queue_user WHERE orderid = %s"
            database.query(sql, (orderiduser_id[1], ))
            database.save()
    database.query('SELECT * FROM queue_user', ())
    order_admin = database.fetch()
    order_list = []
    for item in order_admin:
        sql = 'SELECT * FROM orderuser WHERE (iduser, tableuser, orderid) = (%s, %s, %s)'
        database.query(sql, (item[1], item[2], item[6]))
        orderr = database.fetch()
        if item[4] == 'กำลังปรุง':
            cook = '*** กำลังปรุงอยู่ ***'
        elif item[4] == 0:
            cook = 'กำลังปรุง'
        print(item[0], end='\n')
        # for item_menu in orderr:
        #     print(item_menu)
        # print('----------------------------------------------------------------------')
        orderr = [list(i) for i in orderr]
        cost = sum(float(i[6]) for i in orderr)
        for menu in orderr:
            menu[4] = json.loads(menu[4].replace("'", '"'))
        order_list += [[orderr, cost, cook]]
    print('*************** order_list *******************************************************')
    for stuff in order_list:
        print('=====>', stuff)
    print('**********************************************************************************')
    return render_template('admin_menu.html', datas=order_list)

@app.route('/yourorder', methods=['GET', 'POST'])
def yourorder():
    '''รายการอาหารของลูกค้า'''
    sql = 'SELECT orderid, status FROM queue_user WHERE iduser = %s'
    database.query(sql, (myid, ))
    order_admin = database.fetch()
    sql = 'SELECT orderid, status FROM complete_user WHERE iduser = %s'
    database.query(sql, (myid, ))
    order_admin += database.fetch()
    sql = 'SELECT orderid, status FROM complete_paid WHERE iduser = %s'
    database.query(sql, (myid, ))
    order_admin += database.fetch()
    print(order_admin)
    order_list = []
    for item in order_admin:
        print(item)
        sql = 'SELECT * FROM orderuser WHERE orderid = %s'
        database.query(sql, (item[0],))
        orderr = database.fetch()
        orderr = [list(i) for i in orderr]
        cost = sum(float(i[6]) for i in orderr)
        for menu in orderr:
            menu[4] = json.loads(menu[4].replace("'", '"'))
        queue = item[1]
        if item[1] == '0':
            database.query('SELECT orderid FROM queue_user', ())
            queue = 'อีก ' + str(database.fetch().index((orderr[0][7],))+1) + ' คิว'
        order_list += [[orderr, cost, queue]]
    print('*************** order_list *******************************************************')
    print(*order_list, sep='\n')
    print('**********************************************************************************')
    return render_template('yourorder.html', datas=order_list)

@app.route('/money')
def money():
    sql = 'SELECT iduser, tableuser FROM orderuser WHERE iduser = %s'
    database.query(sql, (myid, ))
    id_table = database.fetch()
    print(id_table)

    sql = 'SELECT menu, num, price FROM orderuser WHERE iduser = %s'
    database.query(sql, (myid, ))
    user_get = database.fetch()
    print(user_get)

    sql = 'SELECT price FROM orderuser WHERE iduser = %s'
    database.query(sql, (myid, ))
    price = database.fetch()
    cost = sum(float(i[0]) for i in price)
    print('ราคาาาาาาาาาาาาาาาาาา', price, cost)

    optionuser = 'SELECT orderoption FROM orderuser WHERE iduser = %s'
    database.query(optionuser, (myid, ))
    get_option = database.fetch()
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
    database.query('SELECT date_month_year FROM complete_paid', ())
    date_day = list(set(database.fetch()))
    date_day = [i[0].replace("'", '').replace(' ', '-') for i in date_day]
    database.query("SELECT menu, num FROM orderuser", ())
    menu = database.fetch()
    dic_menu = {}
    for item in menu:
        if item[0] in dic_menu:
            dic_menu[item[0]] += int(item[1])
        else:
            dic_menu[item[0]] = int(item[1])
    list_menu = []
    for i, j in dic_menu.items():
        list_menu.append([j, i])
    list_menu.sort(reverse=True)
    print(list_menu)
    money = 0
    database.query('SELECT totalprice FROM complete_paid', ())
    price = database.fetch()
    for item in price:
        money += item[0]
    date = 'เลือกทั้งหมด'
    if request.method == 'POST':
        date = request.form['date'].replace('-', ' ')
        if date != 'เลือกทั้งหมด':
            money = 0
        sql = 'SELECT totalprice FROM complete_paid WHERE date_month_year = %s'
        database.query(sql, (date, ))
        price = database.fetch()
        for item in price:
            money += item[0]
        print(date)
        print(date_day)
        print('อิอิ')
    return render_template('admin_account.html', datas=date_day, menu=list_menu, money=money, date=date)

@app.route('/admin_menu_success', methods=['GET', 'POST'])
def admin_menu_success():
    if request.method == 'POST':
        # try:
        orderiduser = request.form
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', orderiduser)
        orderiduser_id = dict(orderiduser)
        orderiduser_id = next(iter((orderiduser_id.items())) )
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', orderiduser_id)
        sql = "SELECT totalprice, iduser, orderid FROM complete_user WHERE orderid = %s"
        database.query(sql, (orderiduser_id[1], ))
        user_data = database.fetch()
        for data in user_data:
            user_data = data
        print('user_data >>>>>>>>>>>>>>>>>>>>>>>>', user_data)
        today = date.today()
        date_paid = today.strftime("%B %d, %Y")
        sql = "INSERT INTO complete_paid (totalprice, date_month_year, iduser, orderid) VALUES (%s, %s, %s, %s)"
        database.query(sql, (user_data[0], date_paid, user_data[1], user_data[2]))
        sql = "DELETE FROM complete_user WHERE orderid = %s"
        database.query(sql, (orderiduser_id[1], ))
        database.save()
    database.query('SELECT * FROM complete_user', ())
    order_admin = database.fetch()
    order_list = []
    for item in order_admin:
        sql = 'SELECT * FROM orderuser WHERE (iduser, tableuser, orderid) = (%s, %s, %s)'
        database.query(sql, (item[1], item[2], item[4]))
        orderr = database.fetch()
        print(item[0], end='\n')
        # for item_menu in orderr:
        #     print(item_menu)
        # print('----------------------------------------------------------------------')
        orderr = [list(i) for i in orderr]
        cost = sum(float(i[6]) for i in orderr)
        for menu in orderr:
            menu[4] = json.loads(menu[4].replace("'", '"'))
        order_list += [[orderr, cost]]
    print('*************** order_list *******************************************************')
    for stuff in order_list:
        print('=====>', stuff)
    print('**********************************************************************************')
    return render_template('admin_menu_success.html', datas=order_list)

if __name__ == '__main__':
    app.run(debug=True)

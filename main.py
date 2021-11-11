"""ก๋วยเตี๋ยวร่มลื่น"""
from flask import Flask, render_template, request
import mysql.connector
import json

app = Flask(__name__)
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Baszaa1234",
    database='menu'
)
curs = mydb.cursor()

@app.route('/')
def firstpage():
    return render_template('firstpage.html')

@app.route('/table')
def table():
    return render_template('table.html')

@app.route('/name')
def name():
    return render_template('takehome.html')

@app.route('/order')
def order():
    return render_template('yourorder.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    #if request.method == 'POST':
    #    name = request.form
    #    if name[0].isalpha():
    #        name = ' ' + name
    return render_template('home.html', myname=name)

@app.route('/menu')
def menu_list():
    curs.execute('SELECT * FROM noodle')
    row = curs.fetchall()
    print(*row, sep='\n')
    return render_template('menu.html', datas=row)

@app.route('/option')
def option_list():
    curs.execute('SELECT * FROM options')
    row = curs.fetchall()
    print(*row, sep='\n')
    curs.execute('SELECT adding FROM options')
    each_option = curs.fetchall()
    #print(*each_option, sep='\n')
    each_option = [json.loads(item[0]) for item in each_option]
    print(each_option)
    return render_template('noodle.html', datas=row, each_option=each_option)

if __name__ == '__main__':
    app.run(debug=True)
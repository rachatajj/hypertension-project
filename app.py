from flask import Flask,render_template, flash, redirect, url_for, session , request, logging ,make_response
import mysql.connector
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps
from decimal import Decimal , ROUND_UP
import pickle
import sklearn
from datetime import date,datetime
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np

app = Flask(__name__, template_folder='templates')
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'
app.secret_key='super secret key'



app.config['MYSQL_HOST'] = 'us-cdbr-iron-east-04.cleardb.net'
app.config['MYSQL_USER'] = 'bd0d036ba691bf'
app.config['MYSQL_PASSWORD'] = '71ecc525'
app.config['MYSQL_DB'] = 'heroku_f9b4f475385c78c'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql2 = MySQL(app)


class RegisterForm(Form):
    name = StringField('ชื่อ-นามสกุล (ไม่ต้องมีคำนำหน้า)', [validators.Length(min=1 , max=50)])
    username = StringField('ชื่อผู้ใช้', [validators.Length(min=4 , max=50)])
    weight = StringField('น้ำหนัก', [validators.Length(min=2,max=4)])
    height = StringField('ส่วนสูง', [validators.Length(min=2,max=4)])

    password = PasswordField('รหัสผ่าน', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="กรุณาตรวจสอบการยืนยันรหัสผ่าน")
    ])
    confirm = PasswordField('ยืนยันรหัสผ่าน')

class ChangePasswordForm(Form):
    password = PasswordField('', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="กรุณาตรวจสอบการยืนยันรหัสผ่าน")
    ])
    confirm = PasswordField('')



def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            # flash('กรุณาเข้าสู่ระบบ','danger')
            return redirect(url_for('login'))
    return wrap

def generateModel():
    cur = mysql.connection.cursor()
    SQL_Query = pd.read_sql_query(''' SELECT sys,dia,hr,result,phase FROM user ''', cur)
    DataSet = pd.DataFrame(SQL_Query)
    X = DataSet.loc[::,'sys':'hr']
    Y = DataSet.loc[::,'result']
    Z = DataSet.loc[::,'phase']
    ModelRandomForest1 = RandomForestClassifier(criterion ='entropy',n_estimators=100,max_depth=500)
    ModelRandomForest2 = RandomForestClassifier(criterion ='entropy',n_estimators=100,max_depth=500)
    dateModel = datetime.now().strftime("%Y-%d-%m")
    Model1 = 'predict_type_' +dateModel+'.sav'
    Model2 = 'predict_phase_' +dateModel+'.sav'
    ModelRandomForest1 = ModelRandomForest1.fit(X,Y)
    ModelRandomForest2 = ModelRandomForest2.fit(X,Z)
    pickle.dump(ModelRandomForest1, open(Model1, 'wb'))
    pickle.dump(ModelRandomForest2, open(Model2, 'wb'))


@app.route('/register' , methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        weight = form.weight.data
        height = form.height.data
        dateofbirth = request.form.get("date")
        sex = request.values.get('optradio')
        password = sha256_crypt.encrypt(str(form.password.data))
        high = int(height)/100
        bmi= int(weight) / (high * high)
        type = 0
        blood_type = request.values.get('select')
        bmi2=Decimal(bmi).quantize(Decimal('.01'), rounding=ROUND_UP)

        if sex  is None:
            flash('กรุณาระบุเพศของคุณ','danger')
        elif blood_type is None:
            flash('กรุณาระบุหมู่เลือดของคุณ','danger')
        elif dateofbirth is None:
            flash('วันเกิด','danger')
        else:
            cur = mysql2.connection.cursor()
            cur.execute("INSERT INTO user(username,password,name,weight,height,sex,bmi,date_birth,blood_type,type) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (username,password,name,weight,height,sex,bmi2,dateofbirth,
            blood_type,type))
            mysql2.connection.commit()
            cur.close()
            flash('สมัครสมาชิกสำเร็จ','success')


    return render_template('register.html', form=form)
@app.route("/manageModel/<string:name>",methods =['GET','POST'])
@is_logged_in
def manageModel(name):
    cur = mysql2.connection.cursor()
    result = cur.execute("SELECT * FROM model WHERE nameModel = %s", [name])
    result = cur.fetchone()
    type = result['type']
    on = 'เปิดใช้งาน'
    off = 'ปิด'
    cur.execute("UPDATE `heroku_f9b4f475385c78c`.`model` SET `status` = %s  WHERE (`type` = %s AND `status` = %s) ",(off,type,on))
    mysql2.connection.commit()

    cur.execute("UPDATE `heroku_f9b4f475385c78c`.`model` SET `status` = %s  WHERE (`nameModel` = %s) ",(on,name))
    mysql2.connection.commit()
    flash('เปลี่ยนโมเดลสำเร็จ','success')

    return redirect(url_for('backoffice'))


@app.route('/backoffice' , methods=['GET','POST'])
@is_logged_in
def backoffice():
    if session['isAdmin'] == True:
        if request.method == 'POST':
            conn = mysql.connector.connect(host = "us-cdbr-iron-east-04.cleardb.net",user = "bd0d036ba691bf", passwd = "71ecc525",database = "heroku_f9b4f475385c78c", port='3306')
            SQL_Query = pd.read_sql_query(''' SELECT sys,dia,hr,result,phase FROM data ''', conn)
            DataSet = pd.DataFrame(SQL_Query)
            X = DataSet.loc[::,'sys':'hr']
            Y = DataSet.loc[::,'result']
            Z = DataSet.loc[::,'phase']
            ModelRandomForest1 = RandomForestClassifier(criterion ='entropy',n_estimators=100,max_depth=500)
            ModelRandomForest2 = RandomForestClassifier(criterion ='entropy',n_estimators=100,max_depth=500)
            dateModel = datetime.now().strftime("%Y-%d-%m")
            Model1 = 'predict_type_' +dateModel+'.sav'
            Model2 = 'predict_phase_' +dateModel+'.sav'
            ModelRandomForest1 = ModelRandomForest1.fit(X,Y)
            ModelRandomForest2 = ModelRandomForest2.fit(X,Z)
            pickle.dump(ModelRandomForest1, open(Model1, 'wb'))
            pickle.dump(ModelRandomForest2, open(Model2, 'wb'))

            cur = mysql2.connection.cursor()
            cur.execute("INSERT INTO model(nameModel,status,type) VALUES(%s,%s,%s)",(Model1,'ปิด','โมเดล1'))
            mysql2.connection.commit()
            cur.execute("INSERT INTO model(nameModel,status,type) VALUES(%s,%s,%s)",(Model2,'ปิด','โมเดล2'))
            mysql2.connection.commit()
            flash('สร้างโมเดลสำเร็จ','success')

            result = cur.execute("SELECT * FROM model ORDER BY date_time DESC")
            data = cur.fetchall()

            return render_template('backoffice.html',data1=data)
        else:
            cur = mysql2.connection.cursor()
            result = cur.execute("SELECT * FROM model ORDER BY date_time DESC")
            data = cur.fetchall()

            return render_template('backoffice.html',data1=data)
    else:
        flash('คุณไม่มีสิทธิ์ในการเข้าใช้งานส่วนนี้','danger')
        return render_template('home.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql2.connection.cursor()
        result = cur.execute("SELECT * FROM user WHERE username = %s", [username])
        if username is None or password_candidate is None:
            session['logged_in'] = false
            flash('กรุณากรอก Username และ Password')
        else:
            if result > 0:
                data = cur.fetchone()
                password = data['password']

                if sha256_crypt.verify(password_candidate,password):
                    session['logged_in'] = True
                    session['username'] = username
                    session['isAdmin'] = False
                    if username == 'admin':
                        session['isAdmin'] = True
                    flash('เข้าสู่ระบบสำเร็จ','success')
                    return redirect(url_for('home'))

                else:
                    error = 'กรุณาตรวจสอบ "รหัสผ่าน" ให้ถูกต้อง'
                    return render_template('login.html', error=error)
                    cursor.close()
            else:
                    error = 'ไม่มี "ชื่อผู้ใช้" นี้ในระบบ'
                    return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('ออกจากระบบเรียบร้อยแล้ว','success')
    return redirect(url_for('login'))



@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

@app.route('/changepsswrd' , methods=('GET', 'POST'))
@is_logged_in
def changepsswrd():
    form = ChangePasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        user_id = session.get('username')
        cur = mysql2.connection.cursor()
        result = cur.execute("SELECT * FROM user WHERE username = %s", [user_id])
        result = cur.fetchone()
        password = result['password']

        password_candidate = request.form['oldpsswrd']
        newpassword = sha256_crypt.encrypt(str(form.password.data))
        if sha256_crypt.verify(password_candidate,password):
            cur.execute("UPDATE `heroku_f9b4f475385c78c`.`user` SET `password` = %s  WHERE (`username` = %s) ",(newpassword,user_id))
            mysql2.connection.commit()
            flash('แก้ไขรหัสผ่านสำเร็จ','success')
            return redirect(url_for('changepsswrd'))
        else:
            flash('กรุณาตรวจสอบรหัสผ่านเดิมให้ถูกต้อง','danger')

    return render_template('changepsswrd.html' , form=form)

@app.route('/home' , methods=('GET', 'POST'))
@is_logged_in
def home():
    user_id = session.get('username')
    cur = mysql2.connection.cursor()
    model1 = cur.execute("SELECT * FROM model WHERE status = 'เปิดใช้งาน' AND type='โมเดล1'")
    model1 = cur.fetchone()
    dateModel1 = model1['date_time']
    model2 = cur.execute("SELECT * FROM model WHERE status = 'เปิดใช้งาน' AND type='โมเดล2'")
    model2 = cur.fetchone()
    dateModel2 = model2['date_time']
    result = cur.execute("SELECT * FROM user WHERE username = %s", [user_id])
    result = cur.fetchone()

    sex = result['sex']
    name = result['name']
    birthdate = result['date_birth']
    weight = result['weight']
    height = result['height']
    bmi = result['bmi']
    blood_type = result['blood_type']

    today = date.today()
    age = today.year-birthdate.year

    try:
        birthday = birthdate.replace(year = today.year)
    except ValueError:
        birthday = birthdate.replace(year = today.year,
                month = born.month + 1, day = 1)



    if request.method == 'POST':

        high = int(height)/100
        bmi= int(weight) / (high * high)
        bmi2=Decimal(bmi).quantize(Decimal('.01'), rounding=ROUND_UP)

        sys = request.values.get('sys')
        dia = request.values.get('dia')
        hr = request.values.get('hr')
        result = cur.execute("SELECT nameModel FROM model WHERE status = 'เปิดใช้งาน' and type='โมเดล1' ")
        result = cur.fetchone()
        result2 = cur.execute("SELECT nameModel FROM model WHERE status = 'เปิดใช้งาน' and type='โมเดล2' ")
        result2 = cur.fetchone()

        model1 = pickle.load(open(result['nameModel'], 'rb'))
        model2 = pickle.load(open(result2['nameModel'], 'rb'))
        result = model1.predict([[sys,dia,hr]])
        phase = model2.predict([[sys,dia,hr]])

        cur = mysql2.connection.cursor()
        if result == ['abnormal']:
            result = 'ไม่ปกติ'
            if phase == ['high']:
                phase = 'ค่อนข้างสูง'
                recommend = 'ค่อนข้างสูง :  มีความดันโลหิตสูงมากกว่าปกติ แต่ไม่มีความรุนแรง ควรไปตรวจความดันซ้ำภายใน 1 ปี '
                cur.execute("INSERT INTO data(sys,dia,hr,bmi,result,phase,recommend,user) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(sys,dia,hr,bmi2,result,phase,recommend,user_id))
                mysql2.connection.commit()
            elif phase == ['Hypertension Phase 1']:
                phase = 'ความดันโลหิตสูงระดับที่ 1'
                recommend = 'ความดันโลหิตสูงระดับที่ 1 มีความดันโลหิตสูงระดับที่1 ควรปรับเปลี่ยนพฤติกรรม งดการสูบบุหรี่ งดการดื่มแอลกอฮอล์ พักผ่อนให้เพียงพอ ไม่นอนดึก ควรออกกำลังกายสม่ำเสมอ หลีกเลี่ยงอาหารหมักดอง ผ่อนคลายจิตใจฝึกสมาธิ'
                cur.execute("INSERT INTO data(sys,dia,hr,bmi,result,phase,recommend,user) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(sys,dia,hr,bmi2,result,phase,recommend,user_id))
                mysql2.connection.commit()
            elif phase == ['Hypertension Phase 2']:
                phase = 'ความดันโลหิตสูงระดับที่ 2'
                recommend = 'ความดันโลหิตสูงระดับที่ 2 : ควรพบแพทย์โดยทันที'
                cur.execute("INSERT INTO data(sys,dia,hr,bmi,result,phase,recommend,user) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(sys,dia,hr,bmi2,result,phase,recommend,user_id))
                mysql2.connection.commit()
            elif phase == ['Hypertension Phase 3']:
                phase = 'ความดันโลหิตสูงระดับที่ 3'
                recommend = 'ความดันโลหิตสูงระดับที่ 3 : มีความรุนแรงมาก ควรพบแพทย์โดยทันที'
                cur.execute("INSERT INTO data(sys,dia,hr,bmi,result,phase,recommend,user) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(sys,dia,hr,bmi2,result,phase,recommend,user_id))
                mysql2.connection.commit()
        else :
            result = 'ปกติ'
            phase = '-'
            recommend = 'ปกติ : รักษาสุขภาพให้คงที่ เพื่อไม่ให้เป็นโรคความดันโลหิตสูง'
            cur.execute("INSERT INTO data(sys,dia,hr,bmi,result,phase,recommend,user) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(sys,dia,hr,bmi2,result,phase,recommend,user_id))
            mysql2.connection.commit()

        cur.execute("SELECT * FROM data WHERE user = %s ORDER BY date_time DESC", [user_id])
        rs = cur.fetchone()
        result = cur.execute("SELECT * FROM user WHERE username = %s", [user_id])
        result = cur.fetchone()
        name = result['name']
        sys = rs['sys']
        dia = rs['dia']
        hr = rs['hr']
        bmi = rs['bmi']
        result = rs['result']
        phase = rs['phase']
        recommend = rs['recommend']
        flash('ประเมินอาการและระดับความรุนแรง สำเร็จ','success')
        cur.close()
        return render_template('result.html', name=name,sys=sys,dia=dia,hr=hr,bmi=bmi,result=result,phase=phase,recommend=recommend)


    if birthday > today:
        age = today.year - birthdate.year - 1
        return render_template('home.html',age=age,sex=sex,bmi=bmi,name=name,weight=weight,height=height,blood_type=blood_type,dateModel1=dateModel1,dateModel2=dateModel2)
    else:
        age = today.year - birthdate.year
        return render_template('home.html',age=age,sex=sex,bmi=bmi,name=name,weight=weight,height=height,blood_type=blood_type,dateModel1=dateModel1,dateModel2=dateModel2)


@app.route('/history')
@is_logged_in
def list():
    user_id = session.get('username')
    cur = mysql2.connection.cursor()
    result = cur.execute("SELECT * FROM data WHERE user = %s ORDER BY date_time DESC", [user_id])
    data = cur.fetchall()
    if result > 0:
        return render_template('history.html' ,data1=data)
    else:
        flash('ไม่มีประวัติการประเมินอาการและระดับความรุนแรง','info')
        return render_template('history.html')
    cur.close()

@app.route('/result')
@is_logged_in
def result():
    return render_template('result.html')


@app.route('/')
@is_logged_in
def default():
    if session['logged_in'] == True :
        return redirect(url_for('home'))
    else :
        return redirect(url_for('login'))



@app.route('/update' , methods=('GET', 'POST'))
@is_logged_in
def update():
    user_id = session.get('username')
    cur = mysql2.connection.cursor()
    result = cur.execute("SELECT * FROM user WHERE username = %s", [user_id])
    result = cur.fetchone()

    username = result['username']
    name = result['name']
    birthdate = result['date_birth']
    weight = result['weight']
    height = result['height']
    bmi = result['bmi']
    blood_type= result['blood_type']

    if request.method == 'POST':

        dateofbirth = request.form.get('date')
        weight = request.values.get('weight')
        height = request.values.get('height')
        blood_type = request.values.get('select')
        idate = datetime.strptime(dateofbirth, '%Y-%m-%d')
        high = int(height)/100
        bmi= int(weight) / (high * high)
        bmi2=Decimal(bmi).quantize(Decimal('.01'), rounding=ROUND_UP)

        cur = mysql2.connection.cursor()
        cur.execute("UPDATE `heroku_f9b4f475385c78c`.`user` SET `date_birth` = %s ,`weight` = %s ,`height` = %s ,`bmi` = %s , `blood_type` = %s WHERE (`username` = %s) ",(idate,weight,height,bmi2,blood_type,user_id))
        mysql2.connection.commit()
        flash('แก้ไขข้อมูลส่วนตัวสำเร็จ','success')
        return redirect(url_for('update'))

    return render_template('update.html',birthdate=birthdate,username=username,bmi=bmi,name=name,weight=weight,height=height,blood_type=blood_type)

if __name__ == '__main__':
        app.run(debug=True)

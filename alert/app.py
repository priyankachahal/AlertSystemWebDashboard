from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
from geopy.geocoders import Nominatim
from geopy.distance import great_circle

import pushpad
import smtplib
import nltk, string, os, sys
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)

project = pushpad.Pushpad(auth_token='3e7558829ba95991c3ae0cd137566a40', project_id=5744)
# Config MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'data'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL()
mysql.init_app(app)


stemmer = nltk.stem.porter.PorterStemmer()
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
gmail_user = 'sjalerts.app@gmail.com'  
gmail_pwd = 'rootroot'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def stem_tokens(tokens):
    return [stemmer.stem(item) for item in tokens]

'''remove punctuation, lowercase, stem'''
def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')

def cosine_sim(text1, text2):
    tfidf = vectorizer.fit_transform([text1, text2])
    return ((tfidf * tfidf.T).A)[0,1]
# Index



@app.route('/')
def index():
    return render_template('home.html')






@app.route('/currentreports')
def currentreports():
    # Create cursor
    conn = mysql.connect()
    cur = conn.cursor()

    # Get reports
    result = cur.execute("SELECT * FROM report where tstamp BETWEEN timestamp(DATE_SUB(NOW(), INTERVAL 24 Hour)) AND timestamp(NOW()) order by 1 desc")

    reports = cur.fetchall()

    if result > 0:
        return render_template('currentreports.html', reports=reports)
    else:
        msg = 'No reports Found'
        return render_template('currentreports.html', msg=msg)
    # Close connection
    cur.close()
    con.close()


@app.route('/pastrep/<string:date>&<string:dateto>')
def pastrep(date,dateto):
    conn = mysql.connect()
    cur = conn.cursor()

    # Get reports
    result = cur.execute("SELECT * FROM pastreport where date BETWEEN %s AND  %s",[date,dateto])

    reports = cur.fetchall()
    cur.close()
    conn.close()
    if result >0:
        return render_template('pastrep.html', reports=reports, date=date,dateto=dateto)
    else:
        msg = 'No reports Found'
        return render_template('nopastrep.html', msg=msg,date=date,dateto=dateto)
        

@app.route('/pastreports', methods=['GET', 'POST'])
def pastreports():
    if 'email' not in session:
         return redirect(url_for('login'))
    if request.method == 'POST':
        date = request.form["date"]
        dateto = request.form["dateto"]
    
    
        return redirect(url_for('pastrep',date=date, dateto=dateto))
        
    return render_template('pastreports.html')
    
     


# Register Form Class

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email id', [validators.Length(min=4, max=50)])
    password = PasswordField('Password', [validators.DataRequired(),validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')
    street = StringField('Street', [validators.Length(min=5, max=50)])
    city = StringField('City', [validators.Length(min=2, max=45)])
    zipcode = StringField('Zipcode', [validators.Length(min=1, max=25)])
    phone = StringField('Phone no', [validators.Length(min=1, max=25)])
# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        street = form.street.data
        city = form.city.data
        zipcode = form.zipcode.data
        phone = form.phone.data
        # Create cursor
        conn = mysql.connect()
        cur = conn.cursor()
        # Execute query
        cur.execute("INSERT INTO users(name, email, password, street,city, zipcode,state) VALUES(%s, %s, %s, %s, %s, %s, %s)", (name, email, password, street,city, zipcode,phone))

        # Commit to DB
        conn.commit()

        # Close connection
        cur.close()
        conn.close()
        flash('You are now registered and can log in', 'success')
        
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        email = request.form['email']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.get_db().cursor()

        # Get user by email
        result = cur.execute("SELECT password,name FROM users WHERE email = %s", [email])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data[0]
            name = data[1]
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['email'] = email
                session['name'] = name
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')
    
@app.route('/editreport',methods=['GET', 'POST'])
@is_logged_in  
def editreport():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        reportID = request.form["reportID"]
        description = request.form["description"]
        conn = mysql.connect()
        cur = conn.cursor()
        re = cur.execute("select * from report where reportid="+reportID)
        datarow = cur.fetchone()
        cur.close()
        conn.close()
        if re<1:
            flash('No such report found. Please enter valid report ID', 'danger')
        else :
            desc= str(datarow[3])        

            conn = mysql.connect()
            cur = conn.cursor()
            cur.execute("UPDATE report SET description = %s where reportid= %s",((str(desc)+"\n"+str(description)),str(reportID)))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('currentreports'))
    return render_template('editreport.html') 
        
@app.route('/report',methods=['GET', 'POST'])
@is_logged_in
def report():
    if 'email' not in session:
         return redirect(url_for('login'))
    if request.method == 'POST' and 'type_em' in request.form:
        address = request.form["address"]
        description = request.form["description"]
        type_em = request.form.get('type_em')
        imagename = "N"
        try:
            image = request.files['image']
        except:
            imagename = "No image provided"
        if imagename != "No image provided":
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagename = filename
        
        geolocator = Nominatim(timeout=3)
        try:
            location = geolocator.geocode(address)
            lati = float(location.latitude)
            longi = float(location.longitude)
        except:
            lati= 0.0
            longi=0.0
        para = (lati,longi)
        email = session['email']
        flag = True
        conn = mysql.connect()
        cur = conn.cursor()
        re = cur.execute("select * from report where type_em = '"+str(type_em)+"' and tstamp BETWEEN timestamp(DATE_SUB(NOW(), INTERVAL 20 MINUTE)) AND timestamp(NOW())")

        datarows = cur.fetchall()
        cur.close()
        conn.close()
        if re < 1:
            flag = True
        else:
            for row in datarows:
                lati2 = float(row[7])
                longi2 = float(row[6])
                desc2 = str(row[3])
                para2 = (lati2,longi2)
                if great_circle(para,para2).meters < 200 and cosine_sim(desc2,description)> 0.60 :
                    flag =False
                    break
                

        
        
         
        # Execute query
        if flag==True:
            
            conn = mysql.connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO report(email, address, description, image, type_em, longi,lati) VALUES(%s, %s, %s,%s, %s, %s, %s)", (email, address, description, imagename, type_em, str(longi),str(lati)))
            conn.commit()
            cur.close()
            conn.close()
            conn = mysql.connect()
            cur = conn.cursor()
            cur.execute("select email from users")
            to = cur.fetchall()
            cur.close()
            conn.close()
            tolist=[]
            for r in to:
                tolist.append(r[0])
            

            subject = type_em + " at " + address
            body = type_em + " at " + address + "\n" + description
            smtpserver = smtplib.SMTP("smtp.gmail.com",587)
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo()
            smtpserver.login(gmail_user, gmail_pwd)
            header = 'To:' + ", ".join(tolist) + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:' + subject + ' \n'
            msg = header + '\n' + body + '\n\n'
            smtpserver.sendmail(gmail_user, to, msg)
            smtpserver.close()
            flash('Emergency reported successfully', 'success')
            notification = pushpad.Notification(project, body=type_em + " at " + address + "\n" +description)
            notification.broadcast()                                
        
        else:
            flash('Emergency has already been reported. You can add extra information to a current report', 'warning')
        

        
        
        return redirect(url_for('dashboard'))
    return render_template('report.html')



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=False)

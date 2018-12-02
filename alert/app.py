import os
import smtplib
import string
from functools import wraps

import nltk
import pushpad
from flask import Flask, render_template, flash, redirect, url_for, session, request
from geopy.distance import great_circle
from geopy.geocoders import Nominatim
from sklearn.feature_extraction.text import TfidfVectorizer
from werkzeug.utils import secure_filename
from wtforms import Form, StringField, PasswordField, validators

from api_rest import user_authenticate_api, user_register_api, get_news_report_api, post_news_report_api, \
    get_news_by_id_report_api, update_news_by_id_report_api, get_registered_users_api

app = Flask(__name__)

project = pushpad.Pushpad(auth_token='3e7558829ba95991c3ae0cd137566a40', project_id=5744)

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
    return ((tfidf * tfidf.T).A)[0, 1]


# Index


@app.route('/')
def index():
    return render_template('home.html')




# Register Form Class

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('email', [validators.Length(min=4, max=50)])
    password = PasswordField('password', [validators.DataRequired(),
                                          validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('password-repeat')
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
        password = form.password.data
        street = form.street.data
        city = form.city.data
        zipcode = form.zipcode.data
        phone = form.phone.data
        # post the call to
        response_dict = user_register_api(name, email, password, street, city, zipcode, phone)
        if "id" in response_dict:
            flash('You are now registered and can log in', 'success')
        else:
            flash('There is a problem in registration flow at the moment', 'error')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        email = request.form['email']
        password_candidate = request.form['password']

        # Get user by email
        response_dict = user_authenticate_api(email, password_candidate)

        if response_dict.get("success"):
            session['logged_in'] = True
            session['email'] = email
            session['name'] = response_dict.get("name")
            flash('You are now logged in', 'success')
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid login'
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
    category = request.args.get('category')
    if category is None:
        result = get_news_report_api(None, "720", "-creationDate")
    else:
        result = get_news_report_api(category, "720", "-creationDate")
    formattedReports = []
    if len(result.get("news")) > 0:
        reports = result.get("news");
        for report in reports:
            formattedReport = [None] * 10
            formattedReport[0] = report.get("id")
            formattedReport[2] = report.get("address")
            formattedReport[3] = report.get("description")
            formattedReport[4] = "No image provided"
            formattedReport[5] = report.get("category")
            formattedReport[8] = report.get("creationDate")
            formattedReports.append(formattedReport)
    return render_template('dashboard.html', reports=formattedReports)



@app.route('/report', methods=['GET', 'POST'])
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
            lati = 0.0
            longi = 0.0
        para = (lati, longi)
        email = session['email']
        flag = True
        response_dict = get_news_report_api(str(type_em), "20", None)
        datarows = list(response_dict.get("news"))

        if len(datarows) < 1:
            flag = True
        else:
            for row in datarows:
                longi2 = float(row.get("location").get("coordinates")[0])
                lati2 = float(row.get("location").get("coordinates")[1])
                desc2 = str(row.get("description"))
                para2 = (lati2, longi2)
                if great_circle(para, para2).meters < 200 and cosine_sim(desc2, description) > 0.60:
                    flag = False
                    break

        # Execute query
        if flag == True:
            post_news_report_api(email, address, description, imagename, type_em, longi, lati)
            response_dict = get_registered_users_api()
            registered_users = response_dict.get("users")
            tolist = []
            for i in range(len(registered_users)):
                tolist.append(registered_users[i].get("email"))
            if len(tolist) > 0:
                subject = type_em + " at " + address
                body = type_em + " at " + address + "\n" + description
                smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
                smtpserver.ehlo()
                smtpserver.starttls()
                smtpserver.ehlo()
                smtpserver.login(gmail_user, gmail_pwd)
                header = 'To:' + ", ".join(tolist) + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:' + subject + ' \n'
                msg = header + '\n' + body + '\n\n'
                smtpserver.sendmail(gmail_user, tolist, msg)
                smtpserver.close()
                #flash('Emergency reported successfully', 'success')
                #notification = pushpad.Notification(project, body=type_em + " at " + address + "\n" + description)
                #notification.broadcast()
        else:
            flash('Emergency has already been reported.', 'warning')

        return redirect(url_for('dashboard'))
    return render_template('report.html')


# unused paths
@app.route('/editreport', methods=['GET', 'POST'])
@is_logged_in
def editreport():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        reportID = request.form["reportID"]
        description = request.form["description"]
        response_dict = get_news_by_id_report_api(reportID)
        if response_dict.get("news") is None:
            flash('No such report found. Please enter valid report ID', 'danger')
        else:
            desc = response_dict.get("news").get("description")
            update_news_by_id_report_api(reportID, str(desc) + "\n" + str(description))
            return redirect(url_for('dashboard'))
    return render_template('editreport.html')


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=False)

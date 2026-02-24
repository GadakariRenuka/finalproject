from flask import Flask, render_template, redirect, request, session, url_for,flash
import mysql.connector
import os
import numpy as np
import joblib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Upload folder config
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MySQL connection
mydb = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='root',
    passwd='',
    database='retinal'
)
mycur = mydb.cursor()

# DB query helpers
def executionquery(query, values):
    mycur.execute(query, values)
    mydb.commit()

def retrivequery1(query, values):
    mycur.execute(query, values)
    return mycur.fetchall()

def retrivequery2(query):
    mycur.execute(query)
    return mycur.fetchall()

@app.route('/about')
def about():
    return render_template("about.html")



@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['confirmpassword']

        if password == c_password:
            query = "SELECT UPPER(email) FROM user3"
            email_data = retrivequery2(query)
            email_data_list = []
            for i in email_data:
                email_data_list.append(i[0])
            if email.upper() not in email_data_list:
                query = "INSERT INTO user3 (name, email, password) VALUES (%s, %s, %s)"
                values = (name, email, password)
                executionquery(query, values)
                flash("Registration successful!", "success")
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID is already exists!")
        return render_template('register.html', message="Conform password is not match!")
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        query = "SELECT UPPER(email) FROM user3"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])
        
        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM user3 WHERE email = %s"
            values = (email,)
            password__data = retrivequery1(query, values)
            if password.upper() == password__data[0][0]:
                global user_email
                user_email = email

                return redirect("/home")
            return render_template('login.html', message= "Invalid Password!!")
        return render_template('login.html', message= "This email ID does not exist!")
    return render_template('login.html')

# Load models
mobilenet_model = load_model('mobilenet_trained_final.h5')
svm_model = joblib.load('svm_mobile_trained.pkl')
target_classes = ['Mild_DR', 'Moderate_DR', 'No_DR', 'Proliferative_DR', 'Severe_DR']

# Feature extraction
def extract_features(image_path):
    img = load_img(image_path, target_size=(150, 150))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = img / 255.0
    features = mobilenet_model.predict(img)
    return features.flatten()

# Prediction
def predict_image(image_path):
    features = extract_features(image_path)
    predicted_class = svm_model.predict([features])
    return target_classes[predicted_class[0]]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            prediction = predict_image(filepath)
            return render_template('upload.html', filename=filename, prediction=prediction)
    return render_template('upload.html')

@app.route('/index2')
def index2():
    return render_template('index2.html')

if __name__ == '__main__':
    app.run(debug=True)

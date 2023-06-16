from flask import Flask, jsonify, request, flash, session
import jwt
import datetime
import mysql.connector
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import io
import os   
import traceback
import pyshorteners
import json
import re
import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import timedelta, datetime
from functools import wraps
from tensorflow import keras
from PIL import Image
from io import BytesIO
from google.cloud import storage


app = Flask(__name__)

# Load custom model
model = tf.keras.models.load_model(('model5.h5'), compile=False, custom_objects={'KerasLayer': hub.KerasLayer})

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"


# Koneksi ke Google Cloud Storage
storage_client = storage.Client()
bucket_name = 'bucket-skinny'  # Replace with your GCS bucket name
bucket = storage_client.get_bucket(bucket_name)


app.config['SECRET_KEY'] = 'c1efa70af3b7404bbc79535ce1551e47'

# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
CORS(app)

app.config['SESSION_PERMANENT'] = True
app.config['MYSQL_HOST'] = '34.132.7.245'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1'
app.config['MYSQL_DB'] = 'skinny'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#mysql = MySQL(app)


# mysql = mysql.connector.connect(
#     host=app.config['MYSQL_HOST'],
#     user=app.config['MYSQL_USER'],
#     password=app.config['MYSQL_PASSWORD'],
#     database=app.config['MYSQL_DB']
# )
def check_mysql_connection():
    try:
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        return conn
    except mysql.connector.Error as err:
        print("Error connecting to MySQL:", err)
        return None

# Mengecek koneksi ke MySQL menggunakan while loop
db_conn = None
while db_conn is None:
    db_conn = check_mysql_connection()
    if db_conn is None:
        print("Waiting for MySQL connection...")
        time.sleep(1)  # Menunggu 1 detik sebelum mencoba kembali

print("Connected to MySQL!")

# Baca data dari file class.json
global class_names,treatment_classes,desc_names,title_treatment_classes,src_classes,notes_classes

with open('class.json', 'r') as json_file:
    class_names = json.load(json_file)
with open('treatmen.json', 'r') as json_file:
    treatment_classes = json.load(json_file)
with open('deskripsi.json', 'r') as json_file:
    desc_names = json.load(json_file)
with open('title.json', 'r') as json_file:
    title_treatment_classes = json.load(json_file)
with open('sumber.json', 'r') as json_file:
    src_classes = json.load(json_file)
with open('notes.json', 'r') as json_file:
    notes_classes = json.load(json_file)



@app.route('/', methods=['GET'])
def index():
    return "Hello, Welcome to Skinny Apps"


@app.route('/register', methods=['POST'])
def register():
    if 'username' not in session:
        try:
            _name = request.form['name']
            _username = request.form['username']
            _password = request.form['password']

            if _username and _password:
                _name = re.sub(r'"', '', _name)
                _username = re.sub(r'"', '', _username)
                _password = re.sub(r'"', '', _password)

                cursor = db_conn.cursor()

                sql = "SELECT * FROM user WHERE username=%s"
                sql_values = (_username,)

                cursor.execute(sql, sql_values)
                row = cursor.fetchone()
                if row:
                    resp = jsonify({'Error': True, 'message': 'you already have an account'})
                    # resp.status_code = 200 
                    return resp
                else:
                    passhash = generate_password_hash(_password)
                    sql = "INSERT INTO user (name, username, password) VALUES (%s, %s, %s)"
                    sql_values = (_name, _username, passhash)
                    cursor.execute(sql, sql_values)
                    db_conn.commit()
                    token = jwt.encode({
                            'user': _username,
                            'expiration': str(datetime.utcnow() + timedelta(days=365))
                    },
                    app.config['SECRET_KEY'])

                    sql = "INSERT INTO token (username, token) VALUES (%s, %s) ON DUPLICATE KEY UPDATE token=%s"
                    sql_values = (_username, token, token)
                    cursor.execute(sql, sql_values)
                    db_conn.commit()
                    cursor.close()

                    return jsonify({'Error': False, 'message': 'You are registered successfully','token': token})

            else:
                resp = jsonify({'Error': True, 'message': 'invalid credentials'})
                # resp.status_code = 200
                return resp
        except:
            resp = jsonify({'Error': True, 'message': 'please fill the form correctly'})
            # resp.status_code = 200
            return resp
    else:
        resp = jsonify({'Error': True, 'message': 'already logged in'})
        # resp.status_code = 200
        return resp


@app.route('/login', methods=['POST'])
def login():
    if 'username' in session and session['username'] is not None:
        resp = jsonify({'Error': True, 'message': 'already logged in'})
        # resp.status_code = 200
        return resp
    else:
        try:
            _username = request.form['username']
            _password = request.form['password']

            if _username and _password:
                _username = re.sub(r'"', '', _username)
                _password = re.sub(r'"', '', _password)
                

                db_conn = None
                while db_conn is None:
                    db_conn = check_mysql_connection()
                    if db_conn is None:
                        print("Waiting for MySQL connection...")
                        time.sleep(1)
                cursor = db_conn.cursor()
                sql = "SELECT token FROM token WHERE username=%s"
                sql_where = (_username,)

                cursor.execute(sql, sql_where)
                row = cursor.fetchone()
                token = row[0]
                

                sql = "SELECT * FROM user WHERE username=%s"
                sql_values = (_username,)

                cursor.execute(sql, sql_values)
                row = cursor.fetchone()
                if row is not None:
                    name = row[0]
                    username = row[1]
                    password = row[2]
                    if check_password_hash(password, _password):
                        session['username'] = username    
                        cursor.close()
                        return jsonify({'Error': False, 'message': 'You are logged in successfully', 'Your Username': username,'Your Name': name,'token': token})

                    else:
                        resp = jsonify({'Error': True, 'message': 'invalid password'})
                        # resp.status_code = 200
                        return resp
                else:
                    resp = jsonify({'Error': True, 'message': 'username is not found'})
                    # resp.status_code = 200
                    return resp
            else:
                resp = jsonify({'Error': True, 'message': 'please fill the form correctly'})
                return resp
        except Exception as e:
            resp = jsonify({'Error': True, 'message': 'invalid credentials'})
            # resp.status_code = 400
            print(f"Error: {e}")
            traceback.print_exc()
            return resp


@app.route('/logout')
def logout():
    username = request.form['username']
    # Kode untuk melakukan pengecekan ke database
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE username = %s", (username,))
    result = cursor.fetchone()[0]
    cursor.close()

    if result > 0 and 'username' in session:
        session.clear()

        # Tambahkan pesan ke session
        session['logout_message'] = 'Anda telah berhasil logout.'
        return jsonify({'error': False, 'message': 'Logout Sukses'}),200
    else:
        return jsonify({'error': True, 'message': 'Logout Gagal, login terlebih dahulu'})


@app.route("/predict", methods=["POST"])
def predict_api():
    token = request.form['token']
    token = re.sub(r'"', '', token)
    cursor = db_conn.cursor()
    sql = "SELECT * FROM token WHERE token=%s"
    sql_where = (token,)

    cursor.execute(sql, sql_where)
    row = cursor.fetchone()
    if not row:
        value = {
            'Error': True,
            "message": 'Token tidak valid'
        }
        return jsonify(value)

    file = request.files['file']
    if 'file' not in request.files:
        value = {
            'Error': True,
            "message": 'Tidak ada file'
        }
        return jsonify(value)


    img = Image.open(file)
    img = img.resize((224, 224))
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)


    prediction = model.predict(img_array)

    # Get the predicted class and Treatment
    predicted_class = np.argmax(prediction, axis=-1)
    predicted_class = str(int(predicted_class))
    class_name = class_names.get(predicted_class, "Class tidak terdeteksi")
    treatment_class = treatment_classes.get(predicted_class, "Treatment tidak ditemukan")
    title_treatment = title_treatment_classes.get(predicted_class, "Judul tidak ditemukan")
    desc_name = desc_names.get(predicted_class, "Deskripsi tidak ditemukan")
    src_class = src_classes.get(predicted_class, "Sumber tidak ditemukan")
    note_class = notes_classes.get(predicted_class, "Pesan tidak ditemukan")

    # Return response
    response = {
        'Error': False,
        'message': "Sukses",
        'Penanganan': {
            'Terdeteksi Jenis': class_name,
            'Deskripsi': desc_name,
            'Penanganan yang dapat dilakukan': treatment_class,
            'Judul Penanganan': title_treatment,
            'Class terprediksi': predicted_class,
            'Sumber': src_class,
            'Pesan': note_class
        }
        
    }
    return jsonify(response)


@app.route("/uploadToDb", methods=["POST"])
def upload_to_db():
    file = request.files['file']
    class_name = request.form["class_name"]
    usernameUs = request.form["username"]
    class_get = request.form['class']

    class_name = re.sub(r'"', '', class_name)
    usernameUs = re.sub(r'"', '', usernameUs)
    class_get = re.sub(r'"', '', class_get)

    img = Image.open(file)

    # Save the image to a temporary file-like object
    temp_file = BytesIO()
    img.save(temp_file, format='JPEG')
    temp_file.seek(0)  # Reset the file position to the beginning

    # Upload image to Google Cloud Storage
    img_path = f"imgPredict/{file.filename}"
    blob = bucket.blob(img_path)
    blob.upload_from_file(temp_file, content_type='image/jpeg')

    # Get the image URL
    LIFETIME = 7 * 24 * 60 * 60

    expiration_time = timedelta(seconds=LIFETIME)
    signed_url = blob.generate_signed_url(
        version='v4',
        expiration=expiration_time,
        method='GET'
    )
    shortener = pyshorteners.Shortener()
    short_url = shortener.tinyurl.short(signed_url)
    cursor = db_conn.cursor()
    # Menjalankan query INSERT ke database
    check_user_query = "SELECT username FROM user WHERE username = %s"
    cursor.execute(check_user_query, (usernameUs,))
    existing_user = cursor.fetchone()

    if existing_user:

        
        query = "INSERT INTO storage (username_img,class_predict,hasil_predict, url_img) VALUES (%s,%s, %s,%s)"
        values = (usernameUs, class_get, class_name, short_url)
        cursor.execute(query, values)
        inserted_id = cursor.lastrowid
        db_conn.commit()
        cursor.close()

        response = {
            'Error': False,
            'message': "Berhasil menambah ke dalam Bookmark",
            'History':{
                'Terdeteksi Jenis': short_url,
                'Class': class_name,
                'id gambar': inserted_id
            }
        }
        return jsonify(response)
    else:
        response = {
            'Error': True,
            'message': "Username tidak ditemukan"
        }
        return jsonify(response)


@app.route("/getHistory/<username>", methods=["GET"])
def getHistory(username):
    # username = request.args.get('username')
    # Menjalankan query SELECT ke database berdasarkan username
    cursor = db_conn.cursor()
    query = "SELECT class_predict,url_img FROM storage WHERE username_img = %s"
    values = (username,)
    cursor.execute(query, values)
    results = cursor.fetchall()
    cursor.close()
    if len(results) == 0:
        response = {
            "Error": True,
            "message": "Data tidak ditemukan"
        }
        return jsonify(response)

    response = {
        "Error": False,
        "message": "Data Berhasil Didapatkan",
        "Daftar History": []
    }

    for result in results:
        signed_url = result[1]
        class_url = result[0]

        class_name = class_names.get(class_url, "Class tidak terdeteksi")
        treatment_class = treatment_classes.get(class_url, "Treatment tidak ditemukan")
        title_treatment = title_treatment_classes.get(class_url, "Judul tidak ditemukan")
        desc_name = desc_names.get(class_url, "Deskripsi tidak ditemukan")
        src_class = src_classes.get(class_url, "Sumber tidak ditemukan")
        note_class = notes_classes.get(class_url, "Pesan tidak ditemukan")

        image_entry = {
            'image':{
            "signed_url": signed_url,
            "class_Predicted": class_url},
            'Penanganan': {
                'Terdeteksi Jenis': class_name,
                'Deskripsi': desc_name,
                'Penanganan yang dapat dilakukan': treatment_class,
                'Judul Penanganan': title_treatment,
                'Sumber': src_class,
                'Pesan': note_class
                }
        }
        response["Daftar History"].append(image_entry)
    return jsonify(response)


# Get image by name biar signedURL nya automated request and load
if __name__ == '__main__':
    app.run(debug=True, port=211)

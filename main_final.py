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
model = tf.keras.models.load_model(('model_nanchy.h5'), custom_objects={'KerasLayer':hub.KerasLayer})

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tester-skinny-fb286f7d29d1.json"
# Load primary Model 
# model = tf.keras.models.load_model('model.h5')

# Koneksi ke Google Cloud Storage
storage_client = storage.Client()
bucket_name = 'bucket-mage'  # Replace with your GCS bucket name
bucket = storage_client.get_bucket(bucket_name)


app.config['SECRET_KEY'] = 'c1efa70af3b7404bbc79535ce1551e47'

# Dictionary for ClassNames
class_names = {
    0: "Blackhead",
    1: "Eksim",
    2: "Flek Hitam",
    3: "Jerawat",
    4: "Herves",
    5: "Kurap",
    6: "Milia",
    7: "Panu"
}

# Dictionary for Treatment
treatment_classes = {
    0 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads'],
    1 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads'],
    2 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads'],
    3 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads'],
    4 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads'],
    5 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads'],
    6 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads'],
    7 : ['1. blablabslaba' , '2. balablablaba', '3. asdasdaads']
    
} 


# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
CORS(app)

app.config['SESSION_PERMANENT'] = True
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'toko_kuy'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#mysql = MySQL(app)


mysql = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)



@app.route('/')
# @token_required
def home():
    # passhash = generate_password_hash('test123')
    if 'username' in session:
        username = session['username']
        return jsonify({'message': 'Hi There!', 'username': username})
    else:
        resp = jsonify({'message': 'Unauthorized'})
        resp.status_code = 401
        return resp


@app.route('/auth')
def auth():
    token = request.args.get('token')
    if token is None:
        return jsonify({'message': 'Token is missing!'}), 401

    try:
        data = jwt.decode(
            token, app.config['SECRET_KEY'], algorithms='HS256')

        if datetime.strptime(data['expiration'], '%Y-%m-%d %H:%M:%S.%f') < datetime.utcnow():
            token = jwt.encode({
                'user': session['username'],
                'expiration': str(datetime.utcnow() + timedelta(weeks=1))
            },
                app.config['SECRET_KEY'])

            sql = "INSERT INTO token (username, token) VALUES(%s, %s) ON DUPLICATE KEY UPDATE token=%s"

            cursor = mysql.cursor()
            cursor.execute(sql, (session['username'], token, token))
            mysql.commit()
            cursor.close()

        return jsonify({'message': 'JWT is verified', 'token': token})
    except:
        return jsonify({'Message': 'Invalid token'}), 403


@app.route('/register', methods=['POST'])
def register():
    if 'username' not in session:
        try:
            _json = request.json
            _name = _json['name']
            _username = _json['username']
            _password = _json['password']

            if _username and _password:
                cursor = mysql.cursor()

                sql = "SELECT * FROM user WHERE username=%s"
                sql_where = (_username,)

                cursor.execute(sql, sql_where)
                row = cursor.fetchone()
                if row:
                    username = row[1]
                    password = row[2]
                    resp = jsonify(
                        {'message': 'Bad Request - you already have an account'})
                    resp.status_code = 400
                    return resp
                else:
                    passhash = generate_password_hash(_password)
                    sql = "INSERT INTO user (name, username, password) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (_name, _username, passhash))
                    session['username'] = _username
                    mysql.commit()
                    cursor.close()

                    return jsonify({'message': 'You are registered successfully'})

            else:
                resp = jsonify(
                    {'message': 'Bad Request - invalid credentials'})
                resp.status_code = 400
                return resp
        except:
            resp = jsonify(
                {'message': 'Bad Request - please fill the form correctly'})
            resp.status_code = 400
            return resp
    else:
        resp = jsonify({'message': 'Bad Request - already logged in'})
        resp.status_code = 400
        return resp


@app.route('/login', methods=['POST'])
def login():
    if 'username' in session and session['username'] is not None:
        resp = jsonify({'message': 'Bad Request - already logged in'})
        resp.status_code = 400
        return resp
    else:
        try:
            _json = request.json
            _username = _json['username']
            _password = _json['password']

            if _username and _password:
                cursor = mysql.cursor()

                sql = "SELECT * FROM user WHERE username=%s"
                sql_where = (_username,)

                cursor.execute(sql, sql_where)
                row = cursor.fetchone()
                if row is not None:
                    username = row[1]
                    password = row[2]
                    if check_password_hash(password, _password):
                        session['username'] = username
                        cursor.close()

                        token = jwt.encode({
                            'user': _username,
                            'expiration': str(datetime.utcnow() + timedelta(seconds=60))
                        },
                            app.config['SECRET_KEY'])

                        session['token'] = token
                        return jsonify({'message': 'You are logged in successfully', 'token': token})

                    else:
                        resp = jsonify(
                            {'message': 'Bad Request - invalid password'})
                        resp.status_code = 400
                        return resp
                else:
                    resp = jsonify(
                        {'message': 'Bad Request - username is not found'})
                    resp.status_code = 400
                    return resp
            else:
                resp = jsonify(
                    {'message': 'Bad Request - please fill the form correctly'})
                resp.status_code = 400
                return resp
        except Exception as e:
            resp = jsonify({'message': 'Bad Request - invalid credendtials'})
            resp.status_code = 400
            print(f"Error: {e}")
            traceback.print_exc()
            return resp


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        return jsonify({'message': 'You successfully logged out'})
    else:
        resp = jsonify({'message': 'Bad Request - log in first'})
        resp.status_code = 400
        return resp
        

@app.route("/predict", methods=["POST"])
def predict_api():
    file = request.files['file']
    if 'file' not in request.files:
        value = {
            "msg": 'Tidak ada file',
        }
        return jsonify(value), 400
    
    if file.filename == '':
        value = {
            "msg": 'Tidak ada file dipilih untuk diupload'
        }
        return jsonify(value), 400
    
    # Read input dari user
    img = Image.open(file)

    # Resize img
    img = img.resize((224, 224))

    # Preprocess the image (masih nunggu ML)
    # ...

    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)

    # Predict img yg udh jadi arr
    prediction = model.predict(img_array)

    # Get the predicted class and Treatment
    predicted_class = np.argmax(prediction, axis=-1)
    predicted_class = int(predicted_class)
    class_name = class_names.get(predicted_class, "Class tidak terdeteksi")
    treatment_class = treatment_classes.get(predicted_class, "Treatment tidak ditemukan")

    #Return response
    response = {
        'predicted_class': predicted_class,
        'Terdeteksi Jenis' : class_name,
        'Penanganan yang dapat dilakukan' : treatment_class
    }   
    return jsonify(response), 200


@app.route("/uploadToDb", methods=["POST"])
def upload_to_db():
    file = request.files['file']
    class_name = request.form["data"]
    usernameUs = request.form["username"]


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

    expiration_time = datetime.timedelta(seconds=LIFETIME)
    signed_url = blob.generate_signed_url(
        version='v4',
        expiration=expiration_time,
        method='GET'
    )
    shortener = pyshorteners.Shortener()
    short_url = shortener.tinyurl.short(signed_url)
    # Menjalankan query INSERT ke database
    cursor = mysql.cursor()
    query = "INSERT INTO storage (username_img,hasil_predict, url_img) VALUES (%s,%s, %s)"
    values = (usernameUs,class_name, short_url)
    cursor.execute(query, values)
    inserted_id = cursor.lastrowid
    mysql.commit()
    cursor.close()
   

    response = {
        'Terdeteksi Jenis': short_url,
        'Class': class_name,
        'id gambar': inserted_id
        # tambah rekomendasi sesuai prediksi sesuai class
    }
    return jsonify(response), 201

@app.route("/getSignedURL/<username>", methods=["GET"])
def get_signed_url(username):
    # Menjalankan query SELECT ke database berdasarkan username
    cursor = mysql.cursor()
    query = "SELECT url_img FROM storage WHERE username_img = %s"
    values = (username,)
    cursor.execute(query, values)
    results = cursor.fetchall()
    cursor.close()
    if len(results) == 0:
        response = {
            "msg": "Data tidak ditemukan"
        }
        return jsonify(response), 404

    signed_urls = [result[0] for result in results]  # Mengambil elemen pertama dari setiap tupel hasil query

    response = {
        "signed_urls": signed_urls
    }
    return jsonify(response), 200


@app.route("/getDataByIdAndUsername/<int:data_id>/<username>", methods=["GET"])
def get_data_by_id_and_username(data_id, username):
    # Menjalankan query SELECT ke database berdasarkan ID dan username
    cursor = mysql.cursor()
    query = "SELECT * FROM storage WHERE id = %s AND username_img = %s"
    values = (data_id, username)
    cursor.execute(query, values)
    result = cursor.fetchone()
    cursor.close()

    if result is None:
        response = {
            "msg": "Data tidak ditemukan"
        }
        return jsonify(response), 404

    # Mengambil nilai-nilai dari kolom-kolom yang diinginkan
    id = result[0]
    jenis_penyakit = result[2]
    image = result[3]

    response = {
        "id": id,
        "jenis_penyakit": jenis_penyakit,
        "image": image
    }
    return jsonify(response), 200




 #Get image by name biar signedURL nya automated request and load
if __name__ == '__main__':
    app.run(debug=True, port=211)

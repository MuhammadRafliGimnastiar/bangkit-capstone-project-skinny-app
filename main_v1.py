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
from collections import OrderedDict
from flask_swagger_ui import get_swaggerui_blueprint


app = Flask(__name__)

SWAGGER_URL = '/docs'  # endpoint dokumentasi swagger
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Skinny"
    },
)


app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Load custom model
model = tf.keras.models.load_model(('model4.h5'), compile=False, custom_objects={
                                   'KerasLayer': hub.KerasLayer})

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service.json"
# Load primary Model
# model = tf.keras.models.load_model('model.h5')

# Koneksi ke Google Cloud Storage
storage_client = storage.Client()
bucket_name = 'trialdb'  # Replace with your GCS bucket name
bucket = storage_client.get_bucket(bucket_name)


app.config['SECRET_KEY'] = 'c1efa70af3b7404bbc79535ce1551e47'

# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
CORS(app)

app.config['SESSION_PERMANENT'] = True
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'testingdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#mysql = MySQL(app)


mysql = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='testingdb'
)

# global predicted_class;
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
# Dictionary for Descripstions
desc_names = {
    0: "Blackhead, juga dikenal sebagai komedo terbuka, adalah kondisi kulit yang umum terjadi akibat penyumbatan pori-pori kulit. Penyumbatan tersebut terjadi ketika kotoran, sel kulit mati, minyak alami kulit (sebum), dan bakteri terperangkap di dalam pori-pori dan mengoksidasi ketika terkena udara. Ini menghasilkan penumpukan bintik-bintik hitam kecil yang sering muncul di area hidung, dahi, dan dagu.",
    1: "Eksim, yang juga dikenal sebagai dermatitis, adalah kondisi peradangan kulit yang menyebabkan gatal, kemerahan, kering, dan ruam pada kulit. Ada beberapa jenis eksim, termasuk dermatitis atopik, dermatitis kontak, dan dermatitis seboroik. Berikut ini adalah deskripsi umum tentang eksim beserta cara pencegahan, penanganan, dan obat yang umum digunakan.",
    2: "Flek hitam adalah suatu kondisi kulit di mana terdapat bercak-bercak gelap yang muncul pada permukaan kulit. Kondisi ini juga dikenal sebagai hiperpigmentasi, di mana melanin, pigmen yang memberikan warna pada kulit, terakumulasi di area tertentu.",
    3: "Penyakit jerawat adalah kondisi kulit yang umum terjadi, terutama pada masa remaja, meskipun dapat juga terjadi pada usia dewasa. Jerawat terjadi ketika folikel rambut tersumbat oleh minyak dan sel kulit mati, sehingga menyebabkan peradangan dan timbulnya benjolan merah atau komedo di kulit. Beberapa faktor yang dapat mempengaruhi perkembangan jerawat meliputi perubahan hormon, produksi minyak berlebih di kulit, bakteri Propionibacterium acnes, dan faktor genetik.",
    4: "Herpes adalah penyakit yang disebabkan oleh virus herpes simplex. Ada dua jenis virus herpes simplex yang umum: herpes simplex tipe 1 (HSV-1) dan herpes simplex tipe 2 (HSV-2). HSV-1 biasanya terkait dengan infeksi pada area mulut dan bibir, sementara HSV-2 biasanya terkait dengan infeksi pada area kelamin.",
    5: "Penyakit kurap, juga dikenal sebagai tinea atau dermatofitosis, adalah infeksi kulit yang disebabkan oleh jamur dermatofit. Infeksi ini umumnya terjadi pada kulit, kuku, dan rambut. Kurap biasanya menyebar melalui kontak langsung dengan orang atau hewan yang terinfeksi, atau melalui kontak dengan benda yang terkontaminasi.",
    6: "Penyakit Milia adalah suatu kondisi kulit yang ditandai oleh adanya benjolan kecil berwarna putih atau kekuningan pada permukaan kulit. Benjolan-benjolan ini muncul akibat penumpukan keratin (protein yang ditemukan pada kulit) di dalam pori-pori kulit. Milia biasanya terjadi di wajah, terutama di sekitar area mata, pipi, dan hidung, namun juga dapat muncul di bagian tubuh lainnya.",
    7: "Panu, juga dikenal sebagai tinea versicolor atau dermatomikosis superfisialis, adalah infeksi kulit yang disebabkan oleh jamur. Infeksi ini biasanya disebabkan oleh jamur Malassezia yang biasanya ada di kulit manusia tanpa menyebabkan masalah. Namun, dalam beberapa kondisi, jamur ini dapat berkembang biak secara berlebihan dan menyebabkan gejala panu."
}

# Dictionary for Title Treatment {Blackhead,Eksim,Flek Hitam,Jerawat,Herves,Kurap,Milia,Panu}
title_treatment_classes = {
    0: ['1. Kompres hangat',
        '2. Ekstraksi manual',
        '3. Perawatan topikal',
        '4. Perawatan profesional'],

    1: ['1. Menghindari pemicu',
        '2. Menggunakan krim kortikosteroid topikal',
        '3. Penggunaan pelembap',
        '4. Obat antihistamin'],

    2: ['1. Melindungi diri dari sinar matahari',
        '2. Hindari paparan sinar matahari secara berlebihan',
        '3. Gunakan produk pemutih kulit',
        '4. Perawatan medis'],

    3: ['1. Menggunakan obat jerawat topikal',
        '2. Menggunakan antibiotik',
        '3. Terapi hormon',
        '4. Perawatan kulit lainnya'],

    4: ['1. Untuk herpes oral ringan ',
        '2. Herpes genital ',
        '3.________________________'
        '4. _______________________'],

    5: ['1. Jika Anda mencurigai memiliki infeksi kurap',
        '2. Gunakan krim atau salep antijamur topika',
        '3. Gunakan obat antijamur oral',
        '4. _______________________'],

    6: ['1. Hindari pemakaian kosmetik berat atau berminyak',
        '2. Membersihkan wajah secara rutin',
        '3. Rajin eksfoliasi',
        '4. Konsultasikan dengan dokter kulit'],

    7: ['1. Konsultasikan dengan dokter',
        '2. Gunakan obat topikal',
        '3. Lakukan perawatan kulit yang tepat',
        '4. _______________________']

}

# Dictionary for Treatment {Blackhead,Eksim,Flek Hitam,Jerawat,Herves,Kurap,Milia,Panu}
treatment_classes = {
    0: ['Tempatkan kain hangat atau kompres hangat pada area yang terkena blackhead untuk membuka pori-pori dan memudahkan pengeluaran kotoran.',
        'Jika blackhead tidak hilang dengan sendirinya, pengeluaran manual dapat dilakukan oleh ahli perawatan kulit yang terlatih. Namun, ini sebaiknya dilakukan oleh profesional untuk menghindari risiko infeksi atau kerusakan pada kulit.',
        'Menggunakan produk perawatan kulit yang mengandung bahan seperti asam salisilat, retinoid, atau benzoyl peroxide dapat membantu mengurangi blackhead.',
        'Prosedur dermatologis seperti peeling kimia, mikrodermabrasi, atau terapi laser dapat membantu membersihkan pori-pori dan mengurangi kemunculan blackhead.'],

    1: ['Jika Anda dapat mengidentifikasi pemicu yang memperburuk gejala eksim Anda, hindarilah faktor-faktor tersebut.',
        'Dokter dapat meresepkan krim atau salep kortikosteroid yang mengandung antiinflamasi untuk mengurangi peradangan dan gatal-gatal.',
        'Gunakan pelembap secara teratur untuk menjaga kelembapan kulit dan mengurangi keringat yang dapat memicu gejala.',
        'Dokter juga dapat meresepkan antihistamin untuk membantu mengurangi gatal-gatal yang disebabkan oleh reaksi alergi.'],

    2: ['Gunakan tabir surya dengan faktor perlindungan matahari (SPF) yang tinggi saat berada di luar ruangan. Gunakan topi, kacamata hitam, dan pakaian pelindung untuk melindungi kulit dari paparan sinar UV.',
        'Batasi waktu berada di bawah sinar matahari langsung, terutama pada jam-jam terik.',
        'Ada berbagai produk pemutih kulit yang tersedia secara bebas di pasaran. Namun, sebaiknya berkonsultasilah dengan dokter atau ahli kecantikan sebelum menggunakan produk tersebut.',
        'Jika flek hitam Anda sangat mengganggu atau sulit diatasi dengan perawatan rumah, Anda dapat berkonsultasi dengan dokter kulit atau dermatologis. Mereka dapat merekomendasikan perawatan medis seperti peeling kimia, terapi laser, atau penggunaan krim pemutih yang lebih kuat.'],

    3: ['Dokter kulit dapat meresepkan krim atau gel yang mengandung bahan seperti benzoyl peroxide, asam salisilat, atau retinoid untuk membantu mengurangi peradangan dan membersihkan pori-pori.',
        'Jika jerawat terinfeksi, dokter dapat meresepkan antibiotik oral atau topikal untuk mengatasi infeksi bakteri.',
        'Untuk kasus jerawat yang berhubungan dengan perubahan hormonal, seperti sindrom ovarium polikistik, dokter dapat meresepkan terapi hormon untuk mengatur keseimbangan hormon.',
        'Dokter kulit juga dapat merekomendasikan terapi tertentu seperti pengelupasan kulit, pengangkatan komedo, atau suntikan kortikosteroid untuk mengatasi jerawat yang parah.'],
    # Baru sampe siniiiiiiiiiii-------------------
    4: ['1. Untuk herpes oral ringan, biasanya penyakit ini sembuh dengan sendirinya dalam waktu satu hingga dua minggu. ',
        '2. Herpes genital sering memerlukan perawatan yang lebih intensif. Dokter dapat meresepkan obat antivirus oral yang dapat mengurangi gejala dan mencegah penularan ke pasangan seksual. ',
        '3. Lorem Ipsum'
        '4. Lorem Ipsum blasae'],

    5: ['1. Jika Anda mencurigai memiliki infeksi kurap, segera konsultasikan dengan dokter atau dermatologis untuk diagnosis dan pengobatan yang tepat.',
        '2. Biasanya, dokter akan meresepkan krim atau salep antijamur topikal yang mengandung bahan aktif seperti miconazole, clotrimazole, atau terbinafine.',
        '3. Selain itu, dalam beberapa kasus, dokter mungkin meresepkan obat antijamur oral untuk infeksi yang lebih parah atau menyebar ke area yang luas.',
        '4. Lorem Ipsum Blabla'],

    6: ['1. Menghindari pemakaian kosmetik berat atau berminyak yang dapat menyumbat pori-pori.',
        '2. Membersihkan wajah secara rutin menggunakan pembersih yang lembut.',
        '3. Menggunakan eksfoliator atau scrub yang lembut untuk mengangkat sel kulit mati dan mencegah penumpukan keratin.',
        '4. Jika milia terletak di area yang sensitif atau mengganggu penampilan, konsultasikan dengan dokter kulit untuk penanganan lebih lanjut.'],

    7: ['Jika Anda curiga mengalami panu, segera berkonsultasilah dengan dokter untuk mendapatkan diagnosis yang tepat.',
        'Dokter mungkin meresepkan krim, lotion, atau sampo antijamur yang mengandung bahan seperti ketoconazole, miconazole, atau selenium sulfida.',
        'Jaga kebersihan kulit dan hindari penggunaan produk kosmetik yang berpotensi menyumbat pori-pori.',
        '4. Lorem Ipsum blabla']

}


def auth():
    try:
        _username = session['username']
        cursor = mysql.cursor()

        sql = "SELECT * FROM token WHERE username=%s"
        sql_where = (_username,)

        cursor.execute(sql, sql_where)
        row = cursor.fetchone()
        if row:
            token = row[1]
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
            return True
    except:
        return "Unauthorized"


@app.route('/')
def home():
    stat = auth()
    if stat is True:
        username = session['username']
        return jsonify({'Error': False, 'message': 'Hi There!', 'username': username})
    else:
        resp = jsonify({'Error': True, 'message': 'Unauthorized'})
        resp.status_code = 400
        return resp


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
                    resp = jsonify(
                        {'Error': True, 'message': 'Bad Request - you already have an account'})
                    resp.status_code = 400
                    return resp
                else:
                    passhash = generate_password_hash(_password)
                    sql = "INSERT INTO user (name, username, password) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (_name, _username, passhash))
                    mysql.commit()
                    cursor.close()

                    return jsonify({'Error': False, 'message': 'You are registered successfully'}), 200

            else:
                resp = jsonify(
                    {'Error': True, 'message': 'Bad Request - invalid credentials'})
                resp.status_code = 400
                return resp
        except:
            resp = jsonify(
                {'Error': True, 'message': 'Bad Request - please fill the form correctly'})
            resp.status_code = 400
            return resp
    else:
        resp = jsonify(
            {'Error': True, 'message': 'Bad Request - already logged in'})
        resp.status_code = 400
        return resp


@app.route('/login', methods=['POST'])
def login():
    if 'username' in session and session['username'] is not None:
        resp = jsonify(
            {'Error': True, 'message': 'Bad Request - already logged in'})
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

                        token = jwt.encode({
                            'user': _username,
                            'expiration': str(datetime.utcnow() + timedelta(seconds=60))
                        },
                            app.config['SECRET_KEY'])

                        sql = "INSERT INTO token (username, token) VALUES (%s, %s) ON DUPLICATE KEY UPDATE token=%s"
                        cursor.execute(sql, (username, token, token))
                        mysql.commit()
                        cursor.close()
                        return jsonify({'Error': False, 'message': 'You are logged in successfully', 'token': token}), 200

                    else:
                        resp = jsonify(
                            {'Error': True, 'message': 'Bad Request - invalid password'})
                        resp.status_code = 400
                        return resp
                else:
                    resp = jsonify(
                        {'Error': True, 'message': 'Bad Request - username is not found'})
                    resp.status_code = 400
                    return resp
            else:
                resp = jsonify(
                    {'Error': True, 'message': 'Bad Request - please fill the form correctly'})
                resp.status_code = 400
                return resp
        except:
            resp = jsonify(
                {'Error': True, 'message': 'Bad Request - invalid credendtials'})
            resp.status_code = 400
            return resp


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        return jsonify({'Error': False, 'message': 'You are logged out successfully'}), 200
    else:
        resp = jsonify(
            {'Error': True, 'message': 'Bad Request - log in first'})
        resp.status_code = 400
        return resp


@app.route("/predict", methods=["POST"])
def predict_api():
    file = request.files['file']
    if 'file' not in request.files:
        value = {
            'Error': True,
            'message': 'Tidak ada file'

        }
        return jsonify(value), 400

    if file.filename == '':
        value = {
            'Error': True,
            'message': 'Tidak ada file dipilih untuk diupload'

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
    treatment_class = treatment_classes.get(
        predicted_class, "Treatment tidak ditemukan")
    title_treatment = title_treatment_classes.get(
        predicted_class, "Judul tidak ditemukan")
    desc_name = desc_names.get(predicted_class, "Deskripsi tidak ditemukan")

    # Return response
    response = {
        'Error': False,
        'message': "Sukses",
        'Penanganan': {
            'Terdeteksi Jenis': class_name,
            'Deskripsi': desc_name,
            'Penanganan yang dapat dilakukan': treatment_class,
            'Judul Penanganan': title_treatment,
            'Class terprediksi': predicted_class
        }

    }
    # response.move_to_end('Terdeteksi Jenis', last=False)
    return jsonify(response), 200
    # else:
    #     value = {
    #             'error': True,
    #             "msg": 'You must Authorized'

    #         }
    #     return jsonify(value), 401


@app.route("/uploadToDb", methods=["POST"])
def upload_to_db():
    file = request.files['file']
    class_name = request.form["data"]
    usernameUs = request.form["username"]
    class_get = request.form['class']

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
    # Menjalankan query INSERT ke database
    cursor = mysql.cursor()
    query = "INSERT INTO storage (username_img,class_predict,hasil_predict, url_img) VALUES (%s,%s, %s,%s)"
    values = (usernameUs, class_get, class_name, short_url)
    cursor.execute(query, values)
    inserted_id = cursor.lastrowid
    mysql.commit()
    cursor.close()

    response = {
        'Error': False,
        'message': "Berhasil menambah ke dalam Bookmark",
        'History': {
            'Terdeteksi Jenis': short_url,
            'Class': class_name,
            'id gambar': inserted_id
        }
    }
    return jsonify(response), 200


@app.route("/getDetail/<username>", methods=["GET"])
def getDetail(username):
    # Menjalankan query SELECT ke database berdasarkan username
    cursor = mysql.cursor()
    query = "SELECT class_predict,url_img FROM storage WHERE username_img = %s"
    values = (username,)
    cursor.execute(query, values)
    results = cursor.fetchall()
    cursor.close()
    if len(results) == 0:
        response = {
            'Error': True,
            'message': "Data tidak ditemukan"
        }
        return jsonify(response), 400

    response = {
        'Error': False,
        'message': "Data Berhasil Didapatkan",
        'Daftar History': []
    }

    for result in results:
        signed_url = result[1]
        class_url = result[0]

        class_name = class_names.get(class_url, "Class tidak terdeteksi")
        treatment_class = treatment_classes.get(
            class_url, "Treatment tidak ditemukan")
        title_treatment = title_treatment_classes.get(
            class_url, "Judul tidak ditemukan")
        desc_name = desc_names.get(class_url, "Deskripsi tidak ditemukan")

        image_entry = {
            'image': {
                "signed_url": signed_url,
                "class_Predicted": class_url},
            'Penanganan': {
                'Terdeteksi Jenis': class_name,
                'Deskripsi': desc_name,
                'Penanganan yang dapat dilakukan': treatment_class,
                'Judul Penanganan': title_treatment
            }
        }
        response["Daftar History"].append(image_entry)

        # penanganan_entry = {
        #     'Terdeteksi Jenis': class_name,
        #     'Deskripsi': desc_name,
        #     'Penanganan yang dapat dilakukan': treatment_class,
        #     'Judul Penanganan': title_treatment
        # }
        # response["Penanganan"].append(penanganan_entry)

    return jsonify(response), 200

# def getDetail(username):
#     # Menjalankan query SELECT ke database berdasarkan username
#     cursor = mysql.cursor()
#     query = "SELECT class_predict,url_img FROM storage WHERE username_img = %s"
#     values = (username,)
#     cursor.execute(query, values)
#     results = cursor.fetchall()
#     cursor.close()
#     if len(results) == 0:
#         response = {
#             "Error": True,
#             "msg": "Data tidak ditemukan"
#         }
#         return jsonify(response), 404

#     # Mengambil elemen pertama dari setiap tupel hasil query
#     signed_urls = [result[0] for result in results]
#     class_url = [result[1] for result in results]

#     class_name = class_names.get(class_url, "Class tidak terdeteksi")
#     treatment_class = treatment_classes.get(class_url, "Treatment tidak ditemukan")
#     title_treatment = title_treatment_classes.get(class_url, "Judul tidak ditemukan")
#     desc_name = desc_names.get(class_url, "Deskripsi tidak ditemukan")

#     response = {
#         "Error": False,
#         "msg": "Data Berhasil Didapatkan",
#         "Image":{
#             "signed_urls": signed_urls,
#             "class_Predicted": class_url
#         },
#         'Penanganan': {
#         'Terdeteksi Jenis': class_name,
#         'Deskripsi': desc_name,
#         'Penanganan yang dapat dilakukan': treatment_class,
#         'Judul Penanganan': title_treatment
#         }
#     }
#     return jsonify(response), 200


 # Get image by name biar signedURL nya automated request and load
if __name__ == '__main__':
    app.run()

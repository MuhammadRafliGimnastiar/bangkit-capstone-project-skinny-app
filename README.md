# bangkit-capstone-project-skinny-app
Ini adalah Respository project capstone Bangkit, Skinny App
# Skinny

Skinny REST-API

# How to Use

- Local Host: Run with python, local IP and Port:5000
  `http://127.0.0.1:211/` or `http://localhost:211/`
- Online:
  `https://skinny-aflmdbaorq-uc.a.run.app/`

# Endpoint Route

- ### Register

  `https://skinny-aflmdbaorq-uc.a.run.app/register`

  - **[POST]** 

    Request:

    ```
    {
        "name": "Skinny",
        "username" : "SkinnyTester",
        "password" : "skinnyoke"
    }
    ```
    
    Response:

    ```
    {
        "Error": false,
        "message": "You are registered successfully"
    }
    ```

- ### Login

  `https://skinny-aflmdbaorq-uc.a.run.app/login`

  - **[POST]** 

    Request:

    ```
     {
        "username" : "SkinnyTester",
        "password" : "skinnyoke"
    }
    ```
   
    Response:

    ```
    {
        "Error": false,
        "Your Name": "Skinny",
        "Your Username": "SkinnyTester",
        "message": "You are logged in successfully",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiU2tpbm55VGVzdGVyIiwiZXhwaXJhdGlvbiI6IjIwMjQtMDYtMTQgMTM6NDU6MjEuMjcxMTYyIn0.lxeyKvwq94fZNzoRXMFNgeFKcAQqY1GVzOZyj_SH5fc"
    }
    ```

- ### Logout

  `https://skinny-aflmdbaorq-uc.a.run.app/logout`

  - **[GET]** 

    Request:

    ```
     {
        "username" : "SkinnyTester"
    }
    ```
   
    Response:

    ```
    {
        "error": false,
        "message": "Logout Sukses"
    }
    ```

- ### Predict

  `https://skinny-aflmdbaorq-uc.a.run.app/predict`

  - **[POST]** 
  Auth required: Yes


    Request:

    ```
     {
        "file" : "image.jpg",
        "token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiU2tpbm55VGVzdGVyIiwiZXhwaXJhdGlvbiI6IjIwMjQtMDYtMTQgMTM6NDU6MjEuMjcxMTYyIn0.lxeyKvwq94fZNzoRXMFNgeFKcAQqY1GVzOZyj_SH5fc"
    }
    ```
   
    Response:

    ```
    {
        "Error": false,
        "Penanganan": {
            "Class terprediksi": "3",
            "Deskripsi": "Penyakit jerawat adalah kondisi kulit yang umum terjadi, terutama pada masa remaja, meskipun dapat juga terjadi pada usia dewasa. Jerawat terjadi ketika folikel rambut tersumbat oleh minyak dan sel kulit mati, sehingga menyebabkan peradangan dan timbulnya benjolan merah atau komedo di kulit. Beberapa faktor yang dapat mempengaruhi perkembangan jerawat meliputi perubahan hormon, produksi minyak berlebih di kulit, bakteri Propionibacterium acnes, dan faktor genetik.",
            "Judul Penanganan": [
                "1. Menggunakan obat jerawat topikal",
                "2. Menggunakan antibiotik",
                "3. Terapi hormon",
                "4. Perawatan laser atau pengelupasan kimia",
                "5. Perawatan kulit lainnya"
            ],
            "Penanganan yang dapat dilakukan": [
                "Dokter kulit dapat meresepkan krim atau gel yang mengandung bahan seperti benzoyl peroxide, asam salisilat, atau retinoid untuk membantu mengurangi peradangan dan membersihkan pori-pori.",
                "Jika jerawat terinfeksi, dokter dapat meresepkan antibiotik oral atau topikal untuk mengatasi infeksi bakteri.",
                "Untuk kasus jerawat yang berhubungan dengan perubahan hormonal, seperti sindrom ovarium polikistik, dokter dapat meresepkan terapi hormon untuk mengatur keseimbangan hormon.",
                "Dalam kasus jerawat yang parah, dokter kulit dapat merekomendasikan penggunaan laser atau pengelupasan kimia untuk menghilangkan lapisan atas kulit yang terkena jerawat.",
                "Dokter kulit juga dapat merekomendasikan terapi tertentu seperti pengelupasan kulit, pengangkatan komedo, atau suntikan kortikosteroid untuk mengatasi jerawat yang parah."
            ],
            "Pesan": "Jika Anda mengalami masalah jerawat yang mengganggu dan sulit diatasi dengan perawatan rumah, disarankan untuk berkonsultasi dengan dokter kulit atau dermatologis untuk diagnosis dan perawatan yang tepat.",
            "Sumber": "https://www.medicalnewstoday.com/articles/107146",
            "Terdeteksi Jenis": "Jerawat"
        },
        "message": "Sukses"
    }
    ```
- ### Upload to Database

  `https://skinny-aflmdbaorq-uc.a.run.app/uploadToDb`

  - **[POST]** 

    Request:

    ```
     {
        "username" : "SkinnyTester",
        "file" : "image.jpg",
        "class_name" : "Jerawat",
        "class": "3"
    }
    ```
   
    Response:

    ```
    {
        "Error": false,
        "History": {
            "Class": "Jerawat",
            "Terdeteksi Jenis": "https://tinyurl.com/28tnpkan",
            "id gambar": 5
        },
        "message": "Berhasil menambah ke dalam Bookmark"
    }
    ```
- ### Get History by User

  `https://skinny-aflmdbaorq-uc.a.run.app//getHistory/<username>`

  - **[GET]** 

    Request:

    ```
     [null]
    ```
   
    Response:

    ```
    {
        "Daftar History": [
            {
                "Penanganan": {
                    "Deskripsi": "Penyakit jerawat adalah kondisi kulit yang umum terjadi, terutama pada masa remaja, meskipun dapat juga terjadi pada usia dewasa. Jerawat terjadi ketika folikel rambut tersumbat oleh minyak dan sel kulit mati, sehingga menyebabkan peradangan dan timbulnya benjolan merah atau komedo di kulit. Beberapa faktor yang dapat mempengaruhi perkembangan jerawat meliputi perubahan hormon, produksi minyak berlebih di kulit, bakteri Propionibacterium acnes, dan faktor genetik.",
                    "Judul Penanganan": [
                        "1. Menggunakan obat jerawat topikal",
                        "2. Menggunakan antibiotik",
                        "3. Terapi hormon",
                        "4. Perawatan laser atau pengelupasan kimia",
                        "5. Perawatan kulit lainnya"
                    ],
                    "Penanganan yang dapat dilakukan": [
                        "Dokter kulit dapat meresepkan krim atau gel yang mengandung bahan seperti benzoyl peroxide, asam salisilat, atau retinoid untuk membantu mengurangi peradangan dan membersihkan pori-pori.",
                        "Jika jerawat terinfeksi, dokter dapat meresepkan antibiotik oral atau topikal untuk mengatasi infeksi bakteri.",
                        "Untuk kasus jerawat yang berhubungan dengan perubahan hormonal, seperti sindrom ovarium polikistik, dokter dapat meresepkan terapi hormon untuk mengatur keseimbangan hormon.",
                        "Dalam kasus jerawat yang parah, dokter kulit dapat merekomendasikan penggunaan laser atau pengelupasan kimia untuk menghilangkan lapisan atas kulit yang terkena jerawat.",
                        "Dokter kulit juga dapat merekomendasikan terapi tertentu seperti pengelupasan kulit, pengangkatan komedo, atau suntikan kortikosteroid untuk mengatasi jerawat yang parah."
                    ],
                    "Pesan": "Jika Anda mengalami masalah jerawat yang mengganggu dan sulit diatasi dengan perawatan rumah, disarankan untuk berkonsultasi dengan dokter kulit atau dermatologis untuk diagnosis dan perawatan yang tepat.",
                    "Sumber": "https://www.medicalnewstoday.com/articles/107146",
                    "Terdeteksi Jenis": "Jerawat"
                },
                "image": {
                    "class_Predicted": "3",
                    "signed_url": "https://tinyurl.com/28tnpkan"
                }
            }
        ],
        "Error": false,
        "message": "Data Berhasil Didapatkan"
    }
    ```

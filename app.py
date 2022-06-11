from re import search
from flask import Flask, render_template, request, jsonify, make_response
from flask_mysqldb import MySQL
import yaml
import numpy as np
import keras
from keras.preprocessing import image
import json
from json import JSONEncoder
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import random

app = Flask(__name__)

model = keras.models.load_model('model_testv2.h5')

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def predict_image(path):
    img = image.load_img(path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    classes = model.predict(images, batch_size=32)
    return classes

def dictionary(result):

    if result[0][0] == 1:
        return {"result":"narrow brown spot"}
    if result[0][1] == 1:
        return {"result":"brown spot"}
    if result[0][2] == 1:
        return {"result":"healthy"}
    if result[0][3] == 1:
        return {"result":"backterial leaf blight"}
    if result[0][4] == 1:
        return {"result":"leaf blast"}
    if result[0][5] == 1:
        return {"result":"leaf scald"}

db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

app.config['JSON_SORT_KEYS'] = False

mysql = MySQL(app)

@app.route("/penyakit", methods=['POST'])
def predict():
    if request.method == 'POST':
        penyakitDetails = request.form
        name = penyakitDetails['nama']
        tanggal = penyakitDetails['tanggal']
        deskripsi = penyakitDetails['deskripsi']
        img = request.files['image']
        createdAt = datetime.now()
        updatedAt = datetime.now()

        splitfile = os.path.splitext(img.filename)
        fileName = splitfile[0] + str(random.randint(1,1000)) + splitfile[1]
        img.save("./static/" + fileName)
        url = os.path.join('static/', fileName)
        img_path = url

        p = predict_image(img_path)
        print(p)
        result = dictionary(p)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO penyakits(nama, indikasi, tanggal, deskripsi, createdAt, updatedAt, image, url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (name, result['result'], tanggal, deskripsi, createdAt, updatedAt, fileName, url))
        mysql.connection.commit()
        cur.close()
        return {
            "status": 200,
            "message": "Penyakit berhasil diprediksi",
            "data": result
        }

@app.route("/penyakit/<int:id_penyakit>", methods=['PUT'])
def update(id_penyakit):
    if request.method == 'PUT':
        cur = mysql.connection.cursor()
        searchpenyakit = cur.execute("SELECT * FROM penyakits WHERE id_penyakit = {}".format(id_penyakit))
        row_headers=[x[0] for x in cur.description]
        if (searchpenyakit > 0):
            penyakit = cur.fetchall()
            json_data=[]
            for result in penyakit:
                json_data.append(dict(zip(row_headers,result)))
            # return jsonify(json_data)
            if (request.files['image'].filename == ''):
                fileName = json_data[0]['image']
            else:
                img = request.files['image']
                os.remove("./static/" + json_data[0]['image'])
                splitfile = os.path.splitext(img.filename)
                fileName = splitfile[0] + str(random.randint(1,1000)) + splitfile[1]
                img.save("./static/" + fileName)
            
            penyakitDetails = request.form
            name = penyakitDetails['nama']
            tanggal = penyakitDetails['tanggal']
            deskripsi = penyakitDetails['deskripsi']
            createdAt = json_data[0]['createdAt']
            updatedAt = datetime.now()

            url = os.path.join('static/', fileName)
            img_path = url

            p = predict_image(img_path)
            print(p)
            result = dictionary(p)

            cur = mysql.connection.cursor()
            cur.execute("UPDATE penyakits SET nama=%s, indikasi=%s, tanggal=%s, deskripsi=%s, createdAt=%s, updatedAt=%s, image=%s, url=%s WHERE id_penyakit=%s", (name, result['result'], tanggal, deskripsi, createdAt, updatedAt, fileName, url, id_penyakit))
            mysql.connection.commit()
            cur.close()
            return {
                "status": 204,
                "message": "Penyakit berhasil perbarui",
                "data": result
            }

        else:
            return "penyakit not found"

@app.route('/penyakit', methods=['GET'])
def get_penyakit():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM penyakits AS result")
    row_headers=[x[0] for x in cur.description]
    if result > 0:
        penyakitDetails = cur.fetchall()
        json_data=[]
        for result in penyakitDetails:
            json_data.append(dict(zip(row_headers,result)))
        return jsonify(json_data)
        # return {
        #     "status": 200,
        #     "message": "Penyakit ditemukan",
        #     "data": penyakitDetails
        # }
    return result

@app.route('/penyakit/<int:id_penyakit>', methods=['GET'])
def get_penyakit_by_id(id_penyakit):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM penyakits WHERE id_penyakit = {}".format(id_penyakit))
    row_headers=[x[0] for x in cur.description]
    if result > 0:
        penyakitDetails = cur.fetchall()
        json_data=[]
        for result in penyakitDetails:
            json_data.append(dict(zip(row_headers,result)))
    
    return jsonify(json_data)
    # return {
    #         "status": 200,
    #         "message": "Penyakit ditemukan",
    #         "data": data
    #     }

@app.route('/penyakit/<int:id_penyakit>', methods=['DELETE'])
def delete(id_penyakit):
    cur = mysql.connection.cursor()
    searchpenyakit = cur.execute("SELECT * FROM penyakits WHERE id_penyakit = {}".format(id_penyakit))
    row_headers=[x[0] for x in cur.description]
    if (searchpenyakit > 0):
        penyakit = cur.fetchall()
        json_data=[]
        for result in penyakit:
            json_data.append(dict(zip(row_headers,result)))
    else:
        return {
            "status": 400,
            "message": "Penyakit tidak ditemukan"
        }
    
    os.remove("./static/" + json_data[0]['image'])
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM penyakits WHERE id_penyakit={}".format(id_penyakit))
    mysql.connection.commit()
    cur.close()

    return {
            "status": 200,
            "message": "Penyakit dihapus",
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
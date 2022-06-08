from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import yaml
import numpy as np
import keras
from keras.preprocessing import image
import json
from json import JSONEncoder

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

mysql = MySQL(app)

@app.route("/predict", methods=['POST'])
def output():
    if request.method == 'POST':
        img = request.files['image']

        img_path = "./static/" + img.filename
        img.save(img_path)

        p = predict_image(img_path)
        print(p)
        result = dictionary(p)
        numpyData = {"array": p}
        encodedNumpyData = json.dumps(p, cls=NumpyArrayEncoder)
    return result

@app.route('/', methods=['POST'])
def index():
    userDetails = request.form
    name = userDetails['name']
    email = userDetails['email']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(name, email) VALUES (%s, %s)", (name, email))
    mysql.connection.commit()
    cur.close()
    return 'User Added'

@app.route('/users', methods=['GET'])
def users():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM users")
    if result > 0:
        userDetails = cur.fetchall()
        return {
            "status": 200,
            "message": "User found",
            "data": userDetails
        }
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
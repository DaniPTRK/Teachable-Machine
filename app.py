from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
import uuid
import os

# initiating site
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pythoneers'

# initiating database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# upload folder for database
app.config['UPLOAD_FOLDER1'] = "machines"

# home page
@app.route("/")
def home():
    return render_template('home.html')

# generate a unique filename
def generate_unique_filename():
    return str(uuid.uuid4())

# upload successful
@app.route("/upload_success")
def upload_success():
    return render_template('upload_success.html')

# submit machine
@app.route("/add_file", methods=['POST', 'GET'])
def add_file():
    if request.method == 'POST':
        # get the submitted file
        uploaded_file = request.files['file']

        # check if file is valid
        if uploaded_file and uploaded_file.filename.endswith('.h5'):
            # check if name is taken
            machine_name = request.form['name']
            existing_machine = Machine.query.filter_by(name=machine_name).first()

            if existing_machine:
                return render_template('upload.html', error='Machine name already taken. Please choose a different name.')

            # unique filename
            unique_filename = generate_unique_filename()
            # assamble path
            file_path = os.path.join(app.config['UPLOAD_FOLDER1'], unique_filename + '.h5')
            
            # save file
            uploaded_file.save(file_path)

            # save to database
            new_model = Machine(name=machine_name, filename=unique_filename)
            db.session.add(new_model)
            db.session.commit()

            return redirect(url_for('upload_success'))
        else:
            return render_template('upload.html', error='Invalid file format. Please upload a .h5 file.')

    return render_template('upload.html')

# download machines page
@app.route("/machines")
def machines():
    models = Machine.query.all()
    return render_template('machines.html', models=models)

# download machine file
@app.route("/download/<filename>")
def download_file(filename):
    machine = Machine.query.filter_by(filename=filename).first()

    if machine:
        file_path = os.path.join(app.config['UPLOAD_FOLDER1'], machine.filename + '.h5')
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

# try machine page
@app.route("/try_machine/<filename>", methods=['GET', 'POST'])
def try_machine(filename):
    # handle POST request when the user uploads a photo
    if request.method == 'POST':
        # get the uploaded photo
        uploaded_photo = request.files['photo']

        # waiting for code for tryig machine

        # placeholder result for demonstration
        result = "Placeholder result for the uploaded photo."

        return render_template('try_machine.html', filename=filename, result=result)

    return render_template('try_machine.html', filename=filename, result=None)

# model for the database
class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(50), nullable=False)

if __name__ == "__main__":
    app.run(debug=True)
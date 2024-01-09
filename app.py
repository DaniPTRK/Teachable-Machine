from flask import Flask, Blueprint, flash, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from os import path
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os

# initfrom machine import train
# importing essentials for training/testing a machine

# initiating site
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pythoneers'

# initiating machine database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# user database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    machines = db.relationship('Machine')

# machine database
class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

def create_database():
    if not path.exists("database.db"):
        db.create_all()
        print('Database created!')

# login manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# upload folder for database
app.config['UPLOAD_FOLDER1'] = "machines"

# authentification
auth = Blueprint('auth', __name__)

# log in
@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for('main_page'))
            else:
                flash('Incorrect password', category='error')
        else:
            flash('Incorrect password', category='error')

    return render_template("login.html")

# log out
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# sign up
@auth.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email already exists', category='error')
        elif len(email) < 6:
            flash("Email too short", category='error')
        elif len(username) < 3:
            flash("Username too short", category='error')
        elif password != confirm:
            flash("Passwords don\'t match", category='error')
        elif len(password) < 7:
            flash("Passwords too short", category='error')
        else:
            new_user = User(email=email, username=username,
                            password=generate_password_hash(password, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash("Account created!", category='success')

            login_user(new_user, remember=True)
            return redirect(url_for('main_page'))
        
    return render_template("signup.html")

app.register_blueprint(auth, url_prefix='/auth')

@app.route("/")
def home():
    return redirect(url_for("auth.login"))

@app.route("/main_page")
@login_required
def main_page():
    return render_template("home.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# get target and photos from user
@app.route("/upload_photos", methods=['GET', 'POST'])
@login_required
def upload_photos():
    if request.method == 'POST':
        # process the uploaded data as needed
        num_classes = 2
        target = []
        uploaded_files = []
        uploaded_photos = []

        # extract data from given classes - hopefully we'll implement more than 2 classes
        for i in range(num_classes):
            target.append(request.form['text_input'])
            uploaded_files.append(request.files.getlist('photo_upload[]'))
        result = None
        for i in range(num_classes):
            if not target:
                return render_template('upload_photos.html', error=f"Please enter what to detect")

            for file in uploaded_files[i]:
                if file.filename == '':
                    return render_template('upload_photos.html', error=f"No file selected")

            if file and allowed_file(file.filename):
                uploaded_photos.append(file)

            if not uploaded_photos[i]:
                return render_template('upload_photos.html', error=f"No valid image selected")
        
        return redirect(url_for('create_machine', target = target, uploaded_photos = uploaded_photos, num_classes = num_classes))

    else:
        result = None

    return render_template('upload_photos.html', result=result)

# create machine
@app.route("/create_machine", methods=['GET', 'POST'])
@login_required
def create_machine():
    if request.method == 'POST':
        target = []
        uploaded_photos = []
        target = request.args['target']
        uploaded_photos = request.args['uploaded_photos']
        num_classes = request.args['num_classes']
        machine_name = request.form['machine_name']
        # create a machine
        train(target, uploaded_photos, machine_name, num_classes)

    return render_template("create_machine.html")

# generate a unique filename
def generate_unique_filename():
    return str(uuid.uuid4())

# upload successful
@app.route("/upload_success")
@login_required
def upload_success():
    return render_template('upload_success.html')

# submit machine
@app.route("/upload_machine", methods=['POST', 'GET'])
@login_required
def upload_machine():
    if request.method == 'POST':
        # get the submitted file
        uploaded_file = request.files['machine_file']

        # check if file is valid
        if uploaded_file and uploaded_file.filename.endswith('.h5'):
            # check if name is taken
            machine_name = request.form['machine_name']

            if not machine_name:
                return render_template('upload_machine.html', error='Please enter a name for your machine.')

            existing_machine = Machine.query.filter_by(name=machine_name).first()

            if existing_machine:
                return render_template('upload_machine.html', error='Machine name already taken. Please choose a different name.')

            # unique filename
            unique_filename = generate_unique_filename()
            # assamble path
            file_path = os.path.join(app.config['UPLOAD_FOLDER1'], unique_filename + '.h5')
            
            # save file
            uploaded_file.save(file_path)

            # save to database
            new_model = Machine(name=machine_name, filename=unique_filename, user_id=current_user.id)
            db.session.add(new_model)
            db.session.commit()

            return redirect(url_for('upload_success'))
        else:
            return render_template('upload_machine.html', error='Invalid file format. Please upload a .h5 file.')

    return render_template('upload_machine.html')

# your machines page
@app.route("/your_machines")
@login_required
def your_machines():
    models = Machine.query.filter_by(user_id=current_user.id).all()
    return render_template('your_machines.html', models=models)

# remove machine
@app.route("/remove_file")
@login_required
def remove_file():
    filename = request.args['filename']
    machine = Machine.query.filter_by(filename=filename).first()

    # Check if the machine exists
    if machine:
        try:
            # Remove the associated file
            file_path = os.path.join(app.config['UPLOAD_FOLDER1'], filename + '.h5')
            os.remove(file_path)

            # Remove the machine record from the database
            db.session.delete(machine)
            db.session.commit()

            flash("Machine removed successfully", category='success')
        except Exception as e:
            flash(f"An error occurred: {str(e)}", category='error')
    else:
        flash("Machine not found", category='error')

    return redirect(url_for('machines'))


# download machines page
@app.route("/machines")
@login_required
def machines():
    models = Machine.query.all()
    return render_template('machines.html', models=models)

# download machine file
@app.route("/download_file")
@login_required
def download_file():
    filename = request.args['filename']
    machine = Machine.query.filter_by(filename=filename).first()

    if machine:
        file_path = os.path.join(app.config['UPLOAD_FOLDER1'], machine.filename + '.h5')
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404

# try machine page
@app.route("/try_machine/<filename>", methods=['GET', 'POST'])
@login_required
def try_machine(filename):
    # handle POST request when the user uploads a photo
    if request.method == 'POST':
        # get the uploaded photo
        uploaded_files = request.files.getlist('photos[]')
        uploaded_photos = []

        for file in uploaded_files:
            if file.filename == '':
                return render_template('upload_photos.html', error=f"No file selected")

            if file and allowed_file(file.filename):
                uploaded_photos.append(file)

        if not uploaded_photos:
            return render_template('upload_photos.html', error=f"No valid image selected")

        # waiting for code for trying machine

    create_database()

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, Blueprint, flash, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from os import path
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os

# initiating site
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pythoneers'

# initiating machine database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

PHOTO_UPLOAD_FOLDER = 'photo_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = PHOTO_UPLOAD_FOLDER

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
login_manager = LoginManager()
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
                flash("Logged in successfully", category='success')
                login_user(user, remember=True)
                return redirect(url_for('upload'))
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

            login_user(user, remember=True)
            return redirect(url_for('upload'))
        
    return render_template("signup.html")

app.register_blueprint(auth, url_prefix='/auth')

@app.route("/")
def home():
    return redirect(url_for("auth.login"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# upload page
@app.route("/home", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # process the uploaded data as needed
        text_input = request.form['text_input']
        uploaded_files = request.files.getlist('photo_upload[]')
        uploaded_photos = []
        photonames = []
        result = None

        if not text_input:
            return render_template('home.html', error=f"Please enter what to detect")

        for file in uploaded_files:
            if file.filename == '':
                return render_template('home.html', error=f"No file selected")

            if file and allowed_file(file.filename):
                uploaded_photos.append(file)

        if not uploaded_photos:
            return render_template('home.html', error=f"No valid photo selected")

        for photo in uploaded_photos:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
            photo.save(filename)
            photonames.append(photo.filename)

        # placeholder response
        result = f"Text input : {text_input}, Number of Photos: {len(uploaded_photos)}, Photos: {photonames}"
    else:
        result = None

    return render_template('home.html', result=result)

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
            new_model = Machine(name=machine_name, filename=unique_filename, user_id=current_user.id)
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

with app.app_context():
    create_database()


if __name__ == "__main__":
    app.run(debug=True)
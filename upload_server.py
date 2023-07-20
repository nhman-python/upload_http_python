import os
import uuid
from datetime import timedelta
from functools import wraps

from flask import render_template, request, Flask, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.permanent_session_lifetime = timedelta(days=20)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20mb
db = SQLAlchemy(app)

# ----------- config ----------- #

ALLOW_UPLOAD = True
ALLOW_EXTENSION = ('.txt', '.jpg', '.zip')  # add here an allowed extension
UPLOAD_FOLDER = 'upload_file'

if not os.path.isdir(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f'upload folder created {UPLOAD_FOLDER}')


# ----------- end config -------- #

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Create the database and tables
if not os.path.exists('users.db'):
    with app.app_context():
        db.create_all()


def valid_path(upload_path: str) -> bool:
    """
    Validates that the path is in the upload folder and not exploitable with ../..
    or something similar.
    :param upload_path: The file path to validate.
    :return: True if the path is valid, False otherwise.
    """
    upload_folder_path = os.path.abspath(UPLOAD_FOLDER)
    full_path = os.path.abspath(os.path.join(upload_folder_path, upload_path))
    return os.path.commonprefix([upload_folder_path, full_path]) == upload_folder_path


def format_size(size):
    """
    Converts the file size in bytes to a more human-friendly format.
    Example: 20971520 bytes => 20 MB
    """
    power = 2 ** 10
    n = 0
    power_labels = {0: 'bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{round(size)} {power_labels[n]}"


UPLOAD_ROUND = format_size(app.config['MAX_CONTENT_LENGTH'])


def valid_extension(file_name: str) -> bool:
    """
    This function checks if the file is allowed to be uploaded to the server.
    :param file_name: The file path to check the extension
    :return: bool
    """
    extension = os.path.splitext(file_name)[1]
    if extension in ALLOW_EXTENSION:
        return True
    return False


def random_file_name(file_path):
    """
    add uuid in the start of the given file path to handel duplication in the upload folder
    :param file_path: the path
    :return: uuid + path + extension
    """
    extension = os.path.splitext(file_path)[1]
    new_path = os.path.join(UPLOAD_FOLDER, f'{uuid.uuid1()}{extension}')
    return new_path


# Update the login_required decorator to redirect to the login page
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' in session:
            return view_func(*args, **kwargs)
        else:
            flash('You need to log in to access this page.', 'error')
            return redirect(url_for('login'))

    return wrapped_view


@app.errorhandler(413)
def request_entity_too_large(_):
    return render_template('index.html',
                           error='The file size exceeds the limit. Maximum allowed file size is 20 MB.'), 413


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file_get = request.files.get('file')
        if not file_get:
            return render_template('index.html', error='Error: No file selected.'), 400
        if not ALLOW_UPLOAD:
            return render_template('index.html', error='The admin has locked the upload for now please try later.'), 403

        if not valid_extension(file_get.filename):
            return render_template('index.html',
                                   error=f'Only this extension are allowed: {", ".join(ALLOW_EXTENSION)}.'), 400

        if file_get.content_length >= app.config['MAX_CONTENT_LENGTH']:
            return render_template('index.html',
                                   error=f'File size exceeds the limit. Maximum allowed file size is 20mb.'), 403
        random_path = random_file_name(file_get.filename)
        file_get.save(random_path)
        return render_template('index.html', info='The file has been saved on the server.')

    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please fill in all the fields', 'error')
            return redirect(url_for('register'))

        # Check if the username already exists in the database
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/delete-file', methods=['POST'])
@login_required
def delete():
    file_path = request.form.get('file_path')
    full_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, file_path))

    if not valid_path(full_path):
        flash('Invalid file path.', 'error')
    elif os.path.isfile(full_path):
        os.remove(full_path)
        flash('File deleted successfully.', 'success')
    else:
        flash('File not found.', 'error')

    return redirect(url_for('admin'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    global ALLOW_UPLOAD
    if request.method == 'POST':
        allow_upload = request.form.get('allow_upload')
        ALLOW_UPLOAD = not ALLOW_UPLOAD if allow_upload else ALLOW_UPLOAD
    # User is logged in, allow access to the admin page
    # to Render the admin page
    list_file = os.listdir(UPLOAD_FOLDER)

    return render_template('admin.html', file_count=len(list_file),
                           files=list_file, allow_upload=ALLOW_UPLOAD)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/change-password', methods=['POST', 'GET'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('password')
        if new_password:
            user = User.query.get(session['user_id'])
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('admin'))

    return render_template('change_password.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


app.run(debug=False)

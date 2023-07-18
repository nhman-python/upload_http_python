import os
import uuid
from datetime import timedelta
from flask import render_template, request, Flask, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash


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


app = Flask(__name__)
app.secret_key = 'secret_token'
app.permanent_session_lifetime = timedelta(days=20)

# ----------- config ----------- #

ALLOW_UPLOAD = True
ALLOW_EXTENSION = ('.txt', '.jpg', '.zip')  # add here an allowed extension
MAX_SIZE = 20 * 1024 * 1024
UPLOAD_FOLDER = 'upload_file'
MAX_SIZE_ROUND = format_size(MAX_SIZE)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f'upload folder created {UPLOAD_FOLDER}')


# ----------- end config -------- #

def get_password():
    with open('.env', 'r') as f:
        password_value = f.readline().split('=')[1].strip()
    return password_value


def get_admin_user():
    with open('.env', 'r') as f:
        admin_value = f.readline().split('=')[1].strip()
    return admin_value


def check_file(file_name: str) -> bool:
    """
    This function checks if the file is allowed to be uploaded to the server.
    :param file_name: The file path to check the extension
    :return: bool
    """
    extension = os.path.splitext(file_name)[1]
    if extension in ALLOW_EXTENSION:
        return True
    return False


def random_name(file_path):
    extension = os.path.splitext(file_path)[1]
    new_path = os.path.join(UPLOAD_FOLDER, f'{uuid.uuid1()}.{extension}')
    return new_path


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if ALLOW_UPLOAD:
            if file and check_file(file.filename):
                if file.content_length <= MAX_SIZE:
                    random_path = random_name(file.filename)
                    file.save(random_path)
                    return render_template('index.html', info='The file has been saved on the server.')
                else:
                    return render_template('index.html',
                                           error=f'File size exceeds the limit. Maximum allowed file size is '
                                                 f'{MAX_SIZE_ROUND}.',
                                           ), 403
            else:
                return render_template('index.html',
                                       error=f'Error: No file selected or file extension not allowed. List of '
                                             f'allowed extensions: {ALLOW_EXTENSION}',
                                       ), 400
        return render_template('index.html', error='the admin lock the upload options'), 403
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    admin_password = get_password()
    admin_username = get_admin_user()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if check_password_hash(admin_username, username) and check_password_hash(admin_password, password):
            session['logged_in'] = True
        return redirect(url_for('admin'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    # Clear the session and redirect to the login page
    session.clear()
    return redirect(url_for('login'))


@app.route('/delete-file', methods=['POST'])
def delete():
    if 'logged_in' in session:
        file_path = request.form.get('file_path')
        full_path = os.path.join(UPLOAD_FOLDER, file_path)
        if os.path.isfile(full_path):
            os.remove(full_path)
        return redirect(url_for('admin'))
    return redirect('/')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global ALLOW_UPLOAD
    # Check if the 'logged_in' key exists in the session
    if 'logged_in' in session:
        if request.method == 'POST':
            allow_upload = request.form.get('allow_upload')
            ALLOW_UPLOAD = not ALLOW_UPLOAD if allow_upload else ALLOW_UPLOAD
        # User is logged in, allow access to the admin page
        # to Render the admin page
        list_file = os.listdir(UPLOAD_FOLDER)

        return render_template('admin.html', file_count=len(list_file),
                               files=list_file, allow_upload=ALLOW_UPLOAD)
    # User is not logged in, redirect to the login page
    return redirect(url_for('login'))


@app.route('/change-password', methods=['POST', 'GET'])
def change_password():
    if 'logged_in' in session:
        if request.method == 'POST':
            change_pass = request.form.get('password')
            change_admin = request.form.get('username')
            if change_pass and change_admin:
                password = generate_password_hash(change_pass)
                admin_user = generate_password_hash(change_admin)
                if os.path.isfile('.env'):
                    with open('.env', 'w') as f:
                        f.write(
                            f'PASSWORD={password}\n'
                            f'ADMIN_USER={admin_user}'
                        )
                        session.pop('logged_in')
                    return render_template('change_password.html', success='the password change successfully',
                                           redict='True')

        return render_template('change_password.html')

    return redirect('/')


app.run(debug=True)

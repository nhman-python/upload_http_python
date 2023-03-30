from flask import Flask, request, redirect, url_for
import os
import random
import uuid

template = """
<!doctype html>
<html>
<head>
    <title>Upload new File</title>
    <style>
        /* CSS reset */
        * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        }

        /* Body styles */
        body {
        font-family: "Times New Roman", serif;
        font-size: 16px;
        line-height: 1.5;
        background-color: #ffffff;
        color: #333;
        }

        /* Heading styles */
        h1 {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 1.5rem 0;
        text-align: center;
        }

        /* Form styles */
        form {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 2rem 0;
        }

        label {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        }

        .upload-btn {
        display: inline-block;
        padding: 10px 20px;
        border: 2px solid #333;
        border-radius: 5px;
        background-color: #7ebfd8;
        color: #333;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        }

        .upload-btn:hover {
        background-color: #0d47a1;
        animation: none;
        }

        .upload-btn input[type="file"] {
        display: none;
        }


        .file-upload {
        display: inline-block;
        padding: 10px 20px;
        border: 2px solid #333;
        border-radius: 5px;
        background-color: #7ebfd8;
        color: #333;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        }

        .file-upload:hover {
        background-color: #333;
        color: #a3d8eb;
        }

        input[type="submit"] {
        display: block;
        width: 100%;
        max-width: 400px;
        margin-top: 2rem;
        padding: 10px 20px;
        font-size: 1.5rem;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        background-color: #333;
        color: #90c1da;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        }

        input[type="submit"]:hover {
        display: block;
        width: 100%;
        max-width: 400px;
        margin-top: 2rem;
        padding: 10px 20px;
        font-size: 1.5rem;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        background-color: #333;
        color: #90c1da;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        }

        /* Responsive styles */
        @media (max-width: 768px) {
        h1 {
        font-size: 2rem;
        }

        label {
        font-size: 1.2rem;
        }

        .file-upload {
        font-size: 1.2rem;
        }

        input[type="submit"] {
        font-size: 1.2rem;
        }
        }


    </style>
</head>
<body>
    <h1>Upload new File</h1>
    <form method="post" enctype="multipart/form-data">
        <label for="fileInput">
        <label for="file-upload" class="upload-btn">
            <span>Select file to upload</span>
            <input type="file" id="file-upload" name="file" />
          </label>
        <br>
        <input type="submit" value="Upload">
        <p>status:</p>
    </form>
</body>
</html>
"""

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'conf', 'txt'}
UPLOAD_FOLDER = '/home/kali/http_upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """
    Malware checker allow only some extentions
    
    """

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


MAX_FILE_SIZE = 3400 * 3400
def generate_random_name():
    name = str(uuid.uuid4()).replace('-', '')  # generate UUID and remove hyphens
    octets = [name[i:i+5] for i in range(0, 40, 4)]  # split into 4 octets of 5 characters each
    return '-'.join(octets)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    try:
        if request.method == 'POST':
            file = request.files['file']
            # check if the post request has the file part
            if 'file' not in request.files:
                return f'{template} <p>Error: try hack me :-)</p>'
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                return f'{template} <h1>Error: file not found</h1>'
            if file and allowed_file(file.filename) and len(file.read()) <= MAX_FILE_SIZE:
                filename = generate_random_name() + os.path.splitext(file.filename)[1]
                if not os.path.exists(filename):
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], filename), 0o600)
                else:
                    return f'{template} <h1>error 09-09-09</h1>'
                return f'{template} <p>File uploaded successfully</p>'
            elif not allowed_file(file.filename):
                return f'{template} <h1>file block</h1>'
    except KeyError as e:
        return '<p>400 Bad Request: The browser (or proxy) sent a request that this server could not understand.</p>'
    except Exception as e:
        return f'{template} <p>we got some error</p>'
    return template

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=443, ssl_context='adhoc')

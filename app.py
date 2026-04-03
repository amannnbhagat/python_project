from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from config import MONGO_URI, SECRET_KEY, UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = SECRET_KEY

# MongoDB
client = MongoClient(MONGO_URI)
db = client['aman_notes_db']
collection = db['aman_notes']

# Upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin":
            session['user'] = "admin"
            return redirect('/')
        else:
            flash("Invalid username or password")

    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# ---------- HOME ----------
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    notes = list(collection.find())
    return render_template('index.html', notes=notes)

# ---------- UPLOAD ----------
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        file = request.files['file']
        title = request.form['title']
        subject = request.form['subject']

        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            collection.insert_one({
                "title": title,
                "subject": subject,
                "filename": file.filename
            })

            flash("Note uploaded successfully")
            return redirect('/')

    return render_template('upload.html')

# ---------- DOWNLOAD ----------
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------- SEARCH ----------
@app.route('/search')
def search():
    if 'user' not in session:
        return redirect('/login')

    query = request.args.get('q', '')

    notes = list(collection.find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"subject": {"$regex": query, "$options": "i"}}
        ]
    }))

    return render_template('index.html', notes=notes)

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    total_notes = collection.count_documents({})
    subjects = collection.distinct("subject")

    data = {}
    for sub in subjects:
        data[sub] = collection.count_documents({"subject": sub})

    return render_template('dashboard.html', total=total_notes, data=data)

# ---------- DELETE ----------
@app.route('/delete/<id>')
def delete_note(id):
    if 'user' not in session:
        return redirect('/login')

    note = collection.find_one({"_id": ObjectId(id)})

    if note:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], note['filename'])

        if os.path.exists(file_path):
            os.remove(file_path)

        collection.delete_one({"_id": ObjectId(id)})

    return redirect('/')

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
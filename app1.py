from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import joblib
import pandas as pd
import re
import string
import smtplib
from email.message import EmailMessage
import google.generativeai as genai
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Configure Gemini
genai.configure(api_key="AIzaSyDieOOoore-p5UNiflcOFeBh7vGdfUzq4E")
model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# # Email function
# def send_email(subject, content):
#     sender_email = "abikishore910@gmail.com"
#     sender_password = "xkwe xjia pfbd jczz"
#     recipient_email = "abikishore1004@gmail.com"

#     msg = EmailMessage()
#     msg['Subject'] = subject
#     msg['From'] = sender_email
#     msg['To'] = recipient_email
#     msg.set_content(content)

#     try:
#         with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
#             smtp.login(sender_email, sender_password)
#             smtp.send_message(msg)
#             print("Email sent successfully.")
#     except Exception as e:
#         print(f"Error sending email: {e}")

def send_email(subject, content, recipient_email):
    sender_email = "abikishore910@gmail.com"
    sender_password = "xkwe xjia pfbd jczz"  # Consider using environment variables for security
    
    # Use the recipient_email parameter if provided, otherwise fall back to default
    to_email = recipient_email 
    print(recipient_email)
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email
    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print(f"Email sent successfully to {to_email}")
            return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False

@app.route('/api/send-email', methods=['POST'])
def api_send_email():
    if request.method == 'POST':
        try:
            data = request.get_json()
            recipient_email = data.get('recipient_email')
            subject = data.get('subject', 'Fake News Detection Results')
            content = data.get('content', '')
            print(f'this is email{recipient_email}')
            # Validate email
            if not recipient_email or '@' not in recipient_email:
                return jsonify({'error': 'Invalid email address'}), 400
                
            # Send email
            send_email(subject,content=content,recipient_email=recipient_email)
            
            return jsonify({'message': 'Email sent successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Text processing functions
def wordopt(text):
    text = text.lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub("\\W", " ", text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    return text

def output_label(n):
    return "Fake News" if n == 0 else "Real News"

# Load model and vectorizer
GBC = joblib.load("gradient_boosting.pkl")
vectorization = joblib.load("tfidf_vectorizer.pkl")

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password, full_name) VALUES (?, ?, ?, ?)",
                (username, email, generate_password_hash(password), full_name)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('profile.html', 
                         username=session['username'],
                         full_name=session['full_name'],
                         email=session['email'])

# Existing routes
@app.route("/")
def home():
    return render_template('home1.html', logged_in='user_id' in session)

@app.route('/index')
def index():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    return render_template('index.html', logged_in='user_id' in session)

@app.route('/about')
def about():
    return render_template('about.html', logged_in='user_id' in session)

@app.route('/discover')
def discover():
    return render_template('discover.html', logged_in='user_id' in session)

@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        flash('Please log in to use the prediction feature.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        news = request.form['news']
        
        processed_text = wordopt(news)
        transformed_text = vectorization.transform([processed_text])
        prediction = GBC.predict(transformed_text)[0]
        confidence = max(GBC.predict_proba(transformed_text)[0]) * 100

        result_label = output_label(prediction)
        result_text = f"The news is predicted as {result_label}"

        # send_email("Fake News Detection Result", result_text)

        return render_template('result3.html', prediction=result_text, confidence=confidence,news=news, logged_in=True)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower()
        prediction = data.get('prediction', '')
        confidence = data.get('confidence', '')
        original_news = data.get('original_news', '')

        news_keywords = ['news', 'fake', 'real', 'verify', 'source', 'prediction', 
                        'confidence', 'article', 'media', 'journalism', 'fact']
        
        is_news_related = any(keyword in user_message for keyword in news_keywords) or prediction

        if is_news_related:
            if any(word in user_message for word in ['how', 'why', 'explain']):
                prompt = f"""Explain why this news prediction ({prediction}, {confidence}% confidence) 
                might be accurate or what limitations it might have."""
            elif any(word in user_message for word in ['verify', 'check', 'confirm']):
                prompt = f"""Provide specific methods to verify this news prediction ({prediction})."""
            elif any(word in user_message for word in ['source', 'origin']):
                prompt = f"""Analyze what characteristics in this news content might have led to the {prediction} prediction."""
            else:
                prompt = f"""The user received a {prediction} prediction with {confidence}% confidence."""
        else:
            prompt = f"""You are a helpful AI assistant. The user asked: "{user_message}"."""

        response = model.generate_content(prompt)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
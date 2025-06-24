from flask import Flask, render_template, request
import joblib
import pandas as pd
import re
import string
import smtplib
from email.message import EmailMessage


def send_email(subject, content):
    sender_email = "abikishore910@gmail.com"
    sender_password = "xkwe xjia pfbd jczz"  # Use an app password if using Gmail
    recipient_email = "abikishore1004@gmail.com"  # Static email address

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


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

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html')


@app.route('/index')
def index():
    return render_template('index.html')



@app.route('/about')
def about():
    return render_template('about.html')




@app.route('/discover')
def discover():
    return render_template('discover.html')




# @app.route('/predict', methods=['POST'])
# def predict():
#     if request.method == 'POST':
#         news = request.form['news']
#         processed_text = wordopt(news)
#         transformed_text = vectorization.transform([processed_text])
#         prediction = GBC.predict(transformed_text)[0]
#         confidence = max(GBC.predict_proba(transformed_text)[0]) * 100
        
#         return render_template('result.html', prediction=output_label(prediction), confidence=confidence)


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        news = request.form['news']
        
        processed_text = wordopt(news)
        transformed_text = vectorization.transform([processed_text])
        prediction = GBC.predict(transformed_text)[0]
        confidence = max(GBC.predict_proba(transformed_text)[0]) * 100

        result_label = output_label(prediction)
        result_text = f"The news is predicted as: {result_label} with {confidence:.2f}% confidence."

        # Send to static email
        send_email("Fake News Detection Result", result_text)

        return render_template('result.html', prediction=result_label, confidence=confidence)


if __name__ == '__main__':
    app.run(debug=True)

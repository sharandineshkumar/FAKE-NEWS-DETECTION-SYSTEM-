from flask import Flask, render_template, request, jsonify 
import joblib
import pandas as pd
import re
import string
import smtplib
from email.message import EmailMessage
import google.generativeai as genai


# Configure Gemini (add this near the top of your app.py)
genai.configure(api_key="AIzaSyDieOOoore-p5UNiflcOFeBh7vGdfUzq4E")

# Create model
model = genai.GenerativeModel('gemini-2.0-flash')



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

        return render_template('result2.html', prediction=result_label, confidence=confidence)




@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower()
        prediction = data.get('prediction', '')
        confidence = data.get('confidence', '')
        original_news = data.get('original_news', '')

        # Check if the message is news-related
        news_keywords = ['news', 'fake', 'real', 'verify', 'source', 'prediction', 
                        'confidence', 'article', 'media', 'journalism', 'fact']
        
        is_news_related = any(keyword in user_message for keyword in news_keywords) or prediction

        if is_news_related:
            # Create context-aware prompts for news-related queries
            if any(word in user_message for word in ['how', 'why', 'explain']):
                prompt = f"""Explain why this news prediction ({prediction}, {confidence}% confidence) 
                might be accurate or what limitations it might have. Provide specific details about 
                what in the content might indicate this classification. Use 3-4 sentences."""
            elif any(word in user_message for word in ['verify', 'check', 'confirm']):
                prompt = f"""Provide specific methods to verify this news prediction ({prediction}) beyond this system. 
                Include practical fact-checking techniques and tools. List 3-4 actionable steps."""
            elif any(word in user_message for word in ['source', 'origin']):
                prompt = f"""Analyze what characteristics in this news content might have led to the {prediction} prediction:
                "{original_news[:500]}". Point out specific indicators and explain why they're significant."""
            else:
                prompt = f"""The user received a {prediction} prediction with {confidence}% confidence. 
                They asked: "{user_message}". 
                Provide a detailed (3-4 sentence) response focused on news verification best practices,
                explaining concepts clearly and offering specific advice when possible."""
        else:
            # Handle general conversation
            prompt = f"""You are a helpful AI assistant that specializes in news verification but can also 
            engage in general conversation. The user asked: "{user_message}". 
            Provide a friendly, informative response in 2-3 sentences. If the topic is related to 
            media, technology, or current events, you can provide more detailed information."""

        response = model.generate_content(prompt)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

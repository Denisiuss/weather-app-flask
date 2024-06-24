import datetime
import logging
import os
from flask import Flask, render_template, request, redirect, send_file, url_for, session, Response
from modules.modules import get_user_history_file, print_data, download_image, record_to_db, save_search_history
from modules.login_in_out import login_in, sign_up
from prometheus_client import Counter, generate_latest

app = Flask(__name__)
app.secret_key = "qweasdzxcasdqweasdzxcasd"
app.permanent_session_lifetime = datetime.timedelta(seconds=60)

logging.basicConfig(filename='logs/weather_app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

BG_COLOR = os.getenv('BG_COLOR')

REQUEST_COUNT = Counter('app_request_count', 'App Request Count', ['method', 'endpoint'])
CITY_REQUEST_COUNT = Counter('city_request_count', 'City Request Count', ['city'])

@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('main'))
    return redirect(url_for('login'))

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('Password')
        logging.info(f"Login attempt with email: {email}")
        return login_in(email, password)
    return render_template('login.html')

@app.route("/signup", methods=['GET', 'POST'])    
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('Password')
        logging.info(f"Signup attempt with email: {email}")
        return sign_up(email, password)
    return render_template('signup.html')


@app.route("/main", methods=['GET', 'POST'])
def main():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    
    if request.method == 'POST':
        name = request.form.get('city_name')
        CITY_REQUEST_COUNT.labels(city=name).inc()
        logging.info(f"City weather information requested for {name}")
        save_search_history(email, name)
        return print_data(name)
    else:
        REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
        logging.warning("Main page accessed")
        print(BG_COLOR)
        return render_template('index.html', bg_color=BG_COLOR)

@app.route('/logout')
def logout():
    session.pop('email', None)
    logging.warning("User logged out")
    return redirect(url_for('login'))

@app.route('/download_image', methods=['GET', 'POST'])
def download():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if request.method == "GET":
        logging.info("Image download requested")
        link = download_image()
        return send_file(link, as_attachment=True)
    
@app.route('/save_to_db', methods=['GET', 'POST'])
def save_to_db():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if request.method == "GET":
        logging.info("Data saved to database")
        record_to_db()
        return redirect(url_for('main'))
    
@app.route('/download-history', methods=['GET'])
def download_history():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    history_file = get_user_history_file(email)
    
    return send_file(history_file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)


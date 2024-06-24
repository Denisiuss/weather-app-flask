import json
from flask import render_template,redirect, url_for, session

def login_in(email, password):
    """
    Login function.
    Opens my_db file to get 'data base' data, validates it with user's input.
    If true -> creates session and redirect to the main page.
    if false -> render login.html with error.
        Params: user's email and password
        Return: redirect to main or login pages.
        /home/denis/Python/weather_app_project/data/dbase.json
        data/dbase.json
    """
    with open('data/dbase.json', 'r') as my_db:
        db_file = json.load(my_db)

    if email in db_file and db_file[email]['password'] == password:
        session['email'] = email
        return redirect(url_for('main'))    
    else:
        return render_template('login.html', error = "Invalid email/password combination")
        
def sign_up(email, password):
    """
    Sign up function.
    Opens my_db file to get 'data base' data, validates it with user's input.
    If true -> render login page with error.
    if false -> add user's credentials to 'data_base' file
        Params: user's email and password
        Return: redirect to login page.
    """
    users = {}
    with open('data/dbase.json', "r+") as my_db:
        db_file = json.load(my_db)
        users = db_file
        if email in db_file:
            return render_template('login.html', error="user already exists")
        
        users[email] = {"password": password}
        my_db.seek(0)
        json.dump(users, my_db, indent=4)
        return redirect(url_for('login'))

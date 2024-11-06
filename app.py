from flask import Flask, render_template, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# MySQL Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='virtualdb.c7kcawq6wjvr.eu-north-1.rds.amazonaws.com',
        user='root',
        password='Onlineawsnm',
        database='virtualdb'
    )

# Registration Form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('student', 'Student')], validators=[DataRequired()])
    submit = SubmitField('Register')

# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Post Form (Admin Only)
class PostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

@app.route('/')
def home():
    return render_template('home.html')  # Render the home page

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  # Create an instance of the registration form
    if form.validate_on_submit():
        username = form.username.data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            flash('Username already taken. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        password = generate_password_hash(form.password.data)
        role = form.role.data.lower()
        cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)',
                       (username, password, role))
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'User {username} registered as {role}', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)  # Pass the form to the template

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Create an instance of the login form
    if form.validate_on_submit():
        username = form.username.data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, role FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user[0], form.password.data):  # Check password using hash
            session['username'] = username
            session['role'] = user[1]
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)  # Pass the form to the template

@app.route('/dashboard')
def dashboard():
    course_urls = [
        'https://virtualbuckeet.s3.eu-north-1.amazonaws.com/java_tutorial.pdf',
        'https://virtualbuckeet.s3.eu-north-1.amazonaws.com/mementopython3-english.pdf'
    ]
    role = session.get('role')
    if role == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts')
        posts = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_dashboard.html', posts=posts, course_urls=course_urls)
    elif role == 'student':
        return render_template('student_dashboard.html', posts=[], course_urls=course_urls)
    else:
        flash('Please log in first', 'warning')
        return redirect(url_for('login'))

@app.route('/post', methods=['GET', 'POST'])
def post_content():
    if session.get('role') != 'admin':
        flash('Only admins can post content.', 'danger')
        return redirect(url_for('dashboard'))

    form = PostForm()
    if form.validate_on_submit():
        content = form.content.data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (content) VALUES (%s)', (content,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Content posted successfully', 'success')
        return redirect(url_for('dashboard'))

    return render_template('post_content.html', form=form)

@app.route('/view_posts')
def view_posts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM posts')
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_posts.html', posts=posts)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

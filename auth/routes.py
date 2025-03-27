import logging

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from werkzeug.security import generate_password_hash, check_password_hash

from auth.forms import SignupForm, LoginForm, TaskForm
from db import get_db_connection
from kafka_manager.producer import send_task_event

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        conn = get_db_connection()
        cur = conn.cursor()
        # Check if user/email already exists
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()
        if existing_user:
            flash("Username or email already exists.", "warning")
            logging.warning("Username or email already exists.")
        else:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            conn.commit()
            flash("Signup successful! You can now log in.", "success")
            logging.info(f"Signup successful for user: {username} with email: {email}")
            return redirect(url_for('auth.login'))
        cur.close()
        conn.close()
    return render_template('signup.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user[3], password):  # Assuming password_hash is 4th column
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash("Login successful!", "success")
            logging.info(f"Login successful for user: {user[1]}")
            return redirect(url_for('auth.dashboard'))
        else:
            flash("Invalid username or password", "danger")
            logging.error(f"Invalid username or password {user[1]}")
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    logging.info("You have been logged out.")
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    form = TaskForm()
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        cursor.execute(
            "INSERT INTO tasks (user_id, title, description) VALUES (%s, %s, %s)",
            (user_id, title, description)
        )
        conn.commit()
        logging.info(f"Task created with title: {title} and description: {description} by user: {user_id}")
        send_task_event('created', {
            'user_id': user_id,
            'title': title,
            'description': description
        })
    cursor.execute(
        "SELECT id, title, description, created_at, completed FROM tasks WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', username=session['username'], form=form, tasks=tasks)


@auth_bp.route('/task/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET completed = NOT completed WHERE id = %s AND user_id = %s",
                   (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('auth.dashboard'))


@auth_bp.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
    conn.commit()
    logging.info(f"Task: {task_id} deleted by user: {user_id}")
    send_task_event('deleted', {
        'task_id': task_id,
        'user_id': user_id
    })
    conn.close()
    return redirect(url_for('auth.dashboard'))


@auth_bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, description FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    task = cursor.fetchone()
    if not task:
        flash("Task not found.")
        return redirect(url_for('auth.dashboard'))
    form = TaskForm()
    if request.method == 'POST' and form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        user_id = session['user_id']
        cursor.execute("UPDATE tasks SET title = %s, description = %s WHERE id = %s AND user_id = %s",
                       (title, description, task_id, user_id))
        conn.commit()
        logging.info(f"Task: {task_id} updated to title: {title} and descripton: {description} by user: {user_id}")
        send_task_event('updated', {
            'task_id': task_id,
            'title': title,
            'description': description,
            'user_id': user_id
        })
        conn.close()
        return redirect(url_for('auth.dashboard'))
    # Pre-fill form with existing values
    form.title.data = task[0]
    form.description.data = task[1]
    conn.close()
    return render_template('edit_task.html', form=form, task_id=task_id)

from flask import Flask, render_template, request, redirect, flash
import sqlite3
import joblib
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

# Load the ML Model and feature names
try:
    model = joblib.load('model.joblib')
    feature_names = joblib.load('feature_names.joblib')
    print("✅ Model loaded successfully!")
    print(f"📊 Model expects: {', '.join(feature_names)}")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    print("Please run 'python model.py' first")
    model = None
    feature_names = ['marks', 'attendance', 'study_hours', 'previous_grade']

# Initialize Database
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            marks INTEGER,
            attendance INTEGER DEFAULT 75,
            study_hours INTEGER DEFAULT 3,
            previous_grade INTEGER DEFAULT 60,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database ready!")

init_db()

# Home page - Show all students
@app.route('/')
def home():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()
    conn.close()
    
    # Calculate statistics
    stats = get_statistics()
    return render_template('index.html', students=students, stats=stats)

# Get statistics for dashboard
def get_statistics():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM students")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(marks) FROM students")
    avg_marks = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT MAX(marks) FROM students")
    highest = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM students WHERE marks >= 50")
    passed = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'avg_marks': round(avg_marks, 1),
        'highest': highest,
        'passed': passed,
        'failed': total - passed
    }

# Add new student
@app.route('/add', methods=['POST'])
def add():
    try:
        name = request.form['name'].strip()
        marks = int(request.form['marks'])
        attendance = int(request.form.get('attendance', 75))
        study_hours = int(request.form.get('study_hours', 3))
        previous_grade = int(request.form.get('previous_grade', 60))
        
        # Validation
        if not name:
            flash('❌ Name cannot be empty!', 'error')
            return redirect('/')
        
        if marks < 0 or marks > 100:
            flash('❌ Marks must be between 0 and 100!', 'error')
            return redirect('/')
        
        if attendance < 0 or attendance > 100:
            flash('❌ Attendance must be between 0 and 100!', 'error')
            return redirect('/')
        
        if study_hours < 0 or study_hours > 24:
            flash('❌ Study hours must be between 0 and 24!', 'error')
            return redirect('/')
        
        # Save to database
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (name, marks, attendance, study_hours, previous_grade) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, marks, attendance, study_hours, previous_grade))
        conn.commit()
        conn.close()
        
        flash(f'✅ Student "{name}" added successfully!', 'success')
        
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
    
    return redirect('/')

# Delete student
@app.route('/delete/<int:id>')
def delete(id):
    try:
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        
        # Get student name for message
        cursor.execute("SELECT name FROM students WHERE id=?", (id,))
        student = cursor.fetchone()
        
        if student:
            cursor.execute("DELETE FROM students WHERE id=?", (id,))
            conn.commit()
            flash(f'🗑️ Student "{student[0]}" deleted!', 'info')
        else:
            flash('❌ Student not found!', 'error')
        
        conn.close()
        
    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
    
    return redirect('/')

# Predict using ML model
@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        flash('⚠️ ML Model not loaded! Please run model.py first.', 'error')
        return redirect('/')
    
    try:
        # Get input values
        marks = int(request.form['marks'])
        attendance = int(request.form.get('attendance', 75))
        study_hours = int(request.form.get('study_hours', 3))
        previous_grade = int(request.form.get('previous_grade', 60))
        
        # Validate inputs
        if marks < 0 or marks > 100:
            flash('❌ Marks must be between 0 and 100!', 'error')
            return redirect('/')
        
        # Prepare features for prediction
        features = np.array([[marks, attendance, study_hours, previous_grade]])
        
        # Make prediction
        result = model.predict(features)[0]
        prediction_text = "PASS ✅" if result == 1 else "FAIL ❌"
        
        # Get confidence score
        confidence = None
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(features)[0]
            confidence = max(proba) * 100
        
        # Get all students for display
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY id DESC")
        students = cursor.fetchall()
        conn.close()
        
        stats = get_statistics()
        
        # Show success message
        flash(f'🤖 AI Prediction: {prediction_text}', 'success')
        
        return render_template('index.html', 
                             students=students,
                             stats=stats,
                             prediction=prediction_text,
                             confidence=confidence,
                             marks_input=marks,
                             attendance_input=attendance,
                             study_hours_input=study_hours,
                             previous_grade_input=previous_grade)
    
    except Exception as e:
        flash(f'❌ Prediction error: {str(e)}', 'error')
        return redirect('/')

# Search students
@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE name LIKE ? ORDER BY id DESC", (f'%{query}%',))
    students = cursor.fetchall()
    conn.close()
    
    stats = get_statistics()
    return render_template('index.html', students=students, stats=stats, search_query=query)

# Clear all students
@app.route('/clear_all')
def clear_all():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students")
    conn.commit()
    conn.close()
    
    flash('🗑️ All students have been cleared!', 'warning')
    return redirect('/')

if __name__ == '__main__':
    print("\n🚀 Starting Flask Server...")
    print("📱 Open your browser and go to: http://127.0.0.1:5000")
    print(" Press CTRL+C to stop the server\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
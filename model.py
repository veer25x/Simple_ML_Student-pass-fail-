import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

print("🤖 Training Advanced ML Model for Student Performance...")
print("="*50)

# Generate synthetic training data
np.random.seed(42)

# Create 200 samples with 4 features
n_samples = 200

# Features: [marks, attendance, study_hours, previous_grade]
marks = np.random.normal(65, 20, n_samples).clip(0, 100)
attendance = np.random.normal(75, 15, n_samples).clip(0, 100)
study_hours = np.random.normal(3, 1.5, n_samples).clip(0, 8)
previous_grade = np.random.normal(60, 20, n_samples).clip(0, 100)

# Create target (pass/fail) based on weighted combination
# Marks have highest importance, then study hours
scores = (marks * 0.6) + (attendance * 0.1) + (study_hours * 0.2) + (previous_grade * 0.1)
threshold = 55  # Threshold for passing
y = (scores > threshold).astype(int)

# Create feature matrix
X = np.column_stack([marks, attendance, study_hours, previous_grade])

print(f"📊 Generated {n_samples} training samples")
print(f"📈 Features: Marks, Attendance (%), Study Hours/day, Previous Grade")
print(f"📊 Class distribution:")
print(f"   Pass (1): {sum(y)} samples ({sum(y)/len(y)*100:.1f}%)")
print(f"   Fail (0): {len(y)-sum(y)} samples ({(len(y)-sum(y))/len(y)*100:.1f}%)")

# Split data for testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n✅ Model Accuracy: {accuracy:.2%}")

# Feature importance
feature_importance = model.feature_importances_
features = ['Marks', 'Attendance', 'Study Hours', 'Previous Grade']

print("\n🎯 Feature Importance:")
for feat, imp in zip(features, feature_importance):
    print(f"   {feat}: {imp:.2%}")

# Save model and feature names
joblib.dump(model, 'model.joblib')
joblib.dump(features, 'feature_names.joblib')

print("\n💾 Model saved as 'model.joblib'")
print("💾 Feature names saved as 'feature_names.joblib'")

# Test predictions
print("\n🧪 Test Predictions:")
test_cases = [
    [85, 90, 5, 80],   # Excellent student
    [45, 85, 3, 50],   # Low marks but good attendance
    [30, 40, 1, 35],   # Poor performance
    [70, 75, 2, 65],   # Average student
    [55, 95, 4, 60],   # Good attendance, average marks
]

for i, test in enumerate(test_cases, 1):
    pred = model.predict([test])[0]
    proba = model.predict_proba([test])[0]
    confidence = max(proba) * 100
    result = "PASS ✅" if pred == 1 else "FAIL ❌"
    
    print(f"\n   Case {i}: Marks={test[0]}, Attendance={test[1]}%, Hours={test[2]}, PrevGrade={test[3]}")
    print(f"   → {result} (Confidence: {confidence:.1f}%)")

print("\n✨ Training complete! Now run 'python app.py'")
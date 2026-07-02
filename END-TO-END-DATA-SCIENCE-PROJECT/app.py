from flask import Flask, render_template, request
import joblib
import pandas as pd

app = Flask(__name__)

# Load trained model
model = joblib.load('model/iris_model.joblib')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Get input values from form
    features = [
        float(request.form['sepal_length']),
        float(request.form['sepal_width']),
        float(request.form['petal_length']),
        float(request.form['petal_width'])
    ]
    
    # Create DataFrame with correct feature names
    input_data = pd.DataFrame([features], columns=[
        'sepal length (cm)',
        'sepal width (cm)',
        'petal length (cm)',
        'petal width (cm)'
    ])
    
    # Make prediction
    prediction = model.predict(input_data)[0]
    species = ['Iris-setosa', 'Iris-versicolor', 'Iris-virginica'][prediction]
    
    return render_template('index.html', prediction=species)

if __name__ == '__main__':
    app.run(debug=True)
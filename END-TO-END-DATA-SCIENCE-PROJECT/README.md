# END-TO-END-DATA-SCIENCE-PROJECT

**COMPANY:-** CODTECH IT SOLUTIONS

**NAME:-** LOKANATH SATAPATHY

**INTERN ID:-** CT12WTOK

**DOMAIN:-** DATA SCIENCE

**DURATION:-** 12 NEEEKS

**MENTOR:-** NEELA SANTOSH



# 🌸 Iris Flower Species Classification Project

## 📝 Project Overview
The **Iris Flower Species Classification** project aims to develop a machine learning model that can accurately predict the species of an Iris flower based on its physical features. The model uses four key features:

- Sepal Length  
- Sepal Width  
- Petal Length  
- Petal Width  

The three species to be classified are:

- *Iris Setosa*  
- *Iris Versicolor*  
- *Iris Virginica*

---

## 🎯 Key Objectives

- 🔍 **Data Analysis**: Explore and understand the Iris dataset.
- 🤖 **Model Training**: Implement a Logistic Regression classification model.
- 🌐 **Web Application**: Develop a user-friendly Flask-based web interface.
- ☁️ **Deployment**: Deploy the model to a cloud platform.  
  > ❗ _Note: Hosting on PythonAnywhere is currently pending due to Python version conflicts, but work is ongoing._

---

## 📁 Project Structure


iris-flower-classification/
├── templates/
│   └── index.html        # Web interface
├── model/
│   └── iris\_model.joblib # Trained ML model
├── app.py                # Main Flask app
├── model\_train.py        # Script to train and save the model
├── requirements.txt      # Python dependencies
└── Procfile              # Deployment configuration



## ⚙️ Technical Details

### 1. **Data Preparation**
- Loaded using `sklearn.datasets`.
- Converted to a pandas DataFrame for easy handling.
- Split into training and test sets using `train_test_split`.

### 2. **Model Training**
- Trained using **Logistic Regression**.
- Achieved ~97% accuracy on test data.
- Model saved using `joblib` for use in the Flask application.

### 3. **Flask Web Application**
- Users input the 4 features through an HTML form.
- Model predicts the flower species and displays it on the same page.
- Includes a **color-coded result box** indicating species visually.

### 4. **Deployment**
- Intended to be deployed on **PythonAnywhere**.
- Configuration includes a `Procfile` and uploaded dependencies.
- Hosting in progress (currently encountering Python version mismatch issues).

---

## 🖥️ User Interface

The web interface is clean and user-friendly:
- Users enter measurements via input fields.
- Result is shown with:
  - Predicted species name.
  - A color indicator (e.g., red for *Setosa*, green-blue for *Versicolor*, blue for *Virginica*).

---

## 🧪 Sample Test Cases

| Case | Sepal Length | Sepal Width | Petal Length | Petal Width | Expected Prediction |
|------|---------------|--------------|---------------|--------------|----------------------|
| 1    | 5.1           | 3.5          | 1.4           | 0.2          | Iris-setosa          |
| 2    | 6.7           | 3.0          | 5.2           | 2.3          | Iris-virginica       |

---

## ✅ Conclusion

This project demonstrates:
- ✅ Building a supervised ML model
- ✅ Creating a web interface with Flask
- ✅ Saving and deploying trained models
- ✅ Integrating ML with real-time prediction via a web app

It’s a complete example of taking a data science concept from development to deployment and is an excellent addition to any machine learning or full-stack portfolio.

---

## 📬 Contact

Created by **[Lokanath Satapathy]**  
Feel free to connect or raise issues for suggestions!




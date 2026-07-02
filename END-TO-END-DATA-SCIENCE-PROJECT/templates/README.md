### **File Name: index.html**

#### **Description:**

This HTML file provides the **frontend user interface** for the *Iris Flower Species Predictor* web application. It allows users to input the physical measurements of an iris flower and receive a prediction of its species based on a machine learning model.

#### **Key Features:**

* **User Input Form:**

  * Collects four essential features from the user:

    * Sepal Length (cm)
    * Sepal Width (cm)
    * Petal Length (cm)
    * Petal Width (cm)
  * Inputs use `<input type="number" step="0.1">` for precision.

* **Prediction Display:**

  * After form submission, the predicted species is displayed using Flask’s templating engine (`{{ prediction }}`).
  * Conditional styling shows:

    * **Species name**
    * **Color-coded box** representing the flower's characteristic color:

      * *Iris-setosa:* Red tones (#FF6B6B)
      * *Iris-versicolor:* Blue-green (#4ECDC4)
      * *Iris-virginica:* Deep blue (#45B7D1)

* **Styling:**

  * Clean, readable design using inline CSS.
  * Organized layout for a user-friendly experience.

#### **Technologies Used:**

* HTML5
* CSS
* Jinja2 templating (used in Flask)

#### **Purpose:**

This file serves as the main interface for user interaction in the Iris prediction web app. It connects with the Flask backend (`app.py`) to send input data and receive the prediction result dynamically.


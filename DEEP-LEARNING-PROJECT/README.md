# DEEP-LEARNING-PROJECT

**COMPANY:-** CODTECH IT SOLUTIONS

**NAME:-** LOKANATH SATAPATHY

**INTERN ID:-** CT12WTOK

**DOMAIN:-** DATA SCIENCE

**DURATION:-** 12 NEEEKS

**MENTOR:-** NEELA SANTOSH


# 🧠 Image Classification using PyTorch

This project demonstrates a complete end-to-end **image classification pipeline** using **PyTorch**, built around the **CIFAR-10** dataset. The implementation includes everything from data preprocessing and augmentation to model training, evaluation, and visualization.

---

## 🚀 Project Highlights

### ✅ Features

- **🔄 Data Augmentation**
  - Random cropping and horizontal flipping to improve generalization.

- **🧱 Model Architecture**
  - Custom CNN with:
    - Multiple convolutional blocks
    - Batch Normalization and ReLU activations
    - Dropout layers for regularization

- **🧪 Training Strategy**
  - Optimizer: `Adam`
  - Loss: `CrossEntropyLoss`
  - Scheduler: `ReduceLROnPlateau`
  - Supports GPU acceleration for faster training

- **📊 Evaluation**
  - Tracks training loss and test accuracy
  - Plots learning curves
  - Displays sample predictions with confidence scores

---

## 📚 Technical Details

- **Dataset**: [CIFAR-10](https://www.cs.toronto.edu/~kriz/cifar.html)
  - 10 classes
  - 32x32 color images
- **Model**: Custom CNN achieving ~88% test accuracy
- **Training Configuration**:
  - **Batch Size**: 128
  - **Learning Rate**: 0.001
  - **Epochs**: 25
  - **Data Augmentation**:
    - `transforms.RandomCrop`
    - `transforms.RandomHorizontalFlip`
  - **Normalization**: Using CIFAR-10 mean and std

---

## 💡 Usage

The notebook/script includes:

1. 📥 Data loading and preprocessing
2. 🏗 Model building and training
3. 📈 Performance tracking
4. 🖼 Result visualization
5. 🔍 Prediction analysis with confidence scores

---

## 📦 Requirements

- `torch`
- `torchvision`
- `matplotlib`
- `numpy`
- `tqdm`

Install them using pip:

```bash
pip install torch torchvision matplotlib numpy tqdm
````

---

## 📸 Output Previews

* Training/Validation Loss Curves
* Accuracy per Epoch
* Sample Predictions with Confidence Scores

---

## 🖥 GPU Acceleration

The implementation automatically uses GPU (if available) to accelerate training.


## 📬 Feedback

Feel free to fork, contribute, or open issues for any bugs or suggestions!

---

**Happy Coding! 🚀**

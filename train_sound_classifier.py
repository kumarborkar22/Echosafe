






import os
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib


# Path to sounds folder
dataset_root = 'sounds'

X, y = [], []

for root, dirs, files in os.walk(dataset_root):
    for file in files:
        if file.lower().endswith(('.wav', '.mpeg')):
            file_path = os.path.join(root, file)
            fname = file.lower()
            if 'gunshot' in fname:
                label = 'gunshot'
            elif 'scream' in fname:
                label = 'scream'
            else:
                label = 'unknown'
            try:
                audio, sr = librosa.load(file_path, sr=None)
                mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
                mfcc_mean = np.mean(mfcc, axis=1)
                X.append(mfcc_mean)
                y.append(label)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

X = np.array(X)
y = np.array(y)

if len(X) == 0:
    raise RuntimeError("No .wav or .mpeg files found in sounds folder. Please check your sounds folder structure.")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train classifier
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(clf, 'sound_classifier.pkl')
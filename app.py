from flask import Flask, render_template, jsonify, request
import sounddevice as sd
import numpy as np
import threading
import librosa
import joblib
import smtplib
from email.mime.text import MIMEText
import time
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)

@app.route("/upload_audio", methods=["POST"])
@app.route("/upload", methods=["POST"])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    import traceback
    try:
        # Read file into memory buffer
        audio_bytes = file.read()
        # Try soundfile first
        import soundfile as sf
        try:
            audio, sr = sf.read(io.BytesIO(audio_bytes))
        except Exception as sf_err:
            tb = traceback.format_exc()
            print(f"soundfile failed: {sf_err}. Trying librosa...\n{tb}")
            try:
                # librosa.load can handle more formats if ffmpeg is installed
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.'+filename.split('.')[-1]) as tmp:
                    tmp.write(audio_bytes)
                    tmp.flush()
                    audio, sr = librosa.load(tmp.name, sr=None, mono=True)
            except Exception as lb_err:
                tb2 = traceback.format_exc()
                print(f"librosa also failed: {lb_err}\n{tb2}")
                return jsonify({'status': 'error', 'message': f'librosa error: {lb_err}', 'traceback': tb2}), 500
        # If stereo, convert to mono
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        mfcc = librosa.feature.mfcc(y=audio.astype(np.float32), sr=sr, n_mfcc=N_MFCC, n_fft=BLOCK_SIZE)
        mfcc_mean = np.mean(mfcc, axis=1).reshape(1, -1)
        result = "Normal"
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(mfcc_mean)[0]
            classes = model.classes_
            max_idx = np.argmax(proba)
            pred = classes[max_idx]
            confidence = proba[max_idx]
            if pred == "gunshot" and confidence > 0.6:
                result = "Alert: Gunshot detected"
            elif pred == "scream" and confidence > 0.6:
                result = "Alert: Scream detected"
            else:
                result = "Alert: Unclassified loud sound detected"
        else:
            pred = model.predict(mfcc_mean)[0]
            if pred == "gunshot":
                result = "Alert: Gunshot detected"
            elif pred == "scream":
                result = "Alert: Scream detected"
            else:
                result = "Alert: Unclassified loud sound detected"
        return jsonify({'status': 'ok', 'result': result})
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error processing uploaded file: {e}\n{tb}")
        return jsonify({'status': 'error', 'message': f'Error processing file: {e}', 'traceback': tb}), 500


app = Flask(__name__)

# @app.route("/test_email", methods=["POST"])
# def test_email():
#     global registered_email
#     if not registered_email:
#         return "No registered email. Please register first.", 400
#     send_alert_email("Test Alert: This is a test email from your sound detection system.")
#     return "Test email sent (if no error). Check your inbox and spam folder.", 200

# Load trained sound classifier
model = joblib.load('sound_classifier.pkl')
SAMPLE_RATE = 16000
BLOCK_SIZE = 4096  # Larger block for better feature extraction
THRESHOLD = 0.5  # Not used for classification now

# For MFCC extraction
N_MFCC = 13


current_level = 0
alert_status = "Normal"
registered_email = None
last_alert_sent = None
last_email_time = 0

# Parameters for audio
SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
THRESHOLD = 0.5  # Placeholder threshold for alert



def send_alert_email(alert_msg):
    global registered_email, last_alert_sent, last_email_time
    # Fallback: set registered_email if not set (for testing)
    if not registered_email:
        registered_email = 'kumarborkar403@gmail.com'  # Replace with your test email
        print("No registered email found. Using fallback email.")
    now = time.time()
    # Only send email if cooldown has passed (10 seconds)
    if now - last_email_time < 10:
        print("Email cooldown active. Not sending email.")
        return
    try:
        # Configure your SMTP server here
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_user = 'kumarborkar403@gmail.com'  # Replace with your email
        smtp_pass = 'nipr xsja cuci fakx'     # Replace with your app password
        msg = MIMEText(f"Distress Alert: {alert_msg}")
        msg['Subject'] = 'Distress Sound Alert'
        msg['From'] = smtp_user
        msg['To'] = registered_email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [registered_email], msg.as_string())
        server.quit()
        last_alert_sent = alert_msg
        last_email_time = now
        print(f"Alert email sent to {registered_email} with message: {alert_msg}")
    except Exception as e:
        print("Email error:", e)

def audio_callback(indata, frames, time, status):
    global current_level, alert_status
    # Flatten audio data
    audio = indata.flatten()
    # Calculate RMS for UI (optional)
    rms = np.sqrt(np.mean(audio**2))
    current_level = float(min(rms * 10, 1.0))
    try:
        mfcc = librosa.feature.mfcc(y=audio.astype(np.float32), sr=SAMPLE_RATE, n_mfcc=N_MFCC, n_fft=BLOCK_SIZE)
        mfcc_mean = np.mean(mfcc, axis=1).reshape(1, -1)
        alert_triggered = False
        alert_type = None
        model_confident = False

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(mfcc_mean)[0]
            classes = model.classes_
            max_idx = np.argmax(proba)
            pred = classes[max_idx]
            confidence = proba[max_idx]
            if pred == "gunshot" and confidence > 0.6:
                alert_triggered = True
                alert_type = "Alert: Gunshot detected"
                model_confident = True
            elif pred == "scream" and confidence > 0.6:
                alert_triggered = True
                alert_type = "Alert: Scream detected"
                model_confident = True
        else:
            pred = model.predict(mfcc_mean)[0]
            if pred == "gunshot":
                alert_triggered = True
                alert_type = "Alert: Gunshot detected"
                model_confident = True
            elif pred == "scream":
                alert_triggered = True
                alert_type = "Alert: Scream detected"
                model_confident = True

        # Only use fallback if model is NOT confident and loudness is high
        if not model_confident and current_level > 0.5:
            alert_triggered = True
            alert_type = "Alert: Unclassified loud sound detected"

        if alert_triggered and alert_type:
            alert_status = alert_type
            send_alert_email(alert_status)
        else:
            alert_status = "Normal"
    except Exception:
        alert_status = "Normal"

@app.route("/register_email", methods=["POST"])
def register_email():
    global registered_email
    email = request.form.get("email")
    if email:
        registered_email = email
        return "Email registered!", 200
    return "No email provided", 400



def start_audio_stream():
    with sd.InputStream(channels=1, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, callback=audio_callback):
        threading.Event().wait()  # Keep thread alive


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/status")
def status():
    return jsonify({"level": current_level, "status": alert_status})


def run_audio_thread():
    audio_thread = threading.Thread(target=start_audio_stream, daemon=True)
    audio_thread.start()


if __name__ == "__main__":
    run_audio_thread()
    app.run(debug=False)  # Disable debug mode to reduce terminal output

import cv2
import numpy as np
import mss
import easyocr
import pyperclip
from pynput import keyboard

# ----------------------------
# CONFIGURACIÓN ROI (AJUSTAR)
# ----------------------------
ROI = {
    "left": 20,
    "top": 520,
    "width": 320,
    "height": 200
}

# OCR reader (carga una vez, es pesado)
reader = easyocr.Reader(['en'], gpu=False)

# ----------------------------
# CAPTURA DE PANTALLA
# ----------------------------
def capture_region():
    with mss.mss() as sct:
        img = sct.grab(ROI)
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

# ----------------------------
# PREPROCESADO
# ----------------------------
def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # upscale (MUY importante para tu caso)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # mejora contraste
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # threshold
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return th

# ----------------------------
# LIMPIEZA DE TEXTO
# ----------------------------
def clean_text(text):
    text = text.upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(c for c in text if c in allowed)

# ----------------------------
# PIPELINE OCR
# ----------------------------
def process():
    img = capture_region()
    proc = preprocess(img)

    # OCR
    result = reader.readtext(proc, detail=0)

    if not result:
        print("No se detectó texto")
        return

    raw_text = "".join(result)
    final_text = clean_text(raw_text)

    if final_text:
        pyperclip.copy(final_text)
        print("Patente detectada:", final_text)
    else:
        print("Texto vacío tras limpieza")

# ----------------------------
# HOTKEY LISTENER
# ----------------------------
def on_press(key):
    try:
        if key == keyboard.Key.f8:
            process()
    except:
        pass

print("Sistema activo. Presioná F8 para capturar.")
print("Ctrl+C para salir.")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

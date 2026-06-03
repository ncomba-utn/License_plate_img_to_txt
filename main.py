import cv2
import numpy as np
import mss
import easyocr
import pyperclip
import pyautogui
import time
from pynput import keyboard, mouse

ROI = {
    "left": 20,
    "top": 520,
    "width": 320,
    "height": 200
}

pos_casilla = None
pos_lupa = None
puntos_calibracion = []
controlador_mouse = mouse.Controller()

pyautogui.PAUSE = 0.1

print("Cargando el motor OCR... Espere un momento.")
reader = easyocr.Reader(['en'], gpu=False)

def capture_region():
    with mss.mss() as sct:
        img = sct.grab(ROI)
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    kernel = np.ones((2, 2), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)
    return th

def clean_text(text):
    text = text.upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(c for c in text if c in allowed)

def process():
    global pos_casilla, pos_lupa

    if pos_casilla is None or pos_lupa is None:
        print("❌ ERROR: Primero debés calibrar la casilla y la lupa con F9.")
        return

    img = capture_region()
    proc = preprocess(img)

    result = reader.readtext(
        proc, 
        detail=0, 
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        paragraph=False
    )

    if not result:
        print("No se detectó texto")
        return

    raw_text = "".join(result).replace(" ", "")
    final_text = clean_text(raw_text)

    if final_text:
        pyperclip.copy(final_text)
        print("Patente detectada:", final_text)

        pyautogui.moveTo(pos_casilla[0], pos_casilla[1])
        pyautogui.click()

        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')

        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.08)

        pyautogui.moveTo(pos_lupa[0], pos_lupa[1])
        pyautogui.click()
        print("🚀 Pegado y búsqueda ejecutada.")

    else:
        print("Texto vacío tras limpieza")

def calibrar_sistema():
    global ROI, pos_casilla, pos_lupa
    pos_actual = controlador_mouse.position
    puntos_calibracion.append(pos_actual)

    paso = len(puntos_calibracion)

    if paso == 1:
        print(f"\n📌 [1/4] Esquina SUP. IZQUIERDA guardada en: {pos_actual}")
        print("👉 Mové el mouse a la esquina INFERIOR DERECHA de la patente y presioná F9.")
    elif paso == 2:
        print(f"📌 [2/4] Esquina INF. DERECHA guardada en: {pos_actual}")
        print("👉 Mové el mouse al CENTRO DE LA CASILLA DE TEXTO blanca y presioná F9.")
    elif paso == 3:
        pos_casilla = pos_actual
        print(f"📌 [3/4] Ubicación de la CASILLA guardada en: {pos_casilla}")
        print("👉 Mové el mouse arriba del BOTÓN DE LA LUPA negra y presioná F9.")
    elif paso == 4:
        pos_lupa = pos_actual
        print(f"📌 [4/4] Ubicación de la LUPA guardada en: {pos_lupa}")

        x1, y1 = puntos_calibracion[0]
        x2, y2 = puntos_calibracion[1]
        ROI["left"] = min(x1, x2)
        ROI["top"] = min(y1, y2)
        ROI["width"] = abs(x2 - x1)
        ROI["height"] = abs(y2 - y1)

        print("\n" + "="*40)
        print("✅ ¡SISTEMA CALIBRADO Y LISTO!")
        print("="*40)
        print(f"• Zona de captura: {ROI}")
        print(f"• Clic en Casilla: {pos_casilla}")
        print(f"• Clic en Lupa:    {pos_lupa}")
        print("\nYa podés usar F10 tranquilamente.")
        print("="*40)

        puntos_calibracion.clear()

def on_press(key):
    try:
        if key == keyboard.Key.f9:
            calibrar_sistema()
        elif key == keyboard.Key.f10:
            process()
    except Exception as e:
        print(f"Error en listener: {e}")

print("\n" + "="*50)
print("🚀 AUTOMATIZADOR COMPLETO ACTIVO")
print("="*50)
print("PASOS PARA CALIBRAR (Presioná F9 en cada uno):")
print(" 1. Esquina superior izquierda de la patente.")
print(" 2. Esquina inferior derecha de la patente.")
print(" 3. Centro del cuadro blanco de texto.")
print(" 4. Centro del botón negro de la lupa.")
print("--------------------------------------------------")
print("• F10: Captura, pega y busca.")
print("• Ctrl+C en consola: Salir.")
print("="*50 + "\n")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

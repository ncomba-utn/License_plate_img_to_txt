import cv2
import numpy as np
import mss
import easyocr
import pyperclip
import pyautogui
import time
import json
import os
import re  # <-- Importamos expresiones regulares para validar el formato
from pynput import keyboard, mouse

CONFIG_FILE = "calibracion.json"

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

def guardar_configuracion():
    config = {
        "ROI": ROI,
        "pos_casilla": pos_casilla,
        "pos_lupa": pos_lupa
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print("\n💾 Calibración guardada automáticamente en:", CONFIG_FILE)

def cargar_configuracion():
    global ROI, pos_casilla, pos_lupa
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            ROI = config["ROI"]
            pos_casilla = config["pos_casilla"]
            pos_lupa = config["pos_lupa"]
            print("\n✅ Calibración previa cargada con éxito.")
            print(f"• Zona de captura: {ROI}")
            print(f"• Clic en Casilla: {pos_casilla}")
            print(f"• Clic en Lupa:    {pos_lupa}")
            print("Ya podés usar F10 directamente sin calibrar.")
        except Exception as e:
            print(f"\n⚠️ No se pudo cargar el archivo de calibración: {e}")
    else:
        print("\nℹ️ No se encontró calibración previa. Por favor, calibrá el sistema con F9.")

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

def es_patente_valida(texto):
    """
    Valida si el texto cumple con:
    - Formato viejo: 3 letras y 3 números (Ej: ABC123)
    - Formato Mercosur: 2 letras, 3 números y 2 letras (Ej: AB123CD)
    """
    patron_viejo = r"^[A-Z]{3}\d{3}$"
    patron_mercosur = r"^[A-Z]{2}\d{3}[A-Z]{2}$"
    
    if re.match(patron_viejo, texto) or re.match(patron_mercosur, texto):
        return True
    return False

def process():
    global pos_casilla, pos_lupa
    
    if pos_casilla is None or pos_lupa is None:
        print("❌ ERROR: Primero debés calibrar la casilla y la lupa con F9.")
        return

    intentos_maximos = 20
    patente_final = None
    mejor_texto_alternativo = ""

    print("\n🔍 Iniciando lectura de patente (Máx. 20 intentos)...")
    
    for intento in range(1, intentos_maximos + 1):
        img = capture_region()
        proc = preprocess(img)

        result = reader.readtext(
            proc, 
            detail=0, 
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            paragraph=False
        )

        if result:
            raw_text = "".join(result).replace(" ", "")
            final_text = clean_text(raw_text)

            # 1. Si el formato es perfecto, se corta el bucle inmediatamente
            if es_patente_valida(final_text):
                patente_final = final_text
                print(f"✅ ¡Patente perfecta detectada en el intento {intento}!: {patente_final}")
                break
            
            # 2. Si no es perfecto, evaluamos si es el "más cercano" por cantidad de caracteres (6 o 7)
            else:
                print(f"⚠️ Intento {intento}/{intentos_maximos}: Formato incorrecto ({final_text if final_text else 'Vacío'}).")
                
                # Guardamos este texto como alternativa si se acerca más al largo de una patente real
                if len(final_text) in [6, 7]:
                    mejor_texto_alternativo = final_text
                elif len(final_text) > len(mejor_texto_alternativo):
                    # Respaldo en caso de que no haya de 6 o 7, elegimos el que tenga más caracteres detectados
                    mejor_texto_alternativo = final_text
        else:
            print(f"⚠️ Intento {intento}/{intentos_maximos}: No se detectó texto.")
        
        time.sleep(0.05)

    # Si salimos del bucle sin la patente perfecta, usamos el mejor intento registrado
    if not patente_final and mejor_texto_alternativo:
        patente_final = mejor_texto_alternativo
        print(f"🧡 No se encontró formato exacto. Usando el intento más cercano: {patente_final}")

    # Si logramos definir un texto para procesar (sea perfecto o el más cercano)
    if patente_final:
        pyperclip.copy(patente_final)
        
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
        print(f"❌ ERROR: Se alcanzaron los {intentos_maximos} intentos y las capturas fueron completamente ilegibles (Vacías).")

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
        
        guardar_configuracion()
        
        print("\nYa podés usar F10 tranquilamente.")
        print("="*40)
        
        puntos_calibracion.clear()

def on_press(key):
    try:
        if key == keyboard.Key.f9:
            calibrar_sistema()
        elif key == keyboard.Key.f10:  # <-- Mantenemos F10 asignada a la acción del script
            process()
    except Exception as e:
        print(f"Error en listener: {e}")

print("\n" + "="*50)
print("🚀 AUTOMATIZADOR COMPLETO ACTIVO")
print("="*50)

cargar_configuracion()

print("--------------------------------------------------")
print("SI NECESITÁS RE-CALIBRAR (Presioná F9 en cada uno):")
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

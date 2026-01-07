import cv2
import pandas as pd
from pyzbar import pyzbar
import json
from datetime import datetime

CSV_PATH = "produtos_br.csv"
JSON_PATH = "leituras.json"

df = pd.read_csv(CSV_PATH, usecols=["code", "product_name", "brands"], dtype=str)
df["code"] = df["code"].astype(str).str.strip()

try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        leituras = json.load(f)
except FileNotFoundError:
    leituras = []

def salvar_leitura(codigo, nome, marca):
    entrada = {
        "codigo": codigo,
        "produto": nome or "",
        "marca": marca or "",
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    leituras.append(entrada)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(leituras, f, indent=2, ensure_ascii=False)

def ler_codigos(frame):
    """Tenta ler códigos tanto na imagem normal quanto espelhada."""
    codigos = pyzbar.decode(frame)
    if not codigos:
        invertido = cv2.flip(frame, 1)  # espelha horizontalmente
        codigos = pyzbar.decode(invertido)
    return codigos

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Erro ao abrir a câmera.")
    exit()

ultimo_codigo = None
print("Aponte a câmera para um código de barras (frontal ou traseira). Pressione Q para sair.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # espelha visualmente (para parecer um espelho)
    barcodes = ler_codigos(frame)

    for barcode in barcodes:
        codigo = barcode.data.decode("utf-8").strip()
        if codigo != ultimo_codigo:
            ultimo_codigo = codigo
            produto = df.loc[df["code"] == codigo]

            if not produto.empty:
                nome = produto.iloc[0]["product_name"]
                marca = produto.iloc[0]["brands"]
                print(f"\nCódigo detectado: {codigo}")
                print(f"Produto: {nome or '(sem nome)'}")
                print(f"Marca: {marca or '(sem marca)'}")
                resposta = input("É esse mesmo? (s/n): ").strip().lower()
                if resposta == "s":
                    salvar_leitura(codigo, nome, marca)
                    print("Produto salvo no JSON.\n")
                else:
                    print("Produto ignorado.\n")
            else:
                print(f"\nCódigo {codigo} não encontrado no dataset.\n")

        x, y, w, h = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, codigo, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Leitor de Codigos", frame)

    if cv2.waitKey(1) & 0xFF in [ord("q"), 27]:
        break

cap.release()
cv2.destroyAllWindows()

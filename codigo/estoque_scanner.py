import cv2
import pandas as pd
from pyzbar import pyzbar
import json
import os

CSV_PATH = "produtos_br.csv"
ESTOQUE_PATH = "estoque.json"

# Carrega o CSV de produtos
df = pd.read_csv(CSV_PATH, usecols=["code", "product_name", "brands"], dtype=str)
df["code"] = df["code"].astype(str).str.strip()

# Carrega ou cria o estoque (com tratamento para arquivo vazio/corrompido)
def carregar_estoque():
    if not os.path.exists(ESTOQUE_PATH):
        return {}
    try:
        with open(ESTOQUE_PATH, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if not conteudo:  # arquivo vazio
                return {}
            return json.loads(conteudo)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

estoque = carregar_estoque()

def salvar_estoque():
    with open(ESTOQUE_PATH, "w", encoding="utf-8") as f:
        json.dump(estoque, f, indent=2, ensure_ascii=False)

def adicionar_ao_estoque(codigo, nome, marca):
    if codigo in estoque:
        estoque[codigo]["quantidade"] += 1
    else:
        estoque[codigo] = {
            "produto": nome or "(sem nome)",
            "marca": marca or "(sem marca)",
            "quantidade": 1
        }
    salvar_estoque()

def mostrar_estoque():
    print("\n--- ESTOQUE ATUAL ---")
    if not estoque:
        print("Estoque vazio.")
    else:
        for codigo, dados in estoque.items():
            print(f"{codigo} | {dados['produto']} | {dados['marca']} | Qtd: {dados['quantidade']}")
    print("---------------------\n")

def ler_codigos(frame):
    codigos = pyzbar.decode(frame)
    if not codigos:
        invertido = cv2.flip(frame, 1)
        codigos = pyzbar.decode(invertido)
    return codigos

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Erro ao abrir a camera.")
    exit()

ultimo_codigo = None
print("Comandos: E = ver estoque | Q = sair")
print("Aponte a camera para um codigo de barras.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    barcodes = ler_codigos(frame)

    for barcode in barcodes:
        codigo = barcode.data.decode("utf-8").strip()
        if codigo != ultimo_codigo:
            ultimo_codigo = codigo
            produto = df.loc[df["code"] == codigo]

            if not produto.empty:
                nome = produto.iloc[0]["product_name"]
                marca = produto.iloc[0]["brands"]
                print(f"Codigo: {codigo}")
                print(f"Produto: {nome or '(sem nome)'}")
                print(f"Marca: {marca or '(sem marca)'}")
                resposta = input("Adicionar ao estoque? (s/n): ").strip().lower()
                if resposta == "s":
                    adicionar_ao_estoque(codigo, nome, marca)
                    qtd = estoque[codigo]["quantidade"]
                    print(f"Adicionado. Quantidade em estoque: {qtd}\n")
                else:
                    print("Ignorado.\n")
            else:
                print(f"Codigo {codigo} nao encontrado no dataset.\n")

        x, y, w, h = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, codigo, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Scanner de Estoque", frame)

    tecla = cv2.waitKey(1) & 0xFF
    if tecla in [ord("q"), 27]:
        break
    elif tecla == ord("e"):
        mostrar_estoque()

cap.release()
cv2.destroyAllWindows()

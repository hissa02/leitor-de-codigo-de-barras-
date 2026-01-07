#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from enum import Enum

import cv2  # OpenCV: a biblioteca que mexe com a imagem (filtros, cores, etc)
import numpy as np # Biblioteca para cálculos matemáticos e matrizes
from PIL import Image
from pyzbar import pyzbar # O "cérebro" que realmente identifica o código de barras
from pyzbar.pyzbar import ZBarSymbol

# Aqui eu defini todos os tipos de códigos que o programa consegue entender
class BarcodeType(Enum):
    EAN13 = "EAN-13"
    EAN8 = "EAN-8"
    UPCA = "UPC-A"
    # ... (outros tipos como QR Code, Data Matrix, etc)
    UNKNOWN = "Unknown"

# Criei essa "caixinha" (dataclass) para guardar os dados de cada código achado
@dataclass
class DetectedCode:
    type: str                # Tipo do código (ex: QR Code)
    data: str                # O que está escrito no código
    confidence: float        # O quanto o programa tem certeza do que leu (0 a 1)
    bounding_box: Tuple[int, int, int, int] # Onde o código está na foto (x, y, largura, altura)
    polygon: List[Tuple[int, int]]          # O desenho exato do código (os 4 cantos)
    processing_time_ms: float               # Quanto tempo demorou pra processar
    
    def to_dict(self) -> dict:
        return asdict(self)

class BarcodeScanner:
    # Dicionário para converter o nome que o ZBar dá para o nome que eu defini
    ZBAR_TYPE_MAP = {
        'EAN13': BarcodeType.EAN13,
        'QRCODE': BarcodeType.QRCODE,
        # ... (mapeamento completo)
    }
    
    def __init__(self, enhance_image: bool = True):
        self.enhance_image = enhance_image # Se True, ele tenta melhorar a imagem se falhar de primeira
        self.supported_types = list(BarcodeType)
        
    def _preprocess_image(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Aqui é o segredo: eu crio várias versões da mesma imagem para facilitar a leitura.
        """
        processed_images = []
        # Converte pra cinza (preto e branco) porque cor não importa pro código de barras
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        processed_images.append(gray) # Versão 1: Cinza normal
        
        if not self.enhance_image:
            return processed_images
            
        # Versão 2: Aumenta o contraste (Equalização de Histograma)
        equalized = cv2.equalizeHist(gray)
        processed_images.append(equalized)
        
        # Versão 3: Filtro CLAHE (ajusta o brilho em partes específicas da foto)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        processed_images.append(clahe.apply(gray))
        
        # Versão 4: Limiarização (deixa a imagem só PRETO e BRANCO puro, sem cinza)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(otsu)
        
        # Versão 5: Sharpened (deixa a imagem mais "afiada"/nítida)
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        processed_images.append(cv2.filter2D(gray, -1, kernel))
        
        return processed_images
    
    def _scan_array(self, image: np.ndarray, start_time: float) -> List[DetectedCode]:
        """
        A lógica principal: roda os filtros e tenta ler em cada um deles.
        """
        detected_codes = []
        seen_data = set() # Pra não repetir o mesmo código se ele for achado em dois filtros
        
        processed_images = self._preprocess_image(image)
        
        for proc_img in processed_images:
            barcodes = pyzbar.decode(proc_img) # Tenta ler
            
            for barcode in barcodes:
                data = barcode.data.decode('utf-8', errors='replace')
                code_key = f"{barcode.type}:{data}"
                
                if code_key in seen_data:
                    continue # Já li esse aqui, pula pro próximo
                
                seen_data.add(code_key)
                
                # Calcula o nível de confiança baseado no contraste e formato
                confidence = self._estimate_confidence(barcode, proc_img)
                
                # Monta o objeto com os resultados
                rect = barcode.rect
                detected = DetectedCode(
                    type=self._map_barcode_type(barcode.type).value,
                    data=data,
                    confidence=confidence,
                    bounding_box=(rect.left, rect.top, rect.width, rect.height),
                    polygon=[(p.x, p.y) for p in barcode.polygon],
                    processing_time_ms=0
                )
                detected_codes.append(detected)
                
        # Calcula o tempo total que levou
        total_time_ms = (time.perf_counter() - start_time) * 1000
        for code in detected_codes:
            code.processing_time_ms = total_time_ms
            
        return detected_codes

    def draw_detections(self, image_path: str, output_path: str, detections: List[DetectedCode]):
        """
        Desenha um retângulo verde e o texto em cima do código na imagem original.
        """
        image = cv2.imread(image_path)
        for detection in detections:
            # Desenha o contorno verde
            pts = np.array(detection.polygon, dtype=np.int32)
            cv2.polylines(image, [pts], True, (0, 255, 0), 2)
            
            # Escreve o que foi lido
            label = f"{detection.type}: {detection.data[:30]}"
            cv2.putText(image, label, (detection.bounding_box[0], detection.bounding_box[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imwrite(output_path, image) # Salva a foto com os desenhos

def run_scanner_demo():
    """
    Função de teste: Varre as pastas de exemplo e mostra os resultados no console.
    """
    print("Iniciando demonstração do scanner...")
    scanner = BarcodeScanner(enhance_image=True)
    
    # Define as pastas de entrada e saída
    dataset_dir = Path(__file__).parent / "dataset"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # ... (lógica para ler arquivos das pastas 'barcodes' e 'qrcodes')
    # No final, ele imprime um resumo de quantos códigos achou e a taxa de sucesso.
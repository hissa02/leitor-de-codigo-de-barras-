# Leitor de Código de Barras

Sistema web para leitura de códigos de barras e QR Codes usando a câmera do celular ou computador.

## Acesse Online

**https://hissa02.github.io/leitor-de-codigo-de-barras-/**

## Funcionalidades

- Leitura de códigos de barras (EAN-13, EAN-8, UPC)
- Leitura de QR Codes
- Controle de zoom da câmera
- Cadastro de produtos não encontrados
- Controle de estoque com quantidade
- Histórico de leituras
- Exportar dados em JSON

## Como Rodar Localmente

### Pré-requisitos

- Python instalado (qualquer versão)

### Passo a Passo

1. Baixe ou clone o repositório:
```bash
git clone https://github.com/hissa02/leitor-de-codigo-de-barras-.git
```

2. Entre na pasta do projeto:
```bash
cd leitor-de-codigo-de-barras-
```

3. Inicie o servidor local:
```bash
python -m http.server 8000 --bind 127.0.0.1
```

4. Abra no navegador:
```
http://127.0.0.1:8000
```

## Bibliotecas Utilizadas

- **Quagga2** - Leitura de códigos de barras
- **jsQR** - Leitura de QR Codes
- **OpenCV.js** - Processamento de imagem
- **PapaParse** - Leitura do arquivo CSV

## Arquivos

- `index.html` - Aplicação principal
- `produtos_br.csv` - Base de dados de produtos

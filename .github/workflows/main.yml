name: S&P 100 Live Radar

on:
  workflow_dispatch:
  schedule:
    - cron: "0 16 * * 1-5"

permissions:
  contents: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install yfinance requests pandas lxml html5lib

      - name: Run 10 Cycles of 10 Stocks
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          # Limpiar progreso anterior para iniciar carga fresca
          rm -f progreso.json
          
          for i in {1..10}
          do
            echo "Iniciando ciclo $i de 10..."
            python agente.py
            
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add index.html progreso.json
            git commit -m "chore: live update batch $i" || echo "No hay cambios"
            git push --force origin HEAD:main
            
            echo "Esperando 90 segundos para que GitHub Pages se actualice..."
            sleep 90
          done

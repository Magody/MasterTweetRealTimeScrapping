import asyncio
import csv
import time
import os
from datetime import datetime
from configparser import ConfigParser
from random import randint
import threading

import torch
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

# Librería para análisis de sentimientos
from transformers import pipeline

from twikit import Client, TooManyRequests

keywords = [
    "Presidente Daniel Noboa",
    "@DanielNoboaOk",
    "#DanielNoboa"
]


# Usar la extension edit cookies y luego el script 00_cookies.py
CSV_FILENAME = 'tweets_noboa.csv'
COOKIES_FILENAME = 'cookies.json'

# =======================================
# CONFIG: LEE NUESTRAS CREDENCIALES
# =======================================
config = ConfigParser()
config.read('config.ini')

if 'X' in config:
    username = config['X'].get('username')
    email = config['X'].get('email')
    password = config['X'].get('password')
else:
    raise ValueError(
        "Archivo config.ini mal configurado. "
        "Asegúrate de incluir la sección [X] con username, email y password."
    )


async def recolectar_tweets():
    """
    Recolecta tweets en tiempo real para múltiples palabras clave.
    - Alterna entre palabras clave en un bucle infinito.
    - Evita duplicados almacenando los tweet_id ya procesados.
    - Repite periódicamente para actualizar las búsquedas.
    """
    client = Client(language='es-MX')

    # Verificar si ya hay cookies guardadas
    try:
        client.load_cookies(COOKIES_FILENAME)
        print("Cookies cargadas correctamente.")
    except FileNotFoundError:
        print("No se encontraron cookies. Iniciando sesión...")
        await client.login(auth_info_1=username, auth_info_2=email, password=password)
        client.save_cookies(COOKIES_FILENAME)
        print(f"Cookies guardadas en '{COOKIES_FILENAME}'.")

    existing_tweet_ids = set()  # Conjunto para almacenar IDs únicos de tweets ya procesados

    # Verificar si el archivo CSV ya existe
    file_exists = os.path.isfile(CSV_FILENAME)
    if file_exists:
        with open(CSV_FILENAME, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_tweet_ids.add(row['tweet_id'])  # Cargar IDs existentes para evitar duplicados

    # Abrir el archivo CSV para escritura (modo append)
    with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Escribir encabezados si el archivo no existe
        if not file_exists:
            writer.writerow([
                "tweet_id",
                "username",
                "user_id",
                "text",
                "created_at",
                "retweet_count",
                "favorite_count"
            ])

        # Bucle principal: alterna entre las palabras clave
        while True:
            for keyword in keywords:
                print(f"\n=== Obteniendo tweets para: '{keyword}' ===")
                total_encontrados = 0
                tweets_paginator = None  # Reiniciar la paginación para cada palabra clave

                while True:  # Bucle de paginación
                    try:
                        # Primera búsqueda o siguiente página
                        if tweets_paginator is None:
                            tweets_paginator = await client.search_tweet(
                                query=keyword,
                                product='Latest'  # Buscar los tweets más recientes
                            )
                        else:
                            # Retardo para evitar bloqueos por exceso de solicitudes
                            wait_time = randint(4, 10)
                            print(f"Esperando {wait_time} segundos antes de la siguiente página...")
                            time.sleep(wait_time)

                            tweets_paginator = await tweets_paginator.next()

                        # Si no hay más tweets, salir del bucle de paginación
                        if not tweets_paginator:
                            print(f"No hay más tweets para '{keyword}'.")
                            break

                        # Procesar los tweets devueltos en esta página
                        for tweet in tweets_paginator:
                            # Evitar duplicados
                            if tweet.id not in existing_tweet_ids:
                                # Escribir el tweet en el archivo CSV
                                writer.writerow([
                                    tweet.id,
                                    tweet.user.name,
                                    tweet.user.id,
                                    tweet.text.replace('\n', ' ').strip(),
                                    tweet.created_at,
                                    tweet.retweet_count,
                                    tweet.favorite_count
                                ])
                                # Agregar el ID del tweet al conjunto
                                existing_tweet_ids.add(tweet.id)
                                total_encontrados += 1

                    except TooManyRequests as e:
                        # Manejar el límite de solicitudes
                        rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
                        print(f"Se alcanzó el límite de solicitudes. Esperando hasta {rate_limit_reset}...")
                        wait_time = rate_limit_reset - datetime.now()
                        seconds_to_wait = max(wait_time.total_seconds(), 0)
                        time.sleep(seconds_to_wait)
                        continue  # Reintentar después de esperar

                    except Exception as e:
                        print(f"Error al procesar tweets: {e}")
                        break

                print(f"Se guardaron {total_encontrados} tweets nuevos para '{keyword}'.")

                # Retardo entre búsquedas de diferentes palabras clave
                time.sleep(30)  # Ajusta este tiempo según tus necesidades


device = 0 if torch.cuda.is_available() else -1
print(f"Device (sentiment model): {device}")
modelo_sentimiento = pipeline(
    "sentiment-analysis", 
    model="nlptown/bert-base-multilingual-uncased-sentiment", 
    device=device
)

def analizar_sentimiento_avanzado(texto):
    try:
        resultado = modelo_sentimiento(texto[:512])
        # La etiqueta es '1 star', '2 stars', '3 stars', '4 stars', '5 stars'
        etiqueta = int(resultado[0]['label'].lower().split()[0])
        if etiqueta > 3:
            return "positivo"
        elif etiqueta < 3:
            return "negativo"
        else:
            return "neutral"
    except Exception as e:
        print(f"Error al procesar el texto: {texto} - {e}")
        return "error"

# LEER CSV, ANALIZAR Y GRAFICAR
procesados_ids = set()

def loop_analisis_y_graficacion():
    """
    Bucle infinito que:
      1) Lee el CSV (tweets_noboa.csv).
      2) Aplica el análisis de sentimiento solo a los tweets nuevos.
      3) Guarda los resultados en el CSV.
      4) Cuenta los resultados y actualiza la gráfica en tiempo real.
      5) Espera unos segundos y repite.
    """
    CSV_TWEETS = "tweets_noboa.csv"
    CSV_SENTIMIENTO = "tweets_sentimiento.csv"
    plt.ion()  # Modo interactivo ON para refrescar la misma ventana
    fig = plt.figure(figsize=(12, 8))
    gs = GridSpec(2, 1, height_ratios=[2, 1], figure=fig)

    ax1 = fig.add_subplot(gs[0])  # Gráfica de barras (sentimientos)
    ax2 = fig.add_subplot(gs[1])  # Gráfica del índice de popularidad

    while True:
        try:
            # Verificar que ambos archivos existan
            if not os.path.isfile(CSV_TWEETS):
                print(f"No se encuentra '{CSV_TWEETS}'. Esperando que el productor genere datos...")
                time.sleep(10)
                continue

            if not os.path.isfile(CSV_SENTIMIENTO):
                tweets_df = pd.read_csv(CSV_TWEETS)
                tweets_df["sentimiento"] = None
                tweets_df.to_csv(CSV_SENTIMIENTO, index=False)
                print(f"Archivo '{CSV_SENTIMIENTO}' creado. Iniciando procesamiento...")
                continue

            # Leer los datos de ambos CSVs
            tweets_df = pd.read_csv(CSV_TWEETS)
            sentimientos_df = pd.read_csv(CSV_SENTIMIENTO)

            # Identificar tweets nuevos
            tweets_procesados_ids = set(sentimientos_df["tweet_id"].astype(str))
            nuevos_tweets_df = tweets_df[~tweets_df["tweet_id"].astype(str).isin(tweets_procesados_ids)]

            if not nuevos_tweets_df.empty:
                print(f"Procesando {len(nuevos_tweets_df)} tweets nuevos...")
                nuevos_tweets_df["sentimiento"] = nuevos_tweets_df["text"].apply(analizar_sentimiento_avanzado)
                sentimientos_df = pd.concat([sentimientos_df, nuevos_tweets_df], ignore_index=True)
                sentimientos_df.to_csv(CSV_SENTIMIENTO, index=False)

            # Contar sentimientos
            conteo_sentimientos = sentimientos_df["sentimiento"].value_counts()
            positivos = conteo_sentimientos.get("positivo", 0)
            negativos = conteo_sentimientos.get("negativo", 0)
            neutrales = conteo_sentimientos.get("neutral", 0)

            # Cálculo del índice de popularidad
            total = positivos + negativos + neutrales
            popularidad = (positivos - negativos) / total if total > 0 else 0

            print("=== Análisis de Sentimientos ===")
            print(f"Positivos: {positivos}, Negativos: {negativos}, Neutrales: {neutrales}")
            print(f"Índice de Popularidad: {popularidad:.2f}\n")

            # Gráfica de barras
            ax1.clear()
            ax1.bar(
                ["Positivo", "Negativo", "Neutral"],
                [positivos, negativos, neutrales],
                color=["green", "red", "gray"],
                alpha=0.7
            )
            ax1.set_xlabel("Sentimiento")
            ax1.set_ylabel("Cantidad de Tweets")
            ax1.set_title("Distribución de Sentimientos en Twitter", fontsize=14)
            ax1.set_ylim(0, max(positivos, negativos, neutrales) + 50)
            ax1.grid(axis="y", linestyle="--", alpha=0.5)

            # Gráfico del índice de popularidad (Gauge)
            ax2.clear()
            ax2.axis('off')
            ax2.set_title("Índice de Popularidad", fontsize=14, pad=20)

            # Fondo del medidor
            theta = np.linspace(-np.pi / 2, np.pi / 2, 100)
            ax2.fill_between(np.cos(theta), 0, np.sin(theta), color="lightgray", alpha=0.3)

            # Colores dinámicos para el indicador
            color = "green" if popularidad > 0 else "red"
            angle = -np.pi / 2 + (popularidad + 1) * (np.pi / 2)
            ax2.arrow(0, 0, np.cos(angle) * 0.8, np.sin(angle) * 0.8,
                      head_width=0.05, head_length=0.1, fc=color, ec=color)

            # Etiquetas en el gauge
            for i, label in enumerate(np.linspace(-1, 1, 11)):
                angle = -np.pi / 2 + i * (np.pi / 10)
                x, y = np.cos(angle) * 1.1, np.sin(angle) * 1.1
                ax2.text(x, y, f"{label:.1f}", ha='center', va='center', fontsize=8)

            # Actualizar las gráficas
            plt.tight_layout()
            plt.draw()
            plt.pause(10)

        except Exception as e:
            print(f"Error en análisis/graficación: {e}")
            time.sleep(5)

# =======================================
def main():
    # 1) Thread para recolección (producer)
    #    Arrancará la corrutina que hace asyncio.run(recolectar_tweets())
    def run_producer():
        asyncio.run(recolectar_tweets())
    
    producer_thread = threading.Thread(target=run_producer, daemon=True)
    producer_thread.start()

    # 2) Bucle principal de análisis y graficación (consumer)
    loop_analisis_y_graficacion()

if __name__ == "__main__":
    main()

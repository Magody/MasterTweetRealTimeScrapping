# **Análisis de Sentimientos en Twitter en Tiempo Real**

Este proyecto permite recolectar tweets en tiempo real utilizando palabras clave específicas, analizar su sentimiento mediante un modelo de machine learning, y visualizar los resultados de forma dinámica con gráficos. Está diseñado para procesar datos de Twitter en vivo, manteniendo un flujo constante de análisis y visualización.

---

## **Por qué se eligió `twikit` en lugar del API de Twitter**

### Limitaciones del API Oficial de Twitter
1. **Restricciones en el número de resultados**:
   - El API oficial de Twitter permite obtener un máximo de 100 resultados por solicitud en sus versiones más accesibles, lo cual no es suficiente para análisis masivos o experimentos en tiempo real.

2. **Datos incompletos**:
   - En muchos casos, los tweets obtenidos a través del API están truncados, especialmente si contienen enlaces o menciones extensas, lo que dificulta realizar un análisis efectivo del texto completo.

![Precios y Restricciones del API](./docs/06_prices_restrictions.png)

---

### Ventajas de `twikit`
1. **Sin límites estrictos de resultados**:
   - `twikit` utiliza técnicas de scraping para obtener tweets directamente de la interfaz de Twitter (X), lo que permite acceder a una mayor cantidad de datos sin las limitaciones impuestas por el API.

2. **Datos más completos**:
   - Al extraer tweets directamente de la plataforma, se obtiene el contenido completo del texto y otros metadatos relevantes para el análisis.

3. **Acceso eficiente y continuo**:
   - Esto facilita experimentos en tiempo real, ya que se puede recolectar una mayor cantidad de datos con mayor frecuencia.

![Portal de Twikit](./docs/05_x_portal.png)

---

## **Características del Proyecto**

1. **Recolección de tweets en tiempo real**:
   - Se utiliza la librería `twikit` para conectarse a Twitter y buscar tweets relacionados con palabras clave específicas.
   - Los datos recolectados se almacenan en un archivo CSV (`tweets_noboa.csv`).

2. **Análisis de sentimientos**:
   - El modelo preentrenado `nlptown/bert-base-multilingual-uncased-sentiment` clasifica los tweets en:
     - Positivos
     - Negativos
     - Neutrales
   - Los resultados se guardan en un archivo separado (`tweets_sentimiento.csv`).

3. **Visualización dinámica**:
   - Se utiliza `matplotlib` para graficar en tiempo real la distribución de los sentimientos y un índice de popularidad basado en los datos procesados.

---

## **Guía de Ejecución**

### 1. **Exportar Cookies desde Twitter**
Utiliza una extensión como **EditThisCookie** para exportar las cookies desde la página de Twitter. Este paso es necesario para autenticar las solicitudes al API de Twitter. 

- Guarda las cookies exportadas en un archivo JSON (`cookies_exported.json`).

![Exportar Cookies](./docs/00_cookies_edit.png)

---

### 2. **Convertir las Cookies al Formato Correcto**
Usa el script `00_cookies.py` para transformar las cookies exportadas al formato requerido por el programa:

```bash
python 00_cookies.py
```

Esto generará un archivo `cookies.json` que será usado para autenticar las solicitudes.

![Conversión de Cookies](./docs/01_cookies_transformation.png)

---

### 3. **Ejecución del Proyecto**
Ejecuta el script principal `app.py` para iniciar la recolección y análisis de tweets:

```bash
python app.py
```

El programa:
- Recolectará tweets periódicamente usando palabras clave.
- Almacena los resultados en `tweets_noboa.csv`.
- Analiza los sentimientos y los guarda en `tweets_sentimiento.csv`.
- Muestra una gráfica dinámica que se actualiza en tiempo real.

![Ejecución en Consola](./docs/02_ejecucion_consola_real_time.png)

---

### 4. **Gráfica de Sentimientos en Tiempo Real**
Conforme se analizan los tweets, la gráfica muestra la distribución de sentimientos y un índice de popularidad (Gauge) basado en los datos procesados.

![Gráfica de Sentimientos](./docs/03_grafica_realtime_1.png)
![Gráfica de Sentimientos](./docs/03_grafica_realtime_2.png)
![Gráfica de Sentimientos](./docs/03_grafica_realtime_3.png)

---

## **Requisitos Previos**

### **Dependencias**
Asegúrate de tener las siguientes librerías instaladas:
- `pandas`
- `matplotlib`
- `torch`
- `transformers`
- `twikit`

Instálalas con el siguiente comando:
```bash
pip install -r requirements.txt
```

### **Configuración de Credenciales**
Configura un archivo `config.ini` con tus credenciales de Twitter:
```ini
[X]
username = "TU_USERNAME"
email = "TU_EMAIL"
password = "TU_PASSWORD"
```

---

## **Estructura del Proyecto**

```
📂 TWEETSSENTIMENT
├── docs/
│   ├── 00_cookies_edit.png          # Imagen de exportar cookies
│   ├── 01_cookies_transformation.png # Imagen de transformación de cookies
│   ├── 02_ejecucion_consola_real_time.png # Consola de ejecución
│   ├── 03_grafica_realtime.png      # Gráfica dinámica de sentimientos
│   ├── 05_x_portal.png              # Portal de Twikit
│   └── 06_prices_restrictions.png   # Precios y restricciones del API de Twitter
├── app.py                           # Script principal
├── 00_cookies.py                    # Conversión de cookies
├── config.ini                       # Credenciales del usuario
├── requirements.txt                 # Dependencias del proyecto
├── tweets_noboa.csv                 # Tweets recolectados
├── tweets_sentimiento.csv           # Tweets analizados
```

---

## **Consideraciones**

1. **Límites de Peticiones**:
   - Si el límite de peticiones a Twitter es alcanzado, el programa esperará automáticamente hasta que el acceso sea reestablecido.

2. **Archivos CSV**:
   - `tweets_noboa.csv`: Contiene los datos recolectados directamente de Twitter.
   - `tweets_sentimiento.csv`: Almacena los datos procesados con el análisis de sentimientos.

3. **Persistencia de Datos**:
   - El análisis de sentimientos se guarda progresivamente, lo que asegura que los datos previos no se vuelvan a procesar.

4. **Gráfica en Tiempo Real**:
   - La gráfica se actualiza dinámicamente con los nuevos datos procesados.

---
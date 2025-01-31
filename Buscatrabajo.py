from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from jinja2 import Environment, FileSystemLoader
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import webbrowser
import unidecode
import traceback
import requests
import time
import math
import sys
import os
import re


# Cambiar al directorio del script para asegurar que se encuentren los archivos necesarios
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Función para normalizar y limpiar textos usando expresiones regulares
def normalize_text(text):
    # Convertir a minúsculas y eliminar acentos
    normalized = unidecode.unidecode(text.lower())
    # Reemplazar caracteres especiales por espacios
    normalized = re.sub(r'[-/():*]', ' ', normalized)
    # Reemplazar múltiples espacios por uno solo y quitar espacios en extremos
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

# Configuración de Jinja2 para generar el HTML de resultados
env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
template = env.get_template('template.html')

def page(ele_res, comp_res):
    filename = 'Resultados.html'
    with open(filename, "w", encoding="utf-8") as fh:
        fh.write(template.render(
            elemp=ele_res,
            comput=comp_res,
            tiene_computrabajo=len(comp_res) > 0
        ))

# Cargar filtros de palabras desde el archivo "filtro.txt"
filtrado = []
try:
    with open('filtro.txt', 'r', encoding='utf-8') as f:
        for line in f:
            palabra = unidecode.unidecode(line.strip().lower())
            if palabra:
                filtrado.append(palabra)
except FileNotFoundError:
    print("No se encontró el archivo 'filtro.txt'. Asegúrate de que esté en el mismo directorio.")
    sys.exit(1)

# Función de barra de progreso para mostrar el avance
def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write(f'[{bar}] {percents}% ...{status}\r')
    sys.stdout.flush()

# --- Selección de Sitio ---
try:
    sitio = int(input("Sitio a buscar: 1 = Elempleo, 2 = Computrabajo, 3 = Ambos: "))
except ValueError:
    print("Por favor ingresa un número válido (1, 2 o 3).")
    sys.exit(1)

# --- Inicialización de Variables Globales ---
tiempo_inicio = time.time()
ele_res = []   # Ofertas válidas en Elempleo
comp_res = []  # Ofertas válidas en Computrabajo
total_ofertas_encontradas = 0
total_ofertas_filtradas = 0

# --- Configuración de Selenium (Chrome) ---
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
options.add_argument("--ignore-ssl-errors")
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('--headless')
options.add_argument('--window-size=1280,800')
s = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=options)

# Limpiar la consola
os.system('cls' if os.name == 'nt' else 'clear')
print('\nInicializando...')

# --- SCRAPING DE ELEMPEO ---
if sitio in [1, 3]:
    contador_elempleo = 0
    total_elempleo = 0

    try:
        # Ir directamente a la URL con filtros aplicados
        driver.get('https://www.elempleo.com/co/ofertas-empleo/bogota?Salaries=2-25-millones:25-3-millones:3-35-millones:35-4-millones&PublishDate=hace-1-semana')
        
        # Espera explícita para que la página cargue
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Aceptar cookies (si aparece)
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnAcceptPolicyNavigationCO"))
            )
            driver.execute_script("arguments[0].click();", cookie_button)
            print("Cookies aceptadas exitosamente en elempleo.com")
        except TimeoutException:
            print("No se encontró el banner de cookies o ya fue aceptado")
        
        # Pequeña espera para asegurar que se apliquen los cambios
        time.sleep(2)
        
        # Calcular el número total de resultados
        try:
            total_results = driver.find_element(By.CLASS_NAME, "js-total-results").text.strip()
            numero_elempleo = int(total_results.replace('.', ''))
            print(f"Número de ofertas encontradas (Elempleo): {numero_elempleo}")
            total_paginas_elempleo = math.ceil(numero_elempleo / 50)
            print(f"Total de páginas a procesar (Elempleo): {total_paginas_elempleo}")
        except (AttributeError, ValueError) as e:
            print("No se pudo obtener el número de resultados en elempleo:", str(e))
            numero_elempleo = 50
            total_paginas_elempleo = 1

        # Navegar por las páginas de resultados
        pagina_actual = 1
        while pagina_actual <= total_paginas_elempleo:
            print(f"Procesando página {pagina_actual} de {total_paginas_elempleo} en Elempleo")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Buscar enlaces que contengan "ofertas-trabajo" en el href
            links = soup.find_all('a', href=lambda href: href and 'ofertas-trabajo' in href)
            
            for elem in links:
                fullstring = elem.get('title')
                href = elem.get('href')
                if fullstring and href:
                    texto_normalizado = normalize_text(fullstring)
                    # Verificar si alguna palabra del filtro se encuentra en la oferta
                    descartar = any(palabra in texto_normalizado for palabra in filtrado)
                    if not descartar:
                        full_url = f"https://www.elempleo.com{href}" if not href.startswith('http') else href
                        ele_res.append((full_url, fullstring))
                        contador_elempleo += 1
                    total_elempleo += 1

            # Intentar ir a la siguiente página
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "js-btn-next"))
                )
                if "disabled" in next_button.get_attribute("class"):
                    print("Última página de Elempleo")
                    break

                driver.execute_script("arguments[0].click();", next_button)
                # Esperar a que la página se actualice
                WebDriverWait(driver, 10).until(EC.staleness_of(next_button))
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.active a.js-page"))
                )
            except TimeoutException:
                print("No se pudo navegar a la siguiente página de Elempleo")
                break

            progress(pagina_actual, total_paginas_elempleo, status=f'Elempleo (página {pagina_actual})')
            pagina_actual += 1

        print(f"\nFiltradas {contador_elempleo} de {total_elempleo} ofertas en elempleo.com\n")
        total_ofertas_encontradas += total_elempleo
        total_ofertas_filtradas += contador_elempleo

    except Exception as e:
        print("Se presentó un error durante el scraping en Elempleo:")
        traceback.print_exc()

driver.quit()

# --- SCRAPING DE COMPUTRABAJO ---
if sitio in [2, 3]:
    contador_computrabajo = 0
    total_computrabajo = 0

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    }
    base_url = 'https://co.computrabajo.com/empleos-en-bogota-dc'
    params = {
        'pubdate': '7',  # ofertas de la semana
        'sal': '5',     # rango salarial
        'p': 1           # página inicial
    }
    base_computrabajo = "https://co.computrabajo.com"
    # Cadenas para identificar enlaces no deseados
    me = "www.computrabajo.com.co/empresas/"
    me3 = "https://www.computrabajo.com.co/ofertas-de-trabajo/"

    try:
        # Petición inicial para obtener el total de ofertas
        response = requests.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        total_results = soup.select_one('h1.title_page span.fwB')
        if total_results:
            numero_ct = int(total_results.text.replace('.', '').replace(' ', ''))
            total_paginas_ct = math.ceil(numero_ct / 20)
            print(f"Total de ofertas encontradas (Computrabajo): {numero_ct}")
            print(f"Total de páginas a procesar (Computrabajo): {total_paginas_ct}")
        else:
            print("No se pudo obtener el número de resultados en Computrabajo")
            numero_ct = 20
            total_paginas_ct = 1

        pagina_actual = 1
        while pagina_actual <= total_paginas_ct:
            print(f"Procesando página {pagina_actual} de {total_paginas_ct} en Computrabajo")
            params['p'] = pagina_actual
            response = requests.get(base_url, params=params, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar todos los enlaces de ofertas
            links = soup.select('a.js-o-link')
            for elem in links:
                fullstring = elem.text.strip()
                enlace = elem.get('href')
                if enlace:  # Asegurarse de que el enlace no sea None
                    texto_normalizado = normalize_text(fullstring)
                    descartar = any(palabra in texto_normalizado for palabra in filtrado)
                    # Evitar enlaces a "empresas" o enlaces no deseados
                    if not descartar and me not in enlace and enlace != me3:
                        enlace_completo = base_computrabajo + enlace if not enlace.startswith('http') else enlace
                        comp_res.append((enlace_completo, fullstring))
                        contador_computrabajo += 1
                    total_computrabajo += 1

            progress(pagina_actual, total_paginas_ct, status=f'Computrabajo (página {pagina_actual})')
            time.sleep(1)  # Pequeña pausa para evitar sobrecargar el servidor
            pagina_actual += 1

    except Exception as e:
        print("Error durante el scraping en Computrabajo:")
        traceback.print_exc()

    print(f"\nFiltradas {contador_computrabajo} de {total_computrabajo} ofertas en computrabajo.com\n")
    total_ofertas_encontradas += total_computrabajo
    total_ofertas_filtradas += contador_computrabajo

# --- GENERAR EL HTML CON LOS RESULTADOS ---
page(ele_res, comp_res)

# Mostrar resultados finales y tiempo de ejecución
tiempo_fin = time.time()
tiempo_total = tiempo_fin - tiempo_inicio

print(f"\nTotal de ofertas encontradas: {total_ofertas_encontradas}")
print(f"Ofertas filtradas: {total_ofertas_filtradas} en {round((tiempo_total / 60), 2)} minutos.")

if sitio == 3:
    print("\nResumen Total:")
    print(f"Filtradas {total_ofertas_filtradas} de {total_ofertas_encontradas} ofertas en total")
else:
    print(f"Filtradas {total_ofertas_filtradas} de {total_ofertas_encontradas} ofertas en total")

# Abrir el archivo HTML generado en el navegador predeterminado
webbrowser.open("Resultados.html")
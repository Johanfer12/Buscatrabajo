from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from jinja2 import Environment, FileSystemLoader
from selenium.webdriver.common.by import By
from selenium import webdriver
import webbrowser
import unidecode
import time
import math
import sys
import os
import requests
from bs4 import BeautifulSoup


# Directorio local
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Creación de archivo html con Jinja2
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

# Cargar filtros de palabras desde archivo
filtrado = []
with open('filtro.txt', 'r', encoding='utf-8') as f:
    for line in f:
        palabra = unidecode.unidecode(line.strip().lower())
        filtrado.append(palabra)

# Barra de progreso:
def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

# Selección de sitio
sitio = int(input("Sitio a buscar: 1 = Elempleo, 2 = Computrabajo, 3 = Ambos: "))

# Inicialización
tiempo_inicio = time.time()
ele_res = []  # Lista de ofertas válidas en elempleo
comp_res = []  # Lista de ofertas válidas en computrabajo

# Estas dos variables son las que nos interesan para el reporte final:
total_ofertas_encontradas = 0
total_ofertas_filtradas = 0

options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
options.add_argument("--ignore-ssl-errors")
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('--headless')
options.add_argument('--window-size=1280,800')
s = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=options)

os.system('cls' if os.name == 'nt' else 'clear')
print('\n' + " Inicializando...")

############## SCRAPING DE ELEMPEO ##############
if sitio == 1 or sitio == 3:
    contador_elempleo = 0
    total_elempleo = 0
    
    # Ir directamente a la URL con filtros aplicados
    driver.get('https://www.elempleo.com/co/ofertas-empleo/?Salaries=45-55-millones:55-6-millones:6-8-millones&PublishDate=hoy')
    time.sleep(3)

    # Aceptar cookies
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btnAcceptPolicyNavigationCO"))
        )
        driver.execute_script("arguments[0].click();", cookie_button)
        print("Cookies aceptadas exitosamente en elempleo.com")
    except TimeoutException:
        print("No se encontró el banner de cookies o ya fue aceptado")
    
    time.sleep(3)

    # Calcular número total de resultados
    try:
        total_results = driver.find_element(By.CLASS_NAME, "js-total-results").text.strip()
        numero_elempleo = int(total_results.replace('.', ''))
        print(f"Número de ofertas encontradas (elempleo): {numero_elempleo}")
        total_paginas_elempleo = math.ceil(numero_elempleo / 50)
        print(f"Total de páginas a procesar (elempleo): {total_paginas_elempleo}")
    except (AttributeError, ValueError) as e:
        print("No se pudo obtener el número de resultados en elempleo:", str(e))
        numero_elempleo = 50
        total_paginas_elempleo = 1

    # Navegar por las páginas
    pagina_actual = 1
    while pagina_actual <= total_paginas_elempleo:
        print(f"Procesando página {pagina_actual} de {total_paginas_elempleo} en elempleo")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = soup.find_all('a', href=lambda href: href and 'ofertas-trabajo' in href)

        # Filtrar cada oferta
        for elem in links:
            fullstring = elem.get('title')
            href = elem.get('href')
            
            if fullstring and href:
                texto_normalizado = unidecode.unidecode(
                    fullstring.lower()
                    .replace('-', ' ')
                    .replace('/', ' ')
                    .replace('(', ' ')
                    .replace(')', ' ')
                    .replace(':', ' ')
                    .replace('*', ' ')
                    .replace('  ', ' ')
                )
                
                # Verificamos si alguna palabra del filtro está en la oferta
                descartar = any(palabra in texto_normalizado for palabra in filtrado)
         
                if not descartar:
                    full_url = f"https://www.elempleo.com{href}" if not href.startswith('http') else href
                    ele_res.append((full_url, fullstring))
                    contador_elempleo += 1
                total_elempleo += 1

        # Ir a la siguiente página
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "js-btn-next"))
            )
            if "disabled" in next_button.get_attribute("class"):
                print("Última página de elempleo")
                break
            
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, 10).until(EC.staleness_of(next_button))
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.active a.js-page"))
            )
            time.sleep(1)
            
        except TimeoutException:
            print("No se pudo navegar a la siguiente página de elempleo")
            break
            
        progress(pagina_actual, total_paginas_elempleo, status=f'Elempleo (página {pagina_actual})')
        pagina_actual += 1

    print(f"\nFiltradas {contador_elempleo} de {total_elempleo} Ofertas en elempleo.com\n")
    
    # Sumar al global
    total_ofertas_encontradas += total_elempleo
    total_ofertas_filtradas += contador_elempleo

############## SCRAPING DE COMPUTRABAJO ##############
if sitio == 2 or sitio == 3:
    contador_computrabajo = 0
    total_computrabajo = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    }
    base_url = 'https://co.computrabajo.com/empleos-en-bogota-dc'
    params = {
        'pubdate': '7',  # semana
        'sal': '15',     # rango salarial
        'p': 1           # página
    }
    base_computrabajo = "https://co.computrabajo.com"
    me = "www.computrabajo.com.co/empresas/"
    me3 = "https://www.computrabajo.com.co/ofertas-de-trabajo/"
    
    try:
        # Petición inicial para obtener total de ofertas
        response = requests.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Total de ofertas
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
            
            # Buscar ofertas
            links = soup.select('a.js-o-link')
            
            for elem in links:
                fullstring = elem.text.strip()
                enlace = elem.get('href')
                
                texto_normalizado = unidecode.unidecode(
                    fullstring.lower()
                    .replace('-', ' ')
                    .replace('/', ' ')
                    .replace('(', ' ')
                    .replace(')', ' ')
                    .replace(':', ' ')
                    .replace('*', ' ')
                    .replace('  ', ' ')
                )
                
                descartar = any(palabra in texto_normalizado for palabra in filtrado)
                
                # Evitar enlaces a "empresas" o enlaces vacíos
                if not descartar and me not in enlace and enlace != me3:
                    enlace_completo = base_computrabajo + enlace if not enlace.startswith('http') else enlace
                    comp_res.append((enlace_completo, fullstring))
                    contador_computrabajo += 1
                total_computrabajo += 1
            
            progress(pagina_actual, total_paginas_ct, status=f'Computrabajo (página {pagina_actual})')
            time.sleep(1)
            pagina_actual += 1
            
    except Exception as e:
        print(f"Error durante el scraping en Computrabajo: {str(e)}")

    print(f"\nFiltradas {contador_computrabajo} de {total_computrabajo} Ofertas en computrabajo.com\n")
    
    # Sumar al global
    total_ofertas_encontradas += total_computrabajo
    total_ofertas_filtradas += contador_computrabajo

############## GENERAR EL HTML ##############
page(ele_res, comp_res)

# Tiempo total
tiempo_fin = time.time()
tiempo_total = tiempo_fin - tiempo_inicio

# Resultados combinados
print(f"Total: {total_ofertas_encontradas} Resultados\n")
print(f"Filtrados: {total_ofertas_filtradas} resultados en {round((tiempo_total/60), 2)} minutos.\n")

# Si se escoge la opción 3, se muestra un resumen total
if sitio == 3:
    print("\nResumen Total:")
    print(f"Filtradas {total_ofertas_filtradas} de {total_ofertas_encontradas} Ofertas en total")
else:
    print(f"Filtradas {total_ofertas_filtradas} de {total_ofertas_encontradas} Ofertas en total")

# Abrir el archivo HTML al final
webbrowser.open("Resultados.html")
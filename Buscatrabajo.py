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

#directorio local
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#Creación de archivo html con Jinja2
env = Environment( loader = FileSystemLoader(os.path.dirname(os.path.abspath(__file__))) )
template = env.get_template('template.html')

def page(ele_res,comp_res):
  filename = ('Resultados.html')
  with open(filename, "w", encoding="utf-8") as fh:
      fh.write(template.render(
          elemp = ele_res,
          comput = comp_res,
      ))
#Cargar filtros de palabras desde archivo

filtrado = []
with open('filtro.txt', 'r', encoding='utf-8') as f:
    for line in f:
        # Eliminar espacios en blanco y convertir a minúsculas
        palabra = unidecode.unidecode(line.strip().lower())
        filtrado.append(palabra)

#Barra de progreso:

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

#Selección de sitio
sitio = int(input("Sitio a buscar: 1 = Elempleo, 2 = Computrabajo, 3 = Ambos: "))

#Inicialización
tiempo_inicio = time.time() #Inicio de tiempo de ejecución
ele_res = [] #Lista de empresas de elempleo
comp_res = [] #Lista de empresas de computrabajo
contador = 0 
total = 0
sig = 1  # Contador de páginas
numero = 0  # Número total de ofertas
OFERTAS_POR_PAGINA = 21  # Número de ofertas por página
correct = 0
tt1 = 0
tt2 = 0
me = "www.computrabajo.com.co/empresas/"
me3 = "https://www.computrabajo.com.co/ofertas-de-trabajo/"
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
options.add_argument("--ignore-ssl-errors")
options.add_argument('--ignore-certificate-errors-spki-list')
#options.add_argument('--headless')
options.add_argument('--window-size=1280,800')
s=Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=options)
os.system('cls')
print('\n' + " Inicializando...")

################ ELEMPLEO INICIO ################

if sitio == 1 or sitio == 3:
    # Ir directamente a la URL con los filtros aplicados
    driver.get('https://www.elempleo.com/co/ofertas-empleo/bogota?Salaries=15-2-millones:2-25-millones:25-3-millones:3-35-millones&PublishDate=hace-1-semana')
    time.sleep(3)

    # Click en el botón de cookies de elempleo
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btnAcceptPolicyNavigationCO"))
        )
        driver.execute_script("arguments[0].click();", cookie_button)
        print("Cookies aceptadas exitosamente en elempleo.com")
    except TimeoutException:
        print("No se encontró el banner de cookies o ya fue aceptado")
    
    time.sleep(3)

    #Calculo de resultados y páginas
    try:
        total_results = driver.find_element(By.CLASS_NAME, "js-total-results").text.strip()
        numero = int(total_results.replace('.', ''))
        print(f"Número de ofertas encontradas: {numero}")
        total_paginas = (numero // 50) + (1 if numero % 50 > 0 else 0)
        print(f"Total de páginas a procesar: {total_paginas}")
        tt1 = numero
    except (AttributeError, ValueError) as e:
        print("No se pudo obtener el número de resultados:", str(e))
        numero = 50
        total_paginas = 5

    # Bucle principal
    while sig <= total_paginas:
        print(f"Procesando página {sig} de {total_paginas}")
        
        #Buscar links de las ofertas
        links = driver.find_elements(By.XPATH,'//a[contains(@href, "ofertas-trabajo")]')

        #Filtrar ofertas
        for elem in links:
            # Normalizar el texto del título (quitar acentos, convertir a minúsculas)
            fullstring = elem.get_attribute("title")
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
            
            # Verificar si alguna palabra del filtro está en el texto normalizado
            res = any(palabra in texto_normalizado for palabra in filtrado)
     
            if not res:
                ele_res.append((elem.get_attribute("href"), elem.get_attribute("title")))
                contador += 1
                total += 1
            else:
                total += 1

        time.sleep(2)

        # Verificar si hay más páginas antes de intentar navegar
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "js-btn-next"))
            )
            # Verificar si estamos en la última página
            if "disabled" in next_button.get_attribute("class"):
                print("Llegamos a la última página")
                break
            
            # Si no es la última página, hacer clic en siguiente
            driver.execute_script("arguments[0].click();", next_button)
            # Esperar a que la página se actualice
            WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.CSS_SELECTOR, "li.active a.js-page").get_attribute("data-page") == str(sig + 1)
            )
        except TimeoutException:
            print("No se pudo navegar a la siguiente página")
            break
            
        progress(sig, total_paginas, status='Filtrando página: ' + str(sig) + ' de ' + str(total_paginas))
        sig += 1

    print('\n')
    print(f"Filtradas {contador} de {total} Ofertas en elempleo.com\n")
    tt2 = contador

####### COMPUTRABAJO INICIO ##########

if sitio == 2 or sitio == 3:
    sig = 1
    contador = 0
    total = 0
    numero_total = 0  # Inicializar variable para el total de ofertas

    # URL directa con filtros aplicados
    driver.get('https://co.computrabajo.com/empleos-en-bogota-dc?pubdate=7&sal=5')
    time.sleep(3)

    # Click en el botón de cookies
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cc-dismiss"))
        )
        # Usar JavaScript para hacer clic
        driver.execute_script("arguments[0].click();", cookie_button)
        print("Cookies aceptadas exitosamente")
    except TimeoutException:
        print("No se encontró el banner de cookies o ya fue aceptado")
    except Exception as e:
        print(f"Error al intentar aceptar cookies: {str(e)}")
        
    time.sleep(2)  # Dar tiempo adicional después de aceptar las cookies

    #Calculo de resultados y páginas
    try:
        total_results = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//h1[@class='title_page']/span[@class='fwB']"))
        ).text
        numero_total = int(total_results.replace('.', '').replace(' ', ''))
        total_paginas = math.ceil(numero_total / 20)
        print(f"Total de ofertas encontradas: {numero_total}")
        print(f"Total de páginas a procesar: {total_paginas}")
        tt1 = numero_total  # Guardar el total de ofertas
    except TimeoutException:
        print("No se pudo obtener el número de resultados")
        total_paginas = 1

    # Modificar el bucle while para usar total_paginas
    while sig <= total_paginas:
        print(f"Procesando página {sig} de {total_paginas}")
        #Buscar links de las ofertas
        links = driver.find_elements(By.CLASS_NAME, 'js-o-link')
        
        #Filtrar ofertas
        for elem in links:
            fullstring = elem.get_attribute("text")
            res = any(ele in unidecode.unidecode(fullstring.replace('-', ' ').replace('   ', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('  ', ' ').replace('*', ' ').lower()) for ele in filtrado)
            enlace = elem.get_attribute("href")

            if not res and enlace.find(me) == -1 and enlace != me3:
                comp_res.append((elem.get_attribute("href"), elem.get_attribute("text")))
                total += 1
                contador += 1
            elif me in enlace or enlace == me3:
                pass
            else:
                total += 1

        time.sleep(2)

        #Click siguiente - actualizado con el nuevo selector
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span.buildLink[title='Siguiente']"))
            )
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
        except TimeoutException:
            print("No se pudo encontrar o hacer clic en el botón siguiente")
            break
        
        progress(sig, total_paginas, status=f'Filtrando página: {sig} de {total_paginas}')
        sig += 1
        correct += 1
        time.sleep(2)

    else:
        print ('\n') #Separado pues la barra de progreso no se ve bien
        print (f"Filtradas {contador} de {total-correct} Ofertas en computrabajo.com\n")
        if sitio == 3:
            tt2 = contador + tt2
        else:
            tt2 = contador

#Resultados
page(ele_res,comp_res)
tiempo_fin = time.time()
tiempo_total = tiempo_fin - tiempo_inicio
print(f"Total: {tt1} Resultados\n")
print(f"Filtrados: {tt2} resultados en {round((tiempo_total/60),2)} minutos.\n")

#Cierre
driver.close()
webbrowser.open("Resultados.html")
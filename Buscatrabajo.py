from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from jinja2 import Environment, FileSystemLoader
from selenium.webdriver.common.by import By
from selenium import webdriver
import webbrowser
import unidecode
import sqlite3
import shutil
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
  with open(filename, 'w') as fh:
      fh.write(template.render(
          elemp = ele_res,
          comput = comp_res,
      ))
#Cargar filtros de palabras desde archivo

filtrado = open('filtro.txt').read().splitlines()

#Barra de progreso:

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

#Cargar base de datos navegador para filtrar los ya visitados
#C:\Users\[Usuario]\AppData\Local\Microsoft\Edge\User Data\Default\History #en el caso de Microsoft Edge#

shutil.copyfile(r"C:\Users\Johan\AppData\Local\Microsoft\Edge\User Data\Default\History", "History.sqlite")
conn = sqlite3.connect("History.sqlite")
cursor = conn.cursor()

def consulta_db(empresa):
    query = "SELECT url FROM urls WHERE url LIKE " + "'%" + empresa + "%'"
    cursor.execute(query)
    return cursor.fetchall()

compdb = consulta_db(r"computrabajo.com.co/ofertas-de-trabajo")
eledb = consulta_db(r"elempleo.com/co/ofertas-trabajo/")

#Filtrar Call Center?

col = int(input("Filtrar Call Center? (1=Si 0=No): "))
if col == 1:
    filtrado.append('call')
    filtrado.append('center')

#Salario mínimo

sal = int(input("Salario mínimo: 1 = >1m 2 = >1.5m: "))

#Inicialización
ele_res = list(tuple())
comp_res = list(tuple())
contador = 0
total = 0
sig = 0
x = 0
correct = 0
tt1 = 0
tt2 = 0
me = "www.computrabajo.com.co/empresas/"
me3 = "https://www.computrabajo.com.co/ofertas-de-trabajo/"
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
options.add_argument("--ignore-ssl-errors")
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('--headless')
options.add_argument('--window-size=1280,800')
s=Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=options)
os.system('cls')
print('\n' + " Inicializando...")

################ ELEMPLEO INICIO ################

driver.get('https://www.elempleo.com/co/ofertas-empleo/bogota')
time.sleep(1)

#Click Cookies
driver.find_element(By.XPATH,'/html/body/div[10]/div/div[2]/a').click()

#Arreglo del bug de no resultados
driver.find_element(By.XPATH,'/html/body/header/div/div[2]/div[2]/div/form/div/button').click()
driver.back()

#Click Salario 1-1.5
if sal == 1:
    driver.find_element(By.XPATH,'/html/body/div[8]/div[4]/div[2]/div[1]/div/div[1]/div/div[2]/label/input').click()
time.sleep(2)

#Click Salario 1.5-2
driver.find_element(By.XPATH,'/html/body/div[8]/div[4]/div[2]/div[1]/div/div[1]/div/div[3]/label/input').click()
time.sleep(2)

#Click Salario 2-2.5
driver.find_element(By.XPATH,'/html/body/div[8]/div[4]/div[2]/div[1]/div/div[1]/div/div[4]/label/input').click()
time.sleep(3)

#Click Fecha
driver.find_element(By.XPATH,'/html/body/div[8]/div[4]/div[2]/div[1]/div/div[3]/div/div[2]/label/input').click()
time.sleep(3)

#Calculo de resultados y páginas

numero = int(driver.find_element(By.XPATH,"/html/body/div[8]/div[2]/div/div/h2/span[1]/strong[3]").text)
os.system('cls')
print (str(numero) + " resultados encontrados en elempleo.com" + '\n')
tt1 = numero
numero = int(math.floor(numero/100))
time.sleep(1)

while sig <= numero:
    
    #Cargar más resultados
    driver.find_element(By.XPATH,"/html/body/div[8]/div[4]/div[1]/div[3]/div/form/div/select/option[3]").click()
    time.sleep(3)

    #Buscar links de las ofertas
    links = driver.find_elements(By.XPATH,'//a[contains(@href, "ofertas-trabajo")]')

    #Filtrar ofertas
    for elem in links:
        
        fullstring = elem.get_attribute("title")
        res = any(ele in unidecode.unidecode(fullstring.replace('-', ' ').replace('   ', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('  ', ' ').replace('*', ' ').lower()) for ele in filtrado)
 
        #Verificar si url está en eledb:
        if res == False:
            
            url = elem.get_attribute("href")
            res2 = any(url in s for s in eledb)
      

        if res == False and res2 == False:

            ele_res.append((elem.get_attribute("href"), elem.get_attribute("title")))
            contador += 1
            total += 1

        else:
            total += 1

    time.sleep(2)
    driver.find_element(By.CLASS_NAME,"js-btn-next").click()
    progress(sig, numero, status='Filtrando página: ' + str(sig) + ' de ' + str(numero))
    time.sleep(2)
    sig +=1 

else:
    print ('\n') #Separado pues la barra de progreso no se ve bien
    print ("Filtradas " + str(contador) + " de " + str(total) + " Ofertas en elempleo.com" + '\n')
    
#Resultados    
tt2 = contador

####### COMPUTRABAJO INICIO ##########

sig = 1
contador = 0
total = 0

#Filtro salario

if sal == 1:
    driver.get('https://www.computrabajo.com.co/empleos-en-bogota-dc?sal=3&pubdate=3')
else:
    driver.get('https://www.computrabajo.com.co/empleos-en-bogota-dc?sal=4&pubdate=3')

#Notificaciones no
#driver.find_element_by_xpath('/html/body/main/div[1]/div[2]/div/button[1]').click()
time.sleep(1)

#Calculo de resultados y páginas
numeropunto = driver.find_element(By.XPATH,'/html/body/main/div[2]/div[2]/div[1]/div[1]/div[1]/h1/span').text
print(numeropunto + " Resultados en Computrabajo: " + "\n")
numero = int(numeropunto.replace('.', ''))
tt1 = numero + tt1
numero = int(math.floor(numero/20))

while sig <= numero:
    
    #Buscar links de las ofertas
    links = driver.find_elements(By.XPATH,'//a[contains(@href, "ofertas-de-trabajo")]')
    
    #Filtrar ofertas
    for elem in links:

        fullstring = elem.get_attribute("text")
        res = any(ele in unidecode.unidecode(fullstring.replace('-', ' ').replace('   ', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('  ', ' ').replace('*', ' ').lower()) for ele in filtrado)
        enlace = elem.get_attribute("href")

        #Verificar si url está en eledb, con la condición de no estar en el filtro anterior, para ahorrar procesamiento.
        if res == False:           
            
            res2 = any(enlace in s for s in compdb)
        
        if res == False and enlace.find(me) == -1 and enlace != me3 and res2 == False:

            comp_res.append((elem.get_attribute("href"), elem.get_attribute("text")))
            total += 1
            contador += 1

        elif me in enlace  or enlace is me3:
            x = 1
        else:
            total += 1

    time.sleep(2)

#Click siguiente

    driver.find_elements(By.XPATH,'//*[@title="Siguiente"]')[0].click()
    progress(sig, numero, status='Filtrando página: ' + str(sig) + ' de ' + str(numero))
    sig +=1
    correct += 1
    time.sleep(2)

else:
    print ('\n') #Separado pues la barra de progreso no se ve bien
    print ("Filtradas " + str(contador) + " de " + str(total-correct) + " Ofertas en computrabajo.com" +'\n')

#Resultados    
tt2 = contador + tt2
print("Total: " + str(tt1) + " Resultados" + '\n')
print("Filtrados: " + str(tt2) + " Resultados" + '\n')

page(ele_res,comp_res)

#Cierre
driver.close()
webbrowser.open("Resultados.html")
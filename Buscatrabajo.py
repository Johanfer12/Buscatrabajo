from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
import webbrowser
import unidecode
import sqlite3
import shutil
import time
import math
import os

#Creación de archivo html

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if os.path.isfile("results.html"):
    os.remove("results.html")

p = open('results.html', 'a')
head = open('encabezado.txt').read().splitlines()

for itm in head:
    p.write(itm + '\n')

linea = open('linea.txt').read()

#Cargar filtros de palabras desde archivo

filtrado = open('filtro.txt').read().splitlines()

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
    #filtrado.append('cliente')
    filtrado.append('center')

#Salario mínimo

sal = int(input("Salario mínimo: 1 = >1m 2 = >1.5m: "))

#Inicialización

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
options.add_argument("--log-level=OFF")
options.add_argument("--ignore-certificate-error")
options.add_argument("--ignore-ssl-errors")
#options.add_argument('--headless')
options.add_argument('--window-size=1920,1080')
options.add_argument("--disable-blink-features=AutomationControlled")
s=Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=options)

################ ELEMPLEO INICIO ################

driver.get('https://www.elempleo.com/co/ofertas-empleo/bogota')
time.sleep(1)

#Click Cookies
driver.find_element(By.XPATH,'/html/body/div[10]/div/div[2]/a').click()

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
print (str(numero) + " resultados encontrados" + '\n')
tt1 = numero
numero = int(math.floor(numero/100))
print(str(numero) + " páginas" + '\n')
time.sleep(1)

while sig <= numero:
    
    #Cargar más resultados
    driver.find_element(By.XPATH,"/html/body/div[8]/div[4]/div[1]/div[4]/div/form/div/select/option[3]").click()
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

            p.write(linea)
            p.write(elem.get_attribute("href") + '">' + elem.get_attribute("title") + "</a></span></p>" +'\n')
            contador += 1
            total += 1

        else:
            total += 1

    time.sleep(2)
    driver.find_element_by_class_name("js-btn-next").click()
    print ("Página " + str (sig) + " de " + str(numero) + " filtrada." + "\n")
    time.sleep(2)
    sig +=1 

else:
    print ("Terminado filtrado elempleo.com" +'\n')
    
#Resultados    
print ("Filtradas " + str(contador) + " de " + str(total) + " Ofertas!")
tt2 = contador

####### COMPUTRABAJO INICIO ##########

head2 = open('encabezado2.txt').read().splitlines()
for itm in head2:
    p.write(itm + '\n')

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
print(numeropunto + " Resultados" + "\n")
numero = int(numeropunto.replace('.', ''))
print(str(numero) + " Resultados sin punto" + "\n")
tt1 = numero + tt1

if numero%20 == 0:
    numero = int(numero/20)
else:
    numero = int(numero/20) + 1

print(str(numero) + " Páginas")

while sig <= numero:
    
    #Buscar links de las ofertas
    links = driver.find_elements_by_xpath('//a[contains(@href, "ofertas-de-trabajo")]')
    
    #Filtrar ofertas
    for elem in links:

        fullstring = elem.get_attribute("text")
        res = any(ele in unidecode.unidecode(fullstring.replace('-', ' ').replace('   ', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('  ', ' ').replace('*', ' ').lower()) for ele in filtrado)
        enlace = elem.get_attribute("href")

        #Verificar si url está en eledb, con la condición de no estar en el filtro anterior, para ahorrar procesamiento.
        if res == False:           
            
            res2 = any(enlace in s for s in compdb)
        
        if res == False and enlace.find(me) == -1 and enlace != me3 and res2 == False:

            p.write(linea)
            p.write(elem.get_attribute("href") + '">' + elem.get_attribute("text") + "</a></span></p>" +'\n')
            total += 1
            contador += 1

        elif me in enlace  or enlace is me3:
            x = 1
        else:
            total += 1

    time.sleep(2)

#Click siguiente

    driver.find_elements_by_xpath('//*[@title="Siguiente"]')[0].click()
    print ("Página " + str(sig) + " de " + str(numero) + " filtrada." + "\n")
    sig +=1
    correct += 1
    time.sleep(2)

else:
    print ("Terminado filtrado computrabajo.com" +'\n')

#Resultados   
 
print ("Filtradas " + str(contador) + " de " + str(total-correct) + " Ofertas!" +'\n')
tt2 = contador + tt2
print("Total: " + str(tt1) + " Resultados" + '\n')
print("Filtrados: " + str(tt2) + " Resultados" + '\n')
#Cierre

p.close()
driver.close()
webbrowser.open("results.html")
time.sleep(300)
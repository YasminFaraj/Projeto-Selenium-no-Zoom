import pandas as pd
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import Counter
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException

edge_options = Options()
edge_options.use_chromium = True

driver = webdriver.Edge(service=Service(), options=edge_options)

#cria os arquivos csv
csv_file_relevantes = 'resultados_zoom_relevantes.csv'
csv_file_avaliados = 'resultados_zoom_avaliados.csv'
csv_file_menor_preco = 'resultados_zoom_menor_preco.csv'

#coleta os resultados das paginas apos as pesquisas
def coletar_resultados(filtro, csv_file):
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Nome do Produto', 'Preço'])

        for page in range(1, 4):
            print(f'Coletando {filtro} - Página {page}')
            results = driver.find_elements(By.XPATH, '//h2[contains(@class, "ProductCard_ProductCard_Name__U_mUQ")]')

            for result in results:
                product_name = result.text

                try:
                    parent_div = result.find_element(By.XPATH, './ancestor::div[contains(@class, "ProductCard")]')
                    product_price = parent_div.find_element(By.XPATH, './/p[@data-testid="product-card::price"]').text
                except NoSuchElementException:
                    product_price = "Preço não disponível"

                print(f"{product_name} - {product_price}")
                writer.writerow([product_name, product_price])

            try:
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[@title="Próxima página"]')))
                next_button.click()
                time.sleep(3)
            except Exception as e:
                print("Próxima página não encontrada ou não clicável:", e)
                break

#pega os melhores produtos e coloca num arquivo csv
def melhores_produtos():
    produtos = []
    precos = []

    for csv_file in [csv_file_relevantes, csv_file_avaliados, csv_file_menor_preco]:
        df = pd.read_csv(csv_file)
        produtos.extend(df['Nome do Produto'].tolist())
        precos.extend(df['Preço'].tolist())

    contagem = Counter(produtos)

    df_resultados = pd.DataFrame(contagem.items(), columns=['Produto', 'Ocorrências'])
    df_resultados['Preço'] = df_resultados['Produto'].map(dict(zip(produtos, precos)))  # Mapear preços

    df_resultados = df_resultados.sort_values(by='Ocorrências', ascending=False)
    df_resultados.to_csv('ranqueamento_produtos.csv', index=False)
    print("Ranqueamento salvo em ranqueamento_produtos.csv")

try:
    driver.get('https://www.zoom.com.br/')

    wait = WebDriverWait(driver, 10)
    search_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="search"]')))
    search_box.send_keys('celular')
    search_box.send_keys(Keys.RETURN)

    time.sleep(3)

    coletar_resultados("Mais Relevantes", csv_file_relevantes)

    order_by_select = wait.until(EC.presence_of_element_located((By.ID, 'orderBy')))
    order_by_select.click()
    rating_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="rating_desc"]')))
    rating_option.click()
    time.sleep(3)
    coletar_resultados("Melhor Avaliado", csv_file_avaliados)

    order_by_select.click()
    price_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="price_asc"]')))
    price_option.click()
    time.sleep(3)
    coletar_resultados("Menor Preço", csv_file_menor_preco)

    melhores_produtos()

finally:
    driver.quit()

print(f'Resultados salvos em {csv_file_relevantes}, {csv_file_avaliados} e {csv_file_menor_preco}')

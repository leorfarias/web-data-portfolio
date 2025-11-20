import os
import time
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def main():
    # --- CONFIGURAÇÃO INICIAL ---
    caminho_base = os.path.expanduser("~")
    caminho_download = os.path.join(caminho_base, "C:\\Users\\leonardo.farias\\OneDrive\\Documentos\\FRANQUIA\\BASES")
    os.makedirs(caminho_download, exist_ok=True)
    

    caminho_arquivo_excel = os.path.join(caminho_download, "pedidos_gestao.xlsx")

    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
      "download.default_directory": caminho_download,
      "download.prompt_for_download": False,
      "download.directory_upgrade": True,
      "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        # --- LOGIN E NAVEGAÇÃO ---
        print("Acessando a página de login...")
        driver.get("https://marca.sintesesolucoes.com.br/SinB2B/")
        usuario = "user"
        senha = "password"
        wait.until(EC.presence_of_element_located((By.ID, "txtUsuario"))).send_keys(usuario)
        driver.find_element(By.ID, "txtSenha").send_keys(senha)
        driver.find_element(By.ID, "btnLogin").click()
        
        print("Navegando para a página de relatórios...")
        time.sleep(5) 
        driver.get("https://marca.sintesesolucoes.com.br/SinB2B/Relatorios/RelatorioExtrato")
        
        print("Aguardando formulário carregar...")
        wait.until(EC.presence_of_element_located((By.ID, "dataInicial")))
        
        print("Preenchendo datas...")
        data_inicio = "01/04/2025"
        campo_data_inicial = driver.find_element(By.ID, "dataInicial")
        driver.execute_script(f"arguments[0].value = '{data_inicio}'; arguments[0].dispatchEvent(new Event('change'));", campo_data_inicial)
        data_fim = "30/04/2025"
        campo_data_final = driver.find_element(By.ID, "dataFinal")
        driver.execute_script(f"arguments[0].value = '{data_fim}'; arguments[0].dispatchEvent(new Event('change'));", campo_data_final)
        print("Datas preenchidas.")
        
        botao_dropdown_colecao = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-id='selectColecao']")))
        botao_dropdown_colecao.click()
        opcao_colecao = wait.until(EC.element_to_be_clickable((By.XPATH, "//a/span[contains(text(), 'Prim. / Verao 2026')]")))
        opcao_colecao.click()
        time.sleep(3)
        
        botao_dropdown_representante = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@data-id='selectRepresentante']")))
        driver.execute_script("arguments[0].click();", botao_dropdown_representante)
        xpath_representante = "//a/span[normalize-space()='FABRICA']"
        opcao_representante = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_representante)))
        opcao_representante.click()
        
        botao_aplicar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'buscarExtrato')]")))
        botao_aplicar.click()
        print("Filtro aplicado.")
        time.sleep(3)
        
        botao_abrir_modal = wait.until(EC.element_to_be_clickable((By.ID, "btnEditarAdmin")))
        botao_abrir_modal.click()
        print("Janela de exportação aberta.")
        time.sleep(2)
        
        botao_continuar_exportacao = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continuar')]")))
        botao_continuar_exportacao.click()
        print("Download iniciado...")

        print(f"Aguardando o download terminar na pasta: {caminho_download}")
        nome_parcial_arquivo = "SinB2B - Extrato de vendas - "
        extensao_arquivo = ".xlsx"
        
        tempo_limite = 90
        tempo_inicial = time.time()
        arquivo_encontrado = False
        caminho_arquivo_final = ""

        while time.time() - tempo_inicial < tempo_limite:
            print(f"Verificando... Arquivos na pasta: {os.listdir(caminho_download)}") 
            arquivos = os.listdir(caminho_download)
            for nome_arquivo in arquivos:
 
                if nome_parcial_arquivo.lower() in nome_arquivo.lower() and nome_arquivo.lower().endswith(extensao_arquivo):
                    print(f"Download concluído! Arquivo encontrado: {nome_arquivo}")
                    arquivo_encontrado = True

                    arquivo_mais_recente = max(glob.glob(os.path.join(caminho_download, f'*{extensao_arquivo}')), key=os.path.getctime)
                    caminho_arquivo_final = os.path.join(caminho_download, "relatorio_sintese_atual.xls")
                    if os.path.exists(caminho_arquivo_final):
                        os.remove(caminho_arquivo_final)
                    os.rename(arquivo_mais_recente, caminho_arquivo_final)
                    print(f"Arquivo renomeado com sucesso para: {caminho_arquivo_final}")
                    break
            if arquivo_encontrado:
                break
            time.sleep(1)

        if not arquivo_encontrado:
            raise Exception(f"Download não concluído no tempo limite de {tempo_limite} segundos.")
        
        return f"Extração concluída com sucesso! O arquivo foi salvo em:\n{caminho_arquivo_final}"

    except Exception as e:
        print(f"Ocorreu um erro durante a execução: {e}")
        traceback.print_exc()
        return f"Ocorreu um erro:\n{e}"

    finally:
        print("Script finalizado. Fechando o navegador.")
        driver.quit()

# Bloco para execução direta do script
if __name__ == "__main__":
    mensagem = main()
    print(mensagem)

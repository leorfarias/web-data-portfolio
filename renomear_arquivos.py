import os

def renomear_arquivos_na_pasta(caminho_da_pasta):
    """
    Renomeia os arquivos em uma pasta, removendo os dois últimos caracteres
    do nome de cada arquivo (antes da extensão).
    """
    try:
        # Verifica se o caminho fornecido é um diretório válido
        if not os.path.isdir(caminho_da_pasta):
            print(f"Erro: O caminho '{caminho_da_pasta}' não é uma pasta válida.")
            return

        print(f"Analisando arquivos em: {caminho_da_pasta}\n")

        # Lista todos os arquivos e pastas no diretório
        for nome_arquivo_original in os.listdir(caminho_da_pasta):
            caminho_completo_original = os.path.join(caminho_da_pasta, nome_arquivo_original)

            # Verifica se o item atual é um arquivo
            if os.path.isfile(caminho_completo_original):
                # Separa o nome do arquivo da sua extensão
                nome_base, extensao = os.path.splitext(nome_arquivo_original)

                # Verifica se o nome base tem pelo menos 2 caracteres para remover
                if len(nome_base) >= 2:
                    # Remove os dois últimos caracteres do nome base
                    novo_nome_base = nome_base[:-2]

                    # Monta o novo nome completo do arquivo com a extensão
                    novo_nome_arquivo = f"{novo_nome_base}{extensao}"
                    caminho_completo_novo = os.path.join(caminho_da_pasta, novo_nome_arquivo)

                    # Renomeia o arquivo
                    os.rename(caminho_completo_original, caminho_completo_novo)
                    print(f'Renomeado: "{nome_arquivo_original}" -> "{novo_nome_arquivo}"')
                else:
                    print(f'Ignorado: "{nome_arquivo_original}" (nome muito curto para renomear)')

        print("\nProcesso de renomeação concluído com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# --- INSTRUÇÕES DE USO ---
if __name__ == "__main__":
    # 1. Altere o caminho abaixo para a pasta onde estão seus arquivos.
    #    IMPORTANTE: Use barras duplas "\\" ou barras normais "/" no caminho.
    #
    # Exemplo no Windows:
    # caminho_pasta = "C:\\Users\\SeuUsuario\\Desktop\\MinhaPasta"
    # ou
    # caminho_pasta = "C:/Users/SeuUsuario/Desktop/MinhaPasta"

    caminho_pasta = "T:\\DESIGN_VM\\2026\\03. INVERNO 26\\01. ATACADO\\01. Sintese\\RENOMEAR\\Tissi e Camila"

    # 2. Execute o script.
    if caminho_pasta == "T:\\DESIGN_VM\\2026\\03. INVERNO 26\\01. ATACADO\\01. Sintese\\RENOMEAR\\Tissi e Camila":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ATENÇÃO: Por favor, edite o script e defina a    !!!")
        print("!!! variável 'caminho_pasta' com o caminho correto.  !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        renomear_arquivos_na_pasta(caminho_pasta)

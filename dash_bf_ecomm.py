import streamlit as st
import pandas as pd
import pyodbc  # Importa a biblioteca que você está usando
import time
import altair as alt
import os
import dotenv

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard Black Friday",
    page_icon="💸",
    layout="wide"
)

# --- 1. DETALHES DA SUA CONEXÃO ---
# Preencha com suas credenciais
server = os.environ['server_integ']
database = os.environ['database_integ']
username = os.environ['login_integ']
password = os.environ['password_integ']
driver = os.environ['driver']
port = os.environ['port']

# Monta a string de conexão
conn_str = f'DRIVER={driver}; SERVER={server}; PORT={port}; DATABASE={database}; UID={username}; PWD={password}'

# --- 2. SUA QUERY SQL ---
# Exatamente a query que você forneceu
query = """
SELECT  [OPERACAO]
      , [COD_ORIGEM]
      , [ORIGEM]
      , [DESC_ORIGEM]
      , [ID_FATURAMENTO]
      , [ID_PEDIDO]
      , [PEDIDO_SITE]
      , [PEDIDO_OMS]
      , [CODIGO_FILIAL_VENDA]
      , [FILIAL_VENDA]
      , [FILIAL_VENDA_CANAL]
      , [VENDEDOR]
      , [CODIGO_FILIAL_FATURAMENTO]
      , [FILIAL_FATURAMENTO]
      , [FILIAL_FATURAMENTO_CANAL]
      , CAST([DATA_VENDA] AS DATE) AS DATA_VENDA
      , CAST([DATA_FATURAMENTO] AS DATE) AS DATA_FATURAMENTO
      , [TICKET]
      , [COD_TIPO_VENDEDOR]
      , [COD_SUBTIPO_VENDEDOR]
      , [VENDA_CODIGO]
      , [PRECO_ORIGINAL]
      , [PRECO_CUSTO]
      , [PRECO_LIQUIDO]
      , [QTDE]
      , [VALOR_TOTAL]
      , [PRODUTO]
      , [DESC_PRODUTO]
      , [COR_PRODUTO]
      , [DESC_COR_PRODUTO]
      , [COLECAO]
      , [DESC_COLECAO]
      , [GRUPO_PRODUTO]
      , [SUBGRUPO_PRODUTO]
      , [LINHA]
      , [GRIFFE]
      , [FABRICANTE]
      , CASE WHEN FABRICANTE = 'DRESS TO' THEN 'INTERNO' ELSE 'EXTERNO' END AS TIPO_FABRICANTE
      , [ESTILISTA]
      , [CODIGO_CLIENTE]
      , [TIPO_VENDA]
      , [ID_CATEGORIA]
      , [DESC_CATEGORIA]
      , [DESC_CANAL_ORIGEM]
      , [FORMA_ENVIO]
      , [TIPO_ENVIO]
  FROM [dbo].[W_DRESS_VENDAS_PRODUTO_MULTICANAL] WITH (NOLOCK)
  WHERE 1=1
    AND CAST([DATA_FATURAMENTO] AS DATE) BETWEEN '2025-11-01' AND GETDATE()-1
    AND FILIAL_VENDA_CANAL IN ('VAREJO', 'E-COMMERCE', 'FRANQUIA')
"""


# --- Função para Buscar Dados ---
@st.cache_data(ttl=60)  # Cache de 60 segundos
def carregar_dados():
    """Busca os dados do banco usando sua conexão e query"""
    print(f"Buscando dados no banco... {time.strftime('%H:%M:%S')}")
    try:
        # Usa o pyodbc.connect diretamente
        conn = pyodbc.connect(conn_str)
        
        # Lê os dados com o pandas
        df = pd.read_sql(query, conn)
        
        # Fecha a conexão
        conn.close()
        
        # Converte colunas de data (o pandas pode não pegar automaticamente)
        df['DATA_FATURAMENTO'] = pd.to_datetime(df['DATA_FATURAMENTO'])
        df['DATA_VENDA'] = pd.to_datetime(df['DATA_VENDA'])
        
        return df
        
    except Exception as e:
        # Mostra um erro amigável no dashboard se a conexão falhar
        st.error(f"Erro ao conectar ao banco ou executar a query: {e}")
        return pd.DataFrame() # Retorna um DataFrame vazio para não quebrar o script


# --- Início do Dashboard ---
df = carregar_dados()

st.title(f"💸 Dashboard de Vendas - Black Friday (Atualizado: {pd.Timestamp.now().strftime('%H:%M:%S')})")

if df.empty:
    st.warning("Nenhum dado encontrado para o período.")
else:
    # --- NOVO: Adicionando o Filtro na Sidebar ---
    st.sidebar.header("Filtros")
    
    # 1. Pega as opções únicas da coluna
    opcoes_canal = sorted(df['FILIAL_VENDA_CANAL'].unique())
    
    # 2. Cria o widget multiselect, com todas as opções marcadas como padrão
    selecao_canal = st.sidebar.multiselect(
        "Selecione o(s) Canal(is) de Venda:",
        options=opcoes_canal,
        default=opcoes_canal 
    )

    # 3. Cria o DataFrame filtrado com base na seleção
    # Se nada for selecionado, ele ficará vazio (o que é o correto)
    df_filtrado = df[df['FILIAL_VENDA_CANAL'].isin(selecao_canal)]
    
    # -----------------------------------------------

    # --- 1. KPIs Principais (Usando agora o df_filtrado) ---
    kpi1, kpi2, kpi3 = st.columns(3)

    # GMV: Soma do VALOR_TOTAL (do df_filtrado)
    gmv = df_filtrado['VALOR_TOTAL'].sum()
    
    # Total de Pedidos: Contagem única de ID_PEDIDO (do df_filtrado)
    total_pedidos = df_filtrado['ID_PEDIDO'].nunique()
    
    # Ticket Médio
    ticket_medio = gmv / total_pedidos if total_pedidos > 0 else 0

    kpi1.metric(
        label="Receita Total (GMV)",
        value=f"R$ {gmv:,.2f}"
    )
    kpi2.metric(
        label="Pedidos Únicos",
        value=f"{total_pedidos:,}"
    )
    kpi3.metric(
        label="Ticket Médio (AOV)",
        value=f"R$ {ticket_medio:,.2f}"
    )

    st.markdown("---")

    # --- 2. Gráficos (Usando agora o df_filtrado) ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Vendas por Dia de Faturamento")
        # Usa o df_filtrado
        vendas_dia = df_filtrado.groupby('DATA_FATURAMENTO')['VALOR_TOTAL'].sum().reset_index()
        st.bar_chart(vendas_dia.set_index('DATA_FATURAMENTO'))

    with col2:
        st.subheader("Top 5 Produtos (por Receita)")
        # Usa o df_filtrado
        top_produtos = df_filtrado.groupby('DESC_PRODUTO')['VALOR_TOTAL'].sum().nlargest(5).sort_values(ascending=True)
        st.bar_chart(top_produtos)

    # --- 3. Tabela de Últimos Pedidos (Usando agora o df_filtrado) ---
    st.subheader("Visão Detalhada dos Itens Faturados")
    # Usa o df_filtrado
    st.dataframe(df_filtrado.sort_values('DATA_FATURAMENTO', ascending=False).head(20))

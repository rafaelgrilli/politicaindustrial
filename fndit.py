import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import plotly.express as px

# --- Funções de Cálculo ---

@st.cache_data
def calcular_parcela_price_cached(valor_financiamento, taxa_juros_mensal, num_parcelas):
    """Calcula a parcela fixa do sistema Price."""
    return calcular_parcela_price(valor_financiamento, taxa_juros_mensal, num_parcelas)

def calcular_parcela_price(valor_financiamento, taxa_juros_mensal, num_parcelas):
    """Calcula a parcela fixa do sistema Price."""
    if num_parcelas <= 0:
        return float('inf')
    if taxa_juros_mensal <= 1e-9:
        return valor_financiamento / num_parcelas
    
    try:
        denominador = 1 - (1 + taxa_juros_mensal)**(-num_parcelas)
        if abs(denominador) < 1e-9:
            return valor_financiamento / num_parcelas
        return (valor_financiamento * taxa_juros_mensal) / denominador
    except OverflowError:
        return float('inf')

@st.cache_data
def calcular_vpl_cached(fluxos_caixa, taxa_desconto_mensal):
    """Calcula o Valor Presente Líquido (VPL) de uma série de fluxos de caixa."""
    return calcular_vpl(fluxos_caixa, taxa_desconto_mensal)

def calcular_vpl(fluxos_caixa, taxa_desconto_mensal):
    """Calcula o Valor Presente Líquido (VPL) de uma série de fluxos de caixa."""
    if abs(taxa_desconto_mensal) < 1e-9:
        return sum(fluxos_caixa)
    
    vpl = 0
    for t, fluxo in enumerate(fluxos_caixa):
        if t > 0 and abs(taxa_desconto_mensal) > 1e-9:
            discount_factor = math.exp(-t * math.log(1 + taxa_desconto_mensal))
        else:
            discount_factor = 1 / ((1 + taxa_desconto_mensal)**t)
        vpl += fluxo * discount_factor
    return vpl

# --- Configurações da Página Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Fomento à Descarbonização (FNDIT)")

st.title("🌱 Simulador de Política Pública de Fomento à Descarbonização")
st.markdown("""
Esta ferramenta permite simular o impacto de diferentes estratégias de alocação de recursos do FNDIT
em projetos de descarbonização, considerando a elasticidade da demanda por crédito.
""")

# --- Add informational expanders ---
with st.expander("ℹ️ Entenda a Elasticidade da Demanda"):
    st.markdown("""
    A elasticidade da demanda mede quanto a quantidade demandada de crédito responde a mudanças na taxa de juros.
    - **Valor de -1.5** significa que uma redução de 1% na taxa de juros aumenta a demanda em aproximadamente 1.5%.
    - **Valores mais negativos** indicam demanda mais sensível a mudanças nas taxas de juros.
    """)

with st.expander("ℹ️ Como interpretar os resultados"):
    st.markdown("""
    **Como interpretar os resultados:**
    - **VPL para o Tomador**: Valores mais altos indicam melhor custo-benefício para quem recebe o financiamento.
    - **Alavancagem**: Mostra quanto capital privado é mobilizado por cada real público investido.
    - **Eficiência de Alocação**: Percentual que mostra o aproveitamento dos recursos disponíveis.
    - **Custo-Efetividade**: Compara o custo do projeto (ou do subsídio) com o preço de mercado da tonelada de CO2e evitada.
    """)

# --- Parâmetros de Entrada na barra lateral ---
st.sidebar.header("⚙️ Parâmetros da Simulação")

# Seção de Parâmetros Financeiros
st.sidebar.subheader("💰 Parâmetros Financeiros")
valor_projeto = st.sidebar.slider("1. Valor do Projeto de Descarbonização (R$)", 
                                  min_value=1_000_000, max_value=100_000_000,
                                  value=30_000_000, step=1_000_000)
st.sidebar.info("Este é o custo total de um projeto de descarbonização, como a instalação de painéis solares ou uma frota de veículos elétricos.")

taxa_juros_full_anual = st.sidebar.slider("2. Taxa de Juros Full (a.a. %) - Mercado", 
                                          min_value=0.0, max_value=15.0, 
                                          value=7.8, step=0.1) / 100
st.sidebar.info("A taxa de juros que o tomador de crédito pagaria em uma condição de mercado 'normal', sem subsídios do FNDIT.")

montante_fndit = st.sidebar.slider("3. Montante no FNDIT para Subsídios/Crédito (R$)", 
                                   min_value=10_000_000, max_value=1_000_000_000, 
                                   value=200_000_000, step=10_000_000)
st.sidebar.info("O total de recursos disponíveis no FNDIT para apoiar os projetos. Este montante pode ser usado para crédito ou subsídio.")

prazo_anos = st.sidebar.slider("4. Prazo para Amortização (anos)", 
                               min_value=1, max_value=20,
                               value=5, step=1)
st.sidebar.info("O número de anos para o tomador de crédito pagar o financiamento.")

taxa_juros_subsidio_anual = st.sidebar.slider("5. Taxa de Juros Subsidiada Alvo (a.a. %)", 
                                               min_value=0.0, max_value=max(0.1, taxa_juros_full_anual * 100),
                                               value=min(3.0, taxa_juros_full_anual * 100), step=0.1) / 100
st.sidebar.info("A taxa de juros reduzida que o FNDIT oferece aos projetos. A diferença entre esta taxa e a taxa 'full' de mercado é o subsídio.")

elasticidade_demanda = st.sidebar.slider("6. Elasticidade da Demanda por Crédito de Descarbonização", 
                                         min_value=-5.0, max_value=-0.1,
                                         value=-1.5, step=0.1)
st.sidebar.info("Mede a sensibilidade da demanda por crédito em relação às mudanças na taxa de juros. Uma elasticidade de -1.5, por exemplo, indica que uma redução de 1% na taxa de juros resulta em um aumento de 1.5% na demanda por projetos.")

taxa_desconto_tomador_anual = st.sidebar.slider("7. Taxa de Desconto para VPL (Tomador) a.a. (%)",
                                                min_value=0.0, max_value=25.0,
                                                value=12.0, step=0.5) / 100
st.sidebar.info("Representa a taxa de retorno mínima aceitável do tomador de crédito. É usada para calcular o valor presente de futuros fluxos de caixa (VPL).")

# Validações dos parâmetros
if taxa_juros_subsidio_anual >= taxa_juros_full_anual:
    st.sidebar.warning("A taxa subsidiada deve ser menor que a taxa full para ter efeito.")
if valor_projeto <= 0:
    st.sidebar.error("O valor do projeto deve ser positivo.")
if montante_fndit < valor_projeto:
    st.sidebar.warning("O montante do FNDIT é menor que o valor de um projeto.")

# Seção de Parâmetros de Descarbonização
st.sidebar.subheader("🌱 Parâmetros de Descarbonização")
abordagem_co2 = st.sidebar.radio(
    "1. Metodologia para Estimativa de CO2 Evitado",
    ["Nenhuma", "Setorial (Recomendado)", "Por Tecnologia Específica", "Meta Customizada"],
    key="abordagem_co2",
    help="Baseado em metodologias do MCTI, EPE e estudos setoriais brasileiros."
)

fator_co2 = 0
metodologia_info = ""

if abordagem_co2 == "Setorial (Recomendado)":
    fatores_setor = {
        "Energia Renovável": {"fator": 180, "base": "Emissões evitadas de termelétricas (0,8 tCO2e/MWh) × fator de capacidade", "fonte": "EPE (2023), MCTI (2023)", "ano": 2023},
        "Eficiência Energética": {"fator": 120, "base": "Redução de consumo em indústrias energy-intensive", "fonte": "Estudos setoriais cimento/aço (2023)", "ano": 2023},
        "Transporte Sustentável": {"fator": 150, "base": "Eletrificação substituindo diesel (2,68 kgCO2/litro)", "fonte": "MCTI - Fatores de Emissão (2024)", "ano": 2024},
        "Agricultura de Baixo Carbono": {"fator": 90, "base": "ILPF, recuperação de pastagens, fixação biológica de N₂", "fonte": "Embrapa, Programa ABC+ (2023)", "ano": 2023},
        "Manejo de Resíduos": {"fator": 80, "base": "Metano evitado (GWP 28× CO₂) + energia renovável", "fonte": "IPCC, metodologias CDM (2023)", "ano": 2023},
        "Outros": {"fator": 60, "base": "Setores diversos com menor potencial específico", "fonte": "Estimativa conservadora (2024)", "ano": 2024}
    }
    setor_name = st.sidebar.selectbox("2. Setor do Projeto", list(fatores_setor.keys()), key="setor_selector")
    fator_co2 = fatores_setor[setor_name]["fator"]
    metodologia_info = f"**Base técnica:** {fatores_setor[setor_name]['base']}\n**Fonte:** {fatores_setor[setor_name]['fonte']}\n**Ano de referência:** {fatores_setor[setor_name]['ano']}"

elif abordagem_co2 == "Por Tecnologia Específica":
    fatores_tecnologia = {
        "Solar Fotovoltaica": {"fator": 200, "calculo": "1.600 MWh/ano × 0,8 tCO2e/MWh × 25 anos / R$ 4 milhões", "premissas": "Fator de capacidade 20% (Nordeste: 25%, Sul: 18%)", "fontes": "ABSolar, ONS (2023)"},
        "Eólica": {"fator": 190, "calculo": "3.000 MWh/ano × 0,8 tCO2e/MWh × 25 anos / R$ 6 milhões", "premissas": "Fator de capacidade 35% (Nordeste: 45%, Sul: 32%)", "fontes": "ABEEólica, ONS (2023)"},
        "Biogás/Biometano": {"fator": 130, "calculo": "Metano evitado (GWP 28) + substituição de diesel", "premissas": "Potencial de aquecimento global do metano (IPCC AR6)", "fontes": "EPE, MCTI (2023)"},
        "Veículos Elétricos": {"fator": 160, "calculo": "30.000 km/ano × 0,15 kWh/km × 0,8 tCO2e/MWh × 10 anos", "premissas": "Vida útil 10 anos, rodagem média brasileira (ANTT 2023)", "fontes": "ANTP, MCTI (2024)"},
        "Captura e Armazenamento de Carbono": {"fator": 110, "calculo": "Custos elevados vs. potencial tecnológico atual", "premissas": "Tecnologia ainda em desenvolvimento no Brasil", "fontes": "Estudos internacionais adaptados (2024)"},
        "Hidrogênio Verde": {"fator": 140, "calculo": "Tecnologia emergente com custos elevados", "premissas": "Baseado em projetos piloto internacionais", "fontes": "IEA, EPE (2023)"},
        "Outras": {"fator": 70, "calculo": "Média ponderada de tecnologias não especificadas", "premissas": "Estimativa conservadora", "fontes": "Várias (2023-2024)"}
    }
    tecnologia_name = st.sidebar.selectbox("2. Tecnologia de Descarbonização", list(fatores_tecnologia.keys()), key="tecnologia_selector")
    fator_co2 = fatores_tecnologia[tecnologia_name]["fator"]
    metodologia_info = f"**Cálculo:** {fatores_tecnologia[tecnologia_name]['calculo']}\n**Premissas:** {fatores_tecnologia[tecnologia_name]['premissas']}\n**Fontes:** {fatores_tecnologia[tecnologia_name]['fontes']}"

elif abordagem_co2 == "Meta Customizada":
    fator_co2 = st.sidebar.slider(
        "2. Fator de Redução (tCO2e/milhão R$/ano)",
        min_value=10, max_value=500, value=100, step=10,
        key="fator_custom_slider",
        help="Range baseado em estudos setoriais brasileiros (2023-2024)."
    )
    metodologia_info = "**Atenção:** Fator customizado - recomenda-se validação técnica com especialista setorial."

regiao = st.sidebar.selectbox(
    "3. Região do Projeto",
    ["Nacional", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
    key="regiao_selector",
    help="Fatores podem variar conforme o potencial regional de cada tipo de projeto."
)

# --- Cálculos Financeiros (não alterado) ---
prazo_meses = prazo_anos * 12
taxa_juros_full_mensal = (1 + taxa_juros_full_anual)**(1/12) - 1 if taxa_juros_full_anual > 0 else 0.0
taxa_juros_subsidio_mensal = (1 + taxa_juros_subsidio_anual)**(1/12) - 1 if taxa_juros_subsidio_anual > 0 else 0.0
taxa_desconto_tomador_mensal = (1 + taxa_desconto_tomador_anual)**(1/12) - 1 if taxa_desconto_tomador_anual > 0 else 0.0

st.header("Resultados da Simulação Financeira")

col1, col2, col3 = st.columns(3)

# Cenário 1: Crédito com Juros Full
with col1:
    st.subheader("Cenário 1: Crédito com Juros Full")
    qtd_projetos_credito_full = montante_fndit // valor_projeto if valor_projeto > 0 else 0
    st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_credito_full):,}".replace(",", "."))
    parcela_full = calcular_parcela_price_cached(valor_projeto, taxa_juros_full_mensal, prazo_meses)
    custo_total_full = parcela_full * prazo_meses
    juros_total_full = custo_total_full - valor_projeto
    st.markdown(f"**Detalhes por Projeto (Juros Full):**")
    st.markdown(f"- Parcela Mensal: R$ {parcela_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.markdown(f"- Juros Totais Pagos: R$ {juros_total_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    fluxos_tomador_full = [-parcela_full] * prazo_meses
    fluxos_tomador_full[0] += valor_projeto
    vpl_tomador_full = calcular_vpl_cached(fluxos_tomador_full, taxa_desconto_tomador_mensal)
    st.markdown(f"- VPL para o Tomador: R$ {vpl_tomador_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# Cenário 2: Subsídio de Juros
with col2:
    st.subheader("Cenário 2: Subsídio de Juros")
    parcela_subsidio = calcular_parcela_price_cached(valor_projeto, taxa_juros_subsidio_mensal, prazo_meses)
    custo_total_subsidio = parcela_subsidio * prazo_meses
    juros_total_subsidio = custo_total_subsidio - valor_projeto
    subs_por_projeto = (parcela_full - parcela_subsidio) * prazo_meses
    
    if subs_por_projeto <= 1e-9 or subs_por_projeto == float('inf'):
        qtd_projetos_capacidade_fndit_display = "Infinito" 
        qtd_projetos_capacidade_fndit = float('inf')
    else:
        qtd_projetos_capacidade_fndit = montante_fndit // subs_por_projeto
        qtd_projetos_capacidade_fndit_display = f"{int(qtd_projetos_capacidade_fndit):,}".replace(",", ".")
        
    st.metric("Projetos Financiáveis (Capacidade FNDIT)", qtd_projetos_capacidade_fndit_display)
    st.markdown(f"**Detalhes por Projeto (Juros Subsidiados):**")
    st.markdown(f"- Parcela Mensal: R$ {parcela_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.markdown(f"- Juros Totais Pagos: R$ {juros_total_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.markdown(f"- **Subsídio FNDIT por Projeto: R$ {subs_por_projeto:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    
    fluxos_tomador_subsidio = [-parcela_subsidio] * prazo_meses
    fluxos_tomador_subsidio[0] += valor_projeto
    vpl_tomador_subsidio = calcular_vpl_cached(fluxos_tomador_subsidio, taxa_desconto_tomador_mensal)
    st.markdown(f"- VPL para o Tomador: R$ {vpl_tomador_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# Cenário 3: Subvenção Total do Projeto
with col3:
    st.subheader("Cenário 3: Subvenção Total")
    qtd_projetos_subvencao = montante_fndit // valor_projeto if valor_projeto > 0 else 0
    st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_subvencao):,}".replace(",", "."))
    st.markdown(f"**Detalhes por Projeto (Subvenção Total):**")
    st.markdown(f"- Valor da Subvenção: R$ {valor_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.markdown(f"*(Não há parcelas ou juros, pois o valor é doado)*")
    st.markdown(f"- VPL para o Tomador: R$ {valor_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- Análise Comparativa e Indicadores de Impacto ---
st.header("Análise Comparativa e Indicadores de Impacto")
col_ind1, col_ind2, col_ind3 = st.columns(3)
with col_ind1:
    st.subheader("Custo de Subsídio por Projeto (FNDIT)")
    if subs_por_projeto > 1e-9:
        st.metric("Subsídio de Juros", f"R$ {subs_por_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown("*(Este é o valor que o FNDIT gasta por projeto para reduzir os juros para o tomador)*")
    else:
        st.info("Não há subsídio de juros ou é insignificante.")
with col_ind2:
    st.subheader("Eficiência de Alocação")
    if taxa_juros_full_anual <= 0:
        st.warning("Não é possível calcular variação percentual na taxa de juros quando a taxa full é 0%.")
        qtd_projetos_demandados_elasticidade = 0
    else:
        variacao_juros_percentual = (taxa_juros_subsidio_anual - taxa_juros_full_anual) / taxa_juros_full_anual
        demanda_base_full = qtd_projetos_credito_full
        aumento_demanda_percentual = elasticidade_demanda * variacao_juros_percentual
        qtd_projetos_demandados_elasticidade = demanda_base_full * (1 + aumento_demanda_percentual)
        st.metric("Projetos Demandados (Elasticidade)", f"{int(qtd_projetos_demandados_elasticidade):,}".replace(",", "."))
        
    if qtd_projetos_capacidade_fndit != float('inf'):
        projetos_efetivos = min(qtd_projetos_demandados_elasticidade, qtd_projetos_capacidade_fndit)
        if qtd_projetos_capacidade_fndit > 0:
            utilizacao_recursos = projetos_efetivos / qtd_projetos_capacidade_fndit
            st.metric("Utilização dos Recursos Disponíveis", f"{utilizacao_recursos:.2%}")
    else:
        st.metric("Projetos Efetivamente Financiáveis", f"{int(qtd_projetos_demandados_elasticidade):,}".replace(",", "."))
        st.info("Capacidade de financiamento é ilimitada com o subsídio atual.")

with col_ind3:
    st.subheader("Alavancagem de Capital Privado")
    if subs_por_projeto > 1e-9:
        alavancagem_subs = valor_projeto / subs_por_projeto
        st.metric("Alavancagem (Subsídio de Juros)", f"{alavancagem_subs:,.2f}x".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"*(Cada R$ 1 do FNDIT em subsídio atrai R$ {alavancagem_subs:,.2f} de capital privado)*".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.info("Não aplicável ou calculável.")
    st.metric("Alavancagem (Subvenção Total)", "Não aplicável (1:1)")

# --- Gráfico de Comparação de Projetos ---
st.header("Comparativo de Quantidade de Projetos")
data = {'Cenário': ['Crédito Full', 'Subsídio Juros (Capac. FNDIT)', 'Subsídio Juros (Demanda)', 'Subvenção Total'],
        'Projetos Financiáveis': [qtd_projetos_credito_full, qtd_projetos_capacidade_fndit, qtd_projetos_demandados_elasticidade, qtd_projetos_subvencao]}
df_projetos = pd.DataFrame(data)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(df_projetos['Cenário'], df_projetos['Projetos Financiáveis'], color=['skyblue', 'lightgreen', 'salmon', 'gold'])
ax.set_ylabel("Quantidade de Projetos")
ax.set_title("Projetos Financiados por Cenário")
plt.xticks(rotation=15, ha='right')
for bar in bars:
    yval = bar.get_height()
    if yval == float('inf'):
        ax.text(bar.get_x() + bar.get_width()/2, 0, "Inf.", ha='center', va='bottom', fontsize=10, color='red')
    else:
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f'{int(yval):,}'.replace(",", "."), ha='center', va='bottom', fontsize=10)
plt.tight_layout()
st.pyplot(fig)

# --- Análise Financeira por Cenário ---
st.header("Análise Financeira por Cenário")
comparison_data = {'Cenário': ['Crédito Full', 'Subsídio Juros', 'Subvenção Total'],
                    'Custo Total por Projeto': [custo_total_full, custo_total_subsidio, valor_projeto],
                    'VPL para Tomador': [vpl_tomador_full, vpl_tomador_subsidio, valor_projeto],
                    'Custo FNDIT por Projeto': [0, subs_por_projeto, valor_projeto]}
df_comparison = pd.DataFrame(comparison_data)
df_display = df_comparison.copy()
for col in ['Custo Total por Projeto', 'VPL para Tomador', 'Custo FNDIT por Projeto']:
    df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if not pd.isna(x) else "R$ 0,00")
st.dataframe(df_display)

# --- Seção de Descarbonização ---
st.markdown("---")
fatores_regionais = {"Nacional": 1.0, "Norte": 1.1, "Nordeste": 1.2, "Centro-Oeste": 0.9, "Sudeste": 1.0, "Sul": 0.95}

fator_co2 = 0
metodologia_info = ""

if abordagem_co2 == "Setorial (Recomendado)":
    fatores_setor = {
        "Energia Renovável": {"fator": 180, "base": "Emissões evitadas de termelétricas (0,8 tCO2e/MWh) × fator de capacidade", "fonte": "EPE (2023), MCTI (2023)", "ano": 2023},
        "Eficiência Energética": {"fator": 120, "base": "Redução de consumo em indústrias energy-intensive", "fonte": "Estudos setoriais cimento/aço (2023)", "ano": 2023},
        "Transporte Sustentável": {"fator": 150, "base": "Eletrificação substituindo diesel (2,68 kgCO2/litro)", "fonte": "MCTI - Fatores de Emissão (2024)", "ano": 2024},
        "Agricultura de Baixo Carbono": {"fator": 90, "base": "ILPF, recuperação de pastagens, fixação biológica de N₂", "fonte": "Embrapa, Programa ABC+ (2023)", "ano": 2023},
        "Manejo de Resíduos": {"fator": 80, "base": "Metano evitado (GWP 28× CO₂) + energia renovável", "fonte": "IPCC, metodologias CDM (2023)", "ano": 2023},
        "Outros": {"fator": 60, "base": "Setores diversos com menor potencial específico", "fonte": "Estimativa conservadora (2024)", "ano": 2024}
    }
    setor_name = st.sidebar.selectbox("2. Setor do Projeto", list(fatores_setor.keys()), key="setor_selector")
    fator_co2 = fatores_setor[setor_name]["fator"]
    metodologia_info = f"**Base técnica:** {fatores_setor[setor_name]['base']}\n**Fonte:** {fatores_setor[setor_name]['fonte']}\n**Ano de referência:** {fatores_setor[setor_name]['ano']}"

elif abordagem_co2 == "Por Tecnologia Específica":
    fatores_tecnologia = {
        "Solar Fotovoltaica": {"fator": 200, "calculo": "1.600 MWh/ano × 0,8 tCO2e/MWh × 25 anos / R$ 4 milhões", "premissas": "Fator de capacidade 20% (Nordeste: 25%, Sul: 18%)", "fontes": "ABSolar, ONS (2023)"},
        "Eólica": {"fator": 190, "calculo": "3.000 MWh/ano × 0,8 tCO2e/MWh × 25 anos / R$ 6 milhões", "premissas": "Fator de capacidade 35% (Nordeste: 45%, Sul: 32%)", "fontes": "ABEEólica, ONS (2023)"},
        "Biogás/Biometano": {"fator": 130, "calculo": "Metano evitado (GWP 28) + substituição de diesel", "premissas": "Potencial de aquecimento global do metano (IPCC AR6)", "fontes": "EPE, MCTI (2023)"},
        "Veículos Elétricos": {"fator": 160, "calculo": "30.000 km/ano × 0,15 kWh/km × 0,8 tCO2e/MWh × 10 anos", "premissas": "Vida útil 10 anos, rodagem média brasileira (ANTT 2023)", "fontes": "ANTP, MCTI (2024)"},
        "Captura e Armazenamento de Carbono": {"fator": 110, "calculo": "Custos elevados vs. potencial tecnológico atual", "premissas": "Tecnologia ainda em desenvolvimento no Brasil", "fontes": "Estudos internacionais adaptados (2024)"},
        "Hidrogênio Verde": {"fator": 140, "calculo": "Tecnologia emergente com custos elevados", "premissas": "Baseado em projetos piloto internacionais", "fontes": "IEA, EPE (2023)"},
        "Outras": {"fator": 70, "calculo": "Média ponderada de tecnologias não especificadas", "premissas": "Estimativa conservadora", "fontes": "Várias (2023-2024)"}
    }
    tecnologia_name = st.sidebar.selectbox("2. Tecnologia de Descarbonização", list(fatores_tecnologia.keys()), key="tecnologia_selector")
    fator_co2 = fatores_tecnologia[tecnologia_name]["fator"]
    metodologia_info = f"**Cálculo:** {fatores_tecnologia[tecnologia_name]['calculo']}\n**Premissas:** {fatores_tecnologia[tecnologia_name]['premissas']}\n**Fontes:** {fatores_tecnologia[tecnologia_name]['fontes']}"

elif abordagem_co2 == "Meta Customizada":
    fator_co2 = st.sidebar.slider(
        "2. Fator de Redução (tCO2e/milhão R$/ano)",
        min_value=10, max_value=500, value=100, step=10,
        key="fator_custom_slider",
        help="Range baseado em estudos setoriais brasileiros (2023-2024)."
    )
    metodologia_info = "**Atenção:** Fator customizado - recomenda-se validação técnica com especialista setorial."

if abordagem_co2 != "Nenhuma" and fator_co2 > 0:
    co2_evitado_anual = (valor_projeto / 1_000_000) * fator_co2 * fatores_regionais[regiao]
    reducao_total_periodo = co2_evitado_anual * prazo_anos

    st.header("🔥 Impacto de Descarbonização Estimado")
    
    with st.expander("📋 Metodologia e Fontes"):
        st.write(metodologia_info)
        if regiao != "Nacional":
            st.info(f"**Fator regional aplicado:** {fatores_regionais[regiao]:.2f}x para {regiao}")
    
    col1_co2, col2_co2, col3_co2, col4_co2 = st.columns(4)
    with col1_co2:
        st.metric("Redução Anual de CO2e", f"{co2_evitado_anual:,.0f} t/ano")
    with col2_co2:
        st.metric("Redução Total no Período", f"{reducao_total_periodo:,.0f} t")
    with col3_co2:
        if subs_por_projeto > 0 and reducao_total_periodo > 0:
            custo_por_tonelada = subs_por_projeto / reducao_total_periodo
            tipo_custo = "Subsídio"
        else:
            custo_por_tonelada = valor_projeto / reducao_total_periodo if reducao_total_periodo > 0 else 0
            tipo_custo = "Investimento"
        st.metric(f"Custo {tipo_custo}/Tonelada", f"R$ {custo_por_tonelada:,.0f}")
    with col4_co2:
        carros_equivalentes = co2_evitado_anual / 4
        st.metric("Equiv. Carros Retirados", f"{carros_equivalentes:,.0f}")
    
    st.subheader("💰 Análise de Custo-Efetividade")
    referencias_mercado = {"Mercado Voluntário (Mín.)": 50, "Mercado Voluntário (Máx.)": 180, "Regulado (Mín.)": 80, "Regulado (Máx.)": 250, "CBIOs (RenovaBio)": 85, "Seu Projeto": custo_por_tonelada}
    df_comparacao = pd.DataFrame([{"Categoria": k, "Custo (R$/tCO2e)": v, "Tipo": "Mercado" if k != "Seu Projeto" else "Projeto"} for k, v in referencias_mercado.items()])
    fig = px.bar(df_comparacao, x="Categoria", y="Custo (R$/tCO2e)", color="Tipo", title="Comparação com Referências do Mercado Brasileiro de Carbono (2024)", color_discrete_map={"Mercado": "lightblue", "Projeto": "darkgreen"})
    st.plotly_chart(fig, use_container_width=True)

    if custo_por_tonelada <= 150:
        st.success(f"✅ **Custo-efetivo**: Abaixo ou igual ao mercado voluntário (R$ {custo_por_tonelada:,.0f}/tCO2e).")
    elif custo_por_tonelada <= 200:
        st.info(f"ℹ️ **Competitivo**: Dentro do range regulado (R$ {custo_por_tonelada:,.0f}/tCO2e).")
    elif custo_por_tonelada <= 350:
        st.warning(f"⚠️ **Acima do mercado**: Justifique os co-benefícios (R$ {custo_por_tonelada:,.0f}/tCO2e).")
    else:
        st.error(f"❌ **Muito alto**: Revise a parametrização (R$ {custo_por_tonelada:,.0f}/tCO2e).")

    st.subheader("🎯 Impacto Agregado da Política")
    if qtd_projetos_capacidade_fndit != float('inf'):
        projetos_efetivos = min(qtd_projetos_demandados_elasticidade, qtd_projetos_capacidade_fndit)
        reducao_total_politica = co2_evitado_anual * projetos_efetivos
        col_impacto1, col_impacto2, col_impacto3 = st.columns(3)
        with col_impacto1:
            st.metric("Redução Anual da Política", f"{reducao_total_politica:,.0f} t/ano")
        with col_impacto2:
            st.metric("Redução Total da Política", f"{reducao_total_politica * prazo_anos:,.0f} t")
        with col_impacto3:
            st.metric("Carros Retirados da Política", f"{reducao_total_politica / 4:,.0f}")
    else:
        st.info("O impacto agregado não pode ser calculado, pois a capacidade de financiamento do FNDIT é ilimitada para o subsídio atual.")
else:
    st.info("Ajuste os parâmetros na barra lateral para ver os resultados financeiros e de descarbonização em tempo real.")

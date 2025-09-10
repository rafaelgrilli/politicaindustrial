import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import plotly.express as px
import plotly.graph_objects as go

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

@st.cache_data
def gerar_plano_amortizacao(valor_financiamento, taxa_juros_mensal, num_parcelas):
    """Gera um plano de amortização no sistema Price."""
    if num_parcelas <= 0 or valor_financiamento <= 0:
        return pd.DataFrame()
    if taxa_juros_mensal <= 1e-9:
        parcela = valor_financiamento / num_parcelas
        dados = {
            'Mês': range(1, num_parcelas + 1),
            'Juros': [0.0] * num_parcelas,
            'Amortização': [parcela] * num_parcelas,
            'Saldo Devedor': [valor_financiamento - parcela * mes for mes in range(1, num_parcelas + 1)]
        }
        return pd.DataFrame(dados)

    parcela = calcular_parcela_price(valor_financiamento, taxa_juros_mensal, num_parcelas)
    saldo_devedor = valor_financiamento
    meses, juros, amortizacoes, saldos = [], [], [], []

    for mes in range(1, num_parcelas + 1):
        juros_mes = saldo_devedor * taxa_juros_mensal
        amortizacao_mes = parcela - juros_mes
        saldo_devedor -= amortizacao_mes
        
        meses.append(mes)
        juros.append(juros_mes)
        amortizacoes.append(amortizacao_mes)
        saldos.append(max(0, saldo_devedor)) # Garantir que o saldo não seja negativo

    return pd.DataFrame({
        'Mês': meses,
        'Juros': juros,
        'Amortização': amortizacoes,
        'Saldo Devedor': saldos
    })

# --- Configurações da Página Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Incentivos à Difusão Tecnológica (FNDIT)")

st.title("🌱 Simulador de Incentivos à Difusão Tecnológica na Indústria")
st.markdown("""
Esta ferramenta permite simular o impacto de diferentes estratégias de alocação de recursos do FNDIT
para subsidiar o custo de capital na aquisição de máquinas, equipamentos e tecnologias.
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
    - **Ganho Econômico Total**: A soma do aumento de produtividade e redução de custos ao longo do projeto.
    - **Eficiência de Fomento**: Mostra o percentual do custo de aquisição da tecnologia que é coberto pelo subsídio do FNDIT, refletindo o retorno do investimento para o poder público.
    """)

# --- Parâmetros de Entrada na barra lateral ---
st.sidebar.header("⚙️ Parâmetros da Simulação")

# Seção de Parâmetros Financeiros
st.sidebar.subheader("💰 Parâmetros Financeiros")
valor_projeto = st.sidebar.slider("1. Valor do Projeto de Aquisição Tecnológica (R$)", 
                                  min_value=1_000_000, max_value=100_000_000,
                                  value=30_000_000, step=1_000_000, key="valor_projeto")
st.sidebar.info("O custo total da máquina, equipamento ou software a ser adquirido.")

taxa_juros_full_anual = st.sidebar.slider("2. Taxa de Juros Full (a.a. %) - Mercado", 
                                          min_value=0.0, max_value=15.0, 
                                          value=7.8, step=0.1, key="taxa_juros_full_anual") / 100
st.sidebar.info("A taxa de juros que o tomador de crédito pagaria em uma condição de mercado 'normal', sem subsídios do FNDIT.")

montante_fndit = st.sidebar.slider("3. Montante no FNDIT para Subsídios/Crédito (R$)", 
                                   min_value=10_000_000, max_value=1_000_000_000, 
                                   value=200_000_000, step=10_000_000, key="montante_fndit")
st.sidebar.info("O total de recursos disponíveis no FNDIT para apoiar os projetos. Este montante pode ser usado para crédito ou subsídio.")

prazo_anos = st.sidebar.slider("4. Prazo para Amortização (anos)", 
                               min_value=1, max_value=20,
                               value=5, step=1, key="prazo_anos")
st.sidebar.info("O número de anos para a indústria pagar o financiamento.")

taxa_juros_subsidio_anual = st.sidebar.slider("5. Taxa de Juros Subsidiada Alvo (a.a. %)", 
                                               min_value=0.0, max_value=max(0.1, taxa_juros_full_anual * 100),
                                               value=min(3.0, taxa_juros_full_anual * 100), step=0.1, key="taxa_juros_subsidio_anual") / 100
st.sidebar.info("A taxa de juros reduzida que o FNDIT oferece aos projetos. A diferença entre esta taxa e a taxa 'full' de mercado é o subsídio.")

elasticidade_demanda = st.sidebar.slider("6. Elasticidade da Demanda por Crédito para Inovação", 
                                         min_value=-5.0, max_value=-0.1,
                                         value=-1.5, step=0.1, key="elasticidade_demanda")
st.sidebar.info("Mede a sensibilidade da demanda por crédito em relação às mudanças na taxa de juros. Uma elasticidade de -1.5, por exemplo, indica que uma redução de 1% na taxa de juros resulta em um aumento de 1.5% na demanda.")

taxa_desconto_tomador_anual = st.sidebar.slider("7. Taxa de Desconto para VPL (Tomador) a.a. (%)",
                                                min_value=0.0, max_value=25.0,
                                                value=12.0, step=0.5, key="taxa_desconto_tomador_anual") / 100
st.sidebar.info("Representa a taxa de retorno mínima aceitável para a indústria. É usada para calcular o valor presente de futuros ganhos e custos.")

# Validações dos parâmetros
if taxa_juros_subsidio_anual >= taxa_juros_full_anual:
    st.sidebar.warning("A taxa subsidiada deve ser menor que a taxa full para ter efeito.")
if valor_projeto <= 0:
    st.sidebar.error("O valor do projeto deve ser positivo.")
if montante_fndit < valor_projeto:
    st.sidebar.warning("O montante do FNDIT é menor que o valor de um projeto.")

# Seção de Parâmetros de Impacto Tecnológico
st.sidebar.subheader("🚀 Parâmetros de Impacto Tecnológico")
abordagem_tecnologica = st.sidebar.radio(
    "1. Metodologia para Estimativa de Impacto",
    ["Nenhuma", "Tipologia Tecnológica (Recomendado)", "Meta Customizada"],
    key="abordagem_tecnologica_radio",
    help="Baseado em estudos e benchmarks de ganhos de produtividade na indústria."
)

ganho_produtividade_anual = 0
reducao_custo_anual = 0
metodologia_info = ""

if abordagem_tecnologica == "Tipologia Tecnológica (Recomendado)":
    fatores_tecnologia = {
        "Robótica e Automação": {"ganho_produtividade_fator": 250_000, "reducao_custo_fator": 80_000, "premissas": "Automatização de tarefas repetitivas, aumento da precisão e velocidade. Baseado em adoção de robôs colaborativos.", "fontes": "McKinsey, IFR (2023)"},
        "Software de Manufatura (MES/ERP)": {"ganho_produtividade_fator": 180_000, "reducao_custo_fator": 60_000, "premissas": "Otimização de planejamento, controle de produção e gestão de estoque em tempo real.", "fontes": "Gartner, BNDES (2024)"},
        "Tecnologias de IoT Industrial": {"ganho_produtividade_fator": 220_000, "reducao_custo_fator": 70_000, "premissas": "Monitoramento preditivo de equipamentos, otimização da cadeia de suprimentos e manutenção preventiva.", "fontes": "IEA, EPE, MME (2023)"},
        "Manufatura Aditiva (Impressão 3D)": {"ganho_produtividade_fator": 150_000, "reducao_custo_fator": 50_000, "premissas": "Produção de protótipos e peças sob demanda, reduzindo tempo e custo de fabricação. Uso em nichos específicos.", "fontes": "BNDES, Senai Cimatec (2023)"},
        "Sistemas de Visão Computacional": {"ganho_produtividade_fator": 200_000, "reducao_custo_fator": 65_000, "premissas": "Inspeção de qualidade automatizada, detecção de defeitos e controle de processos em tempo real.", "fontes": "McKinsey, estudos de mercado (2024)"},
        "Modernização de Máquinas (Retrofitting)": {"ganho_produtividade_fator": 170_000, "reducao_custo_fator": 90_000, "premissas": "Atualização de equipamentos antigos com novas tecnologias de controle e sensoriamento.", "fontes": "ABIMAQ, estudos de caso (2023)"}
    }
    tecnologia_name = st.sidebar.selectbox("2. Tipo de Tecnologia Industrial", list(fatores_tecnologia.keys()), key="tecnologia_selector")
    
    # Calcular ganhos anuais com base nos fatores e valor do projeto
    ganho_produtividade_anual = (valor_projeto / 1_000_000) * fatores_tecnologia[tecnologia_name]["ganho_produtividade_fator"]
    reducao_custo_anual = (valor_projeto / 1_000_000) * fatores_tecnologia[tecnologia_name]["reducao_custo_fator"]
    metodologia_info = f"**Cálculo:** Ganho por R$ 1M investido. \n**Premissas:** {fatores_tecnologia[tecnologia_name]['premissas']}\n**Fontes:** {fatores_tecnologia[tecnologia_name]['fontes']}"

elif abordagem_tecnologica == "Meta Customizada":
    fator_ganho_produtividade = st.sidebar.slider(
        "2. Ganho de Produtividade (R$/milhão R$ investido/ano)",
        min_value=10_000, max_value=500_000, value=200_000, step=10_000,
        key="fator_ganho_produtividade_slider",
        help="Estimativa de aumento na produtividade anual para cada R$ 1 milhão investido no projeto."
    )
    fator_reducao_custo = st.sidebar.slider(
        "3. Redução de Custo Operacional (R$/milhão R$ investido/ano)",
        min_value=10_000, max_value=200_000, value=70_000, step=5_000,
        key="fator_reducao_custo_slider",
        help="Estimativa de economia de custos operacionais anuais para cada R$ 1 milhão investido."
    )
    ganho_produtividade_anual = (valor_projeto / 1_000_000) * fator_ganho_produtividade
    reducao_custo_anual = (valor_projeto / 1_000_000) * fator_reducao_custo
    metodologia_info = "**Atenção:** Fatores customizados - recomenda-se validação com estudos de caso ou especialistas do setor."

# Lógica de controle do botão "Simular"
if 'run_simulation' not in st.session_state:
    st.session_state.run_simulation = False

if st.sidebar.button("Simular"):
    st.session_state.run_simulation = True

# Botão para gerar relatório em PDF (com instruções)
st.sidebar.markdown("---")
if st.sidebar.button("📄 Gerar Relatório PDF"):
    st.warning("Para salvar a página como PDF, utilize a função de impressão do seu navegador (Ctrl+P ou Cmd+P).")

# O resto do código só será executado após o clique no botão
if st.session_state.run_simulation:
    # --- Cálculos Financeiros ---
    prazo_meses = prazo_anos * 12
    taxa_juros_full_anual_display = f"{taxa_juros_full_anual * 100:.2f}%"
    taxa_juros_subsidio_anual_display = f"{taxa_juros_subsidio_anual * 100:.2f}%"
    taxa_juros_full_mensal = (1 + taxa_juros_full_anual)**(1/12) - 1 if taxa_juros_full_anual > 0 else 0.0
    taxa_juros_subsidio_mensal = (1 + taxa_juros_subsidio_anual)**(1/12) - 1 if taxa_juros_subsidio_anual > 0 else 0.0
    taxa_desconto_tomador_mensal = (1 + taxa_desconto_tomador_anual)**(1/12) - 1 if taxa_desconto_tomador_anual > 0 else 0.0

    # Cálculos dos Cenários
    parcela_full = calcular_parcela_price_cached(valor_projeto, taxa_juros_full_mensal, prazo_meses)
    juros_total_full = parcela_full * prazo_meses - valor_projeto
    fluxos_tomador_full = [-parcela_full] * prazo_meses
    fluxos_tomador_full[0] += valor_projeto
    vpl_tomador_full = calcular_vpl_cached(fluxos_tomador_full, taxa_desconto_tomador_mensal)
    
    parcela_subsidio = calcular_parcela_price_cached(valor_projeto, taxa_juros_subsidio_mensal, prazo_meses)
    subs_por_projeto = (parcela_full - parcela_subsidio) * prazo_meses
    fluxos_tomador_subsidio = [-parcela_subsidio] * prazo_meses
    fluxos_tomador_subsidio[0] += valor_projeto
    vpl_tomador_subsidio = calcular_vpl_cached(fluxos_tomador_subsidio, taxa_desconto_tomador_mensal)
    
    qtd_projetos_credito_full = montante_fndit // valor_projeto if valor_projeto > 0 else 0
    if subs_por_projeto <= 1e-9 or subs_por_projeto == float('inf'):
        qtd_projetos_capacidade_fndit = float('inf')
    else:
        qtd_projetos_capacidade_fndit = montante_fndit // subs_por_projeto
    
    qtd_projetos_subvencao = montante_fndit // valor_projeto if valor_projeto > 0 else 0
    
    # Cálculos de Impacto da Demanda
    if taxa_juros_full_anual <= 0:
        qtd_projetos_demandados_elasticidade = 0
    else:
        variacao_juros_percentual = (taxa_juros_subsidio_anual - taxa_juros_full_anual) / taxa_juros_full_anual
        demanda_base_full = qtd_projetos_credito_full
        aumento_demanda_percentual = elasticidade_demanda * variacao_juros_percentual
        qtd_projetos_demandados_elasticidade = demanda_base_full * (1 + aumento_demanda_percentual)
        
    if qtd_projetos_capacidade_fndit != float('inf'):
        projetos_efetivos = min(qtd_projetos_demandados_elasticidade, qtd_projetos_capacidade_fndit)
    else:
        projetos_efetivos = qtd_projetos_demandados_elasticidade

    # --- Dashboard Executivo ---
    st.header("Sumário Executivo da Simulação")
    col_vpl, col_alavancagem, col_custo, col_projetos = st.columns(4)

    with col_vpl:
        st.subheader("Benefício para a Indústria")
        st.metric("VPL do Projeto (com Subsídio)", f"R$ {vpl_tomador_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"O VPL do mesmo projeto sem subsídio seria de R$ {vpl_tomador_full:,.2f}.".replace(",", "X").replace(".", ",").replace("X", "."))

    with col_alavancagem:
        st.subheader("Alavancagem de Capital")
        if subs_por_projeto > 1e-9:
            alavancagem_subs = valor_projeto / subs_por_projeto
            st.metric("Alavancagem", f"{alavancagem_subs:,.2f}x".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.metric("Alavancagem", "Não aplicável")
        st.info("Mede o capital privado mobilizado por cada real público do FNDIT.")
    
    with col_custo:
        st.subheader("Retorno do Subsídio")
        if subs_por_projeto > 0 and (ganho_produtividade_anual + reducao_custo_anual) > 0:
            beneficio_total_periodo = (ganho_produtividade_anual + reducao_custo_anual) * prazo_anos
            eficiencia_fomento = subs_por_projeto / beneficio_total_periodo
            st.metric("Custo FNDIT/Benefício", f"R$ {eficiencia_fomento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.metric("Custo FNDIT/Benefício", "N/A")
        st.info("Relação entre o custo do subsídio e o benefício econômico total gerado pelo projeto.")

    with col_projetos:
        st.subheader("Alcance da Política")
        st.metric("Projetos Efetivamente Financiados", f"{int(projetos_efetivos):,}".replace(",", "."))
        st.info(f"Este número é o mínimo entre a capacidade do FNDIT ({int(qtd_projetos_capacidade_fndit):,}) e a demanda do mercado ({int(qtd_projetos_demandados_elasticidade):,}).".replace(",", ".").replace("X", "."))

    st.markdown("---")

    # --- Análise Detalhada por Cenário ---
    st.header("Análise Detalhada por Cenário")
    col1, col2, col3 = st.columns(3)

    # Cenário 1: Crédito com Juros Full
    with col1:
        st.subheader("Cenário 1: Crédito com Juros Full")
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_credito_full):,}".replace(",", "."))
        st.info(f"Taxa de Juros: {taxa_juros_full_anual_display}")
        st.markdown(f"**Detalhes por Projeto:**")
        st.markdown(f"- Parcela Mensal: R$ {parcela_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- Juros Totais Pagos: R$ {juros_total_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- VPL para o Tomador: R$ {vpl_tomador_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Cenário 2: Subsídio de Juros
    with col2:
        st.subheader("Cenário 2: Subsídio de Juros")
        qtd_projetos_capacidade_fndit_display = f"{int(qtd_projetos_capacidade_fndit):,}".replace(",", ".") if qtd_projetos_capacidade_fndit != float('inf') else "Infinito"
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", qtd_projetos_capacidade_fndit_display)
        st.info(f"Taxa de Juros: {taxa_juros_subsidio_anual_display}")
        st.markdown(f"**Detalhes por Projeto:**")
        st.markdown(f"- Parcela Mensal: R$ {parcela_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- Juros Totais Pagos: R$ {parcela_subsidio * prazo_meses - valor_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- **Subsídio FNDIT por Projeto: R$ {subs_por_projeto:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- VPL para o Tomador: R$ {vpl_tomador_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Cenário 3: Subvenção Total do Projeto
    with col3:
        st.subheader("Cenário 3: Subvenção Total")
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_subvencao):,}".replace(",", "."))
        st.info("Neste modelo, o FNDIT cobre 100% do custo do projeto.")
        st.markdown(f"**Detalhes por Projeto:**")
        st.markdown(f"- Valor da Subvenção: R$ {valor_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"*(Não há parcelas ou juros, pois o valor é doado)*")
        st.markdown(f"- VPL para o Tomador: R$ {valor_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    # --- Gráfico de Amortização ---
    st.header("Evolução Financeira do Financiamento")
    st.info("Este gráfico de linha compara o Saldo Devedor ao longo do tempo para os cenários de Crédito Full e Subsídio de Juros. O subsídio do FNDIT acelera a amortização, reduzindo o tempo para quitar o saldo devedor.")
    
    df_full = gerar_plano_amortizacao(valor_projeto, taxa_juros_full_mensal, prazo_meses)
    df_subsidio = gerar_plano_amortizacao(valor_projeto, taxa_juros_subsidio_mensal, prazo_meses)
    
    fig = go.Figure()
    
    # Saldo Devedor (Eixo Y1)
    fig.add_trace(go.Scatter(x=df_full['Mês'], y=df_full['Saldo Devedor'], mode='lines', 
                             name='Saldo Devedor (Crédito Full)', line=dict(color='#EF553B', dash='dash')))
    fig.add_trace(go.Scatter(x=df_subsidio['Mês'], y=df_subsidio['Saldo Devedor'], mode='lines',
                             name='Saldo Devedor (Subsídio Juros)', line=dict(color='#636EFA', dash='dash')))

    fig.update_layout(
        title="Comparativo de Saldo Devedor por Cenário",
        yaxis_title="Saldo Devedor (R$)",
        xaxis_title="Mês",
        legend_title="Cenários"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- Seção de Impacto Tecnológico ---
    st.markdown("---")
    
    if abordagem_tecnologica != "Nenhuma" and (ganho_produtividade_anual > 0 or reducao_custo_anual > 0):
        
        beneficio_anual_direto = ganho_produtividade_anual + reducao_custo_anual
        retorno_total_periodo = beneficio_anual_direto * prazo_anos

        st.header("🚀 Impacto da Difusão Tecnológica Estimado")
        st.markdown("---")
        
        col1_impacto, col2_impacto = st.columns(2)
        with col1_impacto:
            st.metric("Benefício Econômico Anual", f"R$ {beneficio_anual_direto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.markdown(f"*(Ganho de produtividade + Redução de custos operacionais)*")
        with col2_impacto:
            st.metric("Retorno Total no Período", f"R$ {retorno_total_periodo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.markdown(f"*(Benefício anual total projetado ao longo de {prazo_anos} anos)*")
        
        st.subheader("📊 Eficiência do Fomento")
        st.info("Este gráfico compara o custo do projeto para a indústria com o benefício econômico total esperado. Ele ajuda a justificar o investimento do FNDIT para viabilizar projetos de tecnologia.")

        df_eficiencia_lista = [
            {"Categoria": "Custo do Projeto (sem Subsídio)", "Valor (R$)": valor_projeto, "Tipo": "Custo"},
            {"Categoria": "Subsídio do FNDIT", "Valor (R$)": subs_por_projeto, "Tipo": "Subsídio"},
            {"Categoria": "Ganho da Indústria", "Valor (R$)": retorno_total_periodo, "Tipo": "Benefício"}
        ]
        
        df_eficiencia = pd.DataFrame(df_eficiencia_lista)
        
        fig = px.bar(df_eficiencia, x="Categoria", y="Valor (R$)", color="Tipo", title="Comparativo de Custos e Benefícios",
                     color_discrete_map={"Custo": "#EF553B", "Subsídio": "lightblue", "Benefício": "darkgreen"})
        st.plotly_chart(fig, use_container_width=True)
        
        if retorno_total_periodo > subs_por_projeto:
            st.success(f"✅ **O subsídio é vantajoso**: O retorno total do projeto (R$ {retorno_total_periodo:,.2f}) é maior que o custo do subsídio do FNDIT (R$ {subs_por_projeto:,.2f}).".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.warning(f"⚠️ **Revise o projeto**: O retorno total do projeto (R$ {retorno_total_periodo:,.2f}) é menor que o custo do subsídio do FNDIT (R$ {subs_por_projeto:,.2f}).".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.subheader("🎯 Impacto Agregado da Política")
        st.info("Esta seção mostra o impacto total da política de fomento à difusão tecnológica, considerando a capacidade financeira do FNDIT e a demanda estimada de projetos. Ela traduz os resultados financeiros em métricas mais amplas e de fácil compreensão.")
        if qtd_projetos_capacidade_fndit != float('inf'):
            reducao_total_politica = beneficio_anual_direto * projetos_efetivos
            col_impacto1, col_impacto2 = st.columns(2)
            with col_impacto1:
                st.metric("Geração de Valor Anual da Política", f"R$ {reducao_total_politica:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with col_impacto2:
                st.metric("Geração de Valor Total da Política", f"R$ {reducao_total_politica * prazo_anos:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.markdown("---")
            st.warning(f"""
            **⚠️ Nota importante sobre a Demanda:**
            O FNDIT tem capacidade para financiar **{int(qtd_projetos_capacidade_fndit):,}** projetos, mas a elasticidade da demanda sugere que apenas **{int(qtd_projetos_demandados_elasticidade):,}** projetos seriam efetivamente demandados com a taxa de juros atual.
            Isso significa que, sem outras ações de fomento e articulação com o setor privado, pode haver uma baixa adesão. Para maximizar o impacto, o FNDIT precisa trabalhar a demanda de forma focada, identificando e apoiando empresas com maior potencial de inovação.
            """)
        else:
            st.info("O impacto agregado não pode ser calculado, pois a capacidade de financiamento do FNDIT é ilimitada para o subsídio atual.")
    else:
        st.warning("Ajuste os parâmetros de impacto tecnológico para visualizar os resultados.")
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Simular' para ver os resultados financeiros e de impacto tecnológico.")

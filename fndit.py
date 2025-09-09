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
    - **Eficiência Econômica**: Mostra o percentual do custo de descarbonização que é coberto pelo subsídio do FNDIT.
    """)

# --- Parâmetros de Entrada na barra lateral ---
st.sidebar.header("⚙️ Parâmetros da Simulação")

# Seção de Parâmetros Financeiros
st.sidebar.subheader("💰 Parâmetros Financeiros")
valor_projeto = st.sidebar.slider("1. Valor do Projeto de Descarbonização (R$)", 
                                  min_value=1_000_000, max_value=100_000_000,
                                  value=30_000_000, step=1_000_000, key="valor_projeto")
st.sidebar.info("Este é o custo total de um projeto de descarbonização, como a instalação de painéis solares ou uma frota de veículos elétricos.")

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
st.sidebar.info("O número de anos para o tomador de crédito pagar o financiamento.")

taxa_juros_subsidio_anual = st.sidebar.slider("5. Taxa de Juros Subsidiada Alvo (a.a. %)", 
                                               min_value=0.0, max_value=max(0.1, taxa_juros_full_anual * 100),
                                               value=min(3.0, taxa_juros_full_anual * 100), step=0.1, key="taxa_juros_subsidio_anual") / 100
st.sidebar.info("A taxa de juros reduzida que o FNDIT oferece aos projetos. A diferença entre esta taxa e a taxa 'full' de mercado é o subsídio.")

elasticidade_demanda = st.sidebar.slider("6. Elasticidade da Demanda por Crédito de Descarbonização", 
                                         min_value=-5.0, max_value=-0.1,
                                         value=-1.5, step=0.1, key="elasticidade_demanda")
st.sidebar.info("Mede a sensibilidade da demanda por crédito em relação às mudanças na taxa de juros. Uma elasticidade de -1.5, por exemplo, indica que uma redução de 1% na taxa de juros aumenta a demanda em aproximadamente 1.5%.")

taxa_desconto_tomador_anual = st.sidebar.slider("7. Taxa de Desconto para VPL (Tomador) a.a. (%)",
                                                min_value=0.0, max_value=25.0,
                                                value=12.0, step=0.5, key="taxa_desconto_tomador_anual") / 100
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
    ["Nenhuma", "Tecnologia de Descarbonização Industrial", "Meta Customizada"],
    key="abordagem_co2_radio",
    help="Baseado em metodologias do MCTI, EPE e estudos setoriais brasileiros."
)

fator_co2 = 0
metodologia_info = ""
custo_real_tecnologia = None

if abordagem_co2 == "Tecnologia de Descarbonização Industrial":
    fatores_tecnologia = {
        "Eficiência Energética Industrial": {"fator": 150, "custo_real": 120, "calculo": "Redução de consumo de energia em processos industriais (ex: motores, caldeiras)", "premissas": "Otimização de equipamentos, sistemas de controle, e isolamento térmico.", "fontes": "IEA, EPE, MME (2023)"},
        "Eletrificação de Processos": {"fator": 180, "custo_real": 200, "calculo": "Substituição de combustíveis fósseis (gás, carvão) por eletricidade renovável", "premissas": "Considera a eletrificação de fornos, caldeiras e aquecimento industrial.", "fontes": "IEA, MCTI, estudos setoriais (2024)"},
        "Captura e Utilização de Carbono (CCU)": {"fator": 110, "custo_real": 450, "calculo": "Captura de CO₂ emitido em processos para uso como insumo", "premissas": "Tecnologia em estágio inicial no Brasil, com custos elevados.", "fontes": "IEMA, GCCSI, estudos de caso (2024)"},
        "Hidrogênio Verde (Uso Industrial)": {"fator": 140, "custo_real": 550, "calculo": "Substituição de hidrogênio cinza (gás natural) por H2 verde", "premissas": "Foco em setores como fertilizantes, refino e siderurgia.", "fontes": "IEA, EPE, relatórios setoriais (2023)"},
        "Biocombustíveis (Uso Industrial)": {"fator": 160, "custo_real": 130, "calculo": "Substituição de combustíveis fósseis por bioenergia", "premissas": "Biomassa e biogás para geração de calor e energia.", "fontes": "ABiogás, Embrapa, relatórios industriais (2023)"}
    }
    tecnologia_name = st.sidebar.selectbox("2. Tecnologia de Descarbonização Industrial", list(fatores_tecnologia.keys()), key="tecnologia_selector")
    fator_co2 = fatores_tecnologia[tecnologia_name]["fator"]
    custo_real_tecnologia = fatores_tecnologia[tecnologia_name]["custo_real"]
    metodologia_info = f"**Cálculo:** {fatores_tecnologia[tecnologia_name]['calculo']}\n**Premissas:** {fatores_tecnologia[tecnologia_name]['premissas']}\n**Fontes:** {fatores_tecnologia[tecnologia_name]['fontes']}"

elif abordagem_co2 == "Meta Customizada":
    fator_co2 = st.sidebar.slider(
        "2. Fator de Redução (tCO2e/milhão R$/ano)",
        min_value=10, max_value=500, value=100, step=10,
        key="fator_custom_slider",
        help="Range baseado em estudos setoriais brasileiros (2023-2024)."
    )
    metodologia_info = "**Atenção:** Fator customizado - recomenda-se validação técnica com especialista setorial."

# Lógica de controle do botão "Simular"
if 'run_simulation' not in st.session_state:
    st.session_state.run_simulation = False

if st.sidebar.button("Simular"):
    st.session_state.run_simulation = True

# O resto do código só será executado após o clique no botão
if st.session_state.run_simulation:
    # --- Cálculos Financeiros ---
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
        st.info("Mostra quantos projetos de R$ 30 milhões o FNDIT conseguiria financiar se não subsidiasse juros e usasse todo o seu montante para crédito.")
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
        st.info("Com o subsídio de juros, o FNDIT gasta menos por projeto, podendo financiar mais iniciativas com o mesmo montante.")
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
        st.info("Neste modelo, o FNDIT cobre 100% do custo do projeto, permitindo que o tomador de crédito não tenha despesa alguma. Isso, no entanto, limita a quantidade de projetos financiáveis.")
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
        st.info("Este é o valor que o FNDIT gasta por projeto para reduzir os juros para o tomador, calculado como a diferença entre as parcelas a juros 'full' e as parcelas subsidiadas, ao longo do prazo do financiamento.")
        if subs_por_projeto > 1e-9:
            st.metric("Subsídio de Juros", f"R$ {subs_por_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.info("Não há subsídio de juros ou é insignificante.")
    with col_ind2:
        st.subheader("Eficiência de Alocação")
        st.info("Compara a quantidade de projetos que o FNDIT pode financiar com sua capacidade de crédito versus a quantidade de projetos que seriam demandados no mercado, considerando a elasticidade. Um valor menor que 100% significa que a demanda não preencheria a capacidade de financiamento.")
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
        st.info("Mede o quanto cada real de capital público (subsídio do FNDIT) atrai de capital privado para o projeto. Uma alavancagem de 2x, por exemplo, significa que para cada R$ 1 público, R$ 2 privados são mobilizados.")
        if subs_por_projeto > 1e-9:
            alavancagem_subs = valor_projeto / subs_por_projeto
            st.metric("Alavancagem (Subsídio de Juros)", f"{alavancagem_subs:,.2f}x".replace(",", "X").replace(".", ",").replace("X", "."))
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
    st.info("Este quadro compara os três cenários de financiamento, mostrando o impacto sobre o tomador (VPL) e o custo para o FNDIT. É uma forma de analisar qual estratégia é mais vantajosa para cada tipo de projeto.")
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
    
    if abordagem_co2 != "Nenhuma" and fator_co2 > 0:
        co2_evitado_anual = (valor_projeto / 1_000_000) * fator_co2
        reducao_total_periodo = co2_evitado_anual * prazo_anos

        st.header("🔥 Impacto de Descarbonização Estimado")
        st.markdown("---")
        
        col1_co2, col2_co2, col3_co2, col4_co2 = st.columns(4)
        with col1_co2:
            st.metric("Redução Anual de CO2e", f"{co2_evitado_anual:,.0f} t/ano")
        with col2_co2:
            st.metric("Redução Total no Período", f"{reducao_total_periodo:,.0f} t")
        with col3_co2:
            if subs_por_projeto > 0 and reducao_total_periodo > 0:
                custo_por_tonelada_projeto = subs_por_projeto / reducao_total_periodo
                tipo_custo = "Subsídio"
            else:
                custo_por_tonelada_projeto = valor_projeto / reducao_total_periodo if reducao_total_periodo > 0 else 0
                tipo_custo = "Investimento"
            st.metric(f"Custo {tipo_custo}/Tonelada", f"R$ {custo_por_tonelada_projeto:,.0f}")
        with col4_co2:
            carros_equivalentes = co2_evitado_anual / 4
            st.metric("Equiv. Carros Retirados", f"{carros_equivalentes:,.0f}")
        
        st.subheader("💰 Análise de Custo-Efetividade")
        st.info("Este gráfico compara o custo de descarbonização do seu projeto (custo do subsídio dividido pelo carbono evitado) com as referências de mercado de carbono. Ele ajuda a avaliar se o investimento do FNDIT é competitivo.")
        referencias_mercado = {"Mercado Voluntário (Mín.)": 50, "Mercado Voluntário (Máx.)": 180, "Regulado (Mín.)": 80, "Regulado (Máx.)": 250, "CBIOs (RenovaBio)": 85}
        df_comparacao_lista = [{"Categoria": k, "Custo (R$/tCO2e)": v, "Tipo": "Mercado"} for k, v in referencias_mercado.items()]
        
        if abordagem_co2 == "Tecnologia de Descarbonização Industrial" and 'tecnologia_name' in locals():
            df_comparacao_lista.append({"Categoria": "Custo Real da Tecnologia", "Custo (R$/tCO2e)": custo_real_tecnologia, "Tipo": "Tecnologia"})
        
        df_comparacao_lista.append({"Categoria": "Custo do Seu Projeto (FNDIT)", "Custo (R$/tCO2e)": custo_por_tonelada_projeto, "Tipo": "Projeto"})
        
        df_comparacao = pd.DataFrame(df_comparacao_lista)
        
        fig = px.bar(df_comparacao, x="Categoria", y="Custo (R$/tCO2e)", color="Tipo", title="Comparação com Referências de Mercado e Custo Real de Tecnologias",
                     color_discrete_map={"Mercado": "lightblue", "Tecnologia": "orange", "Projeto": "darkgreen"})
        st.plotly_chart(fig, use_container_width=True)

        if custo_por_tonelada_projeto <= 150:
            st.success(f"✅ **Custo-efetivo**: Abaixo ou igual ao mercado voluntário (R$ {custo_por_tonelada_projeto:,.0f}/tCO2e).")
        elif custo_por_tonelada_projeto <= 200:
            st.info(f"ℹ️ **Competitivo**: Dentro do range regulado (R$ {custo_por_tonelada_projeto:,.0f}/tCO2e).")
        elif custo_por_tonelada_projeto <= 350:
            st.warning(f"⚠️ **Acima do mercado**: Justifique os co-benefícios (R$ {custo_por_tonelada_projeto:,.0f}/tCO2e).")
        else:
            st.error(f"❌ **Muito alto**: Revise a parametrização (R$ {custo_por_tonelada_projeto:,.0f}/tCO2e).")
        
        st.subheader("🔬 Eficiência Econômica do Subsídio")
        st.info("Este indicador mostra o percentual do custo real de descarbonização que é coberto pelo subsídio do FNDIT. Quanto mais próximo de 100%, mais o FNDIT está fechando a lacuna financeira do projeto.")
        if subs_por_projeto > 0 and custo_real_tecnologia is not None:
            eficiencia_economica = custo_por_tonelada_projeto / custo_real_tecnologia
            st.metric("Eficiência Econômica", f"{eficiencia_economica:.2%}")
        else:
            st.info("Não aplicável para este cenário de financiamento ou tecnologia.")

        st.subheader("🎯 Impacto Agregado da Política")
        st.info("Esta seção mostra o impacto total da política de fomento à descarbonização, considerando a capacidade financeira do FNDIT e a demanda estimada de projetos. Ela traduz os resultados financeiros e de carbono em métricas mais amplas e de fácil compreensão.")
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
            st.markdown("---")
            st.warning(f"""
            **⚠️ Nota importante sobre a Demanda:**
            O FNDIT tem capacidade para financiar **{int(qtd_projetos_capacidade_fndit):,}** projetos, mas a elasticidade da demanda sugere que apenas **{int(qtd_projetos_demandados_elasticidade):,}** projetos seriam efetivamente demandados com a taxa de juros atual.
            Isso significa que, sem outras ações de fomento e articulação com o setor privado, pode haver uma baixa adesão. Para maximizar o impacto, o FNDIT precisa trabalhar a demanda de forma focada, identificando e apoiando empresas com maior potencial de descarbonização.
            """)
        else:
            st.info("O impacto agregado não pode ser calculado, pois a capacidade de financiamento do FNDIT é ilimitada para o subsídio atual.")
    else:
        st.warning("Ajuste os parâmetros de descarbonização para visualizar os resultados.")
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Simular' para ver os resultados financeiros e de descarbonização.")

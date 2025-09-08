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
    if num_parcelas <= 0:  # Prazo zero ou negativo não faz sentido para cálculo de parcela
        return float('inf')
    if taxa_juros_mensal <= 1e-9:  # Tratando juros muito próximos de zero como zero para estabilidade
        return valor_financiamento / num_parcelas
    
    try:
        denominador = 1 - (1 + taxa_juros_mensal)**(-num_parcelas)
        if abs(denominador) < 1e-9:  # Caso a taxa seja tão pequena que a exponenciação se aproxime de 1
            return valor_financiamento / num_parcelas
        return (valor_financiamento * taxa_juros_mensal) / denominador
    except OverflowError:  # Para números muito grandes/pequenos
        return float('inf')  # Retorna infinito se o cálculo for inviável

@st.cache_data
def calcular_vpl_cached(fluxos_caixa, taxa_desconto_mensal):
    """Calcula o Valor Presente Líquido (VPL) de uma série de fluxos de caixa."""
    return calcular_vpl(fluxos_caixa, taxa_desconto_mensal)

def calcular_vpl(fluxos_caixa, taxa_desconto_mensal):
    """Calcula o Valor Presente Líquido (VPL) de uma série de fluxos de caixa."""
    if abs(taxa_desconto_mensal) < 1e-9:  # Handle near-zero discount rates
        return sum(fluxos_caixa)
    
    vpl = 0
    for t, fluxo in enumerate(fluxos_caixa):
        # More stable calculation using logarithms for large t
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

# Add informational expanders
with st.expander("ℹ️ Entenda a Elasticidade da Demanda"):
    st.markdown("""
    A elasticidade da demanda mede quanto a quantidade demandada de crédito responde a mudanças na taxa de juros.
    - Valor de -1.5 significa que uma redução de 1% na taxa de juros aumenta a demanda em aproximadamente 1.5%
    - Valores mais negativos indicam demanda mais sensível a mudanças nas taxas de juros
    """)

with st.expander("ℹ️ Como interpretar os resultados"):
    st.markdown("""
    **Como interpretar os resultados:**
    - **VPL para o Tomador**: Valores mais altos indicam melhor custo-benefício para quem recebe o financiamento
    - **Alavancagem**: Mostra quanto capital privado é mobilizado por cada real público investido
    - **Eficiência de Alocação**: Percentual que mostra o aproveitamento dos recursos disponíveis
    - **Custo-Efetividade**: Compara o custo do projeto (ou do subsídio) com o preço de mercado da tonelada de CO2e evitada
    """)

st.sidebar.header("Parâmetros do Projeto e do FNDIT")

# --- Parâmetros de Entrada (mantidos do código 1) ---
valor_projeto = st.sidebar.slider("1. Valor do Projeto de Descarbonização (R$)", 
                                  min_value=1_000_000, max_value=100_000_000,
                                  value=30_000_000, step=1_000_000)
taxa_juros_full_anual = st.sidebar.slider("2. Taxa de Juros Full (a.a. %) - Mercado", 
                                          min_value=0.0, max_value=15.0, 
                                          value=7.8, step=0.1) / 100
montante_fndit = st.sidebar.slider("3. Montante no FNDIT para Subsídios/Crédito (R$)", 
                                   min_value=10_000_000, max_value=1_000_000_000, 
                                   value=200_000_000, step=10_000_000)
prazo_anos = st.sidebar.slider("4. Prazo para Amortização (anos)", 
                               min_value=1, max_value=20,
                               value=5, step=1)
taxa_juros_subsidio_anual = st.sidebar.slider("Taxa de Juros Subsidiada Alvo (a.a. %)", 
                                               min_value=0.0, max_value=max(0.1, taxa_juros_full_anual * 100),
                                               value=min(3.0, taxa_juros_full_anual * 100), step=0.1) / 100
elasticidade_demanda = st.sidebar.slider("Elasticidade da Demanda por Crédito de Descarbonização", 
                                         min_value=-5.0, max_value=-0.1,
                                         value=-1.5, step=0.1)
taxa_desconto_tomador_anual = st.sidebar.slider("Taxa de Desconto para VPL (Tomador) a.a. (%)",
                                                min_value=0.0, max_value=25.0,
                                                value=12.0, step=0.5) / 100

# Add validation checks
if taxa_juros_subsidio_anual >= taxa_juros_full_anual:
    st.sidebar.warning("A taxa subsidiada deve ser menor que a taxa full para ter efeito")
    
if valor_projeto <= 0:
    st.sidebar.error("O valor do projeto deve ser positivo")

if montante_fndit < valor_projeto:
    st.sidebar.warning("O montante do FNDIT é menor que o valor de um projeto")

# --- Seção de parâmetros aprimorada com base nas justificativas brasileiras (código 2) ---
st.sidebar.subheader("🌱 Parâmetros de Descarbonização")

abordagem_co2 = st.sidebar.radio(
    "Metodologia para Estimativa de CO2 Evitado",
    ["Nenhuma", "Setorial (Recomendado)", "Por Tecnologia Específica", "Meta Customizada"],
    help="Baseado em metodologias do MCTI, EPE e estudos setoriais brasileiros"
)

# Adicionar seletor regional
regiao = st.sidebar.selectbox(
    "Região do Projeto",
    ["Nacional", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
    help="Fatores podem variar conforme potencial regional"
)


# --- "Simular" Button ---
if st.sidebar.button("Simular"):
    st.session_state.run_simulation = True
else:
    if 'run_simulation' not in st.session_state:
        st.session_state.run_simulation = False

if st.session_state.run_simulation:
    # --- Cálculos dos Cenários Financeiros (mantidos do código 1) ---
    prazo_meses = prazo_anos * 12
    # Ensure monthly rates are handled correctly for 0% annual rates
    taxa_juros_full_mensal = (1 + taxa_juros_full_anual)**(1/12) - 1 if taxa_juros_full_anual > 0 else 0.0
    taxa_juros_subsidio_mensal = (1 + taxa_juros_subsidio_anual)**(1/12) - 1 if taxa_juros_subsidio_anual > 0 else 0.0
    taxa_desconto_tomador_mensal = (1 + taxa_desconto_tomador_anual)**(1/12) - 1 if taxa_desconto_tomador_anual > 0 else 0.0

    st.header("Resultados da Simulação Financeira")

    col1, col2, col3 = st.columns(3)

    # --- Cenário 1: Crédito com Juros Full ---
    with col1:
        st.subheader("Cenário 1: Crédito com Juros Full")
        qtd_projetos_credito_full = montante_fndit // valor_projeto if valor_projeto > 0 else 0
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_credito_full):,}".replace(",", "."))

        parcela_full = calcular_parcela_price_cached(valor_projeto, taxa_juros_full_mensal, prazo_meses)
        custo_total_full = parcela_full * prazo_meses
        juros_total_full = custo_total_full - valor_projeto
        st.markdown(f"**Detalhes por Projeto (Juros Full):**")
        st.markdown(f"- Parcela Mensal: R$ {parcela_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- Custo Total Financiamento: R$ {custo_total_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- Juros Totais Pagos: R$ {juros_total_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # VPL para o Tomador (cenário sem subsídio - custo)
        if taxa_juros_full_mensal <= 1e-9 and taxa_desconto_tomador_mensal <= 1e-9:
             vpl_tomador_full = 0.0
             st.markdown(f"- VPL para o Tomador (Juros Full): R$ {0.0:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
             st.markdown(f"*(VPL do financiamento. Se juros e taxa de desconto são 0%, VPL é 0)*")
        else:
            fluxos_tomador_full = [-parcela_full] * prazo_meses
            fluxos_tomador_full[0] += valor_projeto  # Recebe o valor no início
            vpl_tomador_full = calcular_vpl_cached(fluxos_tomador_full, taxa_desconto_tomador_mensal)
            st.markdown(f"- VPL para o Tomador (Juros Full): R$ {vpl_tomador_full:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.markdown(f"*(VPL inicial do financiamento. Representa o custo financeiro líquido para o tomador)*")


    # --- Cenário 2: Subsídio de Juros (Full para Subsidiada) ---
    with col2:
        st.subheader("Cenário 2: Subsídio de Juros")

        parcela_subsidio = calcular_parcela_price_cached(valor_projeto, taxa_juros_subsidio_mensal, prazo_meses)
        custo_total_subsidio = parcela_subsidio * prazo_meses
        
        juros_total_subsidio = custo_total_subsidio - valor_projeto
        subs_por_projeto = (parcela_full - parcela_subsidio) * prazo_meses
        
        # FIX para OverflowError: float('inf') para int
        if subs_por_projeto <= 1e-9 or subs_por_projeto == float('inf'):  # Se o subsídio for zero, negativo ou infinito
            qtd_projetos_capacidade_fndit_display = "Infinito" 
            qtd_projetos_capacidade_fndit = float('inf')
        else:
            qtd_projetos_capacidade_fndit = montante_fndit // subs_por_projeto
            qtd_projetos_capacidade_fndit_display = f"{int(qtd_projetos_capacidade_fndit):,}".replace(",", ".")
            
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", qtd_projetos_capacidade_fndit_display)

        st.markdown(f"**Detalhes por Projeto (Juros Subsidiados):**")
        st.markdown(f"- Parcela Mensal: R$ {parcela_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- Custo Total Financiamento: R$ {custo_total_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- Juros Totais Pagos: R$ {juros_total_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"- **Subsídio FNDIT por Projeto: R$ {subs_por_projeto:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))

        # VPL para o Tomador (cenário subsidiado - benefício)
        if taxa_juros_subsidio_mensal <= 1e-9 and taxa_desconto_tomador_mensal <= 1e-9:
            vpl_tomador_subsidio = 0.0
            st.markdown(f"- VPL para o Tomador (Juros Subsidiados): R$ {0.0:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            fluxos_tomador_subsidio = [-parcela_subsidio] * prazo_meses
            fluxos_tomador_subsidio[0] += valor_projeto
            vpl_tomador_subsidio = calcular_vpl_cached(fluxos_tomador_subsidio, taxa_desconto_tomador_mensal)
            st.markdown(f"- VPL para o Tomador (Juros Subsidiados): R$ {vpl_tomador_subsidio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


        st.markdown("---")
        st.markdown("**Com Elasticidade da Demanda:**")
        
        # Previne divisão por zero se taxa_juros_full_anual for 0
        if taxa_juros_full_anual <= 0:
            st.warning("Não é possível calcular variação percentual na taxa de juros quando a taxa full é 0%.")
            qtd_projetos_demandados_elasticidade = 0
            aumento_demanda_percentual_display = "N/A"
        else:
            variacao_juros_percentual = (taxa_juros_subsidio_anual - taxa_juros_full_anual) / taxa_juros_full_anual
            
            demanda_base_full = qtd_projetos_credito_full  # Número de projetos que o FNDIT financiaria a juros full
            
            aumento_demanda_percentual = elasticidade_demanda * variacao_juros_percentual
            qtd_projetos_demandados_elasticidade = demanda_base_full * (1 + aumento_demanda_percentual)
            aumento_demanda_percentual_display = f"{aumento_demanda_percentual:.2%}"
            
        st.metric("Projetos Demandados (Elasticidade)", f"{int(qtd_projetos_demandados_elasticidade):,}".replace(",", "."))
        st.markdown(f"*(Assumindo {int(demanda_base_full):,} projetos como demanda base a juros full)*".replace(",", "."))
        st.markdown(f"*(Aumento de demanda de: {aumento_demanda_percentual_display})*")

        # Calculate efficiency metrics
        if qtd_projetos_capacidade_fndit != float('inf'):
            eficiencia_alocacao = min(qtd_projetos_demandados_elasticidade, qtd_projetos_capacidade_fndit) / qtd_projetos_credito_full
            st.metric("Eficiência de Alocação de Recursos", f"{eficiencia_alocacao:.2%}")

        # Nota sobre capacidade vs demanda
        if qtd_projetos_capacidade_fndit != float('inf') and qtd_projetos_capacidade_fndit > qtd_projetos_demandados_elasticidade:
            st.info("💡 **Nota importante:** A capacidade de financiamento é maior que a demanda estimada. Isso sugere que a demanda real pode ser maior que a prevista pela elasticidade caso haja esforços específicos como: campanhas de divulgação, prospecção ativa de empresas, facilitação de processos ou incentivos adicionais.")
        elif qtd_projetos_capacidade_fndit != float('inf') and qtd_projetos_capacidade_fndit < qtd_projetos_demandados_elasticidade:
            st.warning("⚠️ **Nota importante:** A demanda estimada é maior que a capacidade de financiamento. Isso sugere que os recursos podem ser insuficientes e pode ser necessário priorizar projetos ou buscar fontes adicionais de financiamento.")

        # CORREÇÃO APLICADA AQUI: vírgula em vez de ponto
        st.markdown(f"**Conclusão Elasticidade:** O FNDIT pode subsidiar até {qtd_projetos_capacidade_fndit_display} projetos, mas a demanda estimada é de {int(qtd_projetos_demandados_elasticidade):,} projetos.".replace(",", "."))


    # --- Cenário 3: Subvenção Total do Projeto ---
    with col3:
        st.subheader("Cenário 3: Subvenção Total")
        qtd_projetos_subvencao = montante_fndit // valor_projeto if valor_projeto > 0 else 0
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_subvencao):,}".replace(",", "."))
        st.markdown(f"**Detalhes por Projeto (Subvenção Total):**")
        st.markdown(f"- Valor da Subvenção: R$ {valor_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"*(Não há parcelas ou juros, pois o valor é doado)*")
        st.markdown(f"- VPL para o Tomador (Subvenção): R$ {valor_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))  # VPL é o valor recebido


    st.markdown("---")

    st.header("Análise Comparativa e Indicadores de Impacto")

    col_ind1, col_ind2, col_ind3 = st.columns(3)

    # Custo de Subsídio por Projeto
    with col_ind1:
        st.subheader("Custo de Subsídio por Projeto (FNDIT)")
        if subs_por_projeto > 1e-9:  # Only show if there's a meaningful positive subsidy
            st.metric("Subsídio de Juros", f"R$ {subs_por_projeto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.markdown("*(Este é o valor que o FNDIT gasta por projeto para reduzir os juros para o tomador)*")
        else:
            st.info("Não há subsídio de juros ou é insignificante (taxa subsidiada igual ou maior que a full).")

    # Nova métrica: Eficiência de Alocação de Recursos
    with col_ind2:
        st.subheader("Eficiência de Alocação")
        
        if qtd_projetos_capacidade_fndit != float('inf'):
            # Projetos efetivamente financiados considerando demanda
            projetos_efetivos = min(qtd_projetos_demandados_elasticidade, qtd_projetos_capacidade_fndit)
            st.metric("Projetos Efetivamente Financiáveis", f"{int(projetos_efetivos):,}".replace(",", "."))
            
            # Taxa de utilização dos recursos
            if qtd_projetos_capacidade_fndit > 0:
                utilizacao_recursos = projetos_efetivos / qtd_projetos_capacidade_fndit
                st.metric("Utilização dos Recursos Disponíveis", f"{utilizacao_recursos:.2%}")
        else:
            st.metric("Projetos Efetivamente Financiáveis", f"{int(qtd_projetos_demandados_elasticidade):,}".replace(",", "."))
            st.info("Capacidade de financiamento é ilimitada com o subsídio atual")

    # Alavancagem de Capital Privado (para o cenário de subsídio de juros)
    with col_ind3:
        st.subheader("Alavancagem de Capital Privado")
        if subs_por_projeto > 1e-9:
            alavancagem_subs = valor_projeto / subs_por_projeto
            st.metric("Alavancagem (Subsídio de Juros)", f"{alavancagem_subs:,.2f}x".replace(",", "X").replace(".", ",").replace("X", "."))
            # CORREÇÃO APLICADA AQUI: texto formatado corretamente
            st.markdown(f"*(Cada R$ 1 do FNDIT em subsídio atrai R$ {alavancagem_subs:,.2f} de capital privado para o projeto)*".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.info("Não aplicável ou calculável para Alavancagem com Subsídio de Juros (subsídio zero ou negativo).")
        
        st.metric("Alavancagem (Subvenção Total)", "Não aplicável (1:1)")
        st.markdown("*(Subvenção total não alavanca capital privado, pois o FNDIT cobre 100% do projeto)*")


    st.markdown("---")

    # --- Gráfico de Comparação de Projetos ---
    st.header("Comparativo de Quantidade de Projetos")

    data = {
        'Cenário': ['1. Crédito Full', '2. Subsídio Juros (Capac. FNDIT)', '2. Subsídio Juros (Demanda)', '3. Subvenção Total'],
        'Projetos Financiáveis': [
            qtd_projetos_credito_full,
            qtd_projetos_capacidade_fndit,  # Use the raw float('inf') here for plotting
            qtd_projetos_demandados_elasticidade,
            qtd_projetos_subvencao
        ]
    }
    df_projetos = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(df_projetos['Cenário'], df_projetos['Projetos Financiáveis'], color=['skyblue', 'lightgreen', 'salmon', 'gold'])
    ax.set_ylabel("Quantidade de Projetos")
    ax.set_title("Projetos Financiados por Cenário")
    plt.xticks(rotation=15, ha='right')

    # Adicionar o número em cima de cada barra
    for bar in bars:
        yval = bar.get_height()
        if yval == float('inf'):
            ax.text(bar.get_x() + bar.get_width()/2, 0, "Inf.", ha='center', va='bottom', fontsize=10, color='red')
        else:
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f'{int(yval):,}'.replace(",", "."), ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    st.pyplot(fig)

    # --- Financial Comparison Table and Charts ---
    st.header("Análise Financeira por Cenário")

    # Create a comparison DataFrame
    comparison_data = {
        'Cenário': ['Crédito Full', 'Subsídio Juros', 'Subvenção Total'],
        'Custo Total por Projeto': [custo_total_full, custo_total_subsidio, valor_projeto],
        'VPL para Tomador': [vpl_tomador_full, vpl_tomador_subsidio, valor_projeto],
        'Custo FNDIT por Projeto': [0, subs_por_projeto, valor_projeto]
    }
    df_comparison = pd.DataFrame(comparison_data)

    # Format values for Brazilian display
    df_display = df_comparison.copy()
    for col in ['Custo Total por Projeto', 'VPL para Tomador', 'Custo FNDIT por Projeto']:
        df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if not pd.isna(x) else "R$ 0,00")

    # Display as a table
    st.dataframe(df_display)

    # Add a cost-benefit chart
    fig2, ax2 = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Cost comparison
    df_comparison.plot(x='Cenário', y=['Custo Total por Projeto', 'Custo FNDIT por Projeto'], 
                      kind='bar', ax=ax2[0], title='Comparação de Custos por Projeto')
    ax2[0].tick_params(axis='x', rotation=45)
    ax2[0].set_ylabel("Valor (R$)")
    ax2[0].legend(['Custo Total', 'Custo FNDIT'])
    
    # Format y-axis to Brazilian format
    y_labels = [f"R$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") for x in ax2[0].get_yticks()]
    ax2[0].set_yticklabels(y_labels)
    
    # Plot 2: NPV comparison
    df_comparison.plot(x='Cenário', y='VPL para Tomador', 
                      kind='bar', ax=ax2[1], title='VPL para o Tomador', color='green')
    ax2[1].tick_params(axis='x', rotation=45)
    ax2[1].set_ylabel("VPL (R$)")
    
    # Format y-axis to Brazilian format
    y_labels = [f"R$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") for x in ax2[1].get_yticks()]
    ax2[1].set_yticklabels(y_labels)
    
    plt.tight_layout()
    st.pyplot(fig2)

    st.markdown("---")
    st.subheader("Considerações Adicionais para a Política Pública:")
    st.markdown("""
    * **Qual o objetivo principal?** Maximizar o número de projetos? Maximizar a redução de CO2e? Alavancar mais capital privado? Estimular inovação? A resposta a isso define a "melhor" estratégia.
    * **Análise de Sensibilidade:** Explore diferentes valores para a Elasticidade da Demanda. Como os resultados mudam se a demanda for mais ou menos sensível aos juros?
    * **Barreiras não-financeiras:** Além dos juros, quais outras barreiras (conhecimento técnico, burocracia, acesso à tecnologia) podem estar limitando a demanda por projetos de descarbonização? O FNDIT pode atuar nesses pontos.
    * **Monitoramento e Avaliação:** Implementar um sistema robusto para monitorar o impacto real dos projetos financiados em termos de descarbonização, geração de valor e retorno financeiro.
    * **Estruturas Híbridas:** Considere misturar as estratégias. Por exemplo, uma pequena subvenção inicial (seed money) combinada com crédito subsidiado para o restante do projeto.
    * **Estratégias de Demanda:** Quando a capacidade for maior que a demanda estimada, considere implementar campanhas de divulgação, prospecção ativa de empresas e facilitação de processos para aumentar a demanda real.
    """)

    # --- Seção de resultados de descarbonização (código 2) ---
    st.markdown("---")
    co2_evitado_anual = 0
    metodologia_info = ""
    margem_erro = 0.3  # ±30% conforme documento

    # Fatores regionais (ajuste simplificado)
    fatores_regionais = {
        "Norte": 1.1, "Nordeste": 1.2, "Centro-Oeste": 0.9, 
        "Sudeste": 1.0, "Sul": 0.95, "Nacional": 1.0
    }

    if abordagem_co2 == "Setorial (Recomendado)":
        setor = st.sidebar.selectbox(
            "Setor do Projeto",
            ["Energia Renovável", "Eficiência Energética", "Transporte Sustentável", 
            "Agricultura de Baixo Carbono", "Manejo de Resíduos", "Outros"],
            help="Fatores baseados em estudos da EPE, MCTI e Embrapa"
        )
        
        # Valores atualizados com fontes e anos
        fatores_setor = {
            "Energia Renovável": {
                "fator": 180,
                "base": "Emissões evitadas de termelétricas (0,8 tCO2e/MWh) × fator de capacidade",
                "fonte": "EPE (2023), MCTI (2023)",
                "ano": 2023
            },
            "Eficiência Energética": {
                "fator": 120,
                "base": "Redução de consumo em indústrias energy-intensive",
                "fonte": "Estudos setoriais cimento/aço (2023)",
                "ano": 2023
            },
            "Transporte Sustentável": {
                "fator": 150,
                "base": "Eletrificação substituindo diesel (2,68 kgCO2/litro)",
                "fonte": "MCTI - Fatores de Emissão (2024)",
                "ano": 2024
            },
            "Agricultura de Baixo Carbono": {
                "fator": 90,
                "base": "ILPF, recuperação de pastagens, fixação biológica de N₂",
                "fonte": "Embrapa, Programa ABC+ (2023)",
                "ano": 2023
            },
            "Manejo de Resíduos": {
                "fator": 80,
                "base": "Metano evitado (GWP 28× CO₂) + energia renovável",
                "fonte": "IPCC, metodologias CDM (2023)",
                "ano": 2023
            },
            "Outros": {
                "fator": 60,
                "base": "Setores diversos com menor potencial específico",
                "fonte": "Estimativa conservadora (2024)",
                "ano": 2024
            }
        }
        
        setor_info = fatores_setor[setor]
        co2_evitado_anual = (valor_projeto / 1_000_000) * setor_info["fator"]
        metodologia_info = f"**Base técnica:** {setor_info['base']}\n**Fonte:** {setor_info['fonte']}\n**Ano de referência:** {setor_info['ano']}"

    elif abordagem_co2 == "Por Tecnologia Específica":
        tecnologia = st.sidebar.selectbox(
            "Tecnologia de Descarbonização",
            ["Solar Fotovoltaica", "Eólica", "Biogás/Biometano", "Veículos Elétricos",
            "Captura e Armazenamento de Carbono", "Hidrogênio Verde", "Outras"],
            help="Fatores específicos por tecnologia com base em projetos reais brasileiros"
        )
        
        # Fatores detalhados com informações regionais
        fatores_tecnologia = {
            "Solar Fotovoltaica": {
                "fator": 200,
                "calculo": "1.600 MWh/ano × 0,8 tCO2e/MWh × 25 anos / R$ 4 milhões",
                "premissas": "Fator de capacidade 20% (Nordeste: 25%, Sul: 18%)",
                "fontes": "ABSolar, ONS (2023)"
            },
            "Eólica": {
                "fator": 190,
                "calculo": "3.000 MWh/ano × 0,8 tCO2e/MWh × 25 anos / R$ 6 milhões",
                "premissas": "Fator de capacidade 35% (Nordeste: 45%, Sul: 32%)",
                "fontes": "ABEEólica, ONS (2023)"
            },
            "Biogás/Biometano": {
                "fator": 130,
                "calculo": "Metano evitado (GWP 28) + substituição de diesel",
                "premissas": "Potencial de aquecimento global do metano (IPCC AR6)",
                "fontes": "EPE, MCTI (2023)"
            },
            "Veículos Elétricos": {
                "fator": 160,
                "calculo": "30.000 km/ano × 0,15 kWh/km × 0,8 tCO2e/MWh × 10 anos",
                "premissas": "Vida útil 10 anos, rodagem média brasileira (ANTT 2023)",
                "fontes": "ANTP, MCTI (2024)"
            },
            "Captura e Armazenamento de Carbono": {
                "fator": 110,
                "calculo": "Custos elevados vs. potencial tecnológico atual",
                "premissas": "Tecnologia ainda em desenvolvimento no Brasil",
                "fontes": "Estudos internacionais adaptados (2024)"
            },
            "Hidrogênio Verde": {
                "fator": 140,
                "calculo": "Tecnologia emergente com custos elevados",
                "premissas": "Baseado em projetos piloto internacionais",
                "fontes": "IEA, EPE (2023)"
            },
            "Outras": {
                "fator": 70,
                "calculo": "Média ponderada de tecnologias não especificadas",
                "premissas": "Estimativa conservadora",
                "fontes": "Várias (2023-2024)"
            }
        }
        
        tech_info = fatores_tecnologia[tecnologia]
        co2_evitado_anual = (valor_projeto / 1_000_000) * tech_info["fator"]
        metodologia_info = f"**Cálculo:** {tech_info['calculo']}\n**Premissas:** {tech_info['premissas']}\n**Fontes:** {tech_info['fontes']}"

    elif abordagem_co2 == "Meta Customizada":
        st.sidebar.info("⚠️ Use com cautela - validar com especialista setorial")
        fator_custom = st.sidebar.slider(
            "Fator de Redução (tCO2e/milhão R$/ano)",
            min_value=10, max_value=500, value=100, step=10,
            help="Range baseado em estudos setoriais brasileiros (2023-2024)"
        )
        co2_evitado_anual = (valor_projeto / 1_000_000) * fator_custom
        metodologia_info = "**Atenção:** Fator customizado - recomenda-se validação técnica com especialista setorial"

    # Aplicar fator regional
    co2_evitado_anual *= fatores_regionais[regiao]

    # Aplicar margem de erro ajustável
    sensibilidade = 0
    co2_min, co2_max = 0, 0
    if co2_evitado_anual > 0:
        sensibilidade = st.slider(
            "Margem de Erro Estimada (±%)",
            min_value=10, max_value=50, value=30, step=5,
            help="Ajuste conforme confiança nos parâmetros utilizados"
        )
        co2_min = co2_evitado_anual * (1 - sensibilidade/100)
        co2_max = co2_evitado_anual * (1 + sensibilidade/100)

    # Seção de resultados aprimorada
    if abordagem_co2 != "Nenhuma" and co2_evitado_anual > 0:
        st.header("🔥 Impacto de Descarbonização Estimado")
        
        # Mostrar metodologia utilizada
        if metodologia_info:
            with st.expander("📋 Metodologia e Fontes"):
                st.write(metodologia_info)
                if regiao != "Nacional":
                    st.info(f"**Fator regional aplicado:** {fatores_regionais[regiao]:.2f}x para {regiao}")
                st.caption(f"Margem de erro: ±{sensibilidade}% (ajustável conforme confiança nos parâmetros)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Redução Anual de CO2e", 
                f"{co2_evitado_anual:,.0f} t/ano",
                help=f"Range estimado: {co2_min:,.0f} - {co2_max:,.0f} t/ano"
            )
        
        with col2:
            reducao_total = co2_evitado_anual * prazo_anos
            st.metric("Redução Total no Período", f"{reducao_total:,.0f} t")
        
        with col3:
            # Calcular custo por tonelada evitada
            if subs_por_projeto > 0:
                custo_por_tonelada = subs_por_projeto / co2_evitado_anual
                tipo_custo = "Subsídio"
            else:
                custo_por_tonelada = valor_projeto / co2_evitado_anual
                tipo_custo = "Investimento"
            st.metric(f"Custo {tipo_custo}/Tonelada", f"R$ {custo_por_tonelada:,.0f}")
        
        with col4:
            # Equivalência em carros (4 tCO2e/ano conforme documento)
            carros_equivalentes = co2_evitado_anual / 4
            st.metric("Equiv. Carros Retirados", f"{carros_equivalentes:,.0f}")
        
        # Análise de custo-efetividade com referências brasileiras atualizadas
        st.subheader("💰 Análise de Custo-Efetividade")
        
        # Valores de mercado atualizados 2024
        referencias_mercado = {
            "Mercado Voluntário (Mín.)": 50,
            "Mercado Voluntário (Máx.)": 180,
            "Regulado (Mín.)": 80,
            "Regulado (Máx.)": 250,
            "CBIOs (RenovaBio)": 85,
            "Seu Projeto": custo_por_tonelada
        }
        
        # Criar DataFrame para visualização
        df_comparacao = pd.DataFrame([
            {"Categoria": k, "Custo (R$/tCO2e)": v, "Tipo": "Mercado" if k != "Seu Projeto" else "Projeto"}
            for k, v in referencias_mercado.items()
        ])
        
        # Gráfico de barras
        fig = px.bar(
            df_comparacao, 
            x="Categoria", 
            y="Custo (R$/tCO2e)",
            color="Tipo",
            title="Comparação com Referências do Mercado Brasileiro de Carbono (2024)",
            color_discrete_map={"Mercado": "lightblue", "Projeto": "darkgreen"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise qualitativa atualizada
        if custo_por_tonelada <= 150:
            st.success(f"✅ **Custo-efetivo**: Abaixo ou igual ao mercado voluntário (R$ {custo_por_tonelada:,.0f}/tCO2e)")
        elif custo_por_tonelada <= 200:
            st.info(f"ℹ️ **Competitivo**: Dentro do range regulado (R$ {custo_por_tonelada:,.0f}/tCO2e)")
        elif custo_por_tonelada <= 350:
            st.warning(f"⚠️ **Acima do mercado**: Justificar co-benefícios (R$ {custo_por_tonelada:,.0f}/tCO2e)")
        else:
            st.error(f"❌ **Muito alto**: Revisar parametrização (R$ {custo_por_tonelada:,.0f}/tCO2e)")
        
        # Impacto agregado da política
        st.subheader("🎯 Impacto Agregado da Política")
        
        if qtd_projetos_capacidade_fndit != float('inf'):
            projetos_efetivos = min(qtd_projetos_demandados_elasticidade, qtd_projetos_capacidade_fndit)
            reducao_total_politica = co2_evitado_anual * projetos_efetivos
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Redução Anual da Política", f"{reducao_total_politica:,.0f} t/ano")
            with col2:
                st.metric("Redução Total da Política", f"{reducao_total_politica * prazo_anos:,.0f} t")
            with col3:
                st.metric("Carros Retirados da Política", f"{reducao_total_politica / 4:,.0f}")
        else:
            st.info("O impacto agregado não pode ser calculado pois a capacidade de financiamento do FNDIT é ilimitada para o subsídio atual.")

else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Simular' para ver os resultados.")

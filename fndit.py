import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

# --- Funções de Cálculo ---

def calcular_parcela_price(valor_financiamento, taxa_juros_mensal, num_parcelas):
    """Calcula a parcela fixa do sistema Price."""
    if num_parcelas <= 0: # Prazo zero ou negativo não faz sentido para cálculo de parcela
        return float('inf')
    if taxa_juros_mensal <= 1e-9: # Tratando juros muito próximos de zero como zero para estabilidade
        return valor_financiamento / num_parcelas
    
    try:
        denominador = 1 - (1 + taxa_juros_mensal)**(-num_parcelas)
        if denominador == 0: # Caso a taxa seja tão pequena que a exponenciação se aproxime de 1
            return valor_financiamento / num_parcelas
        return (valor_financiamento * taxa_juros_mensal) / denominador
    except OverflowError: # Para números muito grandes/pequenos
        return float('inf') # Retorna infinito se o cálculo for inviável

def calcular_vpl(fluxos_caixa, taxa_desconto_mensal):
    """Calcula o Valor Presente Líquido (VPL) de uma série de fluxos de caixa."""
    vpl = 0
    # Ajuste para evitar divisão por zero ou problemas com taxa de desconto -100%
    if taxa_desconto_mensal <= -1:
        return float('inf') 
        
    for t, fluxo in enumerate(fluxos_caixa):
        vpl += fluxo / ((1 + taxa_desconto_mensal)**t)
    return vpl

# --- Configurações da Página Streamlit ---
st.set_page_config(layout="wide", page_title="Simulador de Fomento à Descarbonização (FNDIT)")

st.title("🌱 Simulador de Política Pública de Fomento à Descarbonização")
st.markdown("""
Esta ferramenta permite simular o impacto de diferentes estratégias de alocação de recursos do FNDIT
em projetos de descarbonização, considerando a elasticidade da demanda por crédito.
""")

st.sidebar.header("Parâmetros do Projeto e do FNDIT")

# --- Parâmetros de Entrada ---
valor_projeto = st.sidebar.slider("1. Valor do Projeto de Descarbonização (R$)", 
                                  min_value=1_000_000, max_value=100_000_000, # Adjusted min_value for more flexibility
                                  value=30_000_000, step=1_000_000) # Adjusted step
taxa_juros_full_anual = st.sidebar.slider("2. Taxa de Juros Full (a.a. %) - Mercado", 
                                          min_value=0.0, max_value=15.0, 
                                          value=7.8, step=0.1) / 100
montante_fndit = st.sidebar.slider("3. Montante no FNDIT para Subsídios/Crédito (R$)", 
                                   min_value=10_000_000, max_value=1_000_000_000, 
                                   value=200_000_000, step=10_000_000) # Adjusted min_value and step
prazo_anos = st.sidebar.slider("4. Prazo para Amortização (anos)", 
                               min_value=1, max_value=20, # Increased max_value
                               value=5, step=1)
taxa_juros_subsidio_anual = st.sidebar.slider("Taxa de Juros Subsidiada Alvo (a.a. %)", 
                                               min_value=0.0, max_value=taxa_juros_full_anual * 100, # Max can be full rate
                                               value=min(3.0, taxa_juros_full_anual * 100), step=0.1) / 100 # Ensure value doesn't exceed full rate
elasticidade_demanda = st.sidebar.slider("Elasticidade da Demanda por Crédito de Descarbonização", 
                                         min_value=-5.0, max_value=-0.1, # Extended range for more elasticity
                                         value=-1.5, step=0.1)
reducao_co2e_por_projeto_ton = st.sidebar.number_input("Redução de CO2e por projeto (toneladas/ano)", 
                                                         min_value=0, max_value=500000, # Min_value to 0 for initial scenario
                                                         value=10000, step=1000)
taxa_desconto_tomador_anual = st.sidebar.slider("Taxa de Desconto para VPL (Tomador) a.a. (%)",
                                                min_value=0.0, max_value=25.0, # Extended max_value
                                                value=12.0, step=0.5) / 100

# --- "Simular" Button ---
if st.sidebar.button("Simular"):
    st.session_state.run_simulation = True
else:
    if 'run_simulation' not in st.session_state:
        st.session_state.run_simulation = False # Initialize state

if st.session_state.run_simulation:
    # --- Conversões ---
    prazo_meses = prazo_anos * 12
    # Ensure monthly rates are handled correctly for 0% annual rates
    taxa_juros_full_mensal = (1 + taxa_juros_full_anual)**(1/12) - 1 if taxa_juros_full_anual > 0 else 0.0
    taxa_juros_subsidio_mensal = (1 + taxa_juros_subsidio_anual)**(1/12) - 1 if taxa_juros_subsidio_anual > 0 else 0.0
    taxa_desconto_tomador_mensal = (1 + taxa_desconto_tomador_anual)**(1/12) - 1 if taxa_desconto_tomador_anual > 0 else 0.0

    # --- Cálculos dos Cenários ---

    st.header("Resultados da Simulação")

    col1, col2, col3 = st.columns(3)

    # --- Cenário 1: Crédito com Juros Full ---
    with col1:
        st.subheader("Cenário 1: Crédito com Juros Full")
        qtd_projetos_credito_full = montante_fndit // valor_projeto if valor_projeto > 0 else 0
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_credito_full)}")

        parcela_full = calcular_parcela_price(valor_projeto, taxa_juros_full_mensal, prazo_meses)
        custo_total_full = parcela_full * prazo_meses
        juros_total_full = custo_total_full - valor_projeto
        st.markdown(f"**Detalhes por Projeto (Juros Full):**")
        st.markdown(f"- Parcela Mensal: R$ {parcela_full:,.2f}")
        st.markdown(f"- Custo Total Financiamento: R$ {custo_total_full:,.2f}")
        st.markdown(f"- Juros Totais Pagos: R$ {juros_total_full:,.2f}")

        # VPL para o Tomador (cenário sem subsídio - custo)
        # Assuming that if juros_full is 0, VPL of financing is effectively 0 for the borrower
        if taxa_juros_full_mensal <= 1e-9 and taxa_desconto_tomador_mensal <= 1e-9:
             vpl_tomador_full = 0.0
             st.markdown(f"- VPL para o Tomador (Juros Full): R$ {0.0:,.2f}")
             st.markdown(f"*(VPL do financiamento. Se juros e taxa de desconto são 0%, VPL é 0)*")
        else:
            fluxos_tomador_full = [-parcela_full] * prazo_meses
            fluxos_tomador_full[0] += valor_projeto # Recebe o valor no início
            vpl_tomador_full = calcular_vpl(fluxos_tomador_full, taxa_desconto_tomador_mensal)
            st.markdown(f"- VPL para o Tomador (Juros Full): R$ {vpl_tomador_full:,.2f}")
            st.markdown(f"*(VPL inicial do financiamento. Representa o custo financeiro líquido para o tomador)*")


    # --- Cenário 2: Subsídio de Juros (7,8% para 3%) ---
    with col2:
        st.subheader("Cenário 2: Subsídio de Juros")

        parcela_subsidio = calcular_parcela_price(valor_projeto, taxa_juros_subsidio_mensal, prazo_meses)
        custo_total_subsidio = parcela_subsidio * prazo_meses
        
        juros_total_subsidio = custo_total_subsidio - valor_projeto
        subs_por_projeto = (parcela_full - parcela_subsidio) * prazo_meses
        
        # --- FIX PARA OverflowError: float('inf') para int ---
        if subs_por_projeto <= 1e-9 or subs_por_projeto == float('inf'): # Se o subsídio for zero, negativo ou infinito (erro de cálculo), FNDIT pode subsidiar "infinitos" projetos
            qtd_projetos_capacidade_fndit_display = "Infinito" 
            qtd_projetos_capacidade_fndit = float('inf') # Keep as float('inf') for internal calculations
        else:
            qtd_projetos_capacidade_fndit = montante_fndit // subs_por_projeto
            qtd_projetos_capacidade_fndit_display = f"{int(qtd_projetos_capacidade_fndit)}"
            
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", qtd_projetos_capacidade_fndit_display)

        st.markdown(f"**Detalhes por Projeto (Juros Subsidiados):**")
        st.markdown(f"- Parcela Mensal: R$ {parcela_subsidio:,.2f}")
        st.markdown(f"- Custo Total Financiamento: R$ {custo_total_subsidio:,.2f}")
        st.markdown(f"- Juros Totais Pagos: R$ {juros_total_subsidio:,.2f}")
        st.markdown(f"- **Subsídio FNDIT por Projeto: R$ {subs_por_projeto:,.2f}**")

        # VPL para o Tomador (cenário subsidiado - benefício)
        if taxa_juros_subsidio_mensal <= 1e-9 and taxa_desconto_tomador_mensal <= 1e-9:
            vpl_tomador_subsidio = 0.0
            st.markdown(f"- VPL para o Tomador (Juros Subsidiados): R$ {0.0:,.2f}")
        else:
            fluxos_tomador_subsidio = [-parcela_subsidio] * prazo_meses
            fluxos_tomador_subsidio[0] += valor_projeto
            vpl_tomador_subsidio = calcular_vpl(fluxos_tomador_subsidio, taxa_desconto_tomador_mensal)
            st.markdown(f"- VPL para o Tomador (Juros Subsidiados): R$ {vpl_tomador_subsidio:,.2f}")


        st.markdown("---")
        st.markdown("**Com Elasticidade da Demanda:**")
        
        # Previne divisão por zero se taxa_juros_full_anual for 0
        if taxa_juros_full_anual <= 0:
            st.warning("Não é possível calcular variação percentual na taxa de juros quando a taxa full é 0%.")
            qtd_projetos_demandados_elasticidade = 0
            aumento_demanda_percentual_display = "N/A"
        else:
            variacao_juros_percentual = (taxa_juros_subsidio_anual - taxa_juros_full_anual) / taxa_juros_full_anual
            
            demanda_base_full = qtd_projetos_credito_full # Número de projetos que o FNDIT financiaria a juros full
            
            aumento_demanda_percentual = elasticidade_demanda * variacao_juros_percentual
            qtd_projetos_demandados_elasticidade = demanda_base_full * (1 + aumento_demanda_percentual)
            aumento_demanda_percentual_display = f"{aumento_demanda_percentual:.2%}"
            
        st.metric("Projetos Demandados (Elasticidade)", f"{int(qtd_projetos_demandados_elasticidade)}")
        st.markdown(f"*(Assumindo {int(demanda_base_full)} projetos como demanda base a juros full)*")
        st.markdown(f"*(Aumento de demanda de: {aumento_demanda_percentual_display})*")

        st.markdown(f"**Conclusão Elasticidade:** O FNDIT pode subsidiar até {qtd_projetos_capacidade_fndit_display} projetos, mas a demanda estimada é de {int(qtd_projetos_demandados_elasticidade)} projetos. Isso sugere que a demanda de mercado é o fator limitante neste cenário.")


    # --- Cenário 3: Subvenção Total do Projeto ---
    with col3:
        st.subheader("Cenário 3: Subvenção Total")
        qtd_projetos_subvencao = montante_fndit // valor_projeto if valor_projeto > 0 else 0
        st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_subvencao)}")
        st.markdown(f"**Detalhes por Projeto (Subvenção Total):**")
        st.markdown(f"- Valor da Subvenção: R$ {valor_projeto:,.2f}")
        st.markdown(f"*(Não há parcelas ou juros, pois o valor é doado)*")
        st.markdown(f"- VPL para o Tomador (Subvenção): R$ {valor_projeto:,.2f}") # VPL é o valor recebido


    st.markdown("---")

    st.header("Análise Comparativa e Indicadores de Impacto")

    col_ind1, col_ind2, col_ind3 = st.columns(3)

    # Custo de Subsídio por Projeto
    with col_ind1:
        st.subheader("Custo de Subsídio por Projeto (FNDIT)")
        if subs_por_projeto > 1e-9: # Only show if there's a meaningful positive subsidy
            st.metric("Subsídio de Juros", f"R$ {subs_por_projeto:,.2f}")
            st.markdown("*(Este é o valor que o FNDIT gasta por projeto para reduzir os juros para o tomador)*")
        else:
            st.info("Não há subsídio de juros ou é insignificante (taxa subsidiada igual ou maior que a full).")

    # Custo por Tonelada de CO2e Evitada (Estimado)
    with col_ind2:
        st.subheader("Custo por Tonelada de CO2e Evitada")
        if reducao_co2e_por_projeto_ton > 0:
            if subs_por_projeto > 1e-9:
                custo_ton_co2e_subsidio = subs_por_projeto / reducao_co2e_por_projeto_ton
                st.metric("Custo Subsídio/ton CO2e (Juros Subsid.)", f"R$ {custo_ton_co2e_subsidio:,.2f}")
            else:
                st.info("Custo Subsídio/ton CO2e não aplicável (sem subsídio ou subsídio zero).")
            
            custo_ton_co2e_subvencao = valor_projeto / reducao_co2e_por_projeto_ton
            st.metric("Custo Subvenção/ton CO2e (Subvenção Total)", f"R$ {custo_ton_co2e_subvencao:,.2f}")
        else:
            st.warning("Redução de CO2e por projeto deve ser maior que zero para calcular o custo por tonelada.")


    # Alavancagem de Capital Privado (para o cenário de subsídio de juros)
    with col_ind3:
        st.subheader("Alavancagem de Capital Privado")
        if subs_por_projeto > 1e-9:
            alavancagem_subs = valor_projeto / subs_por_projeto
            st.metric("Alavancagem (Subsídio de Juros)", f"{alavancagem_subs:,.2f}x")
            st.markdown(f"*(Cada R$1 do FNDIT em subsídio atrai R${alavancagem_subs:,.2f} de capital privado para o projeto)*")
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
            qtd_projetos_capacidade_fndit, # Use the raw float('inf') here for plotting
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
            ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f'{int(yval)}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("Considerações Adicionais para a Política Pública:")
    st.markdown("""
    * **Qual o objetivo principal?** Maximizar o número de projetos? Maximizar a redução de CO2e? Alavancar mais capital privado? Estimular inovação? A resposta a isso define a "melhor" estratégia.
    * **Análise de Sensibilidade:** Explore diferentes valores para a Elasticidade da Demanda. Como os resultados mudam se a demanda for mais ou menos sensível aos juros?
    * **Barreiras não-financeiras:** Além dos juros, quais outras barreiras (conhecimento técnico, burocracia, acesso à tecnologia) podem estar limitando a demanda por projetos de descarbonização? O FNDIT pode atuar nesses pontos.
    * **Monitoramento e Avaliação:** Implementar um sistema robusto para monitorar o impacto real dos projetos financiados em termos de descarbonização, geração de valor e retorno financeiro.
    * **Estruturas Híbridas:** Considere misturar as estratégias. Por exemplo, uma pequena subvenção inicial (seed money) combinada com crédito subsidiado para o restante do projeto.
    """)
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Simular' para ver os resultados.")

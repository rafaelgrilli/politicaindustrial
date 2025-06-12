import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

# --- Funções de Cálculo ---

def calcular_parcela_price(valor_financiamento, taxa_juros_mensal, num_parcelas):
    """Calcula a parcela fixa do sistema Price."""
    if taxa_juros_mensal == 0:
        return valor_financiamento / num_parcelas
    
    # Ajuste para a fórmula de juros compostos para evitar números muito pequenos
    # Para taxas muito pequenas, (1 + i)^-n pode ser 1, levando a divisão por zero.
    # É melhor tratar isso como zero juros ou uma aproximação.
    # Usando o limite da série:
    # Se i for muito pequeno, (1+i)^-n ~ 1 - n*i
    # 1 - (1+i)^-n ~ n*i
    # P = (V * i) / (n * i) = V / n
    
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
                                  min_value=10_000_000, max_value=100_000_000, 
                                  value=30_000_000, step=5_000_000)
taxa_juros_full_anual = st.sidebar.slider("2. Taxa de Juros Full (a.a. %) - Mercado", 
                                          min_value=5.0, max_value=15.0, 
                                          value=7.8, step=0.1) / 100
montante_fndit = st.sidebar.slider("3. Montante no FNDIT para Subsídios/Crédito (R$)", 
                                   min_value=50_000_000, max_value=1_000_000_000, 
                                   value=200_000_000, step=50_000_000)
prazo_anos = st.sidebar.slider("4. Prazo para Amortização (anos)", 
                               min_value=1, max_value=15, 
                               value=5, step=1)
taxa_juros_subsidio_anual = st.sidebar.slider("Taxa de Juros Subsidiada Alvo (a.a. %)", 
                                               min_value=0.5, max_value=7.0, 
                                               value=3.0, step=0.1) / 100
elasticidade_demanda = st.sidebar.slider("Elasticidade da Demanda por Crédito de Descarbonização", 
                                         min_value=-3.0, max_value=-0.5, 
                                         value=-1.5, step=0.1)
# Novas variáveis para indicadores adicionais
reducao_co2e_por_projeto_ton = st.sidebar.number_input("Redução de CO2e por projeto (toneladas/ano)", 
                                                         min_value=1000, max_value=100000, 
                                                         value=10000, step=1000)
taxa_desconto_tomador_anual = st.sidebar.slider("Taxa de Desconto para VPL (Tomador) a.a. (%)",
                                                min_value=8.0, max_value=20.0,
                                                value=12.0, step=0.5) / 100

# --- Conversões ---
prazo_meses = prazo_anos * 12
taxa_juros_full_mensal = (1 + taxa_juros_full_anual)**(1/12) - 1
taxa_juros_subsidio_mensal = (1 + taxa_juros_subsidio_anual)**(1/12) - 1
taxa_desconto_tomador_mensal = (1 + taxa_desconto_tomador_anual)**(1/12) - 1

# --- Cálculos dos Cenários ---

st.header("Resultados da Simulação")

col1, col2, col3 = st.columns(3)

# --- Cenário 1: Crédito com Juros Full ---
with col1:
    st.subheader("Cenário 1: Crédito com Juros Full")
    qtd_projetos_credito_full = montante_fndit // valor_projeto
    st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_credito_full)}")

    parcela_full = calcular_parcela_price(valor_projeto, taxa_juros_full_mensal, prazo_meses)
    custo_total_full = parcela_full * prazo_meses
    juros_total_full = custo_total_full - valor_projeto
    st.markdown(f"**Detalhes por Projeto (Juros Full):**")
    st.markdown(f"- Parcela Mensal: R$ {parcela_full:,.2f}")
    st.markdown(f"- Custo Total Financiamento: R$ {custo_total_full:,.2f}")
    st.markdown(f"- Juros Totais Pagos: R$ {juros_total_full:,.2f}")

    # VPL para o Tomador (cenário sem subsídio - custo)
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
    
    qtd_projetos_capacidade_fndit = montante_fndit // subs_por_projeto if subs_por_projeto > 0 else float('inf')
    st.metric("Projetos Financiáveis (Capacidade FNDIT)", f"{int(qtd_projetos_capacidade_fndit)}")

    st.markdown(f"**Detalhes por Projeto (Juros Subsidiados):**")
    st.markdown(f"- Parcela Mensal: R$ {parcela_subsidio:,.2f}")
    st.markdown(f"- Custo Total Financiamento: R$ {custo_total_subsidio:,.2f}")
    st.markdown(f"- Juros Totais Pagos: R$ {juros_total_subsidio:,.2f}")
    st.markdown(f"- **Subsídio FNDIT por Projeto: R$ {subs_por_projeto:,.2f}**")

    # VPL para o Tomador (cenário subsidiado - benefício)
    fluxos_tomador_subsidio = [-parcela_subsidio] * prazo_meses
    fluxos_tomador_subsidio[0] += valor_projeto
    vpl_tomador_subsidio = calcular_vpl(fluxos_tomador_subsidio, taxa_desconto_tomador_mensal)
    st.markdown(f"- VPL para o Tomador (Juros Subsidiados): R$ {vpl_tomador_subsidio:,.2f}")


    st.markdown("---")
    st.markdown("**Com Elasticidade da Demanda:**")
    
    # Calcular % de variação nos juros
    # Ajuste: A base é a taxa full, o "preço" que diminui.
    variacao_juros_percentual = (taxa_juros_subsidio_anual - taxa_juros_full_anual) / taxa_juros_full_anual
    
    # Usando 6 projetos como a "demanda base" para juros full, como na discussão
    demanda_base_full = qtd_projetos_credito_full # Número de projetos que o FNDIT financiaria a juros full
    
    # Calcular aumento percentual na demanda
    aumento_demanda_percentual = elasticidade_demanda * variacao_juros_percentual
    
    qtd_projetos_demandados_elasticidade = demanda_base_full * (1 + aumento_demanda_percentual)
    
    st.metric("Projetos Demandados (Elasticidade)", f"{int(qtd_projetos_demandados_elasticidade)}")
    st.markdown(f"*(Assumindo {int(demanda_base_full)} projetos como demanda base a juros full)*")
    st.markdown(f"*(Aumento de demanda de: {aumento_demanda_percentual:.2%})*")

    st.markdown(f"**Conclusão Elasticidade:** O FNDIT pode subsidiar até {int(qtd_projetos_capacidade_fndit)} projetos, mas a demanda estimada é de {int(qtd_projetos_demandados_elasticidade)} projetos. Isso sugere que a demanda de mercado é o fator limitante neste cenário.")


# --- Cenário 3: Subvenção Total do Projeto ---
with col3:
    st.subheader("Cenário 3: Subvenção Total")
    qtd_projetos_subvencao = montante_fndit // valor_projeto
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
    if subs_por_projeto > 0:
        st.subheader("Custo de Subsídio por Projeto (FNDIT)")
        st.metric("Subsídio de Juros", f"R$ {subs_por_projeto:,.2f}")
        st.markdown("*(Este é o valor que o FNDIT gasta por projeto para reduzir os juros para o tomador)*")
    else:
        st.warning("Subsídio de Juros não calculável (taxa subsidiada muito alta ou igual à full).")

# Custo por Tonelada de CO2e Evitada (Estimado)
with col_ind2:
    st.subheader("Custo por Tonelada de CO2e Evitada")
    # Para fins de simulação, vamos usar o valor do projeto como o "custo" para essa métrica,
    # embora na prática o custo do subsídio seja o mais relevante para a política pública.
    # No cenário de subsídio, o custo para o FNDIT é o subsídio.
    if reducao_co2e_por_projeto_ton > 0:
        custo_ton_co2e_subsidio = subs_por_projeto / reducao_co2e_por_projeto_ton
        st.metric("Custo Subsídio/ton CO2e (Juros Subsid.)", f"R$ {custo_ton_co2e_subsidio:,.2f}")
        
        # Para subvenção total, o custo é o valor do projeto
        custo_ton_co2e_subvencao = valor_projeto / reducao_co2e_por_projeto_ton
        st.metric("Custo Subvenção/ton CO2e (Subvenção Total)", f"R$ {custo_ton_co2e_subvencao:,.2f}")
    else:
        st.warning("Redução de CO2e por projeto deve ser maior que zero.")


# Alavancagem de Capital Privado (para o cenário de subsídio de juros)
with col_ind3:
    st.subheader("Alavancagem de Capital Privado")
    # No cenário de subsídio de juros, o tomador ainda financia R$30M. O FNDIT "subsidiia" uma parte.
    # A alavancagem pode ser vista como o capital privado mobilizado pelo subsídio do FNDIT.
    # Aqui, cada projeto de 30M que é financiado com subsídio, mobiliza 30M de capital privado.
    # A alavancagem é então o valor do projeto dividido pelo subsídio do FNDIT.
    if subs_por_projeto > 0:
        alavancagem_subs = valor_projeto / subs_por_projeto
        st.metric("Alavancagem (Subsídio de Juros)", f"{alavancagem_subs:,.2f}x")
        st.markdown(f"*(Cada R$1 do FNDIT em subsídio atrai R${alavancagem_subs:,.2f} de capital privado para o projeto)*")
    else:
        st.info("Não aplicável ou calculável para Alavancagem com Subsídio de Juros.")
    
    # Para subvenção total, a alavancagem é 0 ou indefinida, pois o FNDIT cobre tudo.
    st.metric("Alavancagem (Subvenção Total)", "Não aplicável (1:1)")
    st.markdown("*(Subvenção total não alavanca capital privado, pois o FNDIT cobre 100%)*")


st.markdown("---")

# --- Gráfico de Comparação de Projetos ---
st.header("Comparativo de Quantidade de Projetos")

data = {
    'Cenário': ['1. Crédito Full', '2. Subsídio Juros (Capac. FNDIT)', '2. Subsídio Juros (Demanda)', '3. Subvenção Total'],
    'Projetos Financiáveis': [
        qtd_projetos_credito_full,
        qtd_projetos_capacidade_fndit,
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
    ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, round(yval), ha='center', va='bottom', fontsize=10)

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
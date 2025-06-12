# 🌿 Simulador de Política Pública de Fomento à Descarbonização (FNDIT)

Este projeto oferece um aplicativo interativo construído com Streamlit para simular o impacto de diferentes estratégias de alocação de recursos do Fundo Nacional de Desenvolvimento Industrial e Tecnológico (FNDIT) em projetos de descarbonização. A ferramenta permite comparar cenários de crédito, subsídio de juros e subvenção total, incorporando a sensibilidade da demanda via elasticidade de mercado e outros indicadores-chave para auxiliar na decisão de política pública.

---

## 🎯 Objetivos do Simulador

O principal objetivo do simulador é permitir que formuladores de políticas, analistas e gestores avaliem:

* **Capacidade de Financiamento:** Quantos projetos o montante do FNDIT pode apoiar em diferentes modalidades (crédito, subsídio, subvenção).
* **Impacto da Elasticidade da Demanda:** Como a redução da taxa de juros pode estimular a demanda por projetos de descarbonização.
* **Custo-Benefício:** Análise do custo do subsídio por projeto e o custo por tonelada de CO2e evitada.
* **Alavancagem de Capital:** O potencial de cada estratégia para atrair investimento privado.
* **Viabilidade Financeira para o Tomador:** O impacto da política no Valor Presente Líquido (VPL) dos projetos para as empresas.

---

## ✨ Funcionalidades Principais

* **Parâmetros Configuráveis:** Ajuste facilmente o valor do projeto, taxa de juros (full e subsidiada), montante do FNDIT, prazo de amortização e elasticidade da demanda.
* **Simulação de Cenários:**
    * **Crédito com Juros Full:** O FNDIT atua como um banco, emprestando a valor de mercado.
    * **Subsídio de Juros:** O FNDIT cobre a diferença entre a taxa de mercado e uma taxa subsidiada para o tomador. Inclui cálculo da demanda esperada com base na elasticidade.
    * **Subvenção Total:** O FNDIT cobre 100% do valor do projeto, atuando como um fundo perdido.
* **Indicadores de Impacto:**
    * **VPL para o Tomador:** Avalia o benefício financeiro para a empresa que recebe o fomento.
    * **Custo de Subsídio por Projeto:** Mostra o investimento do FNDIT por iniciativa.
    * **Custo por Tonelada de CO2e Evitada:** Uma métrica de eficiência ambiental para o gasto público.
    * **Alavancagem de Capital Privado:** Quantifica a atração de recursos externos por parte do FNDIT.
* **Visualização Gráfica:** Gráfico comparativo da quantidade de projetos financiados/demandados em cada cenário.

---

## 🚀 Como Configurar e Executar

Siga os passos abaixo para ter o simulador rodando em sua máquina local:

### Pré-requisitos

Certifique-se de ter o Python 3.8+ instalado em seu sistema.

### 1. Clonar o Repositório (ou Salvar o Código)

Se você recebeu este código como um arquivo único (`app.py`), pule esta etapa. Caso contrário, se estiver em um repositório Git, clone-o:

```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_DIRETORIO>

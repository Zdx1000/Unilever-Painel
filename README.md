# Painel MD - Unilever Uni.co

Projeto para estruturar a primeira versao do painel de acompanhamento Uni.co MD, com foco em consolidar bases de clientes, vendas, faturamento, metas e KPIs principais.

## Contexto

MD significa Martins Distribuidora. No contexto Uni.co, a proposta e permitir que pequenos e grandes comercios sejam atendidos pela Martins com acesso facilitado ao mix da Unilever, sem depender exclusivamente do processo convencional ou dos sistemas atuais de acompanhamento como View/NeoGrid.

O objetivo do painel e responder, de forma consolidada:

> Estamos batendo ou nao os indicadores do Uni.co?

## Objetivo da primeira etapa

Criar uma visao inicial de acompanhamento com:

- Indicador
- BU
- Meta
- Realizado
- Percentual de atingimento
- Status
- Faixa de ganho

Nesta etapa, a prioridade e validar se os calculos batem com a logica da Unilever.

## KPIs principais

| KPI | Objetivo | Status no codigo |
|---|---|---|
| Faturamento / YTD | Valor realizado por BU e tipo de valor | Implementado |
| Cobertura Ponderada | Clientes/redes ponderadas positivadas | Implementado, ainda em validacao de regra final |
| Cobertura Numerica | Clientes numericos distintos positivados | Implementado |
| Sortimento Ponderado | Itens/SKUs foco positivados | Pendente |
| Sortimento Numerico | PPA/categorias positivadas | Pendente |
| Execucao de campo | Indicadores operacionais de execucao | Fora da primeira etapa |

## Regras de negocio consideradas

- Ponderada tem apuracao mensal.
- Numerica tem apuracao por bimestre movel.
- Na Numerica, clientes devem ser considerados de forma distinta.
- Atacados entram inicialmente apenas na visao de faturamento.
- Para um item ser considerado positivado, a regra de negocio cita venda minima de 3 unidades.
- Para algumas BUs, existe valor minimo de venda/faturamento para considerar positivacao.
- No codigo atual, a BU `BPC` da base de lojas habilita duas BUs de calculo: `BW` e `PC`.

## Observacoes sobre regras ainda pendentes

Algumas regras aparecem nos documentos de negocio, mas ainda precisam ser implementadas explicitamente no codigo:

- Bimestre movel com controle por mes.
- Venda minima de 3 unidades para item positivado.
- Sortimento Ponderado por SKU/item foco.
- Sortimento Numerico por PPA/categoria.
- Calculo completo de Meta x Realizado x % Atingimento x Status x Faixa de ganho.
- Quebras futuras por vendedor, supervisor ou coordenador.

## Bases usadas

O fluxo atual espera arquivos Excel, principalmente:

- Base de lojas Uni.co
- Arquivo Uni.co com EANs/PPA/BU
- Resumo de metas ponderadas por BU

## Fluxo atual do codigo

1. Importa os arquivos Excel.
2. Padroniza nomes de colunas.
3. Converte tipos de dados principais.
4. Relaciona EANs da base Uni.co com vendas Martins.
5. Separa vendas que estao dentro e fora da base de EANs Uni.co.
6. Expande a base de lojas por BU:
   - `HC = 1` gera BU `HC`
   - `FR = 1` gera BU `FR`
   - `BPC = 1` gera BUs `BW` e `PC`
7. Consolida venda e faturamento no formato longo:
   - `BU`
   - `TIPO_VLR` (`VENDA` ou `FATURAMENTO`)
   - `VALOR`
8. Aplica a meta minima por BU para marcar `POSITIVADO`.
9. Calcula KPIs consolidados por classificacao de PDV e por BU.

## Dependencias principais:

- pandas
- numpy
- openpyxl
- xlsxwriter

## Saidas principais em memoria

O fluxo principal monta:

- `base_df_geral`: base consolidada por CNPJ, BU, tipo de valor, valor, meta e positivacao.
- `dataframe_KIP_final`: KPIs por classificacao de PDV.
- `principal_kpi`: KPIs principais por BU.

A exportacao para Excel existe no projeto para validação.

## Proximos passos do projeto

1. Centralizar constantes como ordem de PDV, mapa de BU e nomes de KPIs.
2. Implementar bimestre movel usando mes/ano da venda.
3. Implementar regra de quantidade minima de 3 unidades.
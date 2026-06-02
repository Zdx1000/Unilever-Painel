import pandas as pd

class PrincipalKips():
    def __init__(self) -> None:
        '''Esta classe tem como objetivo de realizar as principais etapas do processo de tratamento de dados, 
        como padronização de colunas, conversão de tipos de dados e importação de arquivos xlsx'''

    def metas_e_realizado(self, dataframe_Vendas_Na_Base: pd.DataFrame,
                          dataframe_Positivadas: pd.DataFrame,
                          dataframe_Base_de_Lojas: pd.DataFrame) -> pd.DataFrame:
        '''Criação do principal acompanhamento de metas e realizado, onde o objetivo é
        criar uma base de dados que contenha as informações principais para o acompanhamento
        de metas e realizado UNI.CO
        
        Principais KIPs: Cob. Numérica: Apuração Bimestral da Cobertura Numérica
                         Sortimento Numérica: Apuração Bimestral do Sortimento Numérico
                         Sortimento Ponderada: 3 Faixas de EANs por BU
                         Faturamento - YTD: Valor total por BU
                         Cob. Ponderada: 3 Faixas de rede positivadas por BU
                         Execução Ponderada: Não sera implementando nesta etapa'''
        
        kip = dataframe_Vendas_Na_Base.groupby(
            "BU").agg({
                "VLR_VENDA": "sum",
                "VLR_FATURAMENTO": "sum"
            }).reset_index()
        
        def contar_positivados(coluna: str) -> int:
            if coluna not in dataframe_Positivadas.columns:
                return 0

            return int(
                pd.to_numeric(
                    dataframe_Positivadas[coluna],
                    errors="coerce"
                ).fillna(0).eq(1).sum()
            )

        sufixo_venda = "_VENDA_POSITIVADA"
        sufixo_faturamento = "_FATURAMENTO_POSITIVADA"

        bus_positivadas = sorted({
            coluna[:-len(sufixo_venda)]
            for coluna in dataframe_Positivadas.columns
            if coluna.endswith(sufixo_venda)
        } | {
            coluna[:-len(sufixo_faturamento)]
            for coluna in dataframe_Positivadas.columns
            if coluna.endswith(sufixo_faturamento)
        })

        positivados = pd.DataFrame({"BU": bus_positivadas}).assign(
            QTD_VENDA_POSITIVADA=lambda df: df["BU"].apply(
                lambda bu: contar_positivados(f"{bu}{sufixo_venda}")
            ),
            QTD_FATURAMENTO_POSITIVADA=lambda df: df["BU"].apply(
                lambda bu: contar_positivados(f"{bu}{sufixo_faturamento}")
            )
        )

        if "TIPO" in dataframe_Base_de_Lojas.columns:
            tipo = dataframe_Base_de_Lojas["TIPO"].astype(str).str.strip().str.casefold()
            base_numerica = dataframe_Base_de_Lojas[tipo.isin(["numérica", "numerica"])]
        else:
            base_numerica = dataframe_Base_de_Lojas.iloc[0:0]

        def somar_base_numerica(coluna: str) -> float:
            if coluna not in base_numerica.columns:
                return 0.0

            return float(
                pd.to_numeric(
                    base_numerica[coluna],
                    errors="coerce"
                ).fillna(0).sum()
            )

        cobertura_numerica = pd.DataFrame([
            {
                "BU": bu,
                "COB_NUMERICA_VENDA": somar_base_numerica(f"{bu}_VENDA"),
                "COB_NUMERICA_FATURAMENTO": somar_base_numerica(f"{bu}_FATURAMENTO")
            }
            for bu in ["BW", "FR", "HC", "PC"]
        ])

        kip = kip.merge(positivados, on="BU", how="outer")
        kip = kip.merge(cobertura_numerica, on="BU", how="outer")
        kip[[
            "VLR_VENDA",
            "VLR_FATURAMENTO",
            "QTD_VENDA_POSITIVADA",
            "QTD_FATURAMENTO_POSITIVADA",
            "COB_NUMERICA_VENDA",
            "COB_NUMERICA_FATURAMENTO"
        ]] = kip[[
            "VLR_VENDA",
            "VLR_FATURAMENTO",
            "QTD_VENDA_POSITIVADA",
            "QTD_FATURAMENTO_POSITIVADA",
            "COB_NUMERICA_VENDA",
            "COB_NUMERICA_FATURAMENTO"
        ]].fillna(0)
        
        kip["AE"] = 'MD'
        kip = pd.concat(
            [
                kip[["BU", "AE"]].assign(
                    KPI="YTD - Vendas",
                    Realizado=kip["VLR_VENDA"].round(2),
                    Unidade_de_Medida="Real (R$)"
                ),
                kip[["BU", "AE"]].assign(
                    KPI="YTD - Faturamento",
                    Realizado=kip["VLR_FATURAMENTO"].round(2),
                    Unidade_de_Medida="Real (R$)"
                ),
                kip[["BU", "AE"]].assign(
                    KPI="Cob. Ponderada - Vendas",
                    Realizado=kip["QTD_VENDA_POSITIVADA"].astype(int),
                    Unidade_de_Medida="Redes"
                ),
                kip[["BU", "AE"]].assign(
                    KPI="Cob. Ponderada - Faturamento",
                    Realizado=kip["QTD_FATURAMENTO_POSITIVADA"].astype(int),
                    Unidade_de_Medida="Redes"
                ),
                kip[["BU", "AE"]].assign(
                    KPI="Cob. Numérica - Vendas",
                    Realizado=kip["COB_NUMERICA_VENDA"].round(2),
                    Unidade_de_Medida="PDVs"
                ),
                kip[["BU", "AE"]].assign(
                    KPI="Cob. Numérica - Faturamento",
                    Realizado=kip["COB_NUMERICA_FATURAMENTO"].round(2),
                    Unidade_de_Medida="PDVs"
                )
            ],
            ignore_index=True
        )
        
        return kip
        

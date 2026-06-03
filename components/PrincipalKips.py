import pandas as pd

class PrincipalKips():
    def __init__(self) -> None:
        '''Esta classe tem como objetivo de realizar as principais LPIs para o acompanhamento de metas e realizado UNI.CO'''

    def _kpi_YTD_por_BU(self, dataframe_df_geral: pd.DataFrame) -> pd.DataFrame:
        '''Função para calcular o KPI de YTD por BU, onde o objetivo é calcular o valor total por BU e TIPO_VLR
        
        Parametros:

        dataframe_df_geral: DataFrame contendo as colunas "BU", "TIPO_VLR" e "VALOR"'''
        kip_YTD = dataframe_df_geral.groupby(["BU", "TIPO_VLR"], as_index=False).agg({
            "VALOR": "sum"
        })
        kip_YTD["KPI"] = "YTD"
        kip_YTD["AE"] = "MD"
        kip_YTD["Unidade_de_Medida"] = "Real (R$)"
        kip_YTD = kip_YTD.rename(columns={"VALOR": "Realizado"})
        return kip_YTD

    def _kpi_COB_ponderada_por_BU(self, dataframe_df_geral: pd.DataFrame) -> pd.DataFrame:
        '''Função para calcular o KPI de Cobertura Ponderada por BU, onde o objetivo é calcular a quantidade de redes positivadas por BU e TIPO_VLR
        
        Parametros:
        dataframe_df_geral: DataFrame contendo as colunas "BU", "TIPO_VLR", "CNPJ_REDE" e "POSITIVADO"'''
        dataframe_df_geral = dataframe_df_geral[dataframe_df_geral["POSITIVADO"] == 1]
        kip_COB_ponderada = dataframe_df_geral.groupby(["BU", "TIPO_VLR"], as_index=False).agg({
            "CNPJ_REDE": "nunique"
        })
        kip_COB_ponderada["KPI"] = "Cob. Ponderada"
        kip_COB_ponderada["AE"] = "MD"
        kip_COB_ponderada["Unidade_de_Medida"] = "Redes"
        kip_COB_ponderada = kip_COB_ponderada.rename(columns={"CNPJ_REDE": "Realizado"})
        return kip_COB_ponderada
    
    def _kpi_COB_numerica_por_BU(self, dataframe_df_geral: pd.DataFrame) -> pd.DataFrame:
        '''Função para calcular o KPI de Cobertura Numérica por BU, onde o objetivo é calcular a quantidade de PDVs positivados por BU e TIPO_VLR
        
        Parametros:
        dataframe_df_geral: DataFrame contendo as colunas "BU", "TIPO_VLR", "CNPJ" e "POSITIVADO"'''
        dataframe_df_geral = dataframe_df_geral[(dataframe_df_geral["POSITIVADO"] == 1) & (dataframe_df_geral["TIPO"] == "Numérica")]
        kip_COB_numerica = dataframe_df_geral.groupby(["BU", "TIPO_VLR"], as_index=False).agg({
            "CNPJ": "nunique"
        })
        kip_COB_numerica["KPI"] = "Cob. Numérica"
        kip_COB_numerica["AE"] = "MD"
        kip_COB_numerica["Unidade_de_Medida"] = "PDVs"
        kip_COB_numerica = kip_COB_numerica.rename(columns={"CNPJ": "Realizado"})
        return kip_COB_numerica
    
    def _padrao_dataframe(self, dataframe_df_geral: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar um DataFrame padrão contendo as combinações únicas de BU e TIPO_VLR
        
        Parametros:
        dataframe_df_geral: DataFrame contendo as colunas "BU" e "TIPO_VLR"'''
        dataframe_padrao = dataframe_df_geral[["BU", "TIPO_VLR"]].drop_duplicates()
        return dataframe_padrao.reset_index(drop=True)
    
    def metas_e_realizado(self, dataframe_df_geral: pd.DataFrame) -> pd.DataFrame:
        '''Criação do principal acompanhamento de metas e realizado, onde o objetivo é
        criar uma base de dados que contenha as informações principais para o acompanhamento
        de metas e realizado UNI.CO
        
        Principais KIPs: Cob. Numérica: Apuração Bimestral da Cobertura Numérica
                         Sortimento Numérica: Apuração Bimestral do Sortimento Numérico
                         Sortimento Ponderada: 3 Faixas de EANs por BU
                         Faturamento - YTD: Valor total por BU
                         Cob. Ponderada: 3 Faixas de rede positivadas por BU
                         Execução Ponderada: Não sera implementando nesta etapa
                         
        Parametros:
        dataframe_df_geral: DataFrame contendo as colunas "BU", "TIPO_VLR", "VALOR", "CNPJ_REDE", "CNPJ", "POSITIVADO" e "TIPO"'''
        
        padrao = self._padrao_dataframe(dataframe_df_geral)
        kip_YTD = self._kpi_YTD_por_BU(dataframe_df_geral)
        kip_COB_ponderada = self._kpi_COB_ponderada_por_BU(dataframe_df_geral)
        kip_COB_numerica = self._kpi_COB_numerica_por_BU(dataframe_df_geral)

        resultado = pd.concat([kip_YTD, kip_COB_ponderada, kip_COB_numerica], ignore_index=True)
        
        kpis = resultado["KPI"].unique()
        combinacoes_completas = []
        
        for kpi in kpis:
            kpi_data = resultado[resultado["KPI"] == kpi]
            merged = padrao.merge(kpi_data, on=["BU", "TIPO_VLR"], how="left")
            merged["KPI"] = kpi
            combinacoes_completas.append(merged)
        
        resultado_final = pd.concat(combinacoes_completas, ignore_index=True)
        resultado_final["Realizado"] = resultado_final["Realizado"].fillna(0)
        resultado_final["AE"] = resultado_final["AE"].fillna("MD")
        resultado_final["Unidade_de_Medida"] = resultado_final["Unidade_de_Medida"].fillna(resultado_final.groupby("KPI")["Unidade_de_Medida"].transform("first"))
        
        resultado_final = resultado_final.rename(columns={"TIPO_VLR": "TIPO"})
        resultado_final = resultado_final[["BU", "AE", "KPI", "TIPO",
                                           "Realizado", "Unidade_de_Medida"]]

        return resultado_final
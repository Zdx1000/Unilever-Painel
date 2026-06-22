import pandas as pd
import numpy as np

class DataframePrincipal_detalhe():
    def __init__(self) -> None:
        '''Esta classe tem como objetivo de validar todo o fluxo recriando as principais LPIs'''
    
    def dataframe_Base_PPA(self,
                           dataframe_unico_PPA: pd.DataFrame,
                           sortimento_ponderada: pd.DataFrame,
                           sortimento_numetica: pd.DataFrame
                           ) -> pd.DataFrame:

        '''Função para criar o DataFrame base do PPA, onde o objetivo é criar um DataFrame contendo as colunas "BU", "TIPO_VLR", "CNPJ" e "TIPO" a partir dos DataFrames de PPA, Sortimento Ponderada e Sortimento Numérica
        
        Parametros:
        dataframe_unico_PPA: DataFrame contendo as colunas "BU", "CNPJ" e "TIPO_VLR"
        sortimento_ponderada: DataFrame contendo as colunas "BU", "EAN Regular" e "Outros EANS válidos"
        sortimento_numetica: DataFrame contendo as colunas "BU", "EAN Regular" e "Outros EANS válidos
        
        Esta função considera apenas as EAN que estão na base Unilever.
        "'''

        dataframe_base_PPA = dataframe_unico_PPA.copy()
        eans_sortimento = pd.concat(
            [sortimento_ponderada["EAN_REGULAR"], sortimento_ponderada["OUTROS_EANS_VALIDOS"]]
        ).astype(str).str.strip()

        dataframe_base_PPA["SORTIMENTO"] = dataframe_base_PPA["EAN_REGULAR"].astype(str).str.strip().isin(eans_sortimento).astype(int)
        dataframe_base_PPA["NUMERICA"] = dataframe_base_PPA["PPA"].astype(str).str.strip().isin(
            sortimento_numetica["PPA"].astype(str).str.strip()
        ).astype(int)

        return dataframe_base_PPA
    
    def dataframe_principal(self,
                            dataframe_BaseDeLojas: pd.DataFrame,
                            dataframe_base_PPA: pd.DataFrame,
                            dataframe_ponderadas_meta: pd.DataFrame,
                            base_sql: pd.DataFrame,
                            Type_metas_layt: pd.DataFrame
                            ) -> pd.DataFrame:
        '''Função para criar o DataFrame principal, onde o objetivo é criar um DataFrame contendo as colunas "BU", "TIPO_VLR", "CNPJ", "TIPO", "MES" e "VALOR" a partir dos DataFrames de Base de Lojas, Base de PPA, Metas Ponderadas e Base SQL
        
        Parametros:
        dataframe_BaseDeLojas: DataFrame contendo as colunas "BU" e "CNPJ"
        dataframe_base_PPA: DataFrame contendo as colunas "BU", "CNPJ", "TIPO_VLR", "SORTIMENTO" e "NUMERICA"
        dataframe_ponderadas_meta: DataFrame contendo as colunas "BU", "TIPO_VLR" e "VALOR"
        base_sql: DataFrame contendo as colunas "CNPJ", "MES" e "VALOR"'''

        dataFrame_principal_detalhe = pd.merge(
            dataframe_base_PPA,
            dataframe_ponderadas_meta,
            on="BU",
            how="left"
        )

        dataFrame_principal_detalhe = dataFrame_principal_detalhe.merge(
            base_sql,
            on="EAN_REGULAR",
            how="outer"
        )

        dataFrame_principal_detalhe["POSSUI_PPA_CADASTRADA_VD"] = np.where(dataFrame_principal_detalhe["BU"].notna(), "SIM", "NAO")
        dataFrame_principal_detalhe["PPA_COM_VENDA_BU"] = np.where(dataFrame_principal_detalhe["VLR_VENDA"].notna(), "SIM", "NAO")

        dataFrame_principal_detalhe = dataFrame_principal_detalhe.merge(
            dataframe_BaseDeLojas,
            on="CNPJ",
            how="outer"
        )

        dataFrame_principal_detalhe["CNPJ_FORA_DA_BASE_DE_LOJAS"] = np.where(dataFrame_principal_detalhe["CNPJ_REDE"].notna(), "NAO", "SIM")
        dataFrame_principal_detalhe["CNPJ_SEM_VENDA"] = np.where(dataFrame_principal_detalhe["VLR_VENDA"].notna(), "NAO", "SIM")

        dataFrame_principal_detalhe = dataFrame_principal_detalhe.rename(
            columns={
                "VALO_MINIMO_PARA_CONSIDERAR_POSITIVADA": "META_POSITIVADA",
                "VLR_VENDA": "VENDA",
                "VLR_FATURAMENTO": "FATURAMENTO"
            }
        )
        dataFrame_principal_detalhe["ID"] = dataFrame_principal_detalhe.index + 1

        dataFrame_principal_detalhe = dataFrame_principal_detalhe[[
            "ID",
            "POSSUI_PPA_CADASTRADA_VD",
            "PPA_COM_VENDA_BU",
            "CNPJ_FORA_DA_BASE_DE_LOJAS",
            "CNPJ_SEM_VENDA",
            "BU",
            "PPA",
            "EAN_REGULAR",
            "SORTIMENTO",
            "NUMERICA",
            "META_POSITIVADA",
            "ANO",
            "MES",
            "CNPJ",
            "CODIGO",
            "VENDA",
            "FATURAMENTO",
            "QUANTIDADE",
            "CODIGO_RCA",
            "NOME_RCA",
            "CODIGO_SUPERVISOR",
            "NOME_SUPERVISOR",
            "HC",
            "FR",
            "BPC",
            "CNPJ_REDE",
            "TIPO",
            "CLASSIFICACAO_PDV",
            "GRUPO"
        ]]

        metas = Type_metas_layt[[
            "KPI",
            "BU",
            "UNIDADE_DE_MEDIDA",
            "100%_DO_GANHO",
            "50%_DO_GANHO",
            "30%_DO_GANHO",
        ]]

        return dataFrame_principal_detalhe, metas
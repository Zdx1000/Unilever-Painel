import pandas as pd
import numpy as np
import warnings
from datetime import datetime
import locale

warnings.filterwarnings(
    "ignore",
    message="Conditional Formatting extension is not supported and will be removed"
)

from components.ImportarXlsx import ImportarXlsx
from components.ConveterType import ConveterType
from components.PadronizarCol import PadronizarCol
from components.PrincipalKips import PrincipalKips
from components.Teste_unitario import DataframePrincipal_detalhe
    
class Servidor(ImportarXlsx, ConveterType, PadronizarCol, PrincipalKips, DataframePrincipal_detalhe):
    '''Classe principal do projeto, responsável por coordenar as operações de importação, padronização, conversão e correlação dos dados.
    A classe Servidor herda as funcionalidades das classes ImportarXlsx, ConveterType, PadronizarCol e PrincipalKips, permitindo a execução de todas as etapas do processo de análise de dados.
    
    Atributos:
    Diretorios (str): O caminho do diretório onde os arquivos xlsx estão localizados
    
    Métodos:
    correlacionar_BasePorCnpj: Correlaciona a base de lojas com a base de vendas por CNPJ
    correlacionar_BasePorCodBarras: Correlaciona a base de lojas com a base de vendas por Código de Barras
    exportar_para_excel: Exporta um DataFrame para um arquivo Excel
    criar_ean_fora_da_base: Cria uma tabela de vendas que estão fora da base de EANs PPA
    validacao_positivas: Valida se os valores de uma coluna atendem a uma meta e retorna um DataFrame com as vendas positivadas
    
    Herança:
    ImportarXlsx: Permite a importação de arquivos xlsx
    ConveterType: Permite a conversão de tipos de dados em um DataFrame
    PadronizarCol: Permite a padronização dos nomes das colunas em um DataFrame
    '''
    def __init__(self, Diretorios: str = None) -> None:
        super().__init__(Diretorios)

    def correlacionar_BasePorCnpj(self, dataframe_BaseDeLojas: pd.DataFrame, base_sql_CNPJ_vendas: pd.DataFrame, mes: str = None) -> pd.DataFrame:
        '''Função para correlacionar a base de lojas com a base de vendas por CNPJ'''
        if mes is not None:
            base_sql_CNPJ_vendas = base_sql_CNPJ_vendas[base_sql_CNPJ_vendas["nommes"] == mes]
        dataframe_correlacionado = pd.merge(dataframe_BaseDeLojas, 
                                            base_sql_CNPJ_vendas, 
                                            left_on="CNPJ", 
                                            right_on="NUMCGCCPFCLIFRM", 
                                            how='outer',
                                            suffixes=("_xlsx", "_sql"))
        return dataframe_correlacionado
    
    def correlacionar_BasePorCodBarras(self, dataframe_unico_PPA: pd.DataFrame, base_sql_CodBarras_vendas: pd.DataFrame, mes: str = None) -> pd.DataFrame:
        '''Função para correlacionar a base de lojas com a base de vendas por Código de Barras'''
        if mes is not None:
            base_sql_CodBarras_vendas = base_sql_CodBarras_vendas[base_sql_CodBarras_vendas["NOMMES"] == mes]
        dataframe_correlacionado = pd.merge(dataframe_unico_PPA, 
                                            base_sql_CodBarras_vendas, 
                                            left_on="EAN Regular ", 
                                            right_on="CODBRRUNDVNDMRT", 
                                            how="outer",
                                            suffixes=("_xlsx", "_sql"))
        return dataframe_correlacionado
    
    def exportar_para_excel(self, dataframe: dict[str, pd.DataFrame]) -> None:
        '''Função para exportar um DataFrame para um arquivo Excel'''
        try:
            with pd.ExcelWriter(f"{self.Diretorios}/Unico.xlsx", engine='xlsxwriter') as writer:
                for i, (nome, df) in enumerate(dataframe.items()):
                    df.to_excel(writer, sheet_name=nome, index=False)
        except Exception as e:
            print(f"Erro ao exportar o DataFrame para Excel: {e}")

    def criar_ean_fora_da_base(self, dataframe_unico_PPA: pd.DataFrame, base_sql_vendas: pd.DataFrame, mes_atual: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        dataframe_unico_PPA = dataframe_unico_PPA.drop_duplicates(subset=["EAN_REGULAR"])
        base_com_bu = base_sql_vendas.merge(
            dataframe_unico_PPA[["EAN_REGULAR", "BU"]].drop_duplicates(),
            on="EAN_REGULAR",
            how="left"
        )
        base_com_bu = base_com_bu[base_com_bu["MES"] == mes_atual].copy()

        tabela_vendas_fora_da_base = base_com_bu[base_com_bu["BU"].isna()]
        
        tabela_vendas_fora_da_base = tabela_vendas_fora_da_base.drop(columns=["BU"])
        tabela_vendas_fora_da_base = tabela_vendas_fora_da_base.melt(
            id_vars=[coluna for coluna in tabela_vendas_fora_da_base.columns if coluna not in ["VLR_VENDA", "VLR_FATURAMENTO"]],
            value_vars=["VLR_VENDA", "VLR_FATURAMENTO"],
            var_name="TIPO_VLR",
            value_name="VALOR"
        )
        tabela_vendas_fora_da_base["TIPO_VLR"] = tabela_vendas_fora_da_base["TIPO_VLR"].replace({"VLR_VENDA": "VENDAS", "VLR_FATURAMENTO": "FATURAMENTO"})
        tabela_vendas_na_base = base_com_bu[base_com_bu["BU"].notna()]


        return tabela_vendas_fora_da_base, tabela_vendas_na_base

    def validacao_positivas(self, dataframe_vendas_na_base: pd.DataFrame, dataframe_Base_de_Lojas: pd.DataFrame, dataframe_metas: pd.DataFrame) -> pd.DataFrame:
        '''Função para validar se os valores de uma coluna atendem a uma meta'''
        
        dataframe_Base_de_Lojas_BU = dataframe_Base_de_Lojas.melt(
            id_vars=[coluna for coluna in dataframe_Base_de_Lojas.columns if coluna not in ["HC", "FR", "BPC"]],
            value_vars=["HC", "FR", "BPC"],
            var_name="BU",
            value_name="FLAG_BU"
        ).query("FLAG_BU == 1").drop(columns="FLAG_BU")
        dataframe_Base_de_Lojas_BU["BU"] = dataframe_Base_de_Lojas_BU["BU"].map({"HC": ["HC"], "FR": ["FR"], "BPC": ["BW", "PC"]})
        dataframe_Base_de_Lojas_BU = dataframe_Base_de_Lojas_BU.explode("BU", ignore_index=True)

        dataframe_vendas_na_base_bu = dataframe_vendas_na_base.groupby(["ANO", "MES", "CNPJ", "BU"], as_index=False).agg({
            "VLR_VENDA": "sum",
            "VLR_FATURAMENTO": "sum"
        })

   
        base_df_geral = pd.merge(
            dataframe_Base_de_Lojas_BU,
            dataframe_vendas_na_base_bu,
            on=["CNPJ", "BU"],
            how="left",
        ).fillna(0)

        base_df_geral = pd.merge(
            base_df_geral,
            dataframe_metas,
            on="BU",
            how="left"
        )

        base_df_geral = base_df_geral.melt(
            id_vars=[coluna for coluna in base_df_geral.columns if coluna not in ["VLR_VENDA", "VLR_FATURAMENTO"]],
            value_vars=["VLR_VENDA", "VLR_FATURAMENTO"],
            var_name="TIPO_VLR",
            value_name="VALOR"
        )
        base_df_geral["TIPO_VLR"] = base_df_geral["TIPO_VLR"].str.replace("VLR_", "", regex=False)

        base_df_geral["POSITIVADO"] = np.where(
            (base_df_geral["VALOR"] >= base_df_geral["VALO_MINIMO_PARA_CONSIDERAR_POSITIVADA"]), 1, 0
        )

        base_df_geral = base_df_geral.rename(columns={"VALO_MINIMO_PARA_CONSIDERAR_POSITIVADA": "META_PONDERADA"})
        return base_df_geral
    
    def kips_YTD_por_PDV(self, dataframe_base_de_lojas: pd.DataFrame, mes_atual: str) -> pd.DataFrame:
        '''Função para criar a primeira coluna dos KIPs voltado a vendas YTD por PDV,
        onde a função irá agrupar a base de Lojas por PDV e somar as Vendas e Faturamento'''

        dataframe_KIP = dataframe_base_de_lojas[dataframe_base_de_lojas["MES"] == mes_atual].copy()

        dataframe_KIP = dataframe_KIP.groupby(["CLASSIFICACAO_PDV", "TIPO_VLR"]).agg({
            "VALOR": "sum"
        }).reset_index()

        return dataframe_KIP

    def kips_Cob_Pond(self, base_df_geral: pd.DataFrame, mes_atual: str) -> pd.DataFrame:
        '''Função para criar a segunda coluna dos KIPs voltado a Cobertura Ponderada,
        onde a função irá agrupar CLASSIFICACAO_PDV: "Pond. Rede" e "Pond. Indep." somando as positivadas'''      

        base_df_geral_KPI = base_df_geral[base_df_geral["MES"] == mes_atual].copy()

        base_df_geral_KPI = base_df_geral_KPI.groupby(["CLASSIFICACAO_PDV", "TIPO_VLR"]).agg({
            "POSITIVADO": "sum"
        }).reset_index()
        base_df_geral_KPI = base_df_geral_KPI[base_df_geral_KPI["CLASSIFICACAO_PDV"].isin(["Pond. Rede", "Pond. Indep."])]

        return base_df_geral_KPI
    
    def kips_Sort_Pond(self, dataframe_Vendas_Positivadas: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar a terceira coluna dos KIPs voltado a Sortimento Ponderada,
        onde a função irá agrupar CLASSIFICACAO_PDV: "Pond. Rede" e "Pond. Indep." somando as positivadas'''

        dataframe_KIP = dataframe_Vendas_Positivadas.copy()

        return dataframe_KIP

    def kips_Sort_Cob_Num(self, base_df_geral: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar a quarta coluna dos KIPs voltado a Sortimento Cobertura Numérica,'''     

        base_df_geral_KPI = base_df_geral.copy()

        base_df_geral_KPI = base_df_geral_KPI.groupby(["CLASSIFICACAO_PDV", "TIPO_VLR"]).agg({
            "POSITIVADO": "sum"
        }).reset_index()
        base_df_geral_KPI = base_df_geral_KPI[base_df_geral_KPI["CLASSIFICACAO_PDV"].isin(["Num. A", "Num. B", "Num. C"])]

        return base_df_geral_KPI
    
    def kips_tabela(self, dataframe_KIP: pd.DataFrame, dataframe_KIP_CobPond: pd.DataFrame, dataframe_KIP_Sort_Num: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar a tabela final dos KIPs, onde a função irá concatenar os dataframes dos KIPs criados anteriormente'''

        ordem_classificacao_pdv = ["Pond. Rede", "Pond. Indep.", "Num. A", "Num. B", "Num. C", "Atacados"]
        ordem_pdv = {pdv: ordem for ordem, pdv in enumerate(ordem_classificacao_pdv)}
        
        dataframe_KIP = dataframe_KIP[dataframe_KIP["CLASSIFICACAO_PDV"].isin(ordem_classificacao_pdv)]
        dataframe_KIP = dataframe_KIP.sort_values("CLASSIFICACAO_PDV", key=lambda coluna: coluna.map(ordem_pdv))
        dataframe_KIP = dataframe_KIP.rename(columns={"VALOR": "YTD"})

        dataframe_KIP_final = pd.merge(
            dataframe_KIP,
            dataframe_KIP_CobPond,
            on=["CLASSIFICACAO_PDV", "TIPO_VLR"],
            how="left"
        )
        dataframe_KIP_final = dataframe_KIP_final.rename(columns={"POSITIVADO": "Cob. Ponderada"})

        dataframe_KIP_final = pd.merge(
            dataframe_KIP_final,
            dataframe_KIP_Sort_Num,
            on=["CLASSIFICACAO_PDV", "TIPO_VLR"],
            how="left"
        )

        dataframe_KIP_final = dataframe_KIP_final.rename(columns={"POSITIVADO": "Cob. Numérica"})

        return dataframe_KIP_final


if __name__ == "__main__":
    diretorio = "dados"
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    mes_atual = datetime.now().strftime("%B").upper()
    servidor = Servidor(Diretorios=diretorio)

    '''Importação dos arquivos xlsx'''
    dataframe_BaseDeLojas = servidor.importar_excel(
        Inicial_name="Base_",
        Sheet_name="BaseDeLojas",
        Colunas=["CNPJ", "CNPJ_Rede", "HC", "FR", "BPC", "Tipo", "Classificação PDV", "Grupo"],
        Pular_linha=10,
        Mult_xlsx=False
    )

    dataframe_BaseDeLojas = servidor.padronizar_colunas(dataframe_BaseDeLojas)

    dataframe_BaseDeLojas = servidor.converter_tipo_dados(dataframe_BaseDeLojas,
        Dict={
            "HC": "int",
            "FR": "int",
            "BPC": "int",
            "CNPJ": "str",
            "CNPJ_REDE": "str",
            "TIPO": "str",
            "CLASSIFICACAO_PDV": "str",
            "GRUPO": "str"
        }
    )

    dataframe_unico_PPA = servidor.importar_excel(
        Inicial_name="Unico_",
        Sheet_name="EANS_PPA",
        Colunas=["EAN Regular ", "PPA", "BU"],
        Pular_linha=7,
        Mult_xlsx=True
    )

    dataframe_unico_PPA = servidor.padronizar_colunas(dataframe_unico_PPA)

    dataframe_unico_PPA = servidor.converter_tipo_dados(dataframe_unico_PPA,
        Dict={
            "BU": "str",
            "PPA": "str",
            "EAN_REGULAR": "str"
        }
    )

    dataframe_ponderadas_meta = servidor.importar_excel(
        Inicial_name="Unico_",
        Sheet_name="Resumo_Ponderada",
        Colunas=["BU", "Valo Mínimo para considerar Positivada"],
        Pular_linha=7,
        Mult_xlsx=False
    )

    dataframe_ponderadas_meta = servidor.padronizar_colunas(dataframe_ponderadas_meta)

    dataframe_ponderadas_meta = servidor.converter_tipo_dados(dataframe_ponderadas_meta,
        Dict={
              "BU": "str",
              "VALO_MINIMO_PARA_CONSIDERAR_POSITIVADA": "int"
        }
    )

    dataframe_ponderadas_meta = dataframe_ponderadas_meta.groupby("BU").agg(
        {"VALO_MINIMO_PARA_CONSIDERAR_POSITIVADA": "first"}
        ).reset_index()

    base_sql_CNPJ_vendas = servidor.importar_excel(
        Inicial_name="Padrão_de_Vendas",
        Pular_linha=0,
        Mult_xlsx=False
    )

    base_sql_CNPJ_vendas = servidor.converter_tipo_dados(base_sql_CNPJ_vendas,
    Dict={
            "ANO": "int",
            "MES": "str",
            "CNPJ": "str",
            "CODIGO": "int",
            "EAN_REGULAR": "str",
            "VLR_VENDA": "float",
            "VLR_FATURAMENTO": "float",
            "QUANTIDADE": "int",
            "CODIGO_RCA": "str",
            "NOME_RCA": "str",
            "CODIGO_SUPERVISOR": "str",
            "NOME_SUPERVISOR": "str"
        }
    )

    sortimento_ponderada = servidor.importar_excel(
        Inicial_name="Unico_",
        Sheet_name="Sort. - Pond",
        Colunas=["BU", "EAN Regular", "Outros EANS válidos"],
        Pular_linha=7,
        Mult_xlsx=False
    )

    sortimento_ponderada = servidor.padronizar_colunas(sortimento_ponderada)
    sortimento_ponderada = servidor.converter_tipo_dados(sortimento_ponderada,
        Dict={
            "BU": "str",
            "EAN_REGULAR": "str",
            "OUTROS_EANS_VALIDOS": "str"
        }
    )

    sortimento_numetica = servidor.importar_excel(
        Inicial_name="Unico_",
        Sheet_name="Sort. - Num",
        Colunas=["BU", "PPA"],
        Pular_linha=7,
        Mult_xlsx=False
    )

    sortimento_numetica = servidor.padronizar_colunas(sortimento_numetica)
    sortimento_numetica = servidor.converter_tipo_dados(sortimento_numetica,
        Dict={
            "BU": "str",
            "PPA": "str"
        }
    )

    metas_e_realizado = servidor.importar_excel(
        Inicial_name="Unico_",
        Sheet_name="Metas e realizado",
        Pular_linha=8,
        Mult_xlsx=False
    )

    metas_e_realizado = servidor.padronizar_colunas(metas_e_realizado)
    metas_e_realizado = servidor.converter_tipo_dados(metas_e_realizado,
        Dict={
            "KPI": "str",
            "BU": "str",
            "UNIDADE_DE_MEDIDA": "str",
            "(100%_DO_GANHO)": "float",
            "(50%_DO_GANHO)": "float",
            "(30%_DO_GANHO)": "float",
        }
    )

    PPA = servidor.dataframe_Base_PPA(
        dataframe_unico_PPA=dataframe_unico_PPA,
        sortimento_ponderada=sortimento_ponderada,
        sortimento_numetica=sortimento_numetica
    )

    dataFrame_principal_detalhe, metas = servidor.dataframe_principal(
        dataframe_BaseDeLojas=dataframe_BaseDeLojas,
        dataframe_base_PPA=PPA,
        dataframe_ponderadas_meta=dataframe_ponderadas_meta,
        base_sql=base_sql_CNPJ_vendas,
        Type_metas_layt=metas_e_realizado
    )

    exit()

    '''Correlacionar as bases de dados'''

    tabela_vendas_fora_da_base, tabela_vendas_na_base = servidor.criar_ean_fora_da_base(
        dataframe_unico_PPA=dataframe_unico_PPA,
        base_sql_vendas=base_sql_CNPJ_vendas,
        mes_atual=mes_atual
    )

    base_df_geral = servidor.validacao_positivas(
        dataframe_vendas_na_base=tabela_vendas_na_base,
        dataframe_Base_de_Lojas=dataframe_BaseDeLojas,
        dataframe_metas=dataframe_ponderadas_meta
    )

    base_df_geral = servidor.converter_tipo_dados(
        dataframe=base_df_geral,
        Dict={
            "CNPJ": "str",
            "CNPJ_REDE": "str",
            "TIPO": "str",
            "CLASSIFICACAO_PDV": "str",
            "GRUPO": "str",
            "BU": "str",
            "TIPO_VLR": "str",
            "VALOR": "float",
            "META_PONDERADA": "int",
            "POSITIVADO": "int"
        }
    )

    dataframe_KIP = servidor.kips_YTD_por_PDV(base_df_geral, mes_atual=mes_atual)
    dataframe_KIP_CobPond = servidor.kips_Cob_Pond(base_df_geral, mes_atual=mes_atual)
    dataframe_KIP_Sort_Num = servidor.kips_Sort_Cob_Num(base_df_geral)
    dataframe_KIP_final = servidor.kips_tabela(dataframe_KIP, dataframe_KIP_CobPond, dataframe_KIP_Sort_Num)
    dataframe_KIP_final = servidor.padronizar_colunas(dataframe_KIP_final)

    '''Exportar os DataFrames correlacionados para arquivos Excel'''

    principal_kpi = servidor.metas_e_realizado(base_df_geral, mes_atual=mes_atual)


    dataframes_para_exportar = {
        "Principal_KPI": principal_kpi,
        "dataframe_KIP_final": dataframe_KIP_final,
        "Base_geral": base_df_geral,
        "Vendas_Fora_da_Base": tabela_vendas_fora_da_base,
    }

    servidor.exportar_para_excel(dataframes_para_exportar)

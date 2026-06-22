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
from components.DataframeCreat import DataframePrincipal_detalhe
    
class Servidor(ImportarXlsx, ConveterType, PadronizarCol, DataframePrincipal_detalhe):
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

    
    def exportar_para_excel(self, dataframe: dict[str, pd.DataFrame]) -> None:
        '''Função para exportar um DataFrame para um arquivo Excel'''
        try:
            with pd.ExcelWriter(f"{self.Diretorios}/Unico.xlsx", engine='xlsxwriter') as writer:
                for i, (nome, df) in enumerate(dataframe.items()):
                    df.to_excel(writer, sheet_name=nome, index=False)
        except Exception as e:
            print(f"Erro ao exportar o DataFrame para Excel: {e}")

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

    dataframes_para_exportar = {
        "dataFrame_principal_detalhe": dataFrame_principal_detalhe,
        "Metas": metas
    }

    servidor.exportar_para_excel(dataframes_para_exportar)

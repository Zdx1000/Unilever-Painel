import pandas as pd
import numpy as np

from components.ImportarXlsx import ImportarXlsx
from components.ConveterType import ConveterType
from components.PadronizarCol import PadronizarCol
from components.PrincipalKips import PrincipalKips
    
class Servidor(ImportarXlsx, ConveterType, PadronizarCol, PrincipalKips):
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
            with pd.ExcelWriter("Unico.xlsx", engine='xlsxwriter') as writer:
                for i, (nome, df) in enumerate(dataframe.items()):
                    df.to_excel(writer, sheet_name=nome, index=False)
        except Exception as e:
            print(f"Erro ao exportar o DataFrame para Excel: {e}")

    def criar_ean_fora_da_base(self, dataframe_unico_PPA: pd.DataFrame, base_sql_vendas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        dataframe_unico_PPA = dataframe_unico_PPA.drop_duplicates(subset=["EAN_REGULAR"])
        base_com_bu = base_sql_vendas.merge(
            dataframe_unico_PPA[["EAN_REGULAR", "BU"]].drop_duplicates(),
            on="EAN_REGULAR",
            how="left"
        )

        tabela_vendas_fora_da_base = base_com_bu[base_com_bu["BU"].isna()]
        tabela_vendas_fora_da_base = tabela_vendas_fora_da_base.drop(columns=["BU"])
        tabela_vendas_na_base = base_com_bu[base_com_bu["BU"].notna()]

        return tabela_vendas_fora_da_base, tabela_vendas_na_base

    def validacao_positivas(self, dataframe_vendas_na_base: pd.DataFrame, dataframe_Base_de_Lojas: pd.DataFrame) -> pd.DataFrame:
        '''Função para validar se os valores de uma coluna atendem a uma meta'''

        dataframe_vendas_na_base_venda = dataframe_vendas_na_base.pivot_table(
            index="CNPJ",
            columns="BU",
            values=["VLR_FATURAMENTO", "VLR_VENDA"],
            aggfunc="sum",
            fill_value=0
        )

        dataframe_vendas_na_base_venda = dataframe_vendas_na_base_venda.swaplevel(0, 1, axis=1)

        dataframe_vendas_na_base_venda.columns = [
            f"{bu}_{coluna.replace('VLR_', '')}"
            for bu, coluna in dataframe_vendas_na_base_venda.columns
        ]

        dataframe_vendas_na_base_venda = dataframe_vendas_na_base_venda.reset_index()
                
        dataframe_vendas_na_base = pd.merge(
            dataframe_Base_de_Lojas,
            dataframe_vendas_na_base_venda,
            on="CNPJ",
            how="left"
        ).fillna(0)

        return dataframe_vendas_na_base
    
    def calcular_positivacao(self, dataframe_vendas: pd.DataFrame, dataframe_ponderadas_meta: pd.DataFrame) -> pd.DataFrame:
        '''Esta função ira calcular a positivação das vendas e faturamento determinando como positivadas sendo como 1 e não positivadas sendo
        como 0, para isso a função irá comparar o valor de venda e faturamento por BU com a meta ponderada determinada para cada BU, caso o valor
        seja maior ou igual a meta ponderada, a venda será considerada positivada.
        
        Parâmetros:
        dataframe_vendas_na_base (pd.DataFrame): DataFrame contendo as vendas que estão na base de EANs PPA
        dataframe_ponderadas_meta (pd.DataFrame): DataFrame contendo as metas ponderadas para cada BU
        
        Calculo nas colunas: BW_VENDA, FR_VENDA, HC_VENDA, PC_VENDA, BW_FATURAMENTO, FR_FATURAMENTO, HC_FATURAMENTO, PC_FATURAMENTO

        Regra de negócio para a positivação:

        HC usa a flag HC
        FR usa a flag FR
        BW usa a flag BPC
        PC usa a flag BPC

        A lógica agora é esta:

        se HC == 0, então HC_VENDA_POSITIVADA e HC_FATURAMENTO_POSITIVADA serão 0, mesmo que o valor passe da meta
        se FR == 0, então as colunas de FR ficam 0
        se BPC == 0, então tanto BW quanto PC ficam 0

        HC = 0 com valor acima da meta resultou em 0
        BPC = 0 com BW e PC acima da meta resultou em 0
        quando a flag era 1 e a meta era atendida, o resultado é 1.

        '''
        dataframe = dataframe_vendas.copy()

        dataframe_metas_poderadas = dataframe_ponderadas_meta.set_index("BU")["VALO_MINIMO_PARA_CONSIDERAR_POSITIVADA"].to_dict()
        coluna_habilitadora_por_bu = {
            "HC": "HC",
            "FR": "FR",
            "BW": "BPC",
            "PC": "BPC"
        }

        for bu in dataframe_metas_poderadas.keys():
            meta_ponderada = dataframe_metas_poderadas[bu]
            coluna_habilitadora = coluna_habilitadora_por_bu.get(bu)

            if coluna_habilitadora not in dataframe.columns:
                continue

            for tipo in ["VENDA", "FATURAMENTO"]:
                coluna = f"{bu}_{tipo}"
                if coluna in dataframe.columns:
                    dataframe[f"{coluna}_POSITIVADA"] = np.where(
                        (dataframe[coluna_habilitadora] == 1) &
                        (dataframe[coluna] >= meta_ponderada),
                        1,
                        0
                    )
        dataframe = dataframe.drop(columns=[coluna for coluna in dataframe.columns if any(tipo in coluna for tipo in ["VENDA", "FATURAMENTO"]) and not coluna.endswith("POSITIVADA")])

        return dataframe
    
    def kips_YTD_por_PDV(self, dataframe_base_de_lojas: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar a primeira coluna dos KIPs voltado a vendas YTD por PDV,
        onde a função irá agrupar a base de Lojas por PDV e somar as Vendas e Faturamento'''

        dataframe_KIP = dataframe_base_de_lojas.copy()
        
        dataframe_KIP['YTD_VENDA'] = (
            dataframe_KIP['HC_VENDA'] +
            dataframe_KIP['FR_VENDA'] +
            dataframe_KIP['BW_VENDA'] +
            dataframe_KIP['PC_VENDA']
        )
        
        dataframe_KIP['YTD_FATURAMENTO'] = (
            dataframe_KIP['HC_FATURAMENTO'] +
            dataframe_KIP['FR_FATURAMENTO'] +
            dataframe_KIP['BW_FATURAMENTO'] +
            dataframe_KIP['PC_FATURAMENTO']
        )
        
        dataframe_KIP = dataframe_KIP.groupby("CLASSIFICACAO_PDV").agg({
            "YTD_VENDA": "sum",
            "YTD_FATURAMENTO": "sum"
        }).reset_index()
        

        return dataframe_KIP

    def kips_Cob_Pond(self, dataframe_Vendas_Positivadas: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar a segunda coluna dos KIPs voltado a Cobertura Ponderada,
        onde a função irá agrupar CLASSIFICACAO_PDV: "Pond. Rede" e "Pond. Indep." somando as positivadas'''

        dataframe_KIP = dataframe_Vendas_Positivadas.copy()

        dataframe_KIP['CobPond_VENDA'] = (
            dataframe_KIP['HC_VENDA_POSITIVADA'] +
            dataframe_KIP['FR_VENDA_POSITIVADA'] +
            dataframe_KIP['BW_VENDA_POSITIVADA'] +
            dataframe_KIP['PC_VENDA_POSITIVADA']
        )
        
        dataframe_KIP['CobPond_FATURAMENTO'] = (
            dataframe_KIP['HC_FATURAMENTO_POSITIVADA'] +
            dataframe_KIP['FR_FATURAMENTO_POSITIVADA'] +
            dataframe_KIP['BW_FATURAMENTO_POSITIVADA'] +
            dataframe_KIP['PC_FATURAMENTO_POSITIVADA']
        )
        
        dataframe_KIP = dataframe_KIP.groupby("CLASSIFICACAO_PDV").agg({
            "CobPond_VENDA": "sum",
            "CobPond_FATURAMENTO": "sum"
        }).reset_index()

        dataframe_KIP = dataframe_KIP[dataframe_KIP["CLASSIFICACAO_PDV"].isin(["Pond. Rede", "Pond. Indep."])]       

        return dataframe_KIP
    
    def kips_Sort_Pond(self, dataframe_Vendas_Positivadas: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar a terceira coluna dos KIPs voltado a Sortimento Ponderada,
        onde a função irá agrupar CLASSIFICACAO_PDV: "Pond. Rede" e "Pond. Indep." somando as positivadas'''

        dataframe_KIP = dataframe_Vendas_Positivadas.copy()

        return dataframe_KIP

    def kips_Sort_Cob_Num(self, dataframe_Vendas_Positivadas: pd.DataFrame) -> pd.DataFrame:
        '''Função para criar a quarta coluna dos KIPs voltado a Sortimento Cobertura Numérica,'''
        dataframe_KIP = dataframe_Vendas_Positivadas.copy()

        dataframe_KIP['CobNum_VENDA'] = (
            dataframe_KIP['HC_VENDA_POSITIVADA'] +
            dataframe_KIP['FR_VENDA_POSITIVADA'] +
            dataframe_KIP['BW_VENDA_POSITIVADA'] +
            dataframe_KIP['PC_VENDA_POSITIVADA']
        )
        
        dataframe_KIP['CobNum_FATURAMENTO'] = (
            dataframe_KIP['HC_FATURAMENTO_POSITIVADA'] +
            dataframe_KIP['FR_FATURAMENTO_POSITIVADA'] +
            dataframe_KIP['BW_FATURAMENTO_POSITIVADA'] +
            dataframe_KIP['PC_FATURAMENTO_POSITIVADA']
        )
        
        dataframe_KIP = dataframe_KIP.groupby("CLASSIFICACAO_PDV").agg({
            "CobNum_VENDA": "sum",
            "CobNum_FATURAMENTO": "sum",
        }).reset_index()

        dataframe_KIP = dataframe_KIP[dataframe_KIP["CLASSIFICACAO_PDV"].isin(["Num. A", "Num. B", "Num. C"])]       

        return dataframe_KIP
    
    def kips_tabela(self, lista_dataframes: list[pd.DataFrame]) -> pd.DataFrame:
        '''Função para criar a tabela final dos KIPs, onde a função irá concatenar os dataframes dos KIPs criados anteriormente'''

        ordem_classificacao_pdv = ["Pond. Rede", "Pond. Indep.", "Num. A", "Num. B", "Num. C", "Atacados"]

        dataframe_KIP_final = pd.concat(
            [dataframe.set_index("CLASSIFICACAO_PDV") for dataframe in lista_dataframes],
            axis=1
        )

        dataframe_KIP_final = dataframe_KIP_final.reindex(ordem_classificacao_pdv)
        dataframe_KIP_final = dataframe_KIP_final.dropna(how="all").reset_index()

        return dataframe_KIP_final
    


if __name__ == "__main__":
    diretorio = "dados"
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
            "VLR_FATURAMENTO": "float"
        }
    )

    '''Correlacionar as bases de dados'''

    tabela_vendas_fora_da_base, tabela_vendas_na_base = servidor.criar_ean_fora_da_base(
        dataframe_unico_PPA=dataframe_unico_PPA,
        base_sql_vendas=base_sql_CNPJ_vendas
    )

    dataframe_BaseDeLojas = servidor.validacao_positivas(
        dataframe_vendas_na_base=tabela_vendas_na_base,
        dataframe_Base_de_Lojas=dataframe_BaseDeLojas
    )

    '''Tranformar typo de dados para float e arredondar para 2 casas decimais'''
    dataframe_BaseDeLojas = servidor.converter_tipo_dados(
        dataframe=dataframe_BaseDeLojas,
        Dict={
            "BW_FATURAMENTO": "float",
            "FR_FATURAMENTO": "float",
            "HC_FATURAMENTO": "float",
            "PC_FATURAMENTO": "float",
            "BW_VENDA": "float",
            "FR_VENDA": "float",
            "HC_VENDA": "float",
            "PC_VENDA": "float",
        }
    )

    positivacao_calculada = servidor.calcular_positivacao(
        dataframe_vendas=dataframe_BaseDeLojas,
        dataframe_ponderadas_meta=dataframe_ponderadas_meta
    )

    dataframe_KIP = servidor.kips_YTD_por_PDV(dataframe_BaseDeLojas)
    dataframe_KIP_CobPond = servidor.kips_Cob_Pond(positivacao_calculada)
    dataframe_KIP_Sort_Num = servidor.kips_Sort_Cob_Num(positivacao_calculada)
    dataframe_KIP_final = servidor.kips_tabela([dataframe_KIP, dataframe_KIP_CobPond, dataframe_KIP_Sort_Num])

    '''Exportar os DataFrames correlacionados para arquivos Excel'''

    kip = servidor.metas_e_realizado(tabela_vendas_na_base, positivacao_calculada, dataframe_BaseDeLojas)
    print(kip)

    # dataframes_para_exportar = {
    #     "Vendas_Por_CNPJ": base_sql_CNPJ_vendas,
    #     "Base_de_Lojas": dataframe_BaseDeLojas,
    #     "Base_de_EANs_PPA": dataframe_unico_PPA,
    #     "Vendas_Fora_da_Base": tabela_vendas_fora_da_base,
    #     "Vendas_Na_Base": tabela_vendas_na_base,
    #     "Metas_Ponderadas": dataframe_ponderadas_meta,
    #     "Vendas_Positivadas": positivacao_calculada
    # }

    # servidor.exportar_para_excel(dataframes_para_exportar)
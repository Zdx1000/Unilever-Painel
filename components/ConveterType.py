import pandas as pd
from typing import Dict

class ConveterType():
    def __init__(self) -> None:
        '''Conversão de tipos de dados'''
    
    def converter_tipo_dados(self, dataframe: pd.DataFrame, Dict: Dict[str, type]) -> pd.DataFrame:
        '''Função para converter o tipo de dados de colunas específicas em um DataFrame'''
        for coluna, tipo_dado in Dict.items():
            if coluna in dataframe.columns:
                try:
                    if tipo_dado == "str":
                        dataframe[coluna] = dataframe[coluna].astype(str)
                    elif tipo_dado == "int":
                        dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors='coerce').fillna(0).astype(int)
                    elif tipo_dado == "float":
                        dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors='coerce').fillna(0.0).astype(float).round(2)
                except Exception as e:
                    print(f"Erro ao converter a coluna '{coluna}': {e}")
            else:
                print(f"A coluna '{coluna}' não foi encontrada no DataFrame.")
        return dataframe
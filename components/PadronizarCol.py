import pandas as pd

class PadronizarCol():
    def __init__(self) -> None:
        '''Esta função tem como objetivo de padronizar os nomes das colunas
        removendo os espaçamentos em branco, acentos e caracteres especiais'''

    def padronizar_colunas(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        '''A função recebe o DataFrame init e padroniza todas as colunas, e
        retorna o DataFrame com os nomes das colunas padronizados'''
        for coluna in dataframe.columns:
            if coluna in dataframe.columns:
                nova_coluna = coluna.strip()\
                    .upper()\
                        .replace(" ", "_")\
                            .replace("Á", "A")\
                                .replace("É", "E")\
                                    .replace("Í", "I")\
                                        .replace("Ó", "O")\
                                            .replace("Ú", "U")\
                                                .replace("Ç", "C")\
                                                    .replace("Ã", "A")
                dataframe.rename(columns={coluna: nova_coluna}, inplace=True)
            else:
                print(f"A coluna '{coluna}' não foi encontrada no DataFrame.")
        return dataframe

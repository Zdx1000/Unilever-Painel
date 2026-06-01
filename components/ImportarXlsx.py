import os
import pandas as pd

class ImportarXlsx():
    def __init__(self, Diretorios: str = None) -> None:
        '''Importação de arquivos xlsx'''
        self.Diretorios = Diretorios

    def importar_excel(self, Inicial_name: str, Sheet_name: str = None, Colunas: list = None,
                    Pular_linha: int = 0, Mult_xlsx: bool = False) -> pd.DataFrame | None:
        '''Função para importar todos xlsx Descrição_Restante_de_Contagem_por_Item.xlsx'''
        list_Restante_de_Contagem = []
        for arquivos in os.listdir(self.Diretorios):
            if arquivos.startswith(Inicial_name) and (arquivos.endswith(".xlsx")):
                excel_compilado = os.path.join(self.Diretorios, arquivos)
                dataFrame = pd.read_excel(excel_compilado, sheet_name=Sheet_name, header=Pular_linha, usecols=Colunas)
                if isinstance(dataFrame, dict):
                    abas = [aba for aba in dataFrame.values() if isinstance(aba, pd.DataFrame)]
                    if not abas:
                        continue
                    dataFrame = abas[0] if len(abas) == 1 else pd.concat(abas, ignore_index=True)
                
                list_Restante_de_Contagem.append(dataFrame)
        if list_Restante_de_Contagem:
            if Mult_xlsx:
                dataFrame = pd.concat(list_Restante_de_Contagem, ignore_index=True)
            return dataFrame

        dataFrame = pd.DataFrame()
        return dataFrame
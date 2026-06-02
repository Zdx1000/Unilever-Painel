import pandas as pd

class PrincipalKips():
    BUS = ("BW", "FR", "HC", "PC")
    METRICAS_REALIZADO = (
        ("YTD", "VENDAS", "VLR_VENDA", "Real (R$)", False),
        ("YTD", "FATURAMENTO", "VLR_FATURAMENTO", "Real (R$)", False),
        ("Cob. Ponderada", "VENDAS", "QTD_VENDA_POSITIVADA", "Redes", True),
        ("Cob. Ponderada", "FATURAMENTO", "QTD_FATURAMENTO_POSITIVADA", "Redes", True),
        ("Cob. Numérica", "VENDAS", "COB_NUMERICA_VENDA", "PDVs", True),
        ("Cob. Numérica", "FATURAMENTO", "COB_NUMERICA_FATURAMENTO", "PDVs", True)
    )

    def __init__(self) -> None:
        '''Esta classe tem como objetivo de realizar as principais etapas do processo de tratamento de dados, 
        como padronização de colunas, conversão de tipos de dados e importação de arquivos xlsx'''

    def _contar_positivados(self, dataframe: pd.DataFrame, coluna: str) -> int:
        if coluna not in dataframe.columns:
            return 0

        return int(
            pd.to_numeric(
                dataframe[coluna],
                errors="coerce"
            ).fillna(0).eq(1).sum()
        )

    def _calcular_positivados_por_bu(self, dataframe_Positivadas: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "BU": bu,
                "QTD_VENDA_POSITIVADA": self._contar_positivados(
                    dataframe_Positivadas,
                    f"{bu}_VENDA_POSITIVADA"
                ),
                "QTD_FATURAMENTO_POSITIVADA": self._contar_positivados(
                    dataframe_Positivadas,
                    f"{bu}_FATURAMENTO_POSITIVADA"
                )
            }
            for bu in self.BUS
        ])

    def _calcular_cobertura_numerica(self, dataframe_Positivadas: pd.DataFrame) -> pd.DataFrame:
        if "TIPO" in dataframe_Positivadas.columns:
            tipo = dataframe_Positivadas["TIPO"].astype(str).str.strip().str.casefold()
            base_numerica = dataframe_Positivadas[tipo.isin(["numérica", "numerica"])]
        else:
            base_numerica = dataframe_Positivadas.iloc[0:0]

        def contar_cnpjs_positivados(coluna: str) -> int:
            if coluna not in base_numerica.columns or "CNPJ" not in base_numerica.columns:
                return 0

            positivado = pd.to_numeric(base_numerica[coluna], errors="coerce").fillna(0).eq(1)
            return int(base_numerica.loc[positivado, "CNPJ"].dropna().nunique())

        return pd.DataFrame([
            {
                "BU": bu,
                "COB_NUMERICA_VENDA": contar_cnpjs_positivados(f"{bu}_VENDA_POSITIVADA"),
                "COB_NUMERICA_FATURAMENTO": contar_cnpjs_positivados(f"{bu}_FATURAMENTO_POSITIVADA")
            }
            for bu in self.BUS
        ])

    def _calcular_base_metas_e_realizado(self, dataframe_Vendas_Na_Base: pd.DataFrame,
                                         dataframe_Positivadas: pd.DataFrame) -> pd.DataFrame:
        kip = dataframe_Vendas_Na_Base.groupby("BU", as_index=False).agg({
            "VLR_VENDA": "sum",
            "VLR_FATURAMENTO": "sum"
        })

        kip = kip.merge(
            self._calcular_positivados_por_bu(dataframe_Positivadas),
            on="BU",
            how="outer"
        )
        kip = kip.merge(
            self._calcular_cobertura_numerica(dataframe_Positivadas),
            on="BU",
            how="outer"
        )

        colunas_realizado = [coluna for _, _, coluna, _, _ in self.METRICAS_REALIZADO]
        kip[colunas_realizado] = kip[colunas_realizado].fillna(0)
        kip["AE"] = "MD"

        return kip

    def _montar_tabela_metas_e_realizado(self, kip: pd.DataFrame) -> pd.DataFrame:
        linhas = []

        for kpi, tipo, coluna, unidade, inteiro in self.METRICAS_REALIZADO:
            realizado = pd.to_numeric(kip[coluna], errors="coerce").fillna(0)
            realizado = realizado.astype(int) if inteiro else realizado.round(2)

            linhas.append(
                kip[["BU", "AE"]].assign(
                    KPI=kpi,
                    TIPO=tipo,
                    Realizado=realizado,
                    Unidade_de_Medida=unidade
                )
            )

        return pd.concat(linhas, ignore_index=True)

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
        
        kip = self._calcular_base_metas_e_realizado(
            dataframe_Vendas_Na_Base,
            dataframe_Positivadas
        )
        
        return self._montar_tabela_metas_e_realizado(kip)
        

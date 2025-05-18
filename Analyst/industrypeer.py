import yfinance as yf
# from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
import pandas as pd

class IndustryPeerAnalysis:
    def __init__(self, company, openai_api_key):
        self.company = company
        self.openai_api_key = openai_api_key
        self.model = ChatOpenAI(openai_api_key=self.openai_api_key, model="gpt-4")
        self.tickers = []
        self.total_weight = {}
        self.ratios_names = []
        self.all_ratios = {}
        self.industry_averages = {}
    
    def get_financial_data_string(self, ticker_symbol):
        ticker = yf.Ticker(ticker_symbol)
        
        # Fetch financial statements (only needed years)
        bs = ticker.balance_sheet.iloc[:, :2] if not ticker.balance_sheet.empty else pd.DataFrame()
        is_ = ticker.financials.iloc[:, :2] if not ticker.financials.empty else pd.DataFrame()
        cf = ticker.cashflow.iloc[:, :2] if not ticker.cashflow.empty else pd.DataFrame()
        
        # Convert info dictionary to a formatted string
        info_str = f"Info:\n" + "\n".join([f"{k}: {v}" for k, v in ticker.info.items()]) + "\n\n"

        # Convert financial statements to string (handle empty DataFrames)
        bs_str = f"Balance Sheet:\n{bs.to_string()}\n\n" if not bs.empty else "Balance Sheet: Data Unavailable\n\n"
        is_str = f"Income Statement:\n{is_.to_string()}\n\n" if not is_.empty else "Income Statement: Data Unavailable\n\n"
        cf_str = f"Cash Flow Statement:\n{cf.to_string()}\n\n" if not cf.empty else "Cash Flow Statement: Data Unavailable\n\n"
        
        # Combine all data
        combined_data = info_str + bs_str + is_str + cf_str
        return combined_data

    @staticmethod
    def safe_float_conversion(value, default=0.0):
        try:
            return float(value.strip())
        except (ValueError, TypeError, AttributeError):
            return default

    def calculate_weighted_averages(self):
        weighted_averages = {}
        for ratio in self.ratios_names:
            weighted_sum = 0.0
            total_weights = 0.0

            for ticker in self.tickers:
                ratio_str = self.all_ratios[ticker].get(ratio, "N/A")
                ratio_value = self.safe_float_conversion(ratio_str)

                weight_str = self.total_weight.get(ticker, "0")
                weight = self.safe_float_conversion(weight_str, 0.0)

                if ratio_value is not None and weight > 0:
                    weighted_sum += ratio_value * weight
                    total_weights += weight

            if total_weights > 0:
                weighted_avg = weighted_sum / total_weights
            else:
                weighted_avg = None  # or 0.0 if preferred

            weighted_averages[ratio.strip()] = weighted_avg

        self.industry_averages = weighted_averages

    def get_similar_companies(self):
        prompt = ChatPromptTemplate.from_messages([('system','select companies that operate in similar segments, have similar business models, or share product offerings with {company}. Companies that compete directly with {company} in key markets or have similar operating structures should typically be prioritized., only list out their ticker symbols nothing else no other information, add the ticker of {company} in the end, the output should be separated by space no numbers ')])
        chain = prompt | self.model | StrOutputParser()
        industrypeers = chain.invoke({"company": self.company})
        self.tickers = industrypeers.split()
    
    def assign_weights(self):
        industrypeers = ' '.join(self.tickers)
        prompt = ChatPromptTemplate.from_messages([('system','assign weights to the companies based on the similarity to {company}, Assign weights to each peer company based on their relevance to {company} business. Factors influencing these weights include   - Business Overlap: Consider how closely aligned their product offerings are with {company} core businesses.   - Market Position: Take into account companies that are direct competitors in key markets    - Industry Influence: Include companies that operate within similar market environments or share similar economic pressures.. The weights should be between 0 and 1 and should sum to 1. The companies should be listed in the same order as the ticker symbols from the previous step, separated by spaces. List of companies to weigh is {industrypeers}, only give the weights separated by spaces. nothing else no other information, the output should be separated by space no words')])
        chain = prompt | self.model | StrOutputParser()
        weights_str = chain.invoke({"company": self.company, "industrypeers": industrypeers})
        weights = weights_str.split()
        self.total_weight = dict(zip(self.tickers, weights))

    def get_ratios_to_compare(self):
        prompt = ChatPromptTemplate.from_messages([('system',"You are world's greatest financial analyst and you are about to do a financial analysis of {company}, the first thing you're focusing your energy on is to create a list of different financial ratios that are most relevant in comparing the financial health of {company} with its peers. The ratios should be relevant to the industry and should be used to compare the financial health of {company} with its peers. The output should be in a single line and ratios should be separated by **** no other words, no numbers.")])
        chain = prompt | self.model | StrOutputParser()
        ratios_str = chain.invoke({"company": self.company})
        self.ratios_names = ratios_str.split('****')

    def calculate_ratios(self):
        for t in self.tickers:
            financial_data_str = self.get_financial_data_string(t)
            # Need to handle the possibility that financial_data_str is empty or invalid
            prompt = ChatPromptTemplate.from_messages([('system',"You are world's greatest financial analyst and you are about to do a financial analysis of a company. You have gathered the last two years' financial data of the company and now want to calculate ratios using that. You want to calculate these ratios: {ratios}. Calculate these ratios using the data provided with the utmost accuracy. Recheck if needed, then when sure with the answers, give the output. The output should be in a single line, and ratios should be separated by ****, no other words, only numbers. Please find the financial data below: {financial_data_str}")])
            chain = prompt | self.model | StrOutputParser()
            ratios_str = chain.invoke({"ratios": '****'.join(self.ratios_names), "financial_data_str": financial_data_str})
            ratios_values = ratios_str.split('****')
            ratios_dict = dict(zip(self.ratios_names, ratios_values))
            self.all_ratios[t] = ratios_dict

    def analyze(self):
        # Run the full analysis
        self.get_similar_companies()
        self.assign_weights()
        self.get_ratios_to_compare()
        self.calculate_ratios()
        self.calculate_weighted_averages()
    
    def get_result(self):
        result = {
            self.company: self.all_ratios.get(self.company, {}),
            "industry_average": self.industry_averages
        }
        return result
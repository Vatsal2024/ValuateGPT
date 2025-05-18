import streamlit as st
from industrypeer import IndustryPeerAnalysis
from macroanalysis import MacroeconomicAnalyzer
from newsanalyst import NewsAnalyzer
from technicalanalyst import TechnicalAnalysisAnalyzer
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI

# Set the title of the Streamlit app
st.title("ValuateGPT: Financial Analysis and Investment Recommendations")
st.write("Enter a company name or stock symbol to get comprehensive financial insights, industry comparisons, macroeconomic analysis, and expert investment recommendations from ValuateGPT.")

# Input for company name or stock symbol
company_name = st.text_input("Company Name", placeholder="e.g., AAPL, TCS, Google")
openai_api_key = st.text_input("Enter your OpenAI API key", type="password")

# Define the function to run all analyses
def run_analysis(company):
    

    # Industry Peer Analysis
    Industry = IndustryPeerAnalysis(company, openai_api_key)
    Industry.analyze()
    IndustryResults = Industry.get_result()

    # Macroeconomic Analysis
    pdf_path = "financialanalyst/US_Economic_Forecast_Deloitte.pdf"
    macroanalyzer = MacroeconomicAnalyzer(pdf_path, company, openai_api_key)
    macroanalyzer.analyze()
    macro_analysis_result = macroanalyzer.get_analysis()

    # News Analysis
    news_analyzer = NewsAnalyzer(openai_api_key)
    news_result = news_analyzer.analyze_news(company)

    # Technical Analysis
    ta_analyzer = TechnicalAnalysisAnalyzer(openai_api_key)
    ta_analysis_result = ta_analyzer.analyze_technical_data(company)

    # Combine all analysis results
    combined_analysis = f"""
    Industry Analysis:
    {IndustryResults}

    Macroeconomic Analysis:
    {macro_analysis_result}

    News Analysis:
    {news_result}

    Technical Analysis:
    {ta_analysis_result}
    """
    
    # Create the Langchain prompt
    prompt = PromptTemplate(
        input_variables=["combined_analysis"],
        template="""
        You are a financial analyst with expertise in stock market analysis. Based on the following combined analysis of the company, provide a detailed investment recommendation:
        
        {combined_analysis}
        
        Output should include:
        - A summary of the investment outlook considering the factors mentioned above.
        - Clear and specific investment strategy for short-term traders, long-term investors, and current holders.
        - Any risks or opportunities identified for the stock.
        - Be as specific as possible, including potential price targets, trends to watch, and any cautionary advice for investors.
        """
    )

    # Set up Langchain LLM with OpenAI API
    llm = OpenAI(openai_api_key=openai_api_key)
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run the Langchain analysis and return the result
    final_recommendation = chain.run({"combined_analysis": combined_analysis})
    return final_recommendation

# Display the result when the button is clicked
if st.button("Get Company Info"):
    if company_name.strip():
        with st.spinner("Fetching information..."):
            result = run_analysis(company_name)
        st.subheader(f"Financial Insights for {company_name}")
        st.write(result)
    else:
        st.warning("Please enter a company name to proceed.")

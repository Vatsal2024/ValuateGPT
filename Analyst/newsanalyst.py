import json
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
import newselenium

class NewsAnalyzer:
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o"):
        self.model = ChatOpenAI(openai_api_key=openai_api_key, model=model_name)
        
        self.news_analyze_prompt = ChatPromptTemplate.from_messages([
            ("system", "You're the best News trader in the world. You have a secret source that gives you the most accurate news before it happens. You've been using this source to make millions of dollars in the stock market. One day, you receive a message from your source that says: The world is about to end. You have to warn everyone. You're not sure if you should believe it, but you decide to investigate. You start by checking the news and see that there have been a series of strange events happening around the world. You realize that your source was right. The world is about to end. You have to warn everyone before it's too late. You decide to use your trading skills to make as much money as possible before the world ends. You have to act fast. You have to save as many people as you can. You have to be the hero the world needs. You have to be the News Trader."),
            ("human", "You come across news articles of {company} \n the news is {news} \n You have to give your insights on this news. What do you think will happen to the stock price of {company} after this news? Will it go up or down? Why? What should people do with their investments in {company}?")
        ])

        self.output_prompt = ChatPromptTemplate.from_messages([
            ('system', 'Give this content a system essence, remove all the LLMs talking, and explain the info only \n {response}')
        ])

    def extract_content_from_json_file(self, file_path: str):
        extracted_contents = []
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for article in data:
                if 'content' in article and article['content'] is not None:
                    extracted_contents.append(article['content'])
        return extracted_contents

    def analyze_news(self, keyword: str):
        news_extractor = newselenium.NewsExtractor(keyword)
        news_extractor.fetch_articles()
        news_extractor.save_to_json(f"{keyword}_news.json")
        
        json_file_path = f"{keyword}_news.json"
        news_contents = self.extract_content_from_json_file(json_file_path)
        news_articles = " ".join(news_contents)
        
        chain = self.news_analyze_prompt | self.model | StrOutputParser()
        chain2 = self.output_prompt | self.model | StrOutputParser()
        
        response = chain.invoke({"company": keyword, "news": news_articles})
        final_response = chain2.invoke({"response": response})
        
        return final_response

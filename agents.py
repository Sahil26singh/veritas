from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search , scrape_url
from config import GROQ_MODEL
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model = GROQ_MODEL, temperature=0, max_retries=5)


#1st agent
def build_search_agent():
    return create_agent(
        model = llm,
        tools= [web_search]
    )

#2nd agent
def build_reader_agent():
    return create_agent(
        model = llm,
        tools = [scrape_url]
    )


#writer chain

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports. Only state facts supported by the research provided."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional. If reviewer feedback is included in the research, address every point in it."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()

#critic_chain

critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.
Also check that its claims are supported by the source research provided.

Report:
{report}

Source Research:
{research}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()

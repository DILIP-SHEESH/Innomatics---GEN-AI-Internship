from dotenv import load_dotenv
import os

from langchain_core.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceHub

# Load env
load_dotenv()
llm = HuggingFaceHub(
    repo_id="google/flan-t5-large",
    model_kwargs={"temperature": 0.2, "max_length": 512}
)

# ------------------ PROMPTS ------------------

extract_prompt = PromptTemplate(
    input_variables=["resume"],
    template="""
Extract:
- Skills
- Tools
- Experience

Return JSON:
{{
  "skills": [],
  "tools": [],
  "experience": ""
}}

Resume:
{resume}

Rules:
- Do NOT assume anything
"""
)

match_prompt = PromptTemplate(
    input_variables=["resume_data", "job_description"],
    template="""
Compare resume with job description.

Return JSON:
{{
  "matched_skills": [],
  "missing_skills": []
}}

Resume:
{resume_data}

Job Description:
{job_description}
"""
)

score_prompt = PromptTemplate(
    input_variables=["matched", "missing"],
    template="""
Give score (0–100).

Return JSON:
{{
  "score": number
}}

Matched:
{matched}

Missing:
{missing}
"""
)

explain_prompt = PromptTemplate(
    input_variables=["score", "matched", "missing"],
    template="""
Explain score clearly.

Score: {score}
Matched: {matched}
Missing: {missing}
"""
)

extract_chain = extract_prompt | llm
match_chain = match_prompt | llm
score_chain = score_prompt | llm
explain_chain = explain_prompt | llm

# ------------------ PIPELINE ------------------

def run_pipeline(resume, job_description):
    extracted = extract_chain.invoke({"resume": resume})

    matched = match_chain.invoke({
        "resume_data": extracted,
        "job_description": job_description
    })

    score = score_chain.invoke({
        "matched": matched,
        "missing": matched
    })

    explanation = explain_chain.invoke({
        "score": score,
        "matched": matched,
        "missing": matched
    })

    return {
        "extracted": extracted,
        "matched": matched,
        "score": score,
        "explanation": explanation
    }

# ------------------ SAMPLE DATA ------------------

job_description = """
Looking for Data Scientist:
Python, Machine Learning, Deep Learning, NLP, SQL
"""

strong_resume = """
3 years experience.
Skills: Python, Machine Learning, Deep Learning, NLP
Tools: TensorFlow, SQL
"""

average_resume = """
1 year experience.
Skills: Python, Pandas
"""

weak_resume = """
Fresher.
Skills: Excel
"""

print("STRONG:\n", run_pipeline(strong_resume, job_description))
print("\nAVERAGE:\n", run_pipeline(average_resume, job_description))
print("\nWEAK:\n", run_pipeline(weak_resume, job_description))
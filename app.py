import streamlit as st
import docx2txt
import PyPDF2
import google.generativeai as genai
import anthropic
from groq import Groq

# --- Page Config ---
st.set_page_config(page_title="CompIntel AI", page_icon="🕵️", layout="wide")
st.title("Strategic Competitive Intelligence Analyst 🕵️‍♂️")
st.markdown("Upload a competitor's job listings and their recent SEC 10-K/10-Q filing to generate a strategic CMO briefing.")

# --- Sidebar: Model Router ---
st.sidebar.header("⚙️ Engine Settings")
selected_model = st.sidebar.radio(
    "Choose your AI Model:",
    ["Llama 3.1 (Groq)", "Gemini 1.5 Pro", "Claude 3 Opus"]
)

# Dynamically change the API key prompt based on the chosen model
if selected_model == "Gemini 1.5 Pro":
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    st.sidebar.caption("Uses google-generativeai SDK (2M token context)")
elif selected_model == "Claude 3 Opus":
    api_key = st.sidebar.text_input("Enter Anthropic API Key", type="password")
    st.sidebar.caption("Uses Anthropic SDK (200k token context)")
else:
    api_key = st.sidebar.text_input("Enter Groq API Key", type="password")
    st.sidebar.caption("Uses Groq SDK (Llama 3.1 70B - Fast & Free Tier)")

# --- Helper function to extract text ---
def extract_text(file):
    if file.name.endswith(".txt"):
        return file.getvalue().decode("utf-8")
    elif file.name.endswith(".docx"):
        return docx2txt.process(file)
    elif file.name.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(file)
        return "".join([page.extract_text() for page in pdf_reader.pages])
    return ""

# --- File Uploaders ---
col1, col2 = st.columns(2)
with col1:
    jobs_file = st.file_uploader("1. Upload Job Listings (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
with col2:
    sec_file = st.file_uploader("2. Upload SEC Filing (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])

company_name = st.text_input("Target Company Name:")

# --- Core Prompt ---
def generate_prompt(company, jobs_text, sec_text):
    return f"""
You are a competitive intelligence analyst at a rival company. I've uploaded {company}'s complete current job listings and their most recent SEC filing.

<job_listings>
{jobs_text}
</job_listings>

<sec_filing>
{sec_text}
</sec_filing>

Perform a strategic intelligence analysis:

→ Cluster these roles by what they suggest is being built. Don't use the team names they've listed. Infer the actual product initiatives from the skills, tools, and responsibilities described.
→ Identify capabilities or teams that appear entirely new — not mentioned anywhere in the SEC filing. These are unreleased bets.
→ Find roles where seniority is disproportionately high for a new team. This signals executive-level priority.
→ Cross-reference the SEC filing's Risk Factors and Strategy sections with hiring patterns. Where are they investing against a stated risk? Where did they flag a risk but have zero hiring to address it?
→ Predict 3 product launches or strategic moves this company will make in the next 6-12 months. State your confidence level and cite specific job titles and filing sections as evidence.

Format this as a 1-page competitive intelligence briefing for a CMO.
"""

# --- Execution Logic ---
if st.button("Generate Intelligence Briefing", type="primary"):
    if not api_key:
        st.error(f"Please enter your {selected_model} API key in the sidebar.")
    elif not jobs_file or not sec_file or not company_name:
        st.warning("Please upload both files and enter the company name.")
    else:
        with st.spinner(f"Analyzing data with {selected_model}. This may take a minute..."):
            
            # Extract text
            jobs_text = extract_text(jobs_file)
            sec_text = extract_text(sec_file)
            final_prompt = generate_prompt(company_name, jobs_text, sec_text)
            
            try:
                # --- ROUTER: GEMINI ---
                if selected_model == "Gemini 1.5 Pro":
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    response = model.generate_content(
                        final_prompt,
                        generation_config=genai.types.GenerationConfig(temperature=0.2)
                    )
                    report_text = response.text
                
                # --- ROUTER: CLAUDE ---
                elif selected_model == "Claude 3 Opus":
                    client = anthropic.Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=4000,
                        temperature=0.2,
                        messages=[{"role": "user", "content": final_prompt}]
                    )
                    report_text = response.content[0].text
                    
                # --- ROUTER: GROQ (LLAMA 3.1) ---
                # elif selected_model == "Llama 3.1 (Groq)":
                #     client = Groq(api_key=api_key)
                #     response = client.chat.completions.create(
                #         model="openai/gpt-oss-120b",
                #         messages=[{"role": "user", "content": final_prompt}],
                #         temperature=0.2,
                #     )
                #     report_text = response.choices[0].message.content


                elif selected_model == "Llama 3.1 (Groq)":
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[{"role": "user", "content": final_prompt}],
                        temperature=0.2,
                        max_tokens=6000  # Added parameter here
                    )
                    report_text = response.choices[0].message.content

                # --- Output ---
                st.success(f"Analysis Complete (Powered by {selected_model})!")
                st.markdown("### CMO Strategic Intelligence Briefing")
                st.markdown(report_text)
                
            except Exception as e:
                st.error(f"An error occurred with the {selected_model} API: {e}")

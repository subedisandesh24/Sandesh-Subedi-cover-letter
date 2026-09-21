import streamlit as st
from groq import Groq
from PIL import Image
from fpdf import FPDF
from datetime import datetime
import json
import base64
import io
import os
import re
import urllib.request
import unicodedata

# -------------------------------------------------------------------------
# 1. Calibri Font Manager (Works locally & on Streamlit Cloud)
# -------------------------------------------------------------------------
@st.cache_resource
def setup_calibri_fonts():
    """
    Finds native Calibri on Windows or downloads Carlito (Google's metric-identical
    open-source Calibri twin) for Streamlit Cloud/Linux.
    """
    win_dir = "C:\\Windows\\Fonts"
    win_reg = os.path.join(win_dir, "calibri.ttf")
    win_bold = os.path.join(win_dir, "calibrib.ttf")
    win_ital = os.path.join(win_dir, "calibrii.ttf")
    if os.path.exists(win_reg) and os.path.exists(win_bold) and os.path.exists(win_ital):
        return "Calibri", {"": win_reg, "B": win_bold, "I": win_ital}

    if os.path.exists("calibri.ttf") and os.path.exists("calibrib.ttf") and os.path.exists("calibrii.ttf"):
        return "Calibri", {"": "calibri.ttf", "B": "calibrib.ttf", "I": "calibrii.ttf"}

    carlito_urls = {
        "": "https://raw.githubusercontent.com/google/fonts/main/ofl/carlito/Carlito-Regular.ttf",
        "B": "https://raw.githubusercontent.com/google/fonts/main/ofl/carlito/Carlito-Bold.ttf",
        "I": "https://raw.githubusercontent.com/google/fonts/main/ofl/carlito/Carlito-Italic.ttf"
    }
    local_files = {"": "calibri_reg.ttf", "B": "calibri_bold.ttf", "I": "calibri_ital.ttf"}

    try:
        for style, url in carlito_urls.items():
            dest = local_files[style]
            if not os.path.exists(dest):
                urllib.request.urlretrieve(url, dest)
        return "Calibri", local_files
    except Exception:
        return "Helvetica", None


# -------------------------------------------------------------------------
# 2. Clean Text Function
# -------------------------------------------------------------------------
def clean_text(val):
    """Safely converts unicode to clean ASCII, stripping characters that turn into '???' and removes stray asterisks"""
    if val is None:
        return ""
    if isinstance(val, list):
        val = ", ".join(str(item) for item in val if item is not None)
    elif not isinstance(val, str):
        val = str(val)

    # Strip markdown asterisks to guarantee zero raw '*word*' mistakes
    val = val.replace("**", "").replace("*", "")

    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"', "`": "'",
        "–": "-", "—": "-", "―": "-", "…": "...",
        "•": "-", "▪": "-", "►": "-", "·": "-", "★": "-",
        "✓": "[x]", "✔": "[x]", "✔️": "[x]",
        "\u00a0": " ", "\u200b": "", "\u2003": " ", "\t": "    "
    }
    for k, v in replacements.items():
        val = val.replace(k, v)

    val = unicodedata.normalize('NFKD', val).encode('ascii', 'ignore').decode('ascii')
    return val.strip()


# -------------------------------------------------------------------------
# 3. Dynamic Fallback Generators (Zero Percentage, Strictly Requested Docs)
# -------------------------------------------------------------------------
def get_fallback_cover_letter(target_role, org_name, date_str):
    return f"""{date_str}

Hiring Committee
{org_name}

Subject: Application for the position of {target_role}

Dear Hiring Committee,

I am writing to express my enthusiastic interest in the {target_role} position at {org_name}. As an agriculture professional with an ongoing Master of Science in Agriculture (Horticulture) at Agriculture and Forestry University (AFU) and a Bachelor of Science in Agriculture (Merit Scholarship) from Tribhuvan University, Institute of Agriculture and Animal Sciences (IAAS), I bring hands-on experience in agricultural training, rural enterprise facilitation, varietal research, and digital data collection. My background aligns closely with {org_name}'s mission to advance sustainable rural livelihoods, food security, and resilient agrifood systems across Nepal.

Throughout my career, I have demonstrated the ability to bridge field research with grassroots community action. As Province Assistant for Daayitwa NGO under the Growth Entrepreneurship and Employment Promotion (GEEP) program, I supported rural enterprise development across Jaljala, Hupsekot, Badigad, Siranchok, and Myagde rural municipalities. Working collaboratively with municipal authorities, local entrepreneurs, and community leaders, I facilitated stakeholder consultations and field monitoring that created sustainable economic opportunities for local households.

Furthermore, as Agriculture Instructor and focal point for the JICA Partnership Program at Shree Mahendra Secondary School in Kaski, I supervised the practical 'Learn & Earn' program. I guided learners and youth groups through the complete crop production cycle—from seedbed preparation and nursery management to harvesting, post-harvest processing, and local market linkages. My practical facilitation skills are further evidenced by my training delivery with the Stromme Foundation and Harihar Women Savings and Loan Cooperative, where I conducted hands-on sessions on off-season vegetable farming, integrated pest management (IPM), and mushroom cultivation.

In addition to field facilitation, I bring solid research and analytical capabilities. At the Nepal Agricultural Research Council (NARC) Horticulture Research Station in Malepatan, I guided Junior Technical Assistants (JTAs) on field agronomy trials, supervised varietal performance experiments, and contributed to technical reporting. As an enumerator for the National Census of Agriculture 2021/22, I conducted rigorous household surveys using digital tools and participatory techniques (KIIs and FGDs). With multiple peer-reviewed publications and technical proficiency in Arc-GIS, RStudio, SPSS, and Python-based crop analytics, I am well-prepared to support program MEAL, data-driven planning, and impact documentation.

I am eager to contribute my field experience, technical training skills, and dedication to {org_name}'s development interventions. I strictly uphold organizational safeguarding standards, gender equality and social inclusion (GESI), and humanitarian values. I welcome the opportunity to discuss how my competencies align with your program goals.

Sincerely,

Sandesh Subedi
Phone: +977-9866009867
Email: Subedisandesh24@gmail.com
Putalibazar-13, Syangja / Nepal"""


def get_fallback_email(target_role, org_name, requested_docs=None):
    if not requested_docs or len(requested_docs) == 0:
        docs_list = [
            "1. Updated Curriculum Vitae (CV)",
            "2. Cover Letter"
        ]
    else:
        docs_list = [f"{i+1}. {doc}" for i, doc in enumerate(requested_docs)]

    docs_block = "\n".join(docs_list)

    return f"""Dear Hiring Team,

I hope this email finds you well.

I am writing to formally submit my application for the position of {target_role} at {org_name}.

With an ongoing Master of Science in Agriculture (Horticulture) at Agriculture and Forestry University (AFU) and a Bachelor of Science in Agriculture from Tribhuvan University, I bring proven field experience in rural enterprise promotion (Daayitwa GEEP program), participatory farmer training (Stromme Foundation, Harihar Cooperative), JICA program coordination, and agronomic research trials with NARC. I am confident in my capacity to contribute effectively to your field implementation and program outcomes.

Please find attached the requested documents for your review:
{docs_block}

Thank you for your time and consideration. I look forward to hearing from you regarding the next steps in the recruitment process.

Sincerely,

Sandesh Subedi
Phone: +977-9866009867
Email: Subedisandesh24@gmail.com
LinkedIn: linkedin.com/in/sandeshsubedi24
Putalibazar-13, Syangja, Nepal"""


# -------------------------------------------------------------------------
# 4. PDF Builder (Calibri Typography & Justified Responsibilities)
# -------------------------------------------------------------------------
class CompleteCVPDF(FPDF):
    def __init__(self, doc_type="CV"):
        super().__init__(format="A4", unit="mm")
        self.doc_type = doc_type
        self.set_margins(16, 14, 16)
        self.set_auto_page_break(auto=True, margin=15)

        self.font_family, font_paths = setup_calibri_fonts()
        if font_paths:
            for style, path in font_paths.items():
                self.add_font("Calibri", style=style, fname=path)

    @property
    def printable_width(self):
        return self.w - self.l_margin - self.r_margin

    def draw_cv_header(self):
        self.set_y(14)
        self.set_x(self.l_margin)

        # Name on Left
        self.set_font(self.font_family, "B", 18)
        self.set_text_color(20, 20, 20)
        self.cell(95, 10, "SANDESH SUBEDI", align="L")

        # Contact Details on Right
        contact_x = self.w - self.r_margin - 88
        self.set_font(self.font_family, "", 9)

        self.set_xy(contact_x, 14)
        self.set_text_color(60, 60, 60)
        self.cell(88, 3.8, "+977-9866009867", align="R", new_x="LMARGIN", new_y="NEXT")

        self.set_x(contact_x)
        self.cell(88, 3.8, "Subedisandesh24@gmail.com", align="R", new_x="LMARGIN", new_y="NEXT")

        self.set_x(contact_x)
        self.set_text_color(0, 80, 200)
        self.cell(
            88, 3.8, "linkedin.com/in/sandeshsubedi24",
            align="R",
            link="https://www.linkedin.com/in/sandeshsubedi24",
            new_x="LMARGIN",
            new_y="NEXT"
        )
        self.set_text_color(20, 20, 20)
        self.ln(3)

    def draw_section_heading(self, title):
        avail_w = self.printable_width
        self.ln(2)
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 11.5)
        self.set_text_color(15, 15, 15)
        self.cell(avail_w, 5, clean_text(title), new_x="LMARGIN", new_y="NEXT")

        curr_y = self.get_y()
        self.set_draw_color(40, 40, 40)
        self.set_line_width(0.35)
        self.line(self.l_margin, curr_y, self.w - self.r_margin, curr_y)
        self.ln(2.5)

    def draw_org_block(self, org_name, location, role_title, dates, bullets):
        avail_w = self.printable_width
        col_left = 115
        col_right = avail_w - col_left

        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 10.2)
        self.set_text_color(20, 20, 20)
        self.cell(col_left, 4.5, clean_text(org_name), align="L")
        self.set_font(self.font_family, "", 9)
        self.cell(col_right, 4.5, clean_text(location), align="R", new_x="LMARGIN", new_y="NEXT")

        self.set_x(self.l_margin)
        self.set_font(self.font_family, "I", 9.2)
        self.cell(col_left, 4.2, clean_text(role_title), align="L")
        self.set_font(self.font_family, "", 9)
        self.cell(col_right, 4.2, clean_text(dates), align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(0.8)

        self.set_font(self.font_family, "", 9)
        self.set_text_color(35, 35, 35)
        for bullet in bullets:
            self.set_x(self.l_margin)
            # Responsibilities rendered with Justified Alignment ('J')
            self.multi_cell(avail_w, 4.3, f"-  {clean_text(bullet)}", align="J", new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def draw_two_col_entry(self, left_bold, left_sub, right_txt, right_sub=""):
        avail_w = self.printable_width
        col_left = 118
        col_right = avail_w - col_left

        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 9.2)
        self.set_text_color(20, 20, 20)
        self.cell(col_left, 4.2, clean_text(left_bold), align="L")
        self.set_font(self.font_family, "", 9)
        self.cell(col_right, 4.2, clean_text(right_txt), align="R", new_x="LMARGIN", new_y="NEXT")

        if left_sub or right_sub:
            self.set_x(self.l_margin)
            self.set_font(self.font_family, "", 8.8)
            self.set_text_color(50, 50, 50)
            self.cell(col_left, 4.0, clean_text(left_sub), align="L")
            self.cell(col_right, 4.0, clean_text(right_sub), align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def footer(self):
        self.set_y(-12)
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "", 8.5)
        self.set_text_color(90, 90, 90)
        avail_w = self.printable_width
        self.cell(avail_w / 2, 8, "Sandesh Subedi - Phone: +977-9866009867 | Email: Subedisandesh24@gmail.com", align="L")
        self.cell(avail_w / 2, 8, f"{self.page_no()} | P a g e", align="R")


# -------------------------------------------------------------------------
# 5. Dynamic Model Selector
# -------------------------------------------------------------------------
def get_groq_active_models(client):
    try:
        available_models = [m.id for m in client.models.list().data]
        preferred_text = [
            "llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b", "llama-3.1-8b-instant"
        ]
        text_model = next((m for m in preferred_text if m in available_models), None)
        if not text_model:
            text_model = available_models[0] if available_models else "llama-3.3-70b-versatile"

        preferred_vision = [
            "llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview", "qwen/qwen3.8-27b"
        ]
        vision_model = next((m for m in preferred_vision if m in available_models), text_model)
        return text_model, vision_model
    except Exception:
        return "llama-3.3-70b-versatile", "llama-3.2-11b-vision-preview"


# -------------------------------------------------------------------------
# 6. Permanent CV Database (No Percentage Included)
# -------------------------------------------------------------------------
PERMANENT_CV_SECTIONS = {
    "education": [
        {
            "inst": "Agriculture and Forestry University (AFU)",
            "deg": "Masters of Science in Agriculture (Horticulture)",
            "loc": "Chitwan, Nepal",
            "yr": "2025-Present",
            "sub": "MS Thesis: Comparative Study of AI & Manual Data Collection for Assessing Tomato Yield and Quality"
        },
        {
            "inst": "Tribhuvan University, Institute of Agriculture and Animal Sciences",
            "deg": "Bachelors of Science in Agriculture (Merit Scholarship)",
            "loc": "Lamjung, Nepal",
            "yr": "2019-2023",
            "sub": "Thesis: Effect of Mulching Materials on Growth and Yield of Brinjal (Best Presentator Award)"
        },
        {
            "inst": "Prativa Secondary School",
            "deg": "Higher Secondary School - GPA: 3.26/4 (Biology with extra Mathematics)",
            "loc": "Kaski, Nepal",
            "yr": "2016-2018",
            "sub": ""
        }
    ],
    "publications": [
        {
            "title": "Subedi, S., & Adhikari, S. (2024). Effects of mulching materials on growth and yield of brinjal. Agriculture Development Journal, 17(1), 135-143.",
            "doi": "https://doi.org/10.3126/adj.v17i1.67882"
        },
        {
            "title": "Jaiswal, M., Kharel, R., & Subedi, S. (2024). Response of spring rice varieties on different nitrogen management practices in Kapilvastu, Nepal. Agronomy Journal of Nepal, 8(1), 45-56.",
            "doi": "https://doi.org/10.3126/ajn.v8i1.70853"
        },
        {
            "title": "Malla, A. B., Subedi, S., G.C., D. B., & Bhandari, J. (2024). Ecological Status, Threats, and Habitat Characteristics of Panchaule (Dactylorhiza hatagirea) in Ghasa of Mustang District. The Journal of Agriculture and Environment, 25, 99-107.",
            "doi": ""
        },
        {
            "title": "Dahal, S., Subedi, S., & Paudel, N. (2021). A review on Diploknema butyracea (Roxb.) H.J. Lam. (Chiuri) for production, uses, and strategy of management concerning Chepang communities in Nepal. Journal of Multidisciplinary Sciences, 3(16), 22-34.",
            "doi": "https://doi.org/10.33888/jms.2021.316"
        },
        {
            "title": "Subedi, S. (2024). Algal diversity in Nepal and its applications: Current insights and future prospects. Science Heritage Journal, 8(2), 69-78.",
            "doi": "https://doi.org/10.26480/gws.02.2024.69.78"
        }
    ],
    "trainings": [
        ("Integrated Pest Management (IPM), 2023", "Caritas Nepal"),
        ("Training of Trainers (ToT), 2024", "Youth for Community Transformation"),
        ("Arc GIS Training, 2023", "Technical Students' Association of Nepal, Lamjung Campus"),
        ("Vermicompost Preparation, 2022", "Youth for Sustainable Agriculture, Lamjung"),
        ("Biochar Preparation, 2022", "Youth for Sustainable Agriculture, Lamjung"),
        ("Data and Analytics Session on R Studio, 2022", "Technical Students' Association of Nepal, Lamjung"),
        ("Exhibitor - 5th Nepal Agritech International Expo, 2023", "Media Space Solutions Pvt. Ltd"),
        ("Virtual Technical Bootcamp, 2021", "Technical Students' Association of Nepal, Lamjung Campus")
    ],
    "volunteering": [
        ("World Food Forum, Chapter Nepal - Team Member (Gandaki)", "FAO (April 2024 - Present)"),
        ("Awareness 360 Fellowship - Youth & Agrifood Systems", "Awareness 360 (March 2024 - September 2024)"),
        ("Trainer - Off-Season Vegetable Cultivation & IPM", "Harihar Women Savings & Loan Co-op (April-May 2024)"),
        ("Facilitator - Social Justice & Environmental Sustainability", "World Social Forum (February 2024)"),
        ("Moral & Innovative Leadership Facilitator", "Global Peace Foundation (October 2023)")
    ],
    "referees": [
        {
            "name": "Dr. Arjun Kumar Shrestha",
            "title": "Professor & Dean, Faculty of Agriculture, AFU",
            "phone": "+977-9855052791",
            "email": "akshrestha@afu.edu.np"
        },
        {
            "name": "Saroj Adhikari",
            "title": "Senior Technical Officer, Horticulture Research Station, NARC",
            "phone": "+977-9856032191",
            "email": "Sarojadhikari977@gmail.com"
        },
        {
            "name": "Juntara Magar",
            "title": "Livelihoods Specialist / Thematic Lead, WWF Nepal",
            "phone": "+977-9868664685",
            "email": "juntara.budha@wwfnepal.org"
        }
    ]
}

# -------------------------------------------------------------------------
# 7. Streamlit Progressive Workflow State
# -------------------------------------------------------------------------
st.set_page_config(page_title="Sandesh Subedi - Application Matcher", layout="wide")

st.title("🌱 Sandesh Subedi | NGO/INGO Application Generator")

# Initialize Session State Variables
if "scanned_data" not in st.session_state:
    st.session_state.scanned_data = None
if "selected_position" not in st.session_state:
    st.session_state.selected_position = ""
if "generated_app_data" not in st.session_state:
    st.session_state.generated_app_data = None
if "cv_pdf_bytes" not in st.session_state:
    st.session_state.cv_pdf_bytes = None
if "cl_pdf_bytes" not in st.session_state:
    st.session_state.cl_pdf_bytes = None

raw_key = st.secrets.get("GROQ_API_KEY", None)
if not raw_key:
    raw_key = st.sidebar.text_input("Groq API Key (starts with gsk_):", type="password")

api_key = raw_key.strip().strip('"').strip("'") if raw_key else None

input_mode = st.radio(
    "Select Vacancy Input Format:",
    ["📝 Paste Job Description / Text", "🖼️ Upload Vacancy Image / Screenshot"],
    horizontal=True
)

vacancy_text = ""
uploaded_image_bytes = None

if "Paste" in input_mode:
    vacancy_text = st.text_area(
        "Paste Job Vacancy / TOR text here:",
        placeholder="Paste full job description, TOR, requirements, and application instructions here...",
        height=240
    )
else:
    up_file = st.file_uploader("Upload Vacancy Notice (JPG, PNG)", type=["jpg", "jpeg", "png"])
    if up_file:
        uploaded_image_bytes = up_file.getvalue()
        st.image(uploaded_image_bytes, caption="Uploaded Notice", use_container_width=True)

has_input = (bool(vacancy_text.strip()) if "Paste" in input_mode else uploaded_image_bytes is not None)

# -------------------------------------------------------------------------
# STAGE 1: SCAN NOTICE (Extracts Org, Positions, Email, & Requested Docs)
# -------------------------------------------------------------------------
if has_input and api_key:
    st.markdown("---")
    if st.button("🔍 Scan Notice", type="secondary"):
        with st.spinner("Scanning notice for positions, contact email, and requested documents..."):
            try:
                client = Groq(api_key=api_key)
                text_model, vision_model = get_groq_active_models(client)

                scan_prompt = """
                Scan this job announcement carefully and extract:
                1. The organization name.
                2. All distinct individual job vacancies/positions available.
                3. The exact application submission email address mentioned in the announcement (e.g. icdc.vacancy@gmail.com). If none found, return empty string.
                4. The specific list of documents requested by the employer for submission.
                   - If the announcement says something like "submit updated CV and a cover letter", return: ["Updated Curriculum Vitae (CV)", "Cover Letter"].
                   - Only add other documents (like citizenship, academic transcripts, work certificates, PP photos) if the announcement explicitly requests them.

                Return valid JSON only:
                {
                    "organization": "Organization Name",
                    "positions": ["Job Title 1", "Job Title 2"],
                    "submission_email": "example@email.com",
                    "requested_documents": ["Updated Curriculum Vitae (CV)", "Cover Letter"]
                }
                """

                if "Paste" in input_mode:
                    msgs = [
                        {"role": "system", "content": scan_prompt},
                        {"role": "user", "content": f"VACANCY TEXT:\n{vacancy_text}"}
                    ]
                    scan_model = text_model
                else:
                    scan_model = vision_model
                    b64_img = base64.b64encode(uploaded_image_bytes).decode("utf-8")
                    msgs = [
                        {"role": "system", "content": scan_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract organization, positions, application email, and requested documents in JSON:"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                            ]
                        }
                    ]

                res = client.chat.completions.create(
                    model=scan_model,
                    messages=msgs,
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                parsed_scan = json.loads(res.choices[0].message.content)
                st.session_state.scanned_data = parsed_scan
                positions = parsed_scan.get("positions", [])
                if positions:
                    st.session_state.selected_position = positions[0]
            except Exception as e:
                st.error(f"Scan error: {e}")

# -------------------------------------------------------------------------
# STAGE 2 & 3: DISPLAY FINDINGS, ALLOW CHOICE, GENERATE APPLICATION
# -------------------------------------------------------------------------
if st.session_state.scanned_data:
    org_name = st.session_state.scanned_data.get("organization", "Organization")
    positions = st.session_state.scanned_data.get("positions", [])
    sub_email = st.session_state.scanned_data.get("submission_email", "")
    req_docs = st.session_state.scanned_data.get("requested_documents", ["Updated Curriculum Vitae (CV)", "Cover Letter"])
    total_vacancies = len(positions)

    st.markdown("---")
    email_display = f" | 📧 **Send To:** `{sub_email}`" if sub_email else ""
    st.info(f"🏢 **Organization:** {org_name} | 📋 **Vacancies Found:** {total_vacancies}{email_display}")

    if total_vacancies > 1:
        chosen_pos = st.selectbox(
            "Select which vacancy you want to apply for:",
            options=positions,
            index=0
        )
        st.session_state.selected_position = chosen_pos
    elif total_vacancies == 1:
        st.session_state.selected_position = positions[0]
        st.write(f"🎯 **Target Position:** {positions[0]}")
    else:
        manual_pos = st.text_input("Enter Position Title:", value="Agriculture & Livelihoods Officer")
        st.session_state.selected_position = manual_pos

    target_role = st.session_state.selected_position

    # STAGE 3: Show Generate Application Button AFTER choosing
    if target_role:
        st.write("")
        if st.button(f"🚀 Generate Application for '{target_role}'", type="primary"):
            with st.spinner("Crafting complete evidence-based application for Sandesh Subedi in Calibri typography..."):
                try:
                    client = Groq(api_key=api_key)
                    text_model, vision_model = get_groq_active_models(client)

                    today_formatted = datetime.today().strftime("%B %d, %Y")
                    docs_json_str = json.dumps(req_docs)

                    full_prompt = f"""
                    You are a senior recruitment director and technical advisor for international and national NGOs in Nepal (UN agencies, FAO, WFP, USAID, FCDO, CARE, Save the Children, WWF, Plan International, Heifer).

                    Candidate: SANDESH SUBEDI (Phone: +977-9866009867, Email: Subedisandesh24@gmail.com, Address: Putalibazar-13, Syangja / Nepal).
                    Target Position: {target_role}
                    Organization: {org_name}
                    Today's Exact Date: {today_formatted}
                    Application Destination Email: {sub_email}
                    Specifically Requested Documents: {docs_json_str}

                    STRICT CANDIDATE PROFILE & RULES:
                    - Degree: Bachelor of Science in Agriculture (B.Sc. Agriculture) from IAAS Tribhuvan University, Lamjung (Merit Scholarship, Best Presentator Award). Ongoing Master of Science in Agriculture (M.Sc. Ag Horticulture, AFU Chitwan, 2025-Present, thesis combining AI & manual data collection on tomato yield).
                    - ABSOLUTE RULE: DO NOT INCLUDE ANY PERCENTAGE OR '%' SYMBOL ANYWHERE IN EDUCATION, COVER LETTER, OR EMAIL. Do not write '78.3%' or 'Percentage'. Simply mention B.Sc. Agriculture with Merit Scholarship.
                    - Verified Track Record:
                      1. Stromme Foundation (Chitwan, Nov-Jan):
                         Trainer: Hands-on participatory agricultural training covering nursery and soil management, horticulture, mushroom cultivation, apiculture, sericulture, post-harvest handling, agricultural marketing, and rural enterprise development.
                      2. Daayitwa NGO (Kaski, March-May):
                         Province Assistant: Growth Entrepreneurship and Employment Promotion (GEEP) program across Jaljala, Hupsekot, Badigad, Siranchok, and Myagde rural municipalities; enterprise development, grassroots stakeholder & local government coordination, field-level monitoring & documentation.
                      3. Shree Mahendra Secondary School (Bhalam, Kaski, Jan 2024-Dec 2024):
                         Agriculture Instructor: Crop cycle training, supervised 'Learn & Earn' program integrating production to market sales and profit distribution; served as focal point for the JICA Partnership Program coordinating agricultural activities and logframe alignment.
                      4. Horticulture Research Station, NARC (Malepatan, Kaski, June 2022-Dec 2022):
                         Research Assistant: Vegetable/fruit/ornamental varietal trials, guided JTAs in field data collection and trial protocols, trial planning, soil fertility management, and technical progress reporting.
                      5. District Statistics Office, Government of Nepal (Syangja, April 2022-June 2022):
                         Census Enumerator: National Census of Agriculture 2021/22, comprehensive household/farm survey on crop production, livestock, and land use; facilitated FGDs and KIIs; survey quality control.
                      6. Technical Tools: Arc-GIS, RStudio, GenStat, SPSS, Python (Image Detection/Classification), MS Office.

                    ========================================================================
                    SECTION A: EVIDENCE-BASED COVER LETTER (~1 TO 1.2 PAGES)
                    ========================================================================
                    - Tone: Professional, confident, sincere, human, development-oriented, and practical.
                    - Evidence-Based: SHOW real field achievements (GEEP enterprise promotion in 5 rural municipalities, JICA focal point, Learn & Earn, NARC trials, National Agriculture Census).
                    - 5-Paragraph Structure:
                      * Paragraph 1 (Opening): Exact position, organization, professional identity (Agriculture & Horticulture Specialist with proven background in rural enterprise, community mobilization, agricultural research, and value chain development), and specific alignment with project outcomes.
                      * Paragraph 2 (Enterprise & Program Coordination): Concrete achievements from Daayitwa NGO (GEEP program in 5 rural municipalities) and JICA focal point / Learn & Earn Program at Shree Mahendra School.
                      * Paragraph 3 (Training & Smallholder Empowerment): Practical grassroots training delivered with Stromme Foundation and Harihar Women Cooperative, emphasizing hands-on IPM, nursery management, and market linkages.
                      * Paragraph 4 (Research, Data & Technical Rigor): Solid analytical grounding from NARC Horticulture Research Station, National Agriculture Census, Arc-GIS, RStudio, and AI/smart agriculture research.
                      * Paragraph 5 (Closing): Concrete contribution, safeguarding commitment, humanitarian values, availability, and formal sign-off.
                    - Mandatory Opening: Start strictly with: "{today_formatted}\\n\\nHiring Committee\\n{org_name}\\n..."
                    - Mandatory Sign-off: Formally end with:
                      "Sincerely,\\nSandesh Subedi\\nPhone: +977-9866009867\\nEmail: Subedisandesh24@gmail.com\\nPutalibazar-13, Syangja / Nepal"

                    ========================================================================
                    SECTION B: INGO-TAILORED CV
                    ========================================================================
                    - Tagline: Strong scannable headline matching the vacancy.
                    - Summary: 3-4 impactful lines answering who you are, sectors, stakeholders, and outcomes. (Zero % mentions).
                    - Competencies: 8-12 prioritized competencies directly aligned to the JD.
                    - Tailored Experience: 4-5 substantive bullet points for each of the 5 authentic organizations.

                    ========================================================================
                    SECTION C: ADMINISTRATIVE GMAIL APPLICATION MESSAGE & ATTACHMENTS
                    ========================================================================
                    - Formal, clear, and administrative email body.
                    - Clearly state position and vacancy source.
                    - 1-2 sentence suitability statement highlighting B.Sc. Ag (Horticulture/Enterprise experience) and ongoing M.Sc.
                    - ATTACHMENT CHECKLIST RULE:
                      If the notice only asks for updated CV and cover letter, list ONLY:
                      1. Updated Curriculum Vitae (CV)
                      2. Cover Letter
                      If other documents (citizenship, transcripts, certificates, PP photo) were specifically requested in the vacancy, enlist those exact items as well. Do not add unrequested items.

                    CRITICAL INSTRUCTION: You MUST fill all JSON fields completely. DO NOT leave cover_letter or email_body empty or abbreviated.

                    Return valid JSON only matching this schema:
                    {{
                        "cv_professional_tagline": "Horticulture & Livelihoods Specialist | Value Chain Development | Rural Enterprise | MEAL",
                        "cv_professional_summary": "3-4 lines tailored professional summary without any percentage symbols...",
                        "cv_core_competencies": ["Competency 1", "Competency 2", "Competency 3", "Competency 4", "Competency 5", "Competency 6", "Competency 7", "Competency 8"],
                        "tailored_experience": [
                            {{
                                "organization": "Stromme Foundation",
                                "location": "Chitwan, Nepal",
                                "role": "Trainer",
                                "dates": "November - January",
                                "bullets": ["Detailed action-result bullet 1", "Detailed action-result bullet 2", "Detailed action-result bullet 3", "Detailed action-result bullet 4"]
                            }},
                            {{
                                "organization": "Daayitwa NGO",
                                "location": "Gandaki Province / Kaski, Nepal",
                                "role": "Province Assistant, GEEP Program",
                                "dates": "March - May",
                                "bullets": ["Detailed action-result bullet 1", "Detailed action-result bullet 2", "Detailed action-result bullet 3", "Detailed action-result bullet 4"]
                            }},
                            {{
                                "organization": "Shree Mahendra Secondary School",
                                "location": "Bhalam, Kaski, Nepal",
                                "role": "Agriculture Instructor & JICA Focal Point",
                                "dates": "January 2024 - December 2024",
                                "bullets": ["Detailed action-result bullet 1", "Detailed action-result bullet 2", "Detailed action-result bullet 3", "Detailed action-result bullet 4"]
                            }},
                            {{
                                "organization": "Horticulture Research Station, Nepal Agriculture Research Council (NARC)",
                                "location": "Malepatan, Kaski, Nepal",
                                "role": "Research Assistant",
                                "dates": "June 2022 - December 2022",
                                "bullets": ["Detailed action-result bullet 1", "Detailed action-result bullet 2", "Detailed action-result bullet 3", "Detailed action-result bullet 4"]
                            }},
                            {{
                                "organization": "District Statistics Office, Government of Nepal",
                                "location": "Syangja, Nepal",
                                "role": "Census Enumerator (National Census of Agriculture 2021/22)",
                                "dates": "April 2022 - June 2022",
                                "bullets": ["Detailed action-result bullet 1", "Detailed action-result bullet 2", "Detailed action-result bullet 3"]
                            }}
                        ],
                        "cover_letter": "{today_formatted}\\n\\nHiring Committee\\n{org_name}... (complete 5 substantive paragraphs)",
                        "email_subject": "Application for {target_role} - Sandesh Subedi",
                        "email_body": "Formal Gmail body text with correctly matched attachment checklist and contact details..."
                    }}
                    """

                    if "Paste" in input_mode:
                        exec_model = text_model
                        exec_msgs = [
                            {"role": "system", "content": full_prompt},
                            {"role": "user", "content": f"VACANCY TEXT:\n{vacancy_text}"}
                        ]
                    else:
                        exec_model = vision_model
                        b64_img = base64.b64encode(uploaded_image_bytes).decode("utf-8")
                        exec_msgs = [
                            {"role": "system", "content": full_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": f"Tailor application for {target_role} in JSON:"},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                                ]
                            }
                        ]

                    resp = client.chat.completions.create(
                        model=exec_model,
                        messages=exec_msgs,
                        response_format={"type": "json_object"},
                        max_tokens=4096,
                        temperature=0.2
                    )
                    data = json.loads(resp.choices[0].message.content.strip())

                    # Safe extraction for Cover Letter (guaranteed not blank & zero %)
                    cover_letter_val = ""
                    for k in ["cover_letter", "coverLetter", "letter", "application_letter", "cover_letter_body"]:
                        if data.get(k) and str(data[k]).strip():
                            cover_letter_val = str(data[k]).strip()
                            break

                    if not cover_letter_val or len(cover_letter_val) < 80:
                        cover_letter_val = get_fallback_cover_letter(target_role, org_name, today_formatted)

                    # Clean date placeholders & sanitize %
                    raw_cl = clean_text(cover_letter_val)
                    raw_cl = re.sub(r'\[\s*Date\s*\]', today_formatted, raw_cl, flags=re.IGNORECASE)
                    if not raw_cl.startswith(today_formatted):
                        raw_cl = f"{today_formatted}\n\n" + raw_cl
                    data["cover_letter"] = raw_cl

                    # Safe extraction for Email Subject & Body
                    email_body_val = ""
                    for k in ["email_body", "emailBody", "email", "email_text", "email_content", "body"]:
                        if data.get(k) and str(data[k]).strip():
                            email_body_val = str(data[k]).strip()
                            break

                    if not email_body_val or len(email_body_val) < 40:
                        email_body_val = get_fallback_email(target_role, org_name, req_docs)
                    data["email_body"] = clean_text(email_body_val)

                    email_sub_val = data.get("email_subject") or data.get("emailSubject") or f"Application for {target_role} - Sandesh Subedi"
                    data["email_subject"] = clean_text(email_sub_val)

                    avail_w = 210 - 16 - 16

                    # ---------------------------------------------------------
                    # BUILD INGO-STYLE FULL CV PDF (Calibri)
                    # ---------------------------------------------------------
                    cv_pdf = CompleteCVPDF(doc_type="CV")
                    cv_pdf.add_page()
                    cv_pdf.draw_cv_header()

                    # 1. Professional Identity Tagline
                    tagline = clean_text(data.get("cv_professional_tagline", "Horticulture & Livelihoods Specialist | Value Chain Development | Rural Enterprise | MEAL"))
                    cv_pdf.set_x(cv_pdf.l_margin)
                    cv_pdf.set_font(cv_pdf.font_family, "B", 10.5)
                    cv_pdf.set_text_color(0, 80, 160)
                    cv_pdf.cell(avail_w, 5, tagline, new_x="LMARGIN", new_y="NEXT")
                    cv_pdf.ln(1)

                    # 2. Tailored Professional Summary (Justified)
                    summary_text = clean_text(data.get("cv_professional_summary", ""))
                    cv_pdf.set_x(cv_pdf.l_margin)
                    cv_pdf.set_font(cv_pdf.font_family, "", 9.2)
                    cv_pdf.set_text_color(30, 30, 30)
                    cv_pdf.multi_cell(avail_w, 4.3, summary_text, align="J", new_x="LMARGIN", new_y="NEXT")
                    cv_pdf.ln(1.5)

                    # 3. Core Competencies Matrix
                    cv_pdf.draw_section_heading("Core Competencies")
                    competencies = data.get("cv_core_competencies", [])
                    if isinstance(competencies, list) and competencies:
                        col_w = avail_w / 2
                        for i in range(0, len(competencies), 2):
                            cv_pdf.set_x(cv_pdf.l_margin)
                            cv_pdf.set_font(cv_pdf.font_family, "", 9)
                            cv_pdf.set_text_color(35, 35, 35)
                            c1 = f"[x]  {clean_text(competencies[i])}"
                            cv_pdf.cell(col_w, 4.2, c1, align="L")
                            if i + 1 < len(competencies):
                                c2 = f"[x]  {clean_text(competencies[i+1])}"
                                cv_pdf.cell(col_w, 4.2, c2, align="L", new_x="LMARGIN", new_y="NEXT")
                            else:
                                cv_pdf.ln(4.2)
                        cv_pdf.ln(1)

                    # 4. Professional Experience (Responsibilities with Justified Alignment)
                    cv_pdf.draw_section_heading("Professional Experience")
                    for org in data.get("tailored_experience", []):
                        raw_bullets = org.get("bullets", [])
                        if raw_bullets:
                            cv_pdf.draw_org_block(
                                org.get("organization", ""),
                                org.get("location", ""),
                                org.get("role", ""),
                                org.get("dates", ""),
                                [clean_text(b) for b in raw_bullets]
                            )

                    # 5. Education (No Percentage)
                    cv_pdf.draw_section_heading("Education")
                    for edu in PERMANENT_CV_SECTIONS["education"]:
                        cv_pdf.draw_two_col_entry(edu["inst"], edu["deg"], edu["loc"], edu["yr"])
                        if edu.get("sub"):
                            cv_pdf.set_x(cv_pdf.l_margin)
                            cv_pdf.set_font(cv_pdf.font_family, "I", 8.8)
                            cv_pdf.set_text_color(60, 60, 60)
                            cv_pdf.multi_cell(avail_w, 3.8, f"  * {clean_text(edu['sub'])}", align="J", new_x="LMARGIN", new_y="NEXT")
                            cv_pdf.ln(0.5)

                    # 6. Publications (Peer-Reviewed with Clickable DOIs)
                    cv_pdf.draw_section_heading("Peer-Reviewed Publications")
                    cv_pdf.set_font(cv_pdf.font_family, "", 8.8)
                    for pub in PERMANENT_CV_SECTIONS["publications"]:
                        cv_pdf.set_x(cv_pdf.l_margin)
                        cv_pdf.set_text_color(30, 30, 30)
                        p_title = clean_text(pub["title"])
                        p_doi = pub.get("doi", "").strip()

                        if p_doi:
                            cv_pdf.multi_cell(avail_w, 4.0, f"- {p_title}", new_x="LMARGIN", new_y="NEXT")
                            cv_pdf.set_x(cv_pdf.l_margin + 3)
                            cv_pdf.set_text_color(0, 80, 200)
                            cv_pdf.cell(avail_w - 3, 3.8, p_doi, link=p_doi, new_x="LMARGIN", new_y="NEXT")
                        else:
                            cv_pdf.multi_cell(avail_w, 4.0, f"- {p_title}", new_x="LMARGIN", new_y="NEXT")
                        cv_pdf.ln(0.8)

                    # 7. Relevant Trainings & Workshops
                    cv_pdf.draw_section_heading("Trainings & Capacity Building")
                    for tr_title, tr_org in PERMANENT_CV_SECTIONS["trainings"]:
                        cv_pdf.draw_two_col_entry(tr_title, "", tr_org, "")

                    # 8. Volunteering, Fellowships & Community Action
                    cv_pdf.draw_section_heading("Fellowships & Community Leadership")
                    for vol_title, vol_org in PERMANENT_CV_SECTIONS["volunteering"]:
                        cv_pdf.draw_two_col_entry(vol_title, "", vol_org, "")

                    # 9. Technical Skills & Tools
                    cv_pdf.draw_section_heading("Technical Tools & Languages")
                    cv_pdf.set_x(cv_pdf.l_margin)
                    cv_pdf.set_font(cv_pdf.font_family, "B", 9)
                    cv_pdf.write(4.2, "Software & Analysis: ")
                    cv_pdf.set_font(cv_pdf.font_family, "", 9)
                    cv_pdf.write(4.2, "Arc-GIS, RStudio, GenStat, SPSS, Microsoft Office Suite, Kobo Toolbox\n")
                    cv_pdf.ln(1)

                    cv_pdf.set_x(cv_pdf.l_margin)
                    cv_pdf.set_font(cv_pdf.font_family, "B", 9)
                    cv_pdf.write(4.2, "Data Science & AI: ")
                    cv_pdf.set_font(cv_pdf.font_family, "", 9)
                    cv_pdf.write(4.2, "Python (Image Detection, Image Classification, Image Segmentation)\n")
                    cv_pdf.ln(1)

                    cv_pdf.set_x(cv_pdf.l_margin)
                    cv_pdf.set_font(cv_pdf.font_family, "B", 9)
                    cv_pdf.write(4.2, "Languages & Interpersonal: ")
                    cv_pdf.set_font(cv_pdf.font_family, "", 9)
                    cv_pdf.write(4.2, "Nepali (Native), English (Professional Proficiency) | Public Speaking, Training of Trainers (ToT), Mass Mobilization\n")
                    cv_pdf.ln(1)

                    # 10. Professional Referees
                    cv_pdf.draw_section_heading("Referees")
                    for ref in PERMANENT_CV_SECTIONS["referees"]:
                        cv_pdf.set_x(cv_pdf.l_margin)
                        cv_pdf.set_font(cv_pdf.font_family, "B", 9.2)
                        cv_pdf.cell(75, 4, clean_text(ref["name"]), align="L")
                        cv_pdf.set_font("Helvetica", "", 9)
                        cv_pdf.cell(avail_w - 75, 4, f"{clean_text(ref['phone'])} | {clean_text(ref['email'])}", align="R", new_x="LMARGIN", new_y="NEXT")
                        cv_pdf.set_x(cv_pdf.l_margin)
                        cv_pdf.set_font("Helvetica", "I", 8.8)
                        cv_pdf.cell(avail_w, 3.8, clean_text(ref["title"]), new_x="LMARGIN", new_y="NEXT")
                        cv_pdf.ln(1.5)

                    cv_buf = io.BytesIO()
                    cv_pdf.output(cv_buf)

                    # ---------------------------------------------------------
                    # BUILD EVIDENCE-BASED COVER LETTER PDF (Justified Alignment)
                    # ---------------------------------------------------------
                    cl_pdf = CompleteCVPDF(doc_type="Cover Letter")
                    cl_pdf.add_page()
                    cl_pdf.draw_cv_header()
                    cl_pdf.draw_section_heading(f"Application for {target_role}")

                    cl_pdf.set_x(cl_pdf.l_margin)
                    cl_pdf.set_font(cl_pdf.font_family, "", 9.5)
                    cl_pdf.set_text_color(30, 30, 30)
                    cl_pdf.multi_cell(avail_w, 4.7, clean_text(data["cover_letter"]), align="J", new_x="LMARGIN", new_y="NEXT")

                    cl_buf = io.BytesIO()
                    cl_pdf.output(cl_buf)

                    # Store state for persistent downloads
                    st.session_state.generated_app_data = data
                    st.session_state.cv_pdf_bytes = cv_buf.getvalue()
                    st.session_state.cl_pdf_bytes = cl_buf.getvalue()

                except Exception as e:
                    st.error(f"Generation error: {e}")

# -------------------------------------------------------------------------
# STAGE 4: DISPLAY CV, COVER LETTER, AND EMAIL WITH DOWNLOAD BUTTONS
# -------------------------------------------------------------------------
if st.session_state.generated_app_data is not None:
    data = st.session_state.generated_app_data
    current_target = st.session_state.selected_position
    sub_email = st.session_state.scanned_data.get("submission_email", "") if st.session_state.scanned_data else ""
    req_docs = st.session_state.scanned_data.get("requested_documents", ["Updated Curriculum Vitae (CV)", "Cover Letter"]) if st.session_state.scanned_data else ["Updated Curriculum Vitae (CV)", "Cover Letter"]

    st.markdown("---")
    st.success(f"Application ready for: **{current_target}**")

    tab_cv, tab_cl, tab_email = st.tabs(["CV", "Cover Letter", "Email"])

    with tab_cv:
        st.markdown(f"### {clean_text(data.get('cv_professional_tagline', ''))}")
        
        summary_txt = clean_text(data.get("cv_professional_summary", ""))
        st.markdown(f"<div style='text-align: justify; line-height: 1.6; margin-bottom: 15px;'>{summary_txt}</div>", unsafe_allow_html=True)

        st.markdown("#### Core Competencies")
        comps = data.get("cv_core_competencies", [])
        if comps:
            cols = st.columns(3)
            for idx, comp in enumerate(comps):
                cols[idx % 3].write(f"✔ {clean_text(comp)}")

        st.markdown("#### Professional Experience")
        for org in data.get("tailored_experience", []):
            with st.expander(f"📍 {clean_text(org.get('organization', ''))} - {clean_text(org.get('role', ''))}", expanded=True):
                for b in org.get("bullets", []):
                    # Responsibilities displayed with Justified Alignment
                    st.markdown(f"<div style='text-align: justify; margin-bottom: 6px;'>• {clean_text(b)}</div>", unsafe_allow_html=True)

        # Download button placed at the end of the CV tab
        st.write("")
        st.download_button(
            label="📥 Download CV (PDF)",
            data=st.session_state.cv_pdf_bytes,
            file_name=f"Sandesh_Subedi_CV_{current_target.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key="btn_download_cv"
        )

    with tab_cl:
        st.subheader("Cover Letter (Evidence-Based & JD Aligned)")
        cl_display_text = clean_text(data.get("cover_letter", ""))
        st.text_area("Cover Letter Text (Editable):", value=cl_display_text, height=460, key="cl_preview_area")

        # Download button placed at the end of the Cover Letter tab
        st.write("")
        st.download_button(
            label="📥 Download Cover Letter (PDF)",
            data=st.session_state.cl_pdf_bytes,
            file_name=f"Sandesh_Subedi_Cover_Letter_{current_target.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key="btn_download_cl"
        )

    with tab_email:
        st.subheader("Email Template (Formal & Administrative)")

        if sub_email:
            st.text_input("Send To (Recipient):", value=sub_email, key="email_to_recipient")

        email_sub = clean_text(data.get("email_subject", f"Application for {current_target} - Sandesh Subedi"))
        st.text_input("Subject Line:", value=email_sub, key="email_sub_input")

        email_msg = clean_text(data.get("email_body", ""))
        st.text_area("Email Body:", value=email_msg, height=350, key="email_body_area")

        # Dynamic checklist caption reflecting only what was requested
        docs_caption = ", ".join(req_docs)
        st.caption(f"📎 **Requested Attachments:** {docs_caption}")

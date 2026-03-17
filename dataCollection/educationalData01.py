import wikipediaapi
import os
import time
import re
import socket

# ==============================
# CONFIG
# ==============================

socket.setdefaulttimeout(10)

DATA_PATH = r"C:\Users\Sumer\Desktop\RAG_Based_Chatbot-ShikshyaSambad\data\consultant_data01"
os.makedirs(DATA_PATH, exist_ok=True)

REQUEST_DELAY = 3
MAX_RETRIES = 3

wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent="ShikshyaSambadBot/1.0 (Educational RAG Project)"
)

# ==============================
# COUNTRY LIST
# ==============================

countries = [
    "Nepal", "Bangladesh", "Pakistan", "United States", "Canada",
    "United Kingdom", "Australia", "Japan", "China", "South Korea",
    "India", "Spain", "Portugal", "Norway", "Denmark", "Italy",
    "Finland", "United Arab Emirates", "South Africa"
]

# ==============================
# GLOBAL CONSULTANT QUERIES
# ==============================


def generate_student_mobility_queries(country):

    return [
        f"Student visa requirements for {country}",
        f"Student visa process for {country}",
        f"Documents required for student visa in {country}",
        f"Admission requirements for international students in {country}",
        f"Scholarships for international students in {country}",
        f"Government scholarships in {country}",
        f"Top universities in {country} for international students",
        f"Tuition fees for international students in {country}",
        f"Cost of living in {country} for students",
        f"Part-time work for international students in {country}",
        f"Post-study work visa in {country}",
        f"Post-graduation work opportunities in {country}",
        f"Work permit after study in {country}",
        f"English language requirements for universities in {country}",
        f"Accommodation for international students in {country}",
        f"Health insurance requirements for students in {country}"
    ]

# ==============================
# BASE ACADEMIC QUERIES
# ==============================


def generate_academic_queries(country):

    academic_map = {

        "Nepal": [
            "Education in Nepal",
            "History of education in Nepal",
            "Literacy in Nepal",
            "Secondary education in Nepal",
            "Higher education in Nepal",
            "Tribhuvan University",
            "Kathmandu University",
            "National Examinations Board Nepal",
            "Institute of Engineering Nepal",
            "Scholarships for Nepali students abroad",
            "Nepal student visa process",
            "Cost of living in Nepal",
        ],
        "Bangladesh": [
            "Education in Bangladesh",
            "Higher education in Bangladesh",
            "University of Dhaka",
            "Bangladesh University of Engineering and Technology",
            "Literacy in Bangladesh",
            "Secondary education in Bangladesh",
            "Student visa from Bangladesh",
            "Scholarships for Bangladeshi students abroad",
            "Medical education in Bangladesh",
            "Engineering education in Bangladesh",
            "IELTS requirement for Bangladeshi students",
            "Cost of studying abroad for Bangladeshi students",
        ],
        "Pakistan": [
            "Education in Pakistan",
            "Higher education in Pakistan",
            "University of Karachi",
            "Lahore University of Management Sciences",
            "HEC Pakistan scholarships",
            "Student visa from Pakistan",
            "IELTS requirements for Pakistani students",
            "Medical education in Pakistan",
            "Engineering education in Pakistan",
            "Business schools in Pakistan",
            "Literacy in Pakistan",
            "Cost of studying abroad for Pakistani students",
        ],
        "United States": [
            "Education in the United States",
            "Higher education in the United States",
            "Ivy League",
            "Community colleges in the United States",
            "F visa",
            "SAT",
            "ACT (test)",
            "Test of English as a Foreign Language",
            "Optional Practical Training",
            "STEM education in the United States",
            "Medical school in the United States",
            "Engineering education in the United States",
            "Master of Business Administration",
        ],
        "Canada": [
            "Education in Canada",
            "Higher education in Canada",
            "University of Toronto",
            "University of British Columbia",
            "McGill University",
            "Post-Graduation Work Permit",
            "Medical education in Canada",
            "Engineering education in Canada",
            "Express Entry",
            "Cooperative education",
        ],
        "United Kingdom": [
            "Education in the United Kingdom",
            "Higher education in the United Kingdom",
            "University of Oxford",
            "University of Cambridge",
            "Russell Group",
            "UCAS",
            "International English Language Testing System",
            "Medical education in the United Kingdom",
            "Engineering education in the United Kingdom",
            "Business school",
        ],
        "Australia": [
            "Education in Australia",
            "Higher education in Australia",
            "Group of Eight (Australian universities)",
            "Australian National University",
            "University of Melbourne",
            "Medical education in Australia",
            "Vocational education and training in Australia",
        ],
        "Japan": [
            "Education in Japan",
            "Higher education in Japan",
            "University of Tokyo",
            "Kyoto University",
            "Osaka University",
            "Japanese Government Scholarship",
            "Japanese-Language Proficiency Test",
            "Engineering education in Japan",
            "Medical education in Japan",
        ],
        "China": [
            "Education in China",
            "Higher education in China",
            "Peking University",
            "Tsinghua University",
            "Fudan University",
            "Chinese Government Scholarship",
            "Hanyu Shuiping Kaoshi",
            "Medical education in China",
            "Engineering education in China",
            "Confucius Institute",
        ],
        "South Korea": [
            "Education in South Korea",
            "Higher education in South Korea",
            "Seoul National University",
            "Korea Advanced Institute of Science and Technology",
            "Yonsei University",
            "Global Korea Scholarship",
            "Test of Proficiency in Korean",
            "Engineering education in South Korea",
            "Medical education in South Korea",
        ],
        "India": [
            "Education in India",
            "Higher education in India",
            "Indian Institutes of Technology",
            "Indian Institutes of Management",
            "University of Delhi",
            "Joint Entrance Examination",
            "National Eligibility cum Entrance Test (Undergraduate)",
            "Medical education in India",
            "Engineering education in India",
            "Indian Council for Cultural Relations",
            "Literacy in India",
        ],
        "Spain": [
            "Education in Spain",
            "Higher education in Spain",
            "University of Barcelona",
            "Complutense University of Madrid",
            "Diplomas de Español como Lengua Extranjera",
            "Medical education in Spain",
            "Engineering education in Spain",
            "Erasmus programme",
        ],
        "Portugal": [
            "Education in Portugal",
            "Higher education in Portugal",
            "University of Lisbon",
            "University of Porto",
            "Medical education in Portugal",
            "Engineering education in Portugal",
            "Erasmus programme",
        ],
        "Norway": [
            "Education in Norway",
            "Higher education in Norway",
            "University of Oslo",
            "Norwegian University of Science and Technology",
            "Engineering education in Norway",
            "Medical education in Norway",
        ],
        "Denmark": [
            "Education in Denmark",
            "Higher education in Denmark",
            "University of Copenhagen",
            "Technical University of Denmark",
            "Engineering education in Denmark",
            "Medical education in Denmark",
        ],
        "Italy": [
            "Education in Italy",
            "Higher education in Italy",
            "University of Bologna",
            "Sapienza University of Rome",
            "Politecnico di Milano",
            "Medical education in Italy",
            "Engineering education in Italy",
            "Erasmus programme",
        ],
        "Finland": [
            "Education in Finland",
            "Higher education in Finland",
            "University of Helsinki",
            "Aalto University",
            "Engineering education in Finland",
            "Medical education in Finland",
        ],
        "United Arab Emirates": [
            "Education in the United Arab Emirates",
            "Higher education in the United Arab Emirates",
            "United Arab Emirates University",
            "American University of Sharjah",
            "University of Dubai",
            "Medical education in the United Arab Emirates",
            "Engineering education in the United Arab Emirates",
        ],
        "South Africa": [
            "Education in South Africa",
            "Higher education in South Africa",
            "University of Cape Town",
            "University of the Witwatersrand",
            "Stellenbosch University",
            "Medical education in South Africa",
            "Engineering education in South Africa",
            "National Student Financial Aid Scheme",
        ]


    }

    return academic_map.get(country, [
        f"Education in {country}",
        f"Higher education in {country}"
    ])

# ==============================
# MASTER QUERY GENERATOR
# ==============================


def generate_all_queries(country):

    academic = generate_academic_queries(country)
    mobility = generate_student_mobility_queries(country)

    return list(set(academic + mobility))

# ==============================
# CLEAN FILENAME
# ==============================


def clean_filename(text):
    return re.sub(r'[^\w\-_\. ]', '_', text)

# ==============================
# FETCH PAGE
# ==============================


def fetch_wikipedia_page(query):

    for attempt in range(MAX_RETRIES):

        try:
            page = wiki.page(query)

            if page.exists():
                return page

            # fallback search
            results = wiki.search(query)

            if results:
                alt_page = wiki.page(results[0])
                if alt_page.exists():
                    print(f"    ↪ Using fallback: {alt_page.title}")
                    return alt_page

        except Exception:
            print(f"Retry {attempt+1} -> {query}")
            time.sleep(2)

    return None

# ==============================
# SAVE PAGE
# ==============================


def save_page(country, query, page):

    safe_query = clean_filename(query.replace(" ", "_"))
    file_name = f"{country}_{safe_query}.txt"

    path = os.path.join(DATA_PATH, file_name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Title: {page.title}\n")
        f.write(f"Query: {query}\n")
        f.write(f"URL: {page.fullurl}\n")
        f.write("="*60+"\n\n")
        f.write(page.text)

# ==============================
# MAIN RUNNER
# ==============================


def run_collection():

    saved = 0
    skipped = 0

    for country in countries:

        queries = generate_all_queries(country)

        print(f"\n Collecting: {country} ({len(queries)} queries)")

        for query in queries:

            page = fetch_wikipedia_page(query)

            if page:
                save_page(country, query, page)
                print(f"{page.title}")
                saved += 1
            else:
                print(f"Skipped: {query}")
                skipped += 1

            time.sleep(REQUEST_DELAY)

    print("\n DONE")
    print(f"Saved: {saved}")
    print(f"Skipped: {skipped}")

# ==============================
# ENTRY
# ==============================


if __name__ == "__main__":
    run_collection()

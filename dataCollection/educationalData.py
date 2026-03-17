import wikipedia
import os
import time
import traceback

# 1. Configuration
wikipedia.set_lang("en")
data_path = r"C:\Users\Sumer\Desktop\RAG_Based_Chatbot-ShikshyaSambad\data\consultant_data"
if not os.path.exists(data_path):
    os.makedirs(data_path)

# 2. Country List
countries = [
    "Nepal", "Bangladesh", "Pakistan", "United States", "Canada", "United Kingdom",
    "Australia", "Japan", "China", "South Korea", "India", "Spain", "Portugal",
    "Norway", "Denmark", "Italy", "Finland", "United Arab Emirates", "South Africa"
]


# 3. Specialized Query Sets for Every Country
def generate_all_queries(country):
    queries_map = {
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
        ],
    }

    return queries_map.get(country, [
        f"Education in {country}",
        f"Higher education in {country}",
    ])


# 4. Smart Wikipedia fetcher with disambiguation fallback
def fetch_wikipedia_page(query):
    """
    Try to fetch a Wikipedia page. If disambiguation, pick the first valid option.
    Returns the page object or None.
    """
    try:
        # auto_suggest=False is more reliable
        page = wikipedia.page(query, auto_suggest=False)
        return page

    except wikipedia.exceptions.DisambiguationError as e:
        # Disambiguation: try the first suggested option
        if e.options:
            first_option = e.options[0]
            print(f"    ↪ Disambiguation: trying '{first_option}'")
            try:
                page = wikipedia.page(first_option, auto_suggest=False)
                return page
            except Exception:
                return None
        return None

    except wikipedia.exceptions.PageError:
        # Page genuinely doesn't exist, try with auto_suggest as fallback
        try:
            page = wikipedia.page(query, auto_suggest=True)
            return page
        except Exception:
            return None

    except Exception as e:
        # Unexpected error — log it so you can see what's going wrong
        print(f"Unexpected error for '{query}': {type(e).__name__}: {e}")
        return None


# 5. Execution Loop
saved_count = 0
skipped_count = 0

for country in countries:
    queries = generate_all_queries(country)
    print(f"\n Starting Deep-Dive for: {country} ({len(queries)} queries)")

    for query in queries:
        page = fetch_wikipedia_page(query)

        if page:
            safe_query = (
                query.replace(' ', '_')
                     .replace('(', '')
                     .replace(')', '')
                     .replace('/', '_')
                     .replace(':', '')
            )
            file_name = f"{country}_{safe_query}.txt"
            file_path = os.path.join(data_path, file_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Title: {page.title}\n")
                f.write(f"URL: {page.url}\n")
                f.write(f"Query: {query}\n")
                f.write("=" * 60 + "\n\n")
                f.write(page.content)

            print(f"Saved: {page.title}")
            saved_count += 1
        else:
            print(f"Skipped: {query}")
            skipped_count += 1

        time.sleep(1.5)

print(f"\n Global Consultant Database is ready!")
print(f" Saved: {saved_count} files")
print(f" Skipped: {skipped_count} queries")

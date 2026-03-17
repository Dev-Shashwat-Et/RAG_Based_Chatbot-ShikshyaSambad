import requests
from bs4 import BeautifulSoup
import time
import os
import json
import random
from urllib.parse import quote
import re
import hashlib
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings (optional, but cleans up output)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ==============================
# CONFIGURATION – EDIT THESE
# ==============================
DATA_PATH = r"C:\Users\Sumer\Desktop\RAG_Based_Chatbot-ShikshyaSambad\data\consultant_data02"
SERPAPI_API_KEY = "5d2196ca61fad95f66544fd7362ab18b04a364f1d811d167d064e205bcb78998"  # Optional

# ==============================
# SCRAPER CLASS
# ==============================


class StudyAbroadScraper:
    def __init__(self, data_path):
        self.data_path = data_path
        os.makedirs(data_path, exist_ok=True)

        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        self.request_delay = 3
        self.last_request_time = 0

    def _respect_rate_limit(self):
        """Ensure we don't overload servers."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

    def _get_headers(self):
        """Return random headers to mimic a real browser."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    # ------------------------------------------------------------
    # SEARCH METHOD 1: SerpAPI (if API key is provided)
    # ------------------------------------------------------------
    def search_serpapi(self, query, num_results=5):
        """Use SerpAPI to get clean search results."""
        if not SERPAPI_API_KEY:
            return []
        try:
            from serpapi import GoogleSearch
            params = {
                "q": query,
                "api_key": SERPAPI_API_KEY,
                "num": num_results,
                "hl": "en",
                "gl": "us"
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            urls = []
            for r in results.get("organic_results", []):
                link = r.get("link")
                if link:
                    urls.append(link)
            return urls[:num_results]
        except ImportError:
            print("SerpAPI not installed. Run: pip install google-search-results")
            return []
        except Exception as e:
            print(f"SerpAPI error: {e}")
            return []

    # ------------------------------------------------------------
    # SEARCH METHOD 2: Fallback Google scraping
    # ------------------------------------------------------------
    def search_google_fallback(self, query, num_results=5):
        """Scrape Google directly if SerpAPI fails or is unavailable."""
        search_url = f"https://www.google.com/search?q={quote(query)}&num={num_results}"
        self._respect_rate_limit()
        self.last_request_time = time.time()
        try:
            response = requests.get(
                search_url, headers=self._get_headers(), timeout=10)
            if response.status_code != 200:
                print(f"Google returned status {response.status_code}")
                return []
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href.startswith('/url?q='):
                    url = re.findall(r'/url\?q=([^&]+)', href)
                    if url:
                        cleaned = url[0].split('&')[0]
                        if cleaned.startswith('http'):
                            urls.append(cleaned)
                elif href.startswith('http') and not href.startswith('https://www.google.com'):
                    urls.append(href)
            # Deduplicate
            seen = set()
            unique_urls = []
            for u in urls:
                if u not in seen and not u.startswith('https://www.google.com'):
                    seen.add(u)
                    unique_urls.append(u)
            return unique_urls[:num_results]
        except Exception as e:
            print(f"Google search error: {e}")
            return []

    # ------------------------------------------------------------
    # Unified search method
    # ------------------------------------------------------------
    def search_google(self, query, num_results=5):
        """Use SerpAPI if available, otherwise fallback to direct scraping."""
        if SERPAPI_API_KEY:
            urls = self.search_serpapi(query, num_results)
            if urls:
                return urls
            else:
                print("SerpAPI returned no results, falling back to scraping.")
        return self.search_google_fallback(query, num_results)

    # ------------------------------------------------------------
    # Scrape page content
    # ------------------------------------------------------------
    def scrape_page_content(self, url):
        """Extract main content from a webpage, skipping non-HTML, with SSL bypass."""
        self._respect_rate_limit()
        self.last_request_time = time.time()
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=15,
                verify=False  # bypass SSL certificate errors
            )
            if response.status_code != 200:
                print(f"HTTP {response.status_code} for {url}")
                return None

            # Skip non-HTML content
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type and 'text/plain' not in content_type:
                print(
                    f"Skipping non-HTML/plain content: {content_type} for {url}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove noisy elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            text = soup.get_text()
            # Clean whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip()
                      for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return {
                'url': url,
                'title': soup.title.string if soup.title else 'No title',
                'content': text[:50000],  # limit to 50k chars
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    # ------------------------------------------------------------
    # Collect data for a country
    # ------------------------------------------------------------
    def collect_country_data(self, country, queries):
        """Loop through queries, search, scrape, and save results."""
        print(f"\n Collecting data for {country}")
        results = []
        for query in queries:
            print(f"Searching: {query[:80]}...")
            search_urls = self.search_google(f"{query} {country}")
            print(f"      Found {len(search_urls)} URLs")
            for url in search_urls[:3]:  # top 3 per query
                print(f"Scraping: {url[:80]}...")
                content = self.scrape_page_content(url)
                if content:
                    # Create a safe, consistent filename
                    safe_q = re.sub(r'[\\/*?:"<>|]', '', query)[:30]
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    filename = f"{country}_{safe_q}_{url_hash}.txt"
                    filepath = os.path.join(self.data_path, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {content['title']}\n")
                        f.write(f"URL: {content['url']}\n")
                        f.write(f"Query: {query}\n")
                        f.write(f"Country: {country}\n")
                        f.write(f"Date: {content['timestamp']}\n")
                        f.write("="*60 + "\n\n")
                        f.write(content['content'])
                    results.append({
                        'query': query,
                        'file': filename,
                        'content': content
                    })
            time.sleep(2)  # delay between queries
        print(f"Collected {len(results)} items for {country}")
        return results


# ==============================
# COMPREHENSIVE QUERIES PER COUNTRY
# ==============================
queries_by_country = {
    "Nepal": [
        "What documents are required for a Study Visa (academic program) in Nepal?",
        "What documents are required for a Study Visa (volunteer program) in Nepal?",
        "What documents are required for a Study Visa (teaching program) in Nepal?",
        "What is the minimum bank balance for Academic Programs in Nepal? (3000 USD for six months)",
        "What is the minimum bank balance for Non-Academic Programs in Nepal? (1500 USD for six months)",
        "Can I work on a Student Visa in Nepal? (No, paid or unpaid work is prohibited)",
        "Is a progress/academic report card mandatory for visa renewal in Nepal? (Yes)",
        "What is the visa fee for Study Visa (Teaching) in Nepal? (40 USD per month)",
        "What is the visa fee for Study Visa (Volunteer) in Nepal? (40 USD per month, free if recommended by Ministry)",
        "What happens to my Tourist Visa if I change to Study Visa in Nepal? (Tourist Visa gets cancelled)",
        "What is the visa fee for dependent children below 10 years in Nepal? (Free/Gratis visa)",
        "What are the tuition fees for undergraduate programs at Nepali universities? (INR 52.78 L first year at Kathmandu University)",
        "What are the tuition fees for postgraduate programs in Nepal? (INR 99,953 - 3,00,000 first year at Kathmandu University)",
        "What is the fee for MBA/PGDM programs in Nepal? (INR 3,00,000 first year)",
        "What is the fee for MS programs in Nepal? (INR 99,953 first year)",
        "What is the fee for B.E./B.Tech programs in Nepal? (INR 52,77,765 first year)",
        "What are the hostel fees at Nepali universities?",
        "What scholarships are available for studying in Nepal? (Limited data - mainly foreign study scholarships)",
        "Can I work in Nepal after completing my studies? (No, student visas do not permit work)"
    ],
    "India": [
        "What documents are required for a Student Visa to India from Nepal?",
        "Do I need an admission letter from a recognized Indian university/institute?",
        "What is the minimum bank balance required for India student visa? (AED 10,000 for 3 months for UAE residents; similar requirement likely for Nepal)",
        "Is a No Objection Certificate required for medical/paramedical courses in India?",
        "What is the application process for India student visa? (Apply online at indianvisaonline.gov.in)",
        "What is the Study in India Portal and do I need to register? (Mandatory, generate Unique ID for visa application)",
        "What are the tuition fees for international students in Indian universities? (Example: ₹65,000 per year for SAARC students at Ganpat University)",
        "How do tuition fees compare between government and private institutions in India?",
        "What is the Scholarship Programme for Diaspora Children (SPDC) for studying in India?",
        "Am I eligible for SPDC? (Parents must be registered in Indian Mission in Nepal for 2+ years; applicant must have studied in Nepal for classes XI-XII)",
        "What is the age requirement for SPDC? (17 to 21 years)",
        "What is the minimum marks required for SPDC? (60% aggregate in qualifying exam)",
        "What is the income ceiling for parents for SPDC? (Under USD 5,000 per month)",
        "How do I apply for SPDC? (Online at spdcindia.gov.in after securing admission)",
        "Can I apply through educational consultants in Nepal for SPDC? (No; Embassy does not accept applications through consultants)",
        "What is an Employment Visa for India?",
        "What is the minimum salary requirement for Employment Visa in India? (Rs. 16.25 lakhs per annum, except for specific categories like ethnic cooks, language teachers)",
        "Can I get an Employment Visa for voluntary work in India? (Yes, with honorarium up to Rs. 10,000 per month)"
    ],
    "China": [
        "What is the difference between X1 and X2 visas for China? (X1 for study >180 days)",
        "What documents are needed for an X1 visa to China?",
        "Do I need an Admission Letter from a Chinese institution? (Yes, original required)",
        "What is Form JW201/JW202 for China visa? (Visa Application for Study in China)",
        "What happens after I enter China on an X1 visa? (Apply for residence permit within 30 days)",
        "Is there a visa interview for China student visa? (Visa officers may interview applicants and collect fingerprints)",
        "Do I need to take any tests for China admission? (CSCA - Chinese Scholastic Competency Assessment for some universities)",
        "What are the tuition fees for international students in China? (Example: NUAA - CNY 23,900/year for engineering, CNY 22,900/year for business)",
        "What are the accommodation costs in China? (NUAA: CNY 4,000-14,000 per year depending on room type)",
        "What other fees should I budget for in China? (Residence permit: ~CNY 400, application fee: ~CNY 400)",
        "What is the Chinese Government Scholarship (Type A)? (Full tuition, accommodation, insurance, and living stipend of 2,500 RMB/month)",
        "How do I apply for the Chinese Government Scholarship? (Contact Chinese Embassy in Nepal and list NUAA as first choice with Agency Code 10287)",
        "What is the Jiangsu Government Scholarship? (Full tuition, accommodation, insurance, and 15,000 RMB/year stipend)",
        "What is the Nanjing Government Scholarship? (One-time 10,000 RMB)",
        "Are there university-specific scholarships in China? (NUAA Fly-High Scholarship: 100% tuition waiver for first year)",
        "Can scholarships be renewed in China? (Government scholarships renew annually based on academic performance)",
        "What are the post-graduation work opportunities in China? (Not detailed in search results; requires separate work visa application)"
    ],
    "USA": [
        "What are the F1 visa requirements for Nepali students?",
        "What is the SEVIS fee and how to pay it?",
        "What documents are needed for the US student visa interview?",
        "What is the financial proof requirement for US student visa?",
        "Can I work on an F1 visa in the USA? (On-campus, CPT, OPT)",
        "What is the visa application process for USA from Nepal?",
        "What are the average tuition fees for undergraduate programs in USA?",
        "What are the average tuition fees for graduate programs in USA?",
        "How much do community colleges cost in USA?",
        "What is the cost of living in USA for international students?",
        "What scholarships are available for Nepali students in USA?",
        "How to apply for Fulbright scholarships for Nepali students?",
        "Are there university-specific scholarships for international students in USA?",
        "What is the eligibility for need-based financial aid in USA?",
        "What is OPT (Optional Practical Training) in USA?",
        "How long is OPT valid for STEM graduates in USA?",
        "What is the H1B visa process for Nepali students?",
        "Can I apply for green card after studying in USA?"
    ],
    "UK": [
        "What are the UK student visa requirements for Nepali students?",
        "What is a CAS (Confirmation of Acceptance for Studies)?",
        "What is the financial requirement for UK student visa?",
        "Do I need to take IELTS for UK student visa?",
        "What is the visa application process for UK from Nepal?",
        "What are the tuition fees for undergraduate courses in UK?",
        "What are the tuition fees for postgraduate courses in UK?",
        "How much does it cost to live in UK as a student?",
        "What scholarships are available for Nepali students in UK?",
        "What is the Chevening Scholarship for Nepali students?",
        "Are there Commonwealth Scholarships for Nepali students?",
        "How to apply for GREAT scholarships for Nepal?",
        "What is the Graduate Route visa in UK?",
        "How long can I stay in UK after studies on Graduate Route?",
        "What are the requirements for Skilled Worker visa in UK?"
    ],
    "Canada": [
        "What are the Canada student visa requirements for Nepali students?",
        "What is a study permit and how to apply?",
        "What is the Guaranteed Investment Certificate (GIC) requirement?",
        "What documents are needed for Canada student visa?",
        "Can I work part-time on a study permit in Canada?",
        "What are the tuition fees for undergraduate programs in Canada?",
        "What are the tuition fees for graduate programs in Canada?",
        "What is the cost of living in Canada for international students?",
        "What scholarships are available for Nepali students in Canada?",
        "How to apply for Vanier Canada Graduate Scholarships?",
        "Are there university-specific scholarships in Canada?",
        "What is the Post-Graduation Work Permit (PGWP) in Canada?",
        "How long is PGWP valid for?",
        "What are the requirements for Canadian Permanent Residence after studies?"
    ],
    "Australia": [
        "What are the Australia student visa (subclass 500) requirements?",
        "What is the financial capacity requirement for Australia student visa?",
        "Do I need OSHC health insurance for Australia?",
        "What documents are needed for Australia student visa?",
        "Can I work in Australia on a student visa? (48 hours per fortnight)",
        "What are the tuition fees for undergraduate courses in Australia?",
        "What are the tuition fees for postgraduate courses in Australia?",
        "What is the cost of living in Australia for students?",
        "What scholarships are available for Nepali students in Australia?",
        "What is the Australia Awards Scholarship for Nepali students?",
        "Are there university-specific scholarships in Australia?",
        "What is the Temporary Graduate visa (subclass 485) in Australia?",
        "How long is the post-study work visa in Australia?",
        "What are the pathways to Permanent Residency in Australia?"
    ],
    "UAE": [
        "What are the UAE student visa requirements for Nepali students?",
        "Do I need a university admission letter for UAE student visa?",
        "What is the medical test requirement for UAE visa?",
        "Can I work part-time on a student visa in UAE?",
        "What are the tuition fees for universities in UAE?",
        "How much does it cost to live in Dubai/Abu Dhabi as a student?",
        "What scholarships are available for Nepali students in UAE?",
        "Are there university-specific scholarships in UAE?",
        "Can I work in UAE after graduation?",
        "What is the job market like for fresh graduates in UAE?"
    ],
    "Japan": [
        "What are the Japan student visa requirements for Nepali students?",
        "Do I need to know Japanese for a student visa?",
        "What is the Certificate of Eligibility for Japan?",
        "What documents are needed for Japan student visa?",
        "What are the tuition fees for Japanese universities?",
        "What is the cost of living in Japan for students?",
        "What scholarships are available for Nepali students in Japan?",
        "What is the MEXT scholarship for Nepali students?",
        "How to apply for JASSO scholarships?",
        "Can I work in Japan after graduation?",
        "What is the job hunting visa in Japan?"
    ],
    "Korea": [
        "What are the South Korea student visa (D-2) requirements?",
        "Do I need TOPIK score for Korean student visa?",
        "What documents are needed for Korea student visa?",
        "Can I work part-time in Korea on a student visa?",
        "What are the tuition fees for Korean universities?",
        "What is the cost of living in Seoul for students?",
        "What scholarships are available for Nepali students in Korea?",
        "What is the Korean Government Scholarship Program (KGSP)?",
        "Are there university-specific scholarships in Korea?",
        "What is the D-10 job seeker visa in Korea?",
        "How to get a work visa in Korea after studies?"
    ],
    "Pakistan": [
        "What are the Pakistan student visa requirements for Nepali students?",
        "What documents are needed for Pakistan student visa?",
        "Do I need a No Objection Certificate from Pakistan?",
        "What are the tuition fees for Pakistani universities?",
        "What is the cost of living in Pakistan for students?",
        "What scholarships are available for Nepali students in Pakistan?",
        "Can I work in Pakistan after studies?"
    ],
    "Bangladesh": [
        "What are the Bangladesh student visa requirements for Nepali students?",
        "What documents are needed for Bangladesh student visa?",
        "What are the tuition fees for Bangladeshi universities?",
        "What is the cost of living in Bangladesh for students?",
        "What scholarships are available for Nepali students in Bangladesh?",
        "Can I work in Bangladesh after studies?"
    ],
    "Norway": [
        "What are the Norway student visa requirements for Nepali students?",
        "What is the financial requirement for Norway student visa?",
        "Do I need to pay tuition fees in Norway? (Public universities often free)",
        "What are the tuition fees at Norwegian universities?",
        "What is the cost of living in Norway?",
        "What scholarships are available for Nepali students in Norway?",
        "What is the Quota Scheme for developing countries?",
        "Can I stay in Norway after studies to look for work?"
    ],
    "Italy": [
        "What are the Italy student visa requirements for Nepali students?",
        "What is the pre-enrolment process through Universitaly?",
        "What documents are needed for Italy student visa?",
        "What are the tuition fees for Italian universities?",
        "What is the cost of living in Italy for students?",
        "What scholarships are available for Nepali students in Italy?",
        "What is the DSU scholarship for international students?",
        "What is the post-study work options in Italy?"
    ],
    "Spain": [
        "What are the Spain student visa requirements for Nepali students?",
        "Do I need health insurance for Spain student visa?",
        "What documents are needed for Spain student visa?",
        "What are the tuition fees for Spanish universities?",
        "What is the cost of living in Spain?",
        "What scholarships are available for Nepali students in Spain?",
        "What is the MAEC-AECID scholarship?",
        "Can I work in Spain after graduation?"
    ],
    "Portugal": [
        "What are the Portugal student visa requirements for Nepali students?",
        "What is the D4 visa for study in Portugal?",
        "What documents are needed for Portugal student visa?",
        "What are the tuition fees for Portuguese universities?",
        "What is the cost of living in Portugal?",
        "What scholarships are available for Nepali students in Portugal?",
        "What are the post-study work options in Portugal?"
    ],
    "Germany": [
        "What are the Germany student visa requirements for Nepali students?",
        "What is the blocked account requirement for Germany?",
        "Do I need APS certificate for Germany from Nepal?",
        "What documents are needed for Germany student visa?",
        "What are the tuition fees for German universities? (Public universities low fees)",
        "What is the cost of living in Germany?",
        "What scholarships are available for Nepali students in Germany?",
        "What is the DAAD scholarship for Nepali students?",
        "Are there university-specific scholarships in Germany?",
        "What is the 18-month residence permit for job search in Germany?",
        "How to get EU Blue Card after studies in Germany?"
    ],
    "Finland": [
        "What are the Finland student visa requirements for Nepali students?",
        "What is the financial requirement for Finland student visa?",
        "Do I need health insurance for Finland?",
        "What are the tuition fees for Finnish universities?",
        "What is the cost of living in Finland?",
        "What scholarships are available for Nepali students in Finland?",
        "What is the Finland Government Scholarship?",
        "Can I stay in Finland after studies to look for work?"
    ],
    "Singapore": [
        "What are the Singapore student visa requirements for Nepali students?",
        "What is the Student's Pass and how to apply?",
        "What documents are needed for Singapore student visa?",
        "What are the tuition fees for Singapore universities?",
        "What is the cost of living in Singapore?",
        "What scholarships are available for international students in Singapore?",
        "What is the ASEAN scholarship for Nepali students?",
        "What is the post-study work options in Singapore?"
    ],
    "South Africa": [
        "Best universities and colleges in South Africa",
        "Top ranked universities in South Africa for international students",
        "What are the South Africa student visa requirements for Nepali students?",
        "What documents are needed for South Africa study visa?",
        "Do I need a medical certificate for South Africa visa?",
        "What are the tuition fees for South African universities?",
        "What is the cost of living in South Africa for students?",
        "What scholarships are available for international students in South Africa?",
        "What is the Mandela Rhodes Scholarship for Nepali students?",
        "What is the post-study work permit in South Africa?",
        "Can I work in South Africa after graduation?"
    ]
}

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    scraper = StudyAbroadScraper(DATA_PATH)
    for country, queries in queries_by_country.items():
        scraper.collect_country_data(country, queries)
        time.sleep(5)  # extra pause between countries to be gentle
    print("\n Data collection complete!")

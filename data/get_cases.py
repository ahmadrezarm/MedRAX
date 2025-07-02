import requests
from bs4 import BeautifulSoup
import time
import json
from tqdm import tqdm
from frontier_neuro_topics_links import topic_links

def load_topic_links_from_raw_urls(raw_urls):
    topics = []
    for url in raw_urls:
        base = url.split("/research-topics/")[1]
        slug = base.split("/")[1] if "/" in base else base
        title = slug.replace("-", " ").title()
        # Extract specialty between "in" and "volume"/"collection"/"202x"
        words = slug.split("-")
        specialty = ""
        if "in" in words:
            in_idx = words.index("in")
            after = words[in_idx + 1:]
            for i, word in enumerate(after):
                if word in {"volume", "collection", "2020", "2021", "2022", "2023", "2024"}:
                    after = after[:i]
                    break
            specialty = " ".join(after).title()
        topics.append({"title": title, "url": url, "specialty": specialty})
    return topics


def get_response(url):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54"
    }
    return requests.get(url, headers=headers)



def get_papers_from_topic(topic_url):
    response = get_response(topic_url)
    soup = BeautifulSoup(response.text, "html.parser")

    papers = []
    for a in soup.find_all("a", {"role": "heading", "aria-level": "2"}):
        href = a.get("href")
        title = a.text.strip()
        if href and title:
            full_link = "https://www.frontiersin.org" + href
            papers.append({"title": title, "link": full_link})

    return papers

def main():
    all_results = []

    topics = load_topic_links_from_raw_urls(topic_links)
    for topic in tqdm(topics, desc="Processing topics"):
        print(f"Processing topic: {topic['title']}")
        papers = get_papers_from_topic(topic["url"])
        all_results.append({
            "topic": topic["title"],
            "url": topic["url"],
            "specialty": topic["specialty"],
            "papers": papers
        })
        time.sleep(1)

    with open('case_report_topics.json', 'w') as f:
        json.dump(topics, f, indent=2)

    with open('case_reports.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"Saved {len(all_results)} topics to case_reports.json")


if __name__ == "__main__":
    main()

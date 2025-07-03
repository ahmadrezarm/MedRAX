import requests
from bs4 import BeautifulSoup
import time
import json
from tqdm import tqdm
import re



def extract_detailed_paper_data(paper_url, specialty):

    response = requests.get(paper_url)
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else ""

    date_string = soup.find("meta", {"name": "citation_publication_date"})["content"]
    year = int(re.split(r"[-/]", date_string)[0])

    sections = {}
    for h2 in soup.find_all("h2"):
        heading = h2.text.strip()
        content = []
        for sibling in h2.find_next_siblings():
            if sibling.name == "h2":
                break
            if sibling.name == "p":
                content.append(sibling.text.strip())
        if content:
            sections[heading] = "\n".join(content)

    figures = []
    for figwrap in soup.select("div.FigureDesc"):
        # Try to get the image id
        heading = figwrap.find_previous("div", class_="Imageheaders")
        fig_id = heading.text.strip() if heading else ""

        # Get image URL from the <a> tag inside FigureDesc (first choice)
        image_link_tag = figwrap.find("a", href=True)
        if not image_link_tag:
            # Fallback: look for an <a> tag just before this FigureDesc block
            image_link_tag = figwrap.find_previous("a", href=True)

        img_url = ""
        if image_link_tag and image_link_tag["href"].startswith("http"):
            img_url = image_link_tag["href"]
        elif image_link_tag:
            # relative path -> prepend domain
            img_url = "https://www.frontiersin.org" + image_link_tag["href"]

        # Get caption content
        caption = figwrap.get_text(separator=" ", strip=True)

        # Parse subfigures
        subfigures = []
        if "(A)" in caption or "(B)" in caption:
            matches = re.findall(r"\(([A-Z])\)\s*([^()]+)", caption)
            for label, subcap in matches:
                subfigures.append({
                    "label": label,
                    "caption": subcap.strip()
                })

        figures.append({
            "id": fig_id,
            "caption": caption,
            "image_url": img_url,
            "subfigures": subfigures if subfigures else None
        })

    return {
        "title": title,
        "url": paper_url,
        "specialty": specialty,
        "year": year,
        "sections": sections,
        "figures": figures
    }


def process_case_report_json(input_path, output_path):
    with open(input_path, 'r') as f:
        data = json.load(f)

    results = []
    for topic in tqdm(data, desc="Processing topics"):
        specialty = topic.get("specialty", "")
        for paper in topic.get("papers", []):
            detailed = extract_detailed_paper_data(paper["link"], specialty)
            results.append(detailed)
            time.sleep(1)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    process_case_report_json("data/case_reports_links.json", "data/detailed_case_reports.json")
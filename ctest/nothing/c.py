"""
Kanji JSON ma english_meaning ra eng fields lai Hindi ma translate garera
nepali_meaning / nepali fields ko thau ma replace garne.

Usage:
    py translate_kanji_to_hindi.py input.json output.json
"""

import json
import sys
import requests
import re

API_KEY = "AIzaSyAN0L9vlPvbRLbmHMW53XdeNuWf74AiE8Q"  # yaha aafno API key rakhne
API_URL = "https://translation.googleapis.com/language/translate/v2"


def translate_batch(text_list, source_lang="en", target_lang="ja"):
    """List of texts euta API call ma translate garne"""
    if not text_list:
        return []

    params = {
        "q": text_list,
        "source": source_lang,
        "target": target_lang,
        "format": "text",
        "key": API_KEY,
    }

    response = requests.post(API_URL, data=params)

    if response.status_code != 200:
        raise Exception(f"Translation failed: {response.status_code} - {response.text}")

    result = response.json()
    return [t["translatedText"] for t in result["data"]["translations"]]


def collect_texts(entries):
    """english_meaning ra sabai example.eng haru collect garne, translate garna"""
    texts = []
    for entry in entries:
        texts.append(entry.get("english_meaning", ""))
        for ex in entry.get("examples", []):
            texts.append(ex.get("eng", ""))
    return texts


def apply_translations(entries, translations):
    """Translated text haru fera nepali_meaning / nepali fields ma halne"""
    idx = 0
    for entry in entries:
        entry["nepali_meaning"] = translations[idx]
        idx += 1
        for ex in entry.get("examples", []):
            ex["nepali"] = translations[idx]
            idx += 1
    return entries


def chunk_list(lst, size=100):
    """Google Translate API ma euta request ma dherai text pathauna, chunks ma tokrne
    (rate limit / payload size bhanda tarne ko lagi)"""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def main():
    if len(sys.argv) != 3:
        print("Usage: py translate_kanji_to_hindi.py input.json output.json")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Single object ho ki list ho, dubai handle garne
    entries = data if isinstance(data, list) else [data]

    texts = collect_texts(entries)

    all_translations = []
    for chunk in chunk_list(texts, 100):
        translated_chunk = translate_batch(chunk)
        all_translations.extend(translated_chunk)
        print(f"Translated {len(all_translations)}/{len(texts)} texts...")

    entries = apply_translations(entries, all_translations)

    result = entries if isinstance(data, list) else entries[0]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Done! Saved to {output_path}")


if __name__ == "__main__":
    main()
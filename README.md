# Sakura News (Yahoo! JAPAN RSS fetch)

Sakura Academy ko lagi Yahoo! JAPAN news RSS fetch garne sample. Ahile
sabैभन्दा simple stage: **RSS fetch matra**, translation/API pachi thapinchha.

## Run

```bash
python fetch_news_sample.py
```

Yesले Yahoo ko 5 category (top-picks, domestic, world, business, IT) bata
prati 5 headlines fetch garcha, terminal ma print garcha, ra
`output/news_sample.json` ma save garcha. Kunai API key/dependency chaidaina.

## Next steps (aaने)

- [ ] Japanese -> English translation (Google Translate API)
- [ ] JLPT level tagging / furigana
- [ ] GitHub Actions bata automatic schedule
- [ ] Sakura Academy frontend/Hostinger MySQL ma output push

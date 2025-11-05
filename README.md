# Topic Recurrence Prototype (Per-Restaurant)

By **Shishay Sium Araya** · MIT License

### Executive Summary
This prototype delivers a focused, end-to-end solution for detecting **recurrent themes in restaurant reviews**.  
It combines TF-IDF text representations with efficient clustering to surface the most common discussion topics customers raise about each venue.  
Designed for **clarity, speed, and reproducibility**, the pipeline can analyse a single restaurant or scale across multiple datasets, producing structured summaries that support evidence-based decision-making and customer insight analysis.

Extract **recurring topics** from user reviews for **one restaurant per run**.  
Fast, reproducible pipeline with clear topic labels.

> Prototype target date: 6 November 2025  
> Deliverables: repository, Report.

---

## 1) Overview

The pipeline finds **main themes** in Google Local Reviews for a single restaurant and can run in batch across many restaurants.

Core engine (`src/pipeline.py`):

- **TF-IDF** features (unigrams + bigrams)
- **MiniBatchKMeans** clustering
- **Automatic K** selection (tiny heuristic by corpus size)
- **Labels** from centroid top TF-IDF terms
- Robust TF-IDF defaults for tiny corpora (dynamic `min_df`, safe `max_df`)

Design goals: interpretability, speed, clean code, reproducibility.

---

## 2) Objectives

- Run **one restaurant per execution** (`--restaurant-id` flag).
- Produce human-readable **topic labels**.

---

## 3) Data

Small curated slice of **Google Local Reviews** (McAuley Lab, UCSD).  
Each line in a JSONL file is one review.

Minimum fields:

| Field          | Description               |
| :------------- | :------------------------ |
| `gPlusPlaceId` | Unique business ID        |
| `reviewText`   | Raw review text           |
| `rating`       | Numeric rating (optional) |
| `categories`   | Category list (optional)  |

### Example files (kept in repo)

```

data/
├─ restaurant_106603537575677448372_katzs_delicatessen.jsonl
├─ restaurant_112863106599855196547_amys_baking_company.jsonl
├─ restaurant_114850556776252373970_hopdoddy_burger_bar.jsonl
├─ restaurant_115691289199130168021_home_slice_pizza.jsonl
└─ restaurant_117304934396765704634_vips_gran_via.jsonl

```

 A compact catalog `data/restaurants_all.jsonl` (restaurant id, name, categories) can be built via `scripts/extract_categories.py`.

---

## 4) Project layout

```
Ansearch_first_Project/
├─ data/
│  ├─ restaurants_all.jsonl
│  ├─ restaurant_106603537575677448372_katzs_delicatessen.jsonl
│  ├─ restaurant_112863106599855196547_amys_baking_company.jsonl
│  ├─ restaurant_114850556776252373970_hopdoddy_burger_bar.jsonl
│  ├─ restaurant_115691289199130168021_home_slice_pizza.jsonl
│  └─ restaurant_117304934396765704634_vips_gran_via.jsonl
│
├─ output/
│  ├─ topics_106603537575677448372_katzs_delicatessen.json
│  ├─ topics_112863106599855196547_amys_baking_company.json
│  ├─ topics_114850556776252373970_hopdoddy_burger_bar.json
│  ├─ topics_115691289199130168021_home_slice_pizza.json
│  ├─ topics_117304934396765704634_vips_gran_via.json
│  └─ topic_summary.csv
│
├─ scripts/
│  ├─ extract_all_restaurants.py
│  ├─ flex_to_jsonl.py
│  ├─ resolve_place_names.py
│  ├─ summarize_outputs.py
│  └─ run_all_topics.sh
│
├─ src/
│  ├─ __init__.py
│  ├─ cli.py
│  ├─ loaders.py
│  └─ pipeline.py
│
├─ tests/
│  ├─ conftest.py
│  ├─ data_fixture.jsonl
│  ├─ test_basic.py
│  └─ test_resolve_place_names.py
│
├─ .env.example
├─ .gitignore
├─ LICENSE
├─ Makefile
├─ pyproject.toml
├─ pytest.ini
├─ README.md
└─ requirements.txt
````

---

## 4.1) Requirements

Before running the project, ensure the following tools and versions are installed:

| Requirement | Minimum Version | Purpose |
| :----------- | :--------------- | :-------- |
| **Python**   | 3.10+ (tested on 3.11) | Core runtime |
| **pip**      | 23+ | Python package manager |
| **virtualenv** or **venv** | — | Environment isolation |
| **make**     | 4.3+ | Automates build/test commands |
| **bash/zsh shell** | — | Runs `run_all_topics.sh` |
| **spaCy** + `en_core_web_sm` model | — | Tokenisation and stop-word filtering |
| **scikit-learn** | ≥ 1.2 | TF-IDF + MiniBatchKMeans |
| **pandas / numpy** | — | Data wrangling |
| **pytest** | — | Unit testing |

💡 *Tip:* All required packages are automatically installed via  
make deps or pip install -r requirements.txt.

---

## 5) Environment setup

### Quick start (recommended)

```bash
make deps
make env          # optional: creates .env if missing
````

### Manual

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
```

---

## 6) Running the pipeline

### Batch: all curated restaurants

```bash
make topics
make summary
```

### Single restaurant

```bash
python -m src.cli \
  --input data/restaurant_106603537575677448372_katzs_delicatessen.jsonl \
  --restaurant-id 106603537575677448372 \
  --id-col gPlusPlaceId \
  --text-col reviewText \
  --engine simple \
  --min-docs 2 \
  --topk 8 \
  --out output/topics_106603537575677448372_katzs_delicatessen.json
```
### Engine Explanation
The flag `--engine simple` refers to a TF-IDF (unigram + bigram) vectorisation step
combined with **MiniBatchKMeans** clustering, using an automatic K selection
heuristic.  
This design was chosen for its simplicity, transparency, and speed compared
with heavier topic-modelling methods such as LDA or BERTopic. It provides
interpretable clusters suitable for quick experimentation in limited time.
---

## 7) Output structure

Per-restaurant JSON:

```json
{
  "metadata": {
    "engine": "simple",
    "restaurant_id": "106603537575677448372",
    "language": "english",
    "n_docs": 392
  },
  "topics": [
    {
      "id": 0,
      "label": "sandwiches, sandwiches huge, awesome sandwiches",
      "top_terms": ["sandwiches","sandwiches huge","awesome sandwiches"],
      "size": 47
    }
  ]
}
```

Summary CSV (after `make summary`):

| restaurant_id         | name               | n_topics | top_1      | top_2 | top_3    |
| :-------------------- | :----------------- | :------- | :--------- | :---- | :------- |
| 106603537575677448372 | katzs_delicatessen | 7        | sandwiches | staff | pastrami |
| 115691289199130168021 | home_slice_pizza   | 7        | awesome    | great | night    |

### Reproducibility
All random components (TF-IDF shuffling and clustering initialisation) use
`random_state=42` to ensure deterministic results.  
The prototype was developed and tested on **Python 3.11**.
---

## 8) Testing & linting (automated)
Unit tests are provided under `tests/` to validate data-loading and name-resolution logic.

Run all tests with:
```bash
make test    # pytest (unit tests)
```

Expected:

```
.....            # tests
all checks passed
```


## 9) Automation, Design & Quality Framework

### 9.1 Automated workflow

| Target         | Description                                                    |
| :------------- | :------------------------------------------------------------- |
| `make deps`    | Create local `.venv`, install deps, download spaCy model.      |
| `make env`     | Create `.env` from `.env.example` if missing.                  |
| `make test`    | Run **pytest** (deprecation warnings silenced for clean logs). |
| `make topics`  | Generate topic clusters for all available restaurant JSONLs.   |
| `make summary` | Aggregate all outputs into `output/topic_summary.csv`.         |
| `make all`     | Run test → topics → summary.                      |

### 9.2 Core design principles & trade-offs

| Decision                    | Why                                         | Trade-off                           |
| :-------------------------- | :------------------------------------------ | :---------------------------------- |
| TF-IDF + MiniBatchKMeans    | Simple, fast, interpretable for short texts | Not probabilistic/overlapping       |
| Auto-K heuristic            | Adapts to dataset size w/out grid search    | Coarser than silhouette/grid search |
| Dynamic `min_df` / `max_df` | Safe for tiny corpora, avoids fit errors    | May retain some rare n-grams        |
| JSONL I/O                   | Stream-friendly, robust for large inputs    | Slightly larger disk footprint      |
| Makefile-driven QA          | One-command reproducibility                 | Requires a Unix-like shell          |

### Limitations
While the current prototype performs well on English-language data, a few
restaurants such as **VIPS Gran Vía** contain reviews in Spanish.  
Because the preprocessing pipeline assumes English tokenisation and
stop-word lists, topic labels in other languages may appear less consistent.
A future enhancement could include automatic language detection and
language-specific tokenisers or stop-word filters to improve multilingual
robustness.

---

## 10) License

Released under the **MIT License** (see `LICENSE`).

*Notes:* Outputs are intentionally committed under `output/` so results are visible without re-running the pipeline. The `.env.example` sets `PYTHONPATH=.` for smooth local imports.

The repository includes a compact summary of approximately 23 000 restaurant entries
in data/restaurants_all.jsonl, extracted and filtered from the original 3.1 million Google Local Reviews records.
This file contains high-level metadata only for efficient exploration.

Each line of restaurants_all.jsonl has the following structure:

```json
{
  "restaurant_id": "<gPlusPlaceId>",
  "name": "<display name>",
  "slug": "<slugified name>",
  "categories": ["Restaurant", "Deli", "Pizza"],
  "n_reviews": 245
} 
```


Five individual JSONL files are included in data/, each containing all reviews for a single restaurant.
These serve as the core demonstration set for topic extraction and testing.

Users with the complete Google Local Reviews dataset can rerun
scripts/extract_all_restaurants.py to generate new restaurant samples or extend analysis to other IDs.

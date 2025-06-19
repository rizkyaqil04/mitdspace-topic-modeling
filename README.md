# 📚 TopikAI - Scientific Publication Pipeline

TopikAI is a microservice-based system designed to scrape scientific publications, preprocess textual data, train topic modeling models using BERTopic, and expose monitoring metrics through Prometheus and Grafana.

---

## 📦 Features

* 🔍 **Scraping** scientific publications from MIT DSpace.
* 🧹 **Automated text preprocessing** of scraped data.
* 🧠 **Topic modeling** using BERTopic + SentenceTransformer.
* 🧪 **Experiment tracking and model management** using MLflow.
* 📊 **Monitoring** of training process and coherence score via Prometheus.
* 📈 **Metrics visualization** through Grafana.

---

## 🏗️ Architecture System


```mermaid
flowchart LR
    client(("User")) --> web["FastAPI Gateway"] & grafana["Grafana"]
    web --> scraper["Scraper"] & preprocessor["Preprocessor"] & trainer["Trainer"]
    trainer --> mlflow["MLflow"]
    grafana --> prometheus["Prometheus"]

     web:::service
     grafana:::service
     scraper:::service
     preprocessor:::service
     trainer:::service
     mlflow:::service
     prometheus:::service
    classDef service stroke:#333,stroke-width:1px
    style client stroke:#000000
```

---

## 🚀 Getting Started

### 🧰 Prerequisites

* Linux (tested on Ubuntu/Fedora/Arch)
* Docker & Docker Compose v2+
* Git

### 🔧 Installation

```bash
git clone https://github.com/rizkyaqil04/mitdspace-topic-modeling.git
cd mitdspace-topic-modeling
docker compose up --build -d
```

---

## 🗂️ Project Structure

```
.
├── services/
│   ├── web/               # API Gateway
│   ├── scraper/           # Scraper service
│   ├── preprocessor/      # Preprocessor service
│   ├── trainer/           # Topic model training service
│   └── monitoring/        # Prometheus exporter
├── data/
│   ├── raw/               # Scraped raw data
│   └── processed/         # Preprocessed & embedded data
├── runs/                  # Training results each training
└── docker-compose.yml     # Service orchestration
```

---

## ⚙️ API Endpoints

| Method | Endpoint      | Description                         | Body Required                             |
| ------ | ------------- | ----------------------------------- | ----------------------------------------- |
| POST   | `/scrape`     | Scrape publication data from DSpace | `{ title_per_page: int, max_pages: int }` |
| POST   | `/preprocess` | Preprocess scraped data             | `{ filename: string }`                    |
| POST   | `/train`      | Train BERTopic model                | None                                      |
| GET    | `/result`     | Retrieve training result            | None                                      |

> All endpoints are available through the API Gateway at `http://localhost:8000`

---

## 📊 Monitoring Stack

Prometheus and Grafana are deployed as separate services to monitor training metrics such as *coherence score* and *duration*. This stack can also be extended to observe scraping and preprocessing activities.

- **Prometheus** scrapes metrics from the `trainer` and other exporters.
- **Grafana** provides real-time dashboards for metric visualization.

Access the Grafana UI at: [http://localhost:3000](http://localhost:3000)  
Default login: `admin` / `admin`

### 🔌 Connecting Grafana to Prometheus

To start visualizing data, add Prometheus as a data source in Grafana:

1. Open [http://localhost:3000](http://localhost:3000) and log in.
2. Navigate to **Sidebar → Data Sources**.
3. Click **Add data source** and select **Prometheus**.
4. In the **URL** field, enter: `http://prometheus:9090`
5. Click **Save & test** to save and verify the connection.

Once connected, you can begin creating dashboards or importing existing ones to monitor system metrics.

---

## 📚 References

* [MIT DSpace](https://dspace.mit.edu/)
* [BERTopic Documentation](https://maartengr.github.io/BERTopic/)
* [Sentence Transformers](https://www.sbert.net/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Prometheus](https://prometheus.io/)
* [Grafana](https://grafana.com/)

---

## 📄 License

[MIT License](LICENSE) – feel free to use, modify, and contribute!

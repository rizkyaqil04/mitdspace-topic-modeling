# DSPACE_TITLES_TOPIC_MODELING

Using BERTopic for topic modeling of titles in dspace.mit.edu

---

## Daftar Isi
1. [Arsitektur Singkat](#arsitektur-singkat)
2. [Fitur Utama](#fitur-utama)
3. [Persiapan](#persiapan)
4. [Struktur Direktori](#struktur-direktori)
5. [Cara Menjalankan](#cara-menjalankan)
6. [Cara Menggunakan](#cara-menggunakan)

---

## Arsitektur Singkat
DSPACE_TITLES_TOPIC_MODELING menggunakan **BERTopic** untuk mengekstraksi topik dari judul penelitian yang diambil dari **dspace.mit.edu**. Model ini bekerja dengan workflow implementasi sebagai berikut:
1. **Pengumpulan dan Penyimpanan Data** 
   - Data dikumpulkan secara otomatis melalui web scraping menggunakan **Crawl4AI**, yang mengambil judul paper dari **dspace.mit.edu**.
   - Hasil scraping disimpan dalam **JSON file** di direktori `data/raw/`, memastikan data tetap ringan dan mudah diakses.
   - Pipeline dijalankan secara terjadwal menggunakan **Github Actions**, memungkinkan proses scraping terjadi pada interval waktu tertentu.

2. **Preprocessing dan Embedding**
   - Data diproses menggunakan **NLTK**, mencakup:
     - Case folding (mengubah semua teks menjadi huruf kecil).
     - Tokenisasi (memecah judul menjadi kata-kata).
     - Stopword removal dan stemming untuk menyederhanakan teks.
   - Teks yang telah diproses dikonversi ke dalam **word embeddings** menggunakan model **Sentence Transformer (all-MiniLM-L6-v2)** untuk menangkap makna semantik dari judul paper.
   - Embeddings yang dihasilkan disimpan dalam file **NumPy (`embeddings.npy`)** di direktori `data/processed/` untuk reuse tanpa perlu perhitungan ulang.

3. **Clustering dan Topic Modeling**
   - Untuk mengelompokkan judul paper ke dalam topik, digunakan metode **MiniBatchKMeans**, yang lebih ringan dibandingkan HDBSCAN.
   - Jumlah cluster ditentukan secara otomatis berdasarkan evaluasi model, dengan nilai awal **10 cluster**.
   - Setelah clustering, **Class-based TF-IDF (c-TFIDF)** digunakan untuk mengekstrak kata-kata yang paling mewakili setiap topik yang terbentuk.
   - Hasil akhir berupa daftar **topik dan kata-kata kunci** yang relevan dengan setiap kelompok paper.

4. **Pelatihan dan Evaluasi Model** (Bagian ini masih belum)
   - Model **BERTopic** dilatih menggunakan data yang telah diproses dalam batch kecil (~500 judul per batch) untuk menghemat memori.
   - **MLflow** digunakan untuk mencatat parameter, metrik evaluasi, dan menyimpan versi model yang dihasilkan.
   - Evaluasi dilakukan menggunakan **coherence score**, memastikan bahwa topik yang ditemukan memiliki kualitas yang baik dan relevan.

5. **Deployment dan API Development** (Bagian ini masih belum)
   - Model yang telah dilatih dikemas dalam **Docker container** untuk memastikan kompatibilitas lintas lingkungan.
   - API dikembangkan menggunakan **FastAPI**, memungkinkan pengguna untuk menginput judul paper baru dan mendapatkan prediksi topik secara real-time.
   - Deployment dilakukan secara otomatis melalui **GitLab CI/CD**, memastikan model terbaru selalu tersedia di server produksi.

6. **Monitoring dan Maintenance** (Bagian ini masih belum)
   - Performa model dipantau menggunakan **ELK Stack (Elasticsearch, Logstash, Kibana)** untuk mendeteksi degradasi akibat perubahan pola data.
   - Jika kualitas model menurun, pipeline **CI/CD** akan memicu retraining otomatis, memastikan topik yang dihasilkan tetap relevan dengan tren penelitian terbaru.
   - **MiniBatchKMeans** memudahkan update model tanpa retraining penuh, sehingga model tetap ringan untuk dijalankan pada server dengan spesifikasi rendah.

---

## Fitur Utama
- **Ekstraksi otomatis** topik dari judul penelitian.
- **Modeling berbasis BERTopic**, yang mendukung clustering teks dengan embedding.
- **Visualisasi interaktif** hasil topik dengan plot dan dashboard.
- **Dukungan ekspor** hasil dalam format CSV dan JSON.

---

## Persiapan
### Prasyarat
Pastikan Anda telah menginstal **Python 3.8+** dan pustaka berikut:
```bash
pip install -r requirements.txt
```

Jika `requirements.txt` belum tersedia, pastikan pustaka berikut telah diinstal:
```bash
pip install aiofiles==24.1.0 
aiohappyeyeballs==2.4.6
aiohttp==3.11.12
aio...(daftar lengkap pustaka)...
umap-learn==0.5.7
urllib3==2.3.0
xxhash==3.5.0
yarl==1.18.3
zipp==3.21.0
```

---

## Struktur Direktori
```
DSPACE_TITLES_TOPIC_MODELING/
│-- data/
│   ├── processed/
│   │   ├── data_preprocessed.json
│   │   ├── embeddings.npy
│   │   ├── mit_preprocessed.json
│   │   ├── scholar_preprocessed.json
│   │   ├── sinta_preprocessed.json
│   ├── raw/
│   │   ├── mit_scraped.json
│   │   ├── mit_scraped_10k.json
│   │   ├── scholar_scraped.json
│   │   ├── sinta_scraped.json
│-- results/
│   ├── topics.json
│-- src/
│   ├── preprocessing/
│   │   ├── preprocessing.py
│   ├── scraping/
│   │   ├── mit_scraping.py
│   │   ├── scholar_scraping.py
│   │   ├── sinta_scraping.py
│   ├── testing/
│   │   ├── test_classify.py
│   ├── training/
│   │   ├── bert-kmeans.py
│   │   ├── bert.py
│-- .gitignore
│-- README.md
│-- main.py
│-- requirements.txt
```

---

## Cara Menjalankan
1. **Persiapkan dataset**: Pastikan file yang diperlukan tersedia di dalam folder `data/`.
2. **Jalankan preprocessing**:
   ```bash
   python src/preprocessing/preprocessing.py
   ```
3. **Jalankan scraping**:
   ```bash
   python src/scraping/mit_scraping.py
   python src/scraping/scholar_scraping.py
   python src/scraping/sinta_scraping.py
   ```
4. **Latih model BERTopic**:
   ```bash
   python src/training/bert-kmeans.py
   ```
5. **Testing**:
   ```bash
   python src/testing/test_classify.py
   ```
6. **Visualisasi hasil**:
   ```bash
   python src/visualize.py
   ```

---

## Cara Menggunakan
- Jika ingin melihat ringkasan topik yang ditemukan:
  ```python
  from bertopic import BERTopic
  import pickle

  with open("results/topics.json", "rb") as file:
      topic_model = pickle.load(file)

  print(topic_model.get_topic_info())
  ```
- Untuk mencari topik dari judul baru:
  ```python
  new_titles = ["Deep Learning for Autonomous Vehicles"]
  topics, probs = topic_model.transform(new_titles)
  print(topics)
  ```

# **Aurora QA Service**

A lightweight question-answering service that responds to natural-language questions about members, based on data retrieved from Aurora’s public `/messages` API.

The system exposes a single endpoint:

```
GET /ask?question=...
```

and returns an answer inferred from real member messages.

---

## **1. Goal**

This project implements a small QA system that can answer questions such as:

- *“When is Layla planning her trip to London?”*  
- *“How many cars does Vikram Desai have?”*  
- *“What are Amira’s favorite restaurants?”*

The service fetches member messages from Aurora’s public API:

```
https://november7-730026606190.europe-west1.run.app/messages
```

and uses rule-based logic to interpret the question, identify the relevant member, and infer an answer.

---

## **2. Features**

### ✔ Natural-language question endpoint  
```
GET /ask
```
Returns a JSON response:
```json
{ "answer": "…" }
```

### ✔ Robust member identification
The system can identify a member from the question using:
- full-name match  
- unique first-name match  
- heuristic fallback for ambiguous names  
- (bonus) fuzzy suggestion when the user asks for a name that doesn’t exist  
  > “I couldn’t find any member named *Amira*, but I did find *Amina Van Den Berg*…”

### ✔ Handles assignment’s example questions  
Implemented specialized logic for:
- **Car count** (“how many cars…”)
- **Trip timing** (“when is X planning their trip to Y…”)
- **Favorite restaurants**

### ✔ Debug endpoints  
```
/debug/messages_sample
/debug/member_names
```

Useful for inspecting the real API data.

---

## **3. Project Structure**

```
ml_qa_service/
│
├── main.py
├── requirements.txt
├── README.md
│
└── app/
    ├── api.py
    ├── data_client.py
    ├── models.py
    └── qa_engine.py
```

---

## **4. How to Run Locally**

### **1. Create virtual environment**
```bash
python -m venv .venv
```

Activate:

**Windows**
```bash
.venv\Scriptsctivate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

---

### **2. Install dependencies**
```bash
pip install -r requirements.txt
```

---

### **3. Start the server**
```bash
python main.py
```

Server runs at:

```
http://127.0.0.1:8000
```

---

### **4. Open Swagger UI**
Visit:

```
http://127.0.0.1:8000/docs
```

You can test `/ask`, `/health`, and the debug endpoints there.

---

## **5. Example Queries**

### **1. Car count**
**Question**:  
```
How many cars does Vikram Desai have?
```
**Answer (example)**  
```
Vikram Desai has 2 cars.
```

---

### **2. Trip planning**
**Question:**  
```
When is Layla planning her trip to London?
```
**Answer (example)**  
```
Layla is planning her trip to London around June 5th, 2025.
```

---

### **3. Favorite restaurants + fuzzy suggestion**
**Question:**  
```
What are Amira’s favorite restaurants?
```
If “Amira” does not exist but “Amina” does, answer becomes:

```
I couldn't find any member named Amira, but I did find Amina Van Den Berg.

Here is what their messages say:
Amina’s favorite restaurants are …
```

---

## **6. Design Notes (Bonus Goal #1)**

The system follows a simple, interpretable pipeline:

1. **Fetch Data**  
   - Retrieve raw JSON from Aurora’s `/messages` endpoint.
   - Convert it into internal `MemberMessage` objects.

2. **Member Resolution**  
   - Full-name substring match  
   - Unique first-name match  
   - Most-frequent-name tie-break  
   - Fuzzy fallback using `SequenceMatcher` (80% similarity threshold)  

3. **Question Type Classification**  
   A small rule-based classifier:
   - `"car_count"`
   - `"trip_when"`
   - `"favorite_restaurants"`
   - `"generic"`

4. **Answer Extraction**  
   Dedicated handlers parse:
   - numbers before “car(s)”
   - date-like expressions (`June 5th`, `06/05/2025`)
   - any messages mentioning “favorite restaurant(s)”

5. **Fallback**  
   If no specialized logic matches, return the most recent message from that member.

This design keeps the system easy to understand, extend, and debug.

---

## **7. Data Insights (Bonus Goal #2)**

While inspecting the dataset, a few observations emerged:

- **Member names vary in format**  
  Some are two words, some have middle names, some include hyphens or mixed casing.

- **Duplicate/ambiguous first names**  
  Example: Several members share first names like *Emily*, *John*, *Layla*.  
  → This required more careful first-name logic.

- **Message text is free-form**  
  - Some messages are complete sentences.  
  - Others are phrases or notes.  
  - Dates appear in multiple formats (`June 5`, `06/05/2025`).  

- **Not all members discuss cars / trips / restaurants**  
  Many questions cannot be answered from available messages — system handles this safely.

These insights helped determine which rules and fallbacks were necessary.

---

## **8. Limitations**

- Rule-based NLP, not a machine-learning model  
  → Handles the assignment examples but won’t understand complex phrasing.

- Trip logic assumes queries contain `"trip to <destination>"`  
  → Variations like “visiting London” may not match.

- Car detection relies on `"X car(s)"` patterns  
  → More subtle mentions (“my new Tesla”) are not covered.

- Fuzzy matching can suggest the wrong member if names are very close  
  → System clearly communicates when a suggestion is used.

- No chronological sorting of timestamps yet  
  → Uses message order from API as-is.

These trade-offs keep the design simple and aligned with the assignment scope.

---

## **9. Deployment (Optional)**

If deploying on Render or similar:

- **Build command:**  
  ```
  pip install -r requirements.txt
  ```

- **Start command:**  
  ```
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```

---

## **10. Submission Checklist**

✔ Public GitHub repository  
✔ Service deployed (optional)  
✔ README with design notes & data insights  
✔ Demonstration via Swagger UI or short video  

# **TechSpec: Sandbox для тестирования prompt \+ JSON Schema \+ pipeline анализа документов по возврату кауции (Poland “kaucja”)**

## **0\) Контекст и цель**

**Цель приложения:** локальная песочница (инструмент тестировщика/юриста) для:

1. загрузки набора документов по кейсу (PDF/DOC/DOCX, в т.ч. сканы),

2. прогонки OCR через **Mistral OCR** с сохранением всех артефактов (текст/таблицы/изображения),

3. формирования единого запроса к LLM по фиксированному формату \<BEGIN\_DOCUMENTS\>…,

4. получения **строго валидного JSON** по заданной **JSON Schema**,

5. визуализации результата \+ “gap list” (чего не хватает) \+ метрик (tokens, стоимость, тайминги),

6. управления версиями промптов (и связанной схемы).

**Ключевое ограничение (из вашего system prompt):** модель анализирует **только предоставленные документы** (OCR → Markdown) и **не использует веб / инструменты**.

---

## **1\) Область (Scope)**

### **1.1 In-scope (MVP)**

* UI на **Gradio**:

  * загрузка нескольких файлов,

  * выбор провайдера/модели/параметров,

  * выбор версии промпта,

  * запуск пайплайна,

  * просмотр:

    * человекочитаемого результата,

    * сырого JSON,

    * списка “что запросить у пользователя”,

    * метрик (tokens/стоимость/тайминги),

    * истории прогонов (run history).

* OCR:

  * Mistral OCR (через API),

  * сохранение артефактов: извлечённый Markdown, таблицы (отдельные файлы), изображения (из OCR и/или рендер страниц при плохом качестве).

* LLM:

  * **OpenAI**: GPT‑5.1 и GPT‑5.2; параметр reasoning effort: auto|low|medium|high (в UI).

  * **Google**: Gemini 3.1 Pro, Gemini 3.1 Flash (точные идентификаторы фиксируются в конфиге).

* Хранилище:

  * SQLite (метаданные),

  * файловая структура для артефактов,

  * session\_id/run\_id,

  * сохранение параметров, артефактов, итогового JSON, usage/стоимости/таймингов, статуса/ошибок.

* Валидация:

  * проверка JSON на соответствие JSON Schema,

  * фиксация ошибок в UI и базе.

### **1.2 Out-of-scope (пока)**

* Многошаговые агентные циклы, RAG, контекст-кэширование, распределённые очереди, аккаунтинг пользователей.

* Облачный деплой/мульти-тенантность/ACL.

* Автоматическое обновление тарифов провайдеров (в MVP — через конфиг).

---

## **2\) UX и пользовательские сценарии (Gradio)**

### **2.1 Основные экраны/блоки UI**

**A. Панель запуска (Run Config)**

* File upload (multiple): PDF/DOC/DOCX.

* Provider: OpenAI | Google.

* Model dropdown:

  * OpenAI: gpt-5.1, gpt-5.2 (строки должны совпадать с API).

  * Google: gemini-3.1-pro-preview, gemini-3.1-flash-preview (или актуальные, см. конфиг). 

* Reasoning/thinking:

  * OpenAI reasoning effort: auto/low/medium/high (auto \= “не передавать параметр, оставить дефолт модели”). В OpenAI Responses API это reasoning.effort. 

  * Google thinkingLevel (если нужно): auto/low/medium/high (реализовать как mapping на generationConfig.thinkingConfig.thinkingLevel). 

* Prompt set:

  * Prompt name (например kaucja\_gap\_analysis)

  * Version dropdown (v001, v002, …)

  * Просмотр текста system prompt (read-only) \+ кнопка “Edit / Save as new version” (локальный режим).

* OCR options:

  * table\_format: html|markdown|none (default: html чтобы таблицы сохранялись отдельно). 

  * include\_image\_base64: true|false (default true).

  * extract\_header/extract\_footer: false (default) (можно включить, если нужно).

* Run button: “Analyze”.

**B. Прогресс и логи**

* Прогресс-бар: OCR → LLM → финал.

* Поле “runtime log” (последние N строк), плюс ссылка на полный лог файла.

**C. Результаты**

* Human-readable view:

  * critical\_gaps\_summary (список),

  * next\_questions\_to\_user (до 10),

  * checklist таблица (item\_id, importance, status, confidence),

  * раскрываемые детали по item\_id (findings/quotes/requests).

* Raw JSON viewer (текст \+ кнопки Copy/Download).

* Метрики:

  * OCR: pages, OCR time, OCR cost (если считаем),

  * LLM: prompt/completion/total tokens (нормализованные), provider raw usage, LLM time, LLM cost,

  * Total time, Total cost.

**D. История прогонов**

* Фильтры: session\_id, provider, model, prompt\_version, дата.

* Выбор run\_id → загрузка результатов/артефактов.

* Кнопки: “Open artifacts folder”, “Export run bundle (zip)” (опционально).

### **2.2 UX сценарии**

1. **Новый прогон**

* Пользователь выбирает prompt version, загружает файлы, выбирает модель, жмёт Analyze.

* Видит прогресс, затем результат, raw JSON, gap list, метрики.

* При ошибке (OCR/LLM/JSON) видит понятное сообщение \+ технический stacktrace в раскрываемом блоке.

2. **Тюнинг промпта**

* Пользователь открывает текущий system prompt → редактирует → “Save as new version”.

* Версия появляется в dropdown.

* Повторяет прогон, сравнивает outputs и метрики.

3. **Сравнение моделей**

* Один и тот же набор документов прогоняется через GPT‑5.1 vs GPT‑5.2 vs Gemini 3.1 Pro/Flash.

* В истории видно: разница в gaps, валидации, стоимости, времени.

---

## **3\) Архитектура (модули и границы)**

### **3.1 Принципы**

* Модульность “как для будущего web-app”, без преждевременного масштабирования.

* “Детерминируемость” прогона: хранить все входы/артефакты/версии промпта/схемы.

### **3.2 Предлагаемая структура репозитория**

app/  
  \_\_init\_\_.py  
  config/  
    settings.py            \# pydantic-settings  
    providers.yaml         \# доступные модели, параметры, лимиты  
    pricing.yaml           \# тарифы (input/output) \+ дата обновления  
  prompts/  
    kaucja\_gap\_analysis/  
      v001/  
        system\_prompt.txt  
        schema.json  
        meta.yaml  
      v002/  
        ...  
  schemas/  
    kaucja\_gap\_analysis\_v001.json   \# копия/линк на prompts/.../schema.json (по выбору)  
  ocr\_client/  
    mistral\_ocr.py  
    quality.py  
  llm\_client/  
    base.py  
    openai\_client.py  
    gemini\_client.py  
    normalize\_usage.py  
    cost.py  
  pipeline/  
    orchestrator.py  
    pack\_documents.py  
    validate\_output.py  
  storage/  
    db.py                  \# SQLAlchemy/SQLite  
    models.py              \# ORM models  
    repo.py                \# CRUD  
    artifacts.py           \# файловая структура, записи файлов  
  ui/  
    gradio\_app.py  
    components.py  
    renderers.py  
  utils/  
    ids.py  
    timeit.py  
    errors.py  
    json.py  
    zip\_export.py  
tests/  
  ...  
---

## **4\) Данные и хранение**

### **4.1 Идентификаторы**

* **session\_id**: UUIDv4 (строка).

* **run\_id**: UUIDv4 (строка) — уникален для каждого запуска.

* **doc\_id**: строка фиксированной длины, например "0000001" … "0009999" (с leading zeros), уникальна внутри run\_id.

### **4.2 Файловая структура артефактов**

Корень: data/

data/  
  sessions/  
    \<session\_id\>/  
      runs/  
        \<run\_id\>/  
          run.json                    \# метаданные прогона (конфиг, статусы)  
          logs/  
            run.log  
          documents/  
            \<doc\_id\>/  
              original/  
                \<original\_filename\>  
              ocr/  
                raw\_response.json  
                combined.md  
                pages/  
                  0001.md  
                  0002.md  
                tables/  
                  tbl-0.html  
                  tbl-1.html  
                images/  
                  img-0.jpeg  
                  img-1.png  
                page\_renders/         \# только для “плохих” страниц (эвристики)  
                  0001.png  
                quality.json  
          llm/  
            request.txt               \# system+user (опционально разделить)  
            response\_raw.txt  
            response\_parsed.json  
            validation.json

### **4.3 SQLite схема (минимальная)**

Таблицы:

**sessions**

* session\_id (PK)

* created\_at

**runs**

* run\_id (PK)

* session\_id (FK)

* created\_at

* provider (openai|google)

* model

* openai\_reasoning\_effort (auto|low|medium|high|null)

* gemini\_thinking\_level (auto|low|medium|high|null)

* prompt\_name

* prompt\_version

* schema\_version

* status (created|running|completed|failed)

* error\_code, error\_message (nullable)

* timings\_json (OCR/LLM/total) — JSON TEXT

* usage\_json (raw provider usage) — JSON TEXT

* usage\_normalized\_json (prompt\_tokens/completion\_tokens/total\_tokens) — JSON TEXT

* cost\_json (LLM, OCR, total \+ currency \+ pricing\_version) — JSON TEXT

* artifacts\_root\_path (строка)

**documents**

* id (PK int)

* run\_id (FK)

* doc\_id

* original\_filename

* original\_mime

* original\_path

* ocr\_status (pending|ok|failed)

* ocr\_model

* pages\_count

* ocr\_artifacts\_path

* ocr\_error (nullable)

**llm\_outputs**

* run\_id (PK/FK)

* response\_json\_path

* response\_valid (bool)

* schema\_validation\_errors\_path (nullable)

Примечание: большие тексты лучше держать в файловой системе, в SQLite — только пути.

---

## **5\) Интеграции**

## **5.1 OCR: Mistral OCR**

### **5.1.1 Вызов OCR**

Использовать официальный Python SDK mistralai и метод client.ocr.process (пример в документации). 

Рекомендуемые параметры (MVP):

* model="mistral-ocr-latest"

* table\_format="html" (таблицы отдельными артефактами; в markdown будут placeholders вида \[tbl-3.html\](tbl-3.html)) 

* include\_image\_base64=True (чтобы сохранять extracted images)

* (опционально) extract\_header/extract\_footer — выключено по умолчанию.

**Поддержка форматов:** в документации заявлена поддержка document\_url для pdf, pptx, docx и др. — это закрывает PDF/DOCX; для DOC можно конвертировать в DOCX/PDF через LibreOffice. 

### **5.1.2 Контракт ответа OCR (как сохраняем)**

Сохраняем:

* raw\_response.json — полный ответ OCR (как пришёл от API).

* per-page markdown: pages/\<page\_index\>.md

* combined.md — конкатенация страниц.

* таблицы: tables/tbl-\<n\>.html (или .md, если выбрано markdown).

* изображения: images/img-\<n\>.\<ext\> (декодировать base64 → файл).

* quality.json — наши эвристики качества.

В ответе OCR каждая страница содержит markdown, а также поля images, tables, hyperlinks, header/footer, dimensions и др. 

### **5.1.3 Page renders (фрагменты/изображения страниц при плохом OCR)**

**Требование:** хранить изображения/фрагменты страниц, если OCR “не смог корректно перевести в текст”.

В MVP: реализовать **эвристику “плохой страницы”**, например:

* len(markdown.strip()) \< N (N \~ 200\)

* доля “placeholder-only” контента слишком велика

* много символов replacement � или мусора

* слишком мало буквенных символов относительно длины

Если страница “плохая”:

* для PDF: рендерить страницу в PNG (через pymupdf или pdf2image) и сохранять в page\_renders/.

* для DOCX: если нет рендера — сохраняем только extracted images и сам оригинал.

---

## **5.2 LLM: OpenAI (GPT‑5.1, GPT‑5.2)**

### **5.2.1 API стиль**

Использовать **Responses API** (не ChatCompletions), т.к.:

* явная поддержка reasoning параметров,

* явная поддержка text.format для structured outputs.

### **5.2.2 System prompt**

Поскольку вы тестируете именно **system instruction**, передавать её как message с ролью system (или developer, но лучше system для прозрачности). В Responses API роли developer/system приоритетнее user. 

### **5.2.3 Reasoning effort**

В OpenAI Responses API: reasoning: { effort: ... }, поддерживаются значения low|medium|high (и другие), причём gpt-5.1 по документации defaults to none и поддерживает none|low|medium|high. 

**Требование UI:** auto|low|medium|high

* auto \= не передавать reasoning.effort (пусть будет дефолт модели).

* low|medium|high \= передавать строго.

### **5.2.4 Строгий JSON по JSON Schema**

В Responses API: text: { format: { type:"json\_schema", name:"...", schema:{...}, strict:true } } — это и есть enforcement schema. 

### **5.2.5 Usage**

OpenAI возвращает usage.input\_tokens, usage.output\_tokens, usage.total\_tokens. 

Для UI “prompt\_tokens/completion\_tokens”:

* prompt\_tokens \= input\_tokens

* completion\_tokens \= output\_tokens

* total\_tokens \= total\_tokens

Хранить:

* raw usage (как пришло),

* normalized usage (приведённый формат для UI).

### **5.2.6 Pricing / cost estimate**

Для MVP:

* храним тарифы в config/pricing.yaml (ручное обновление),

* считаем: cost \= input\_tokens \* price\_in \+ output\_tokens \* price\_out (обычно цены per 1M tokens).

Пример цен (на момент документа OpenAI Pricing): GPT‑5.2 и GPT‑5.1 имеют разные ставки. 

(В UI обязательно показывать дату/версию тарифа из конфига, чтобы юрист не воспринимал это как “онлайн-истину”.)

---

## **5.3 LLM: Google (Gemini 3.1 Pro / Flash)**

### **5.3.1 API/SDK**

Использовать **Google Gen AI SDK** (google-genai) и client.models.generate\_content. Документация SDK официально покрывает Gemini Developer API и Vertex AI. 

### **5.3.2 Модели и идентификаторы**

В документации “Gemini 3” встречаются:

* gemini-3.1-pro-preview

* gemini-3.1-flash-preview 

**Важно:** зафиксировать model IDs в config/providers.yaml и не “хардкодить” в коде.

### **5.3.3 System instruction**

Gemini API поддерживает system\_instruction / systemInstruction; в python SDK: types.GenerateContentConfig(system\_instruction="..."). 

### **5.3.4 Строгий JSON по JSON Schema**

Gemini structured outputs:

* response\_mime\_type \= "application/json"

* response\_json\_schema \= \<json schema\> 

В MVP: schema брать из выбранной версии prompt set (одна версия system prompt ↔ одна schema).

### **5.3.5 Usage / tokens**

В REST ответе Gemini есть usageMetadata с полями promptTokenCount, candidatesTokenCount, totalTokenCount, а также thoughtsTokenCount для thinking models. 

Нормализация для UI:

* prompt\_tokens \= usageMetadata.promptTokenCount

* completion\_tokens \= usageMetadata.candidatesTokenCount

* total\_tokens \= usageMetadata.totalTokenCount

Сохранять также thoughtsTokenCount как отдельную метрику (полезно при сравнении “reasoning/thinking”).

### **5.3.6 Pricing / cost estimate**

Gemini Developer API pricing отличается для Pro и Flash и включает разные ставки на input/output (per 1M tokens). 

Как и у OpenAI — хранить в pricing.yaml и показывать “pricing version date”.

---

## **5.4 Общий провайдерный интерфейс (для простого переключения)**

### **5.4.1 LLMClient контракт**

class LLMClient(Protocol):  
    def generate\_json(  
        self,  
        \*,  
        system\_prompt: str,  
        user\_content: str,  
        json\_schema: dict,  
        model: str,  
        params: dict,          \# reasoning/thinking/temp/max\_tokens  
        run\_meta: dict,        \# session\_id, run\_id, prompt\_version, etc.  
    ) \-\> LLMResult:            \# {raw\_text, parsed\_json, raw\_response, usage\_raw, usage\_norm, cost, timings}  
        ...

### **5.4.2 OCRClient контракт**

class OCRClient(Protocol):  
    def process\_document(  
        self,  
        \*,  
        input\_path: Path,  
        doc\_id: str,  
        options: OCROptions,  
        output\_dir: Path,  
    ) \-\> OCRResult:  \# {pages, combined\_markdown\_path, tables\_dir, images\_dir, raw\_response\_path, quality\_warnings}  
        ...  
---

## **6\) Pipeline (MVP orchestrator)**

### **6.1 Шаги пайплайна**

1. **Init run**

* Создать run\_id, определить artifacts\_root.

* Записать runs запись со статусом running.

2. **Ingest & OCR**

    Для каждого файла:

* сохранить оригинал,

* присвоить doc\_id,

* прогнать OCR,

* сохранить артефакты,

* записать documents запись (pages\_count, пути, статус).

3. **Pack documents**

* собрать user\_content строго в формате контракта:

  * \<BEGIN\_DOCUMENTS\>

  * \<DOC\_START id="0000001"\> \+ markdown

  * \<DOC\_END\>

  * …

  * \<END\_DOCUMENTS\>

4. **LLM call**

* загрузить выбранную system\_prompt.txt и schema.json по prompt\_version,

* вызвать LLM client (OpenAI/Gemini) с enforced JSON schema,

* сохранить raw response, parsed JSON.

5. **Validation**

* проверить parsed JSON jsonschema-валидатором,

* дополнительно проверить “семантические инварианты” (см. ниже).

6. **Persist & finalize**

* записать usage/cost/timings,

* поставить статус completed или failed,

* показать в UI.

### **6.2 Семантические инварианты (доп. проверки поверх JSON schema)**

Потому что schema гарантирует синтаксис, но не “правильность”:

* checklist должен содержать **ровно 22** item\_id (все обязательные ids).

* item\_id уникальны.

* status ∈ {confirmed, missing, ambiguous, conflict}

* Для confirmed: findings не пустой, хотя бы один finding имеет doc\_id и quote.

* Для missing: request\_from\_user.ask непустой.

* next\_questions\_to\_user max 10\.

Эти проверки валидации хранить как validation.json (warnings/errors).

---

## **7\) Prompt management**

### **7.1 Версионирование**

**Единица версионирования \= PromptVersion**, включающая:

* system\_prompt.txt

* schema.json

* meta.yaml (created\_at, author, note, changelog)

Структура: prompts/\<prompt\_name\>/vNNN/...

### **7.2 UI операции**

* выбрать версию,

* “View” (показать system prompt и schema),

* “Edit system prompt” → “Save as new version”:

  * создать vNNN+1,

  * сохранить в файловую систему,

  * обновить dropdown.

* (опционально) “Edit schema” (только для power users) — перед сохранением валидировать JSON Schema (минимум: JSON parse \+ наличие корневого объекта).

---

## **8\) Метрики, тайминги, стоимость**

### **8.1 Тайминги**

* t\_ocr\_total\_ms

* t\_llm\_total\_ms

* t\_total\_ms

* (опционально) per-doc OCR time

### **8.2 Tokens/usage**

* OpenAI: input/output/total tokens. 

* Gemini: promptTokenCount/candidatesTokenCount/totalTokenCount \+ thoughtsTokenCount (если есть). 

### **8.3 Стоимость**

* llm\_cost\_usd

* ocr\_cost\_usd (если включено)

* total\_cost\_usd

**OCR pricing:** Mistral OCR 3 в материалах упоминается как \~$2 за 1000 страниц (в зависимости от контекста/условий) — в MVP зафиксировать в pricing.yaml как “ocr\_per\_page\_usd \= 0.002”. 

---

## **9\) Обработка ошибок (error taxonomy)**

### **9.1 Категории**

* FILE\_UNSUPPORTED — формат/файл не распознан.

* OCR\_API\_ERROR — HTTP/timeout/quota.

* OCR\_PARSE\_ERROR — неожиданный формат ответа.

* LLM\_API\_ERROR — HTTP/timeout/quota.

* LLM\_INVALID\_JSON — JSON не парсится.

* LLM\_SCHEMA\_INVALID — JSON не проходит schema.

* CONTEXT\_TOO\_LARGE — превышение лимитов.

* STORAGE\_ERROR — SQLite locked / write fail / permission.

* UNKNOWN\_ERROR

### **9.2 UX при ошибках**

* Показывать:

  * краткое сообщение (для юриста),

  * “Details” (stacktrace \+ raw error payload),

  * ссылку на лог и artifacts folder.

### **9.3 Ретраи (MVP)**

* OCR: 1 retry на сетевые ошибки с экспоненциальной паузой.

* LLM: 1 retry на 429/5xx.

* Не ретраить на schema invalid (это логическая ошибка промпта/схемы).

---

## **10\) Безопасность и приватность (минимум для MVP)**

* Документы считаются **небезопасными** (prompt-injection). Реализуется на уровне **system prompt** \+ жёстко отключённые инструменты.

  * OpenAI: tools=\[\], tool\_choice="none" (чтобы модель не уходила в tool calls).

  * Gemini: не передавать tools (googleSearch/urlContext и т.п.).

* Хранение артефактов локально \= потенциально ПДн в сыром OCR. В TechSpec зафиксировать:

  * “данные могут содержать PESEL/IBAN/ID; хранение на диске \= ответственность пользователя”

  * опционально: “Delete run” в UI (удаляет папку \+ записи в SQLite) — полезно, но не обязательно.

---

## **11\) Definition of Done (DoD)**

MVP считается готовым, если:

1. Можно загрузить 2+ документа (PDF/DOCX), получить doc\_id на каждый и сохранить оригиналы.

2. OCR выполняется через Mistral OCR и сохраняет:

   * raw\_response.json,

   * combined.md,

   * tables/ и images/ при соответствующих опциях. 

3. Формируется user\_content строго в формате \<BEGIN\_DOCUMENTS\>...\<END\_DOCUMENTS\>.

4. OpenAI провайдер:

   * работает gpt-5.1 и gpt-5.2,

   * переключается reasoning effort,

   * enforced JSON schema через text.format strict. 

5. Google провайдер:

   * работает gemini-3.1-pro-preview и gemini-3.1-flash-preview (или актуальные IDs из конфига),

   * system\_instruction применяется,

   * enforced JSON schema через response\_mime\_type \+ response\_json\_schema. 

6. Ответ LLM валидируется jsonschema; ошибки показываются.

7. Метрики:

   * tokens (normalized),

   * стоимость по pricing.yaml,

   * тайминги OCR/LLM/total

      — отображаются в UI и сохраняются в SQLite. 

8. Есть история прогонов с возможностью открыть прошлый run.

---

# **12\) Контракты (Deliverable \#2)**

## **12.1 Контракт OCR-артефактов (внутренний формат приложения)**

### **OCRResult (логический объект)**

{  
  "doc\_id": "0000001",  
  "ocr\_model": "mistral-ocr-latest",  
  "pages\_count": 7,  
  "combined\_markdown\_path": "documents/0000001/ocr/combined.md",  
  "raw\_response\_path": "documents/0000001/ocr/raw\_response.json",  
  "tables\_dir": "documents/0000001/ocr/tables",  
  "images\_dir": "documents/0000001/ocr/images",  
  "page\_renders\_dir": "documents/0000001/ocr/page\_renders",  
  "quality": {  
    "warnings": \["..."\],  
    "bad\_pages": \[2,5\]  
  }  
}

### **Правила сохранения**

* combined.md — конкатенация pages\[i\].markdown (OCR output). 

* Если table\_format=html|markdown, OCR заменяет таблицы/картинки плейсхолдерами (\!\[img-0.jpeg\](img-0.jpeg), \[tbl-3.html\](tbl-3.html)), и реальные данные маппятся через поля images и tables. 

---

## **12.2 Контракт упаковки документов для LLM**

**Формат user content:**

\<BEGIN\_DOCUMENTS\>  
\<DOC\_START id="0000001"\>  
... markdown for doc 0000001 ...  
\<DOC\_END\>  
\<DOC\_START id="0000002"\>  
... markdown for doc 0000002 ...  
\<DOC\_END\>  
\<END\_DOCUMENTS\>

**Нормализация markdown перед упаковкой:**

* не удалять плейсхолдеры изображений/таблиц (они могут быть важными маркерами),

* по желанию добавить “страничные разделители”, например:

  * \\n\\n---\\n\\n\[PAGE 3\]\\n\\n между страницами,

* сохранить исходные строки (чтобы quotes в ответе могли быть verbatim).

---

## **12.3 JSON Schema ответа (версия v001)**

Ниже — базовая schema, согласованная с вашим system prompt. Она рассчитана на **строгий режим** (additionalProperties: false), и фиксирует enum’ы по статусам/важности/item\_id.

Важно: JSON Schema не гарантирует уникальность item\_id по массиву checklist. Это проверяется дополнительной семантической валидацией в коде.  
{  
  "$schema": "https://json-schema.org/draft/2020-12/schema",  
  "$id": "kaucja\_gap\_analysis\_v001",  
  "type": "object",  
  "additionalProperties": false,  
  "required": \[  
    "case\_facts",  
    "checklist",  
    "critical\_gaps\_summary",  
    "next\_questions\_to\_user",  
    "conflicts\_and\_red\_flags",  
    "ocr\_quality\_warnings"  
  \],  
  "properties": {  
    "case\_facts": {  
      "type": "object",  
      "additionalProperties": false,  
      "required": \[  
        "parties",  
        "property\_address",  
        "lease\_type",  
        "key\_dates",  
        "money",  
        "notes"  
      \],  
      "properties": {  
        "parties": {  
          "type": "object",  
          "description": "Факты о сторонах (tenant/landlord и т.п.). Каждое поле — объект Fact.",  
          "additionalProperties": { "$ref": "\#/$defs/fact" }  
        },  
        "property\_address": { "$ref": "\#/$defs/fact" },  
        "lease\_type": { "$ref": "\#/$defs/fact" },  
        "key\_dates": {  
          "type": "object",  
          "description": "Ключевые даты (подписание, начало, окончание, выезд, протокол и т.п.). Каждое поле — объект Fact.",  
          "additionalProperties": { "$ref": "\#/$defs/fact" }  
        },  
        "money": {  
          "type": "object",  
          "description": "Денежные параметры (kaucja, czynsz, удержания и т.п.). Каждое поле — объект Fact.",  
          "additionalProperties": { "$ref": "\#/$defs/fact" }  
        },  
        "notes": {  
          "type": "array",  
          "items": { "type": "string" }  
        }  
      }  
    },  
    "checklist": {  
      "type": "array",  
      "minItems": 1,  
      "items": { "$ref": "\#/$defs/checklist\_item" }  
    },  
    "critical\_gaps\_summary": {  
      "type": "array",  
      "items": { "type": "string" }  
    },  
    "next\_questions\_to\_user": {  
      "type": "array",  
      "maxItems": 10,  
      "items": { "type": "string" }  
    },  
    "conflicts\_and\_red\_flags": {  
      "type": "array",  
      "items": {  
        "type": "object",  
        "additionalProperties": false,  
        "required": \["type", "description", "related\_doc\_ids"\],  
        "properties": {  
          "type": { "type": "string", "enum": \["conflict", "red\_flag"\] },  
          "description": { "type": "string" },  
          "related\_doc\_ids": {  
            "type": "array",  
            "items": { "$ref": "\#/$defs/doc\_id" }  
          }  
        }  
      }  
    },  
    "ocr\_quality\_warnings": {  
      "type": "array",  
      "items": { "type": "string" }  
    }  
  },  
  "$defs": {  
    "doc\_id": {  
      "type": "string",  
      "pattern": "^\[0-9\]{7}$"  
    },  
    "fact\_source": {  
      "type": "object",  
      "additionalProperties": false,  
      "required": \["doc\_id", "quote"\],  
      "properties": {  
        "doc\_id": { "$ref": "\#/$defs/doc\_id" },  
        "quote": { "type": "string" }  
      }  
    },  
    "fact": {  
      "type": "object",  
      "additionalProperties": false,  
      "required": \["value", "status", "sources"\],  
      "properties": {  
        "value": {},  
        "status": {  
          "type": "string",  
          "enum": \["confirmed", "missing", "ambiguous", "conflict"\]  
        },  
        "sources": {  
          "type": "array",  
          "items": { "$ref": "\#/$defs/fact\_source" }  
        }  
      }  
    },  
    "finding": {  
      "type": "object",  
      "additionalProperties": false,  
      "required": \["doc\_id", "quote", "why\_this\_quote\_matters"\],  
      "properties": {  
        "doc\_id": { "$ref": "\#/$defs/doc\_id" },  
        "quote": { "type": "string", "maxLength": 400 },  
        "why\_this\_quote\_matters": { "type": "string" }  
      }  
    },  
    "request\_from\_user": {  
      "type": "object",  
      "additionalProperties": false,  
      "required": \["type", "ask", "examples"\],  
      "properties": {  
        "type": { "type": "string", "enum": \["upload\_document", "provide\_info"\] },  
        "ask": { "type": "string" },  
        "examples": { "type": "array", "items": { "type": "string" } }  
      }  
    },  
    "checklist\_item": {  
      "type": "object",  
      "additionalProperties": false,  
      "required": \[  
        "item\_id",  
        "importance",  
        "status",  
        "what\_it\_supports",  
        "findings",  
        "missing\_what\_exactly",  
        "request\_from\_user",  
        "confidence"  
      \],  
      "properties": {  
        "item\_id": {  
          "type": "string",  
          "enum": \[  
            "CONTRACT\_EXISTS",  
            "CONTRACT\_SIGNED\_AND\_DATED",  
            "PROPERTY\_ADDRESS\_CONFIRMED",  
            "LEASE\_TYPE\_CONFIRMED",  
            "KAUCJA\_CLAUSE\_PRESENT",  
            "KAUCJA\_AMOUNT\_STATED",  
            "KAUCJA\_PAYMENT\_PROOF",  
            "CZYNSZ\_AT\_DEPOSIT\_DATE",  
            "CZYNSZ\_AT\_RETURN\_DATE",  
            "MOVE\_IN\_PROTOCOL",  
            "MOVE\_OUT\_PROTOCOL",  
            "VACATE\_DATE\_PROOF",  
            "KEY\_HANDOVER\_PROOF",  
            "METER\_READINGS\_AT\_EXIT",  
            "UTILITIES\_SETTLEMENT",  
            "RENT\_AND\_FEES\_PAID",  
            "LANDLORD\_DEDUCTIONS\_EXPLAINED",  
            "PHOTOS\_VIDEOS\_CONDITION",  
            "PRECOURT\_DEMAND\_LETTER",  
            "DELIVERY\_PROOF",  
            "LANDLORD\_RESPONSE",  
            "TENANT\_BANK\_ACCOUNT\_FOR\_RETURN"  
          \]  
        },  
        "importance": { "type": "string", "enum": \["critical", "recommended"\] },  
        "status": { "type": "string", "enum": \["confirmed", "missing", "ambiguous", "conflict"\] },  
        "what\_it\_supports": { "type": "string" },  
        "findings": { "type": "array", "items": { "$ref": "\#/$defs/finding" } },  
        "missing\_what\_exactly": { "type": "string" },  
        "request\_from\_user": { "$ref": "\#/$defs/request\_from\_user" },  
        "confidence": { "type": "string", "enum": \["high", "medium", "low"\] }  
      }  
    }  
  }  
}  
---

# **13\) План реализации (Deliverable \#3)**

## **Итерация 0 — Скелет проекта \+ конфиг**

**Задачи**

* Создать структуру модулей, settings, providers.yaml, pricing.yaml.

* Базовые dataclasses/Pydantic модели для RunConfig, OCRResult, LLMResult.

* SQLite \+ миграции (или создание таблиц при старте).

**Приёмка**

* python \-m app.ui.gradio\_app поднимает пустой UI.

* Создаётся SQLite, таблицы есть, можно создать “пустой run” запись.

---

## **Итерация 1 — Storage \+ artifacts manager**

**Задачи**

* Реализовать storage/artifacts.py (создание директорий, запись файлов).

* Реализовать storage/repo.py (CRUD runs/documents).

* Логи per-run.

**Приёмка**

* При нажатии “Analyze” (без OCR/LLM) создаётся run\_id, папка, запись в DB.

---

## **Итерация 2 — Mistral OCR client \+ сохранение артефактов**

**Задачи**

* ocr\_client/mistral\_ocr.py: вызов client.ocr.process.

* Парсинг ответа: pages\[\], markdown, tables, images.

* Сохранение raw\_response.json, pages/\*.md, combined.md, tables/\*.html, images/\*.

* Эвристики качества \+ page\_renders для плохих страниц (PDF-only).

**Приёмка**

* На тестовом PDF создаются ожидаемые файлы.

* В UI отображается список doc\_id и путь к combined.md.

---

## **Итерация 3 — LLM clients (OpenAI \+ Gemini) \+ structured outputs**

**Задачи**

* OpenAI:

  * Реализовать вызов Responses API с reasoning.effort и text.format json\_schema strict.

  * Извлечь output JSON string, распарсить.

* Gemini:

  * Реализовать system\_instruction, response\_mime\_type=application/json, response\_json\_schema.

* normalize usage для обоих провайдеров.

* cost calculation по pricing.yaml.

**Приёмка**

* Можно прогнать фиктивный \<BEGIN\_DOCUMENTS\> и получить валидный JSON (хотя бы “hello schema”).

* В UI показываются токены и стоимость.

---

## **Итерация 4 — Pipeline orchestrator end-to-end**

**Задачи**

* pipeline/orchestrator.py: OCR всех документов → pack → LLM → validation → persist.

* pipeline/validate\_output.py: jsonschema \+ семантические инварианты.

* Статусы running/completed/failed.

**Приёмка**

* E2E прогон с 2 документами возвращает результат, сохраняется, отображается.

---

## **Итерация 5 — UI: результаты, история, просмотр промптов**

**Задачи**

* Рендер checklist в таблицу.

* Просмотр critical gaps \+ next questions.

* Raw JSON viewer.

* История прогонов, переключение run\_id.

**Приёмка**

* Юрист может без кода сравнить 2 прогона.

---

## **Итерация 6 — Prompt management UI (edit \+ save new version)**

**Задачи**

* Сканирование prompts/\<prompt\_name\>/vNNN.

* Editor system\_prompt → save as new version.

* (опционально) schema editor.

**Приёмка**

* Новая версия появляется в UI и используется в прогоне.

---

# **14\) Риски и улучшения (Deliverable \#4)**

## **14.1 Риск: контекст слишком большой**

**Симптом:** многостраничные договоры \+ переписка → не помещается в контекст модели.

**Митигации**

* MVP: pre-check размера (приблизительная оценка по длине текста) и ошибка CONTEXT\_TOO\_LARGE.

* Next step: “компрессия контекста”:

  * предварительная экстракция ключевых фрагментов (регулярками \+ heuristic),

  * двухпроходка: (1) извлечь факты, (2) gap analysis.

## **14.2 Риск: structured outputs / schema subset ограничения**

Gemini structured outputs поддерживает подмножество JSON Schema и может отвергать слишком глубокие/большие схемы; OpenAI strict также имеет ограничения. 

**Митигации**

* Держать schema “плоской” и избегать чрезмерных anyOf/$ref в MVP.

* Валидация schema перед запуском.

* В крайнем случае fallback: application/json без schema \+ post-валидация \+ repair call (опционально).

## **14.3 Риск: OCR качество на плохих сканах**

**Митигации**

* Рендер “плохих страниц” в page\_renders/ для ручной проверки.

* Добавить preprocessing (deskew/contrast) позже.

## **14.4 Риск: стоимость и тарифы “уплывают”**

**Митигации**

* pricing.yaml с updated\_at \+ показывать в UI.

* Возможность быстро редактировать тарифы.

---

Ниже — практичный “скелет”, который можно прямо положить в репозиторий: **форматы providers.yaml и pricing.yaml (с реальными значениями на сегодня)** \+ **псевдокод orchestrator’а** и **структура Gradio Blocks**, чтобы разработчик сразу начал писать.

---

## **1\)** 

## **config/providers.yaml**

##  **— реестр провайдеров/моделей/капабилити**

Идея: этот файл отвечает на вопросы UI и pipeline:

* какие провайдеры доступны,

* какие модели у них есть (строки model\_id — “истина”),

* какие параметры показывать (reasoning/thinking),

* какие ограничения (контекст/макс-вывод),

* где брать ключи (env vars),

* какие эндпоинты/клиенты использовать.

  ### **Предлагаемый формат (пример)**

  \# config/providers.yaml  
  version: 1  
  updated\_at: "2026-02-24"  
  defaults:  
    llm:  
      temperature: 0.0  
      max\_output\_tokens: 8000  
    ocr:  
      provider: "mistral"  
      model: "mistral-ocr-2512"  
    
  llm\_providers:  
    openai:  
      type: "openai"  
      base\_url: "https://api.openai.com/v1"  
      api\_key\_env: "OPENAI\_API\_KEY"  
    
      \# В MVP лучше фиксировать Responses API (единый интерфейс \+ structured outputs)  
      api\_mode: "responses"  
    
      \# app-level "auto" означает: параметр НЕ отправляем, пусть будет дефолт модели  
      ui:  
        reasoning\_effort\_values: \["auto", "low", "medium", "high"\]  
        show\_service\_tier: false   \# можно включить позже  
    
      default\_params:  
        temperature: 0.0  
        max\_output\_tokens: 8000  
        reasoning\_effort: "auto"  
        service\_tier: "auto"       \# OpenAI Responses API: auto/default/flex/priority (опционально)  
    
      models:  
        gpt-5.2:  
          id: "gpt-5.2"  
          display\_name: "GPT-5.2"  
          capabilities:  
            structured\_output\_json\_schema: true  
            reasoning\_effort\_supported: \["none", "low", "medium", "high", "xhigh"\]  
            images\_as\_input: true  
          limits:  
            context\_window\_tokens: 400000  
            max\_output\_tokens: 128000  
    
        gpt-5.1:  
          id: "gpt-5.1"  
          display\_name: "GPT-5.1"  
          capabilities:  
            structured\_output\_json\_schema: true  
            reasoning\_effort\_supported: \["none", "low", "medium", "high"\]  
            images\_as\_input: true  
          limits:  
            context\_window\_tokens: 400000  
            max\_output\_tokens: 128000  
    
    google:  
      type: "google\_genai"  
      \# MVP: Developer API (API key). Позже можно добавить vertex\_ai режим.  
      auth:  
        mode: "api\_key"  
        api\_key\_env: "GOOGLE\_API\_KEY"  
    
      ui:  
        \# у Gemini нет "reasoning effort" как у OpenAI; есть thinking/thoughts и др. механики.  
        \# Для MVP можно скрыть и оставить дефолт модели.  
        show\_thinking\_controls: false  
    
      default\_params:  
        temperature: 0.0  
        max\_output\_tokens: 8000  
    
      models:  
        gemini-3.1-pro-preview:  
          id: "gemini-3.1-pro-preview"  
          display\_name: "Gemini 3.1 Pro (Preview)"  
          capabilities:  
            structured\_output\_json\_schema: true  
            multimodal: true  
            thinking\_supported: true  
          limits:  
            context\_window\_in\_tokens: 1048576  
            context\_window\_out\_tokens: 65536  
    
        gemini-3-flash-preview:  
          id: "gemini-3-flash-preview"  
          display\_name: "Gemini 3 Flash (Preview)"  
          capabilities:  
            structured\_output\_json\_schema: true  
            multimodal: true  
            thinking\_supported: true  
          limits:  
            context\_window\_in\_tokens: 1048576  
            context\_window\_out\_tokens: 65536  
    
  ocr\_providers:  
    mistral:  
      type: "mistral"  
      base\_url: "https://api.mistral.ai/v1"  
      api\_key\_env: "MISTRAL\_API\_KEY"  
      models:  
        mistral-ocr-2512:  
          id: "mistral-ocr-2512"  
          display\_name: "Mistral OCR 3 (v25.12)"  
          output:  
            \# MVP: сохраняем markdown и артефакты; "html\_tables" зависит от реального ответа API  
            primary\_text\_format: "markdown"  
          capabilities:  
            returns\_images: true  
            returns\_tables: true  
            supports\_annotations: true

  ### **Почему именно такие model\_id**

* OpenAI: gpt-5.1, gpt-5.2, обе поддерживают structured outputs и reasoning effort (у 5.2 есть xhigh). 

* Google Gemini: для Gemini API актуальны gemini-3.1-pro-preview и gemini-3-flash-preview. 

* Mistral OCR 3: модель mistral-ocr-2512. 

  ---

  ## **2\)** 

  ## **config/pricing.yaml**

  ##  **— расчет стоимости (LLM \+ OCR)**

Задача файла: дать калькулятору “тарифную сетку”, отделенную от кода, с датой актуальности.

### **Предлагаемый формат (пример)**

\# config/pricing.yaml

version: 1

updated\_at: "2026-02-24"

currency: "USD"

llm:

  openai:

    \# OpenAI различает service tier (default/flex/priority) \+ cached input.

    \# В MVP можно считать только "standard" (= default), но структура позволяет расширить.

    service\_tiers:

      standard:

        unit: "per\_1m\_tokens"

        models:

          gpt-5.2:

            input: 1.75

            cached\_input: 0.175

            output: 14.00

          gpt-5.1:

            input: 1.25

            cached\_input: 0.125

            output: 10.00

      flex:

        unit: "per\_1m\_tokens"

        models:

          gpt-5.2:

            input: 0.875

            cached\_input: 0.0875

            output: 7.00

          gpt-5.1:

            input: 0.625

            cached\_input: 0.0625

            output: 5.00

      priority:

        unit: "per\_1m\_tokens"

        models:

          gpt-5.2:

            input: 3.50

            cached\_input: 0.35

            output: 28.00

          gpt-5.1:

            input: 2.50

            cached\_input: 0.25

            output: 20.00

  google:

    \# Gemini: у Pro цены зависят от длины промпта (\<=200k / \>200k).

    models:

      gemini-3.1-pro-preview:

        unit: "per\_1m\_tokens"

        prompt\_threshold\_tokens: 200000

        tiers:

          le\_threshold:

            input: 2.00

            output: 12.00   \# includes thinking tokens

            context\_caching: 0.20

          gt\_threshold:

            input: 4.00

            output: 18.00   \# includes thinking tokens

            context\_caching: 0.40

      gemini-3-flash-preview:

        unit: "per\_1m\_tokens"

        tiers:

          standard:

            input\_text\_image\_video: 0.50

            input\_audio: 1.00

            output: 3.00     \# includes thinking tokens

            context\_caching\_text\_image\_video: 0.05

            context\_caching\_audio: 0.10

ocr:

  mistral:

    \# OCR тарифицируется не токенами, а страницами.

    models:

      mistral-ocr-2512:

        unit: "per\_1000\_pages"

        price: 2.00

        batch\_discount\_multiplier: 0.50   \# если позже добавите batch OCR

### **Подтверждение цен (чтобы не гадать)**

* OpenAI (Standard/Flex/Priority по 1M токенов, включая cached input): 

* Gemini 3.1 Pro Preview: $2/$12 до 200k токенов, $4/$18 свыше 200k; “Output price (including thinking tokens)”. 

* Gemini 3 Flash Preview: $0.50 input (text/image/video), $3 output; “Output price (including thinking tokens)”. 

* Mistral OCR 3: $2 / 1000 pages (и batch скидка 50%). 

  ---

  ## **3\) Псевдокод orchestrator’а (pipeline) — максимально “пиши-код”**

Ниже — каркас, который совпадает с вашими модулями: ocr\_client, llm\_client, pipeline, storage, ui.

### **Типы данных (ориентир)**

\# src/pipeline/types.py

from \_\_future\_\_ import annotations

from dataclasses import dataclass

from typing import Any, Literal, Optional

ProviderName \= Literal\["openai", "google"\]

OcrProviderName \= Literal\["mistral"\]

@dataclass(frozen=True)

class RunConfig:

    session\_id: str

    provider: ProviderName

    model: str

    reasoning\_effort: Literal\["auto", "low", "medium", "high"\]

    prompt\_ref: str  \# e.g. "kaucja\_intake:v0003"

    max\_output\_tokens: int

    temperature: float

    service\_tier: Literal\["auto", "default", "flex", "priority"\]  \# OpenAI only, optional

@dataclass(frozen=True)

class UploadedFile:

    original\_name: str

    mime\_type: str

    local\_path: str  \# where Gradio saved the upload

@dataclass(frozen=True)

class OcrArtifactPaths:

    markdown\_path: str

    tables\_json\_path: Optional\[str\]

    images\_dir: Optional\[str\]

    raw\_response\_path: str

    page\_map\_json\_path: Optional\[str\]  \# mapping page \-\> artifacts

@dataclass(frozen=True)

class OcrDocument:

    doc\_id: str

    original\_name: str

    page\_count: Optional\[int\]

    artifacts: OcrArtifactPaths

    ocr\_warnings: list\[str\]

@dataclass(frozen=True)

class LlmUsage:

    prompt\_tokens: Optional\[int\]

    completion\_tokens: Optional\[int\]

    total\_tokens: Optional\[int\]

    \# optional breakdowns:

    cached\_prompt\_tokens: Optional\[int\]

    reasoning\_tokens: Optional\[int\]

@dataclass(frozen=True)

class RunMetrics:

    ocr\_ms: int

    llm\_ms: int

    total\_ms: int

    llm\_usage: Optional\[LlmUsage\]

    llm\_cost\_usd: Optional\[float\]

    ocr\_cost\_usd: Optional\[float\]

    total\_cost\_usd: Optional\[float\]

@dataclass(frozen=True)

class RunResult:

    run\_id: str

    session\_id: str

    docs: list\[OcrDocument\]

    packed\_documents: str

    llm\_raw\_text: str

    llm\_json: dict\[str, Any\] | None

    schema\_validation\_errors: list\[str\]

    metrics: RunMetrics

    status: Literal\["success", "partial\_success", "failed"\]

    errors: list\[str\]

### **Orchestrator (пошагово)**

\# src/pipeline/orchestrator.py

from \_\_future\_\_ import annotations

import json

import time

from pathlib import Path

from typing import Any

from pipeline.types import RunConfig, UploadedFile, RunResult, OcrDocument

from pipeline.document\_packer import pack\_documents

from pipeline.validation import validate\_against\_schema

from pipeline.costing import estimate\_costs

class Orchestrator:

    def \_\_init\_\_(self, \*, storage, prompts\_repo, ocr\_client, llm\_client, artifacts):

        self.storage \= storage

        self.prompts\_repo \= prompts\_repo

        self.ocr\_client \= ocr\_client

        self.llm\_client \= llm\_client

        self.artifacts \= artifacts

    def run(self, cfg: RunConfig, files: list\[UploadedFile\]) \-\> RunResult:

        run\_id \= self.storage.create\_run(cfg=cfg, files=files)

        errors: list\[str\] \= \[\]

        status: str \= "success"

        t\_total0 \= time.perf\_counter()

        \# 1\) OCR for each doc

        t\_ocr0 \= time.perf\_counter()

        ocr\_docs: list\[OcrDocument\] \= \[\]

        for idx, f in enumerate(files, start=1):

            doc\_id \= f"{idx:07d}"  \# stable formatting

            self.storage.create\_document(run\_id=run\_id, doc\_id=doc\_id, original\_name=f.original\_name)

            \# 1.1 persist original upload

            orig\_path \= self.artifacts.save\_original(run\_id, doc\_id, f.local\_path, f.original\_name)

            try:

                \# 1.2 OCR call (may return text \+ tables \+ images)

                ocr\_res \= self.ocr\_client.ocr(

                    input\_path=orig\_path,

                    doc\_id=doc\_id,

                    run\_id=run\_id,

                )

                \# 1.3 persist OCR artifacts

                paths \= self.artifacts.save\_ocr\_artifacts(run\_id, doc\_id, ocr\_res)

                \# 1.4 update DB

                self.storage.finish\_document\_ocr(

                    run\_id=run\_id,

                    doc\_id=doc\_id,

                    page\_count=ocr\_res.page\_count,

                    artifacts=paths,

                    warnings=ocr\_res.warnings,

                )

                ocr\_docs.append(

                    OcrDocument(

                        doc\_id=doc\_id,

                        original\_name=f.original\_name,

                        page\_count=ocr\_res.page\_count,

                        artifacts=paths,

                        ocr\_warnings=ocr\_res.warnings,

                    )

                )

            except Exception as e:

                \# стратегия MVP: не падать целиком, а пометить документ как failed и продолжить

                status \= "partial\_success"

                err \= f"OCR failed for doc\_id={doc\_id}: {type(e).\_\_name\_\_}: {e}"

                errors.append(err)

                self.storage.fail\_document\_ocr(run\_id=run\_id, doc\_id=doc\_id, error=err)

                continue

        t\_ocr1 \= time.perf\_counter()

        if not ocr\_docs:

            status \= "failed"

            self.storage.finish\_run\_failed(run\_id=run\_id, error="All documents failed OCR.")

            return self.storage.build\_run\_result(run\_id)

        \# 2\) Pack documents for LLM

        packed \= pack\_documents(ocr\_docs)  \# \<BEGIN\_DOCUMENTS\> ... \<DOC\_START id="..."\> ...

        packed\_path \= self.artifacts.save\_text(run\_id, "packed\_documents.txt", packed)

        \# 3\) Load prompt \+ schema

        system\_prompt, response\_schema \= self.prompts\_repo.load(cfg.prompt\_ref)

        self.artifacts.save\_text(run\_id, "system\_prompt.txt", system\_prompt)

        self.artifacts.save\_json(run\_id, "response\_schema.json", response\_schema)

        \# 4\) Call LLM (strict JSON)

        t\_llm0 \= time.perf\_counter()

        try:

            llm\_resp \= self.llm\_client.generate\_structured(

                provider=cfg.provider,

                model=cfg.model,

                system\_prompt=system\_prompt,

                user\_content=packed,

                json\_schema=response\_schema,

                reasoning\_effort=cfg.reasoning\_effort,

                temperature=cfg.temperature,

                max\_output\_tokens=cfg.max\_output\_tokens,

                service\_tier=cfg.service\_tier,

                metadata={"session\_id": cfg.session\_id, "run\_id": run\_id},

            )

            llm\_raw\_text \= llm\_resp.raw\_text

            llm\_json \= llm\_resp.parsed\_json  \# may be None if parse failed

            usage \= llm\_resp.usage  \# normalized usage object or None

            self.artifacts.save\_text(run\_id, "llm\_raw.txt", llm\_raw\_text)

            self.artifacts.save\_json(run\_id, "llm\_parsed.json", llm\_json if llm\_json is not None else {})

        except Exception as e:

            status \= "failed"

            err \= f"LLM call failed: {type(e).\_\_name\_\_}: {e}"

            errors.append(err)

            self.storage.finish\_run\_failed(run\_id=run\_id, error=err)

            return self.storage.build\_run\_result(run\_id)

        t\_llm1 \= time.perf\_counter()

        \# 5\) Validate JSON strictly against schema

        validation\_errors \= validate\_against\_schema(llm\_json, response\_schema)

        self.artifacts.save\_json(run\_id, "schema\_validation.json", {"errors": validation\_errors})

        \# 6\) Cost \+ timings

        metrics \= estimate\_costs(

            cfg=cfg,

            usage=usage,

            ocr\_docs=ocr\_docs,

            pricing=self.storage.load\_pricing\_snapshot(),

            ocr\_ms=int((t\_ocr1 \- t\_ocr0) \* 1000),

            llm\_ms=int((t\_llm1 \- t\_llm0) \* 1000),

            total\_ms=int((time.perf\_counter() \- t\_total0) \* 1000),

        )

        \# 7\) Persist final

        self.storage.finish\_run\_success(

            run\_id=run\_id,

            status=status,

            packed\_documents\_path=str(packed\_path),

            llm\_json=llm\_json,

            llm\_raw\_text=llm\_raw\_text,

            validation\_errors=validation\_errors,

            metrics=metrics,

            errors=errors,

        )

        return self.storage.build\_run\_result(run\_id)

### **Важные “неочевидности”, которые лучше учесть сразу**

* **OpenAI cached tokens**: cached\_tokens присутствует в деталях usage и нужен для корректной цены. 

* **OpenAI reasoning tokens**: они могут быть отдельно, но по стоимости считаются как output tokens (важно для честной оценки). 

* **Gemini usage\_metadata**: есть отдельные поля prompt\_token\_count, candidates\_token\_count, thoughts\_token\_count, total\_token\_count — для ценника “output includes thinking” это критично. 

  ---

  ## **4\) Формат упаковки** 

  ## **\<BEGIN\_DOCUMENTS\>**

  ##  **— генератор (минимальный)**

  \# src/pipeline/document\_packer.py  
  from \_\_future\_\_ import annotations  
    
  from pathlib import Path  
    
  def pack\_documents(ocr\_docs: list) \-\> str:  
      parts: list\[str\] \= \["\<BEGIN\_DOCUMENTS\>"\]  
      for d in ocr\_docs:  
          md \= Path(d.artifacts.markdown\_path).read\_text(encoding="utf-8", errors="replace")  
          parts.append(f'\<DOC\_START id="{d.doc\_id}"\>')  
          parts.append(md.rstrip())  
          parts.append("\<DOC\_END\>")  
      parts.append("\<END\_DOCUMENTS\>")  
      return "\\n".join(parts) \+ "\\n"  
  ---

  ## **5\) Gradio Blocks — структура UI “под тестировщика”**

Ниже — компоновка, которую удобно расширять, но она уже закрывает ваш MVP:

* Run (загрузка, выбор модели/промпта, запуск)

* Results (human view \+ raw JSON \+ gaps)

* History (список прогонов из SQLite)

* Prompts (редактирование/сохранение новой версии)

  ### **Псевдокод Gradio**

  \# src/ui/app.py  
  from \_\_future\_\_ import annotations  
    
  import gradio as gr  
    
  from ui.controllers import (  
      ui\_load\_models,  
      ui\_run\_analysis\_stream,  
      ui\_list\_runs,  
      ui\_load\_run,  
      ui\_list\_prompts,  
      ui\_load\_prompt,  
      ui\_save\_prompt\_as\_new\_version,  
  )  
    
  def build\_ui() \-\> gr.Blocks:  
      with gr.Blocks(title="Kaucja Intake Sandbox") as demo:  
          \# Shared state  
          session\_id \= gr.State(value=None)  
          current\_run\_id \= gr.State(value=None)  
    
          with gr.Tab("Run"):  
              with gr.Row():  
                  files \= gr.Files(  
                      label="Документы (PDF/DOC/DOCX)",  
                      file\_types=\[".pdf", ".doc", ".docx"\],  
                      file\_count="multiple",  
                  )  
    
                  with gr.Column():  
                      provider \= gr.Dropdown(  
                          label="Провайдер",  
                          choices=\["openai", "google"\],  
                          value="openai",  
                      )  
                      model \= gr.Dropdown(label="Модель", choices=\[\], value=None)  
    
                      reasoning\_effort \= gr.Radio(  
                          label="Reasoning effort (OpenAI)",  
                          choices=\["auto", "low", "medium", "high"\],  
                          value="auto",  
                          visible=True,  
                      )  
    
                      prompt\_ref \= gr.Dropdown(label="Промпт (name:version)", choices=\[\], value=None)  
    
                      max\_output\_tokens \= gr.Slider(  
                          label="max\_output\_tokens",  
                          minimum=512,  
                          maximum=64000,  
                          step=256,  
                          value=8000,  
                      )  
    
                      temperature \= gr.Slider(  
                          label="temperature",  
                          minimum=0.0,  
                          maximum=2.0,  
                          step=0.1,  
                          value=0.0,  
                      )  
    
                      run\_btn \= gr.Button("Запустить анализ", variant="primary")  
    
              with gr.Row():  
                  progress\_md \= gr.Markdown(value="Готов к запуску.")  
              with gr.Row():  
                  run\_log \= gr.Textbox(label="Лог пайплайна", lines=14)  
    
          with gr.Tab("Results"):  
              with gr.Row():  
                  human\_view \= gr.Markdown(label="Человекочитаемый результат")  
              with gr.Row():  
                  critical\_gaps \= gr.JSON(label="critical\_gaps\_summary")  
                  next\_questions \= gr.JSON(label="next\_questions\_to\_user")  
              with gr.Row():  
                  raw\_json \= gr.Code(label="Raw JSON (model output)", language="json")  
              with gr.Row():  
                  metrics \= gr.JSON(label="Метрики / Стоимость / Тайминги")  
              with gr.Row():  
                  ocr\_warnings \= gr.JSON(label="OCR warnings")  
    
          with gr.Tab("History"):  
              with gr.Row():  
                  refresh\_btn \= gr.Button("Обновить список прогонов")  
                  runs\_table \= gr.Dataframe(  
                      headers=\["run\_id", "created\_at", "provider", "model", "prompt\_ref", "status", "total\_cost\_usd"\],  
                      row\_count=10,  
                      col\_count=7,  
                      interactive=False,  
                  )  
              with gr.Row():  
                  load\_btn \= gr.Button("Загрузить выбранный run\_id")  
                  selected\_run\_id \= gr.Textbox(label="run\_id", placeholder="Вставьте run\_id из таблицы")  
    
          with gr.Tab("Prompts"):  
              with gr.Row():  
                  prompts\_list \= gr.Dropdown(label="Выбор промпта", choices=\[\], value=None)  
                  reload\_prompts\_btn \= gr.Button("Обновить")  
              with gr.Row():  
                  prompt\_text \= gr.Textbox(label="system prompt", lines=18)  
                  schema\_text \= gr.Code(label="JSON schema", language="json")  
              with gr.Row():  
                  save\_as\_new\_btn \= gr.Button("Сохранить как новую версию")  
                  save\_note \= gr.Markdown()  
    
          \# \--- wiring \---  
    
          \# provider \-\> model choices  
          provider.change(  
              fn=ui\_load\_models,  
              inputs=\[provider\],  
              outputs=\[model, reasoning\_effort\],  
          )  
    
          \# init prompt list  
          demo.load(fn=ui\_list\_prompts, inputs=\[\], outputs=\[prompt\_ref, prompts\_list\])  
    
          reload\_prompts\_btn.click(fn=ui\_list\_prompts, inputs=\[\], outputs=\[prompt\_ref, prompts\_list\])  
    
          \# prompts editor  
          prompts\_list.change(fn=ui\_load\_prompt, inputs=\[prompts\_list\], outputs=\[prompt\_text, schema\_text\])  
    
          save\_as\_new\_btn.click(  
              fn=ui\_save\_prompt\_as\_new\_version,  
              inputs=\[prompts\_list, prompt\_text, schema\_text\],  
              outputs=\[prompts\_list, prompt\_ref, save\_note\],  
          )  
    
          \# run pipeline (streaming updates)  
          run\_btn.click(  
              fn=ui\_run\_analysis\_stream,  
              inputs=\[files, provider, model, reasoning\_effort, prompt\_ref, max\_output\_tokens, temperature, session\_id\],  
              outputs=\[  
                  progress\_md,  
                  run\_log,  
                  human\_view,  
                  critical\_gaps,  
                  next\_questions,  
                  raw\_json,  
                  metrics,  
                  ocr\_warnings,  
                  current\_run\_id,  
                  session\_id,  
              \],  
          )  
    
          \# history  
          refresh\_btn.click(fn=ui\_list\_runs, inputs=\[\], outputs=\[runs\_table\])  
          load\_btn.click(fn=ui\_load\_run, inputs=\[selected\_run\_id\], outputs=\[  
              human\_view, critical\_gaps, next\_questions, raw\_json, metrics, ocr\_warnings, current\_run\_id  
          \])  
    
      return demo

  ### **Что важно в UI-хендлерах**

* ui\_run\_analysis\_stream лучше сделать **генератором** (yield), чтобы обновлять progress\_md / run\_log по этапам (“OCR doc 1/3…”, “LLM request…”, “Validating…”).

* ui\_load\_models должен:

  * подтягивать providers.yaml,

  * менять choices для model,

  * прятать reasoning\_effort, если provider \!= openai.

  ---

Ниже — три «готовых блока», которые можно сразу вставлять в репозиторий/TechSpec:

1. **нормализатор usage** (OpenAI Responses \+ Gemini generateContent) \+ **точные формулы стоимости** (по pricing.yaml),

2. **минимальная SQLite-схема** под runs / docs / artifacts,

3. **human renderer**: из JSON-ответа модели → читабельный отчёт \+ таблица checklist (для Gradio).

   ---

   ## **1\) Нормализация usage (OpenAI Responses vs Gemini usageMetadata)**

   ### **1.1 Канонический формат NormalizedUsage**

**OpenAI Responses API** возвращает usage в виде:

* input\_tokens

* input\_tokens\_details.cached\_tokens

* output\_tokens

* output\_tokens\_details.reasoning\_tokens

* total\_tokens 

**Gemini API (models.generateContent)** возвращает usageMetadata:

* promptTokenCount

* cachedContentTokenCount

* candidatesTokenCount

* toolUsePromptTokenCount

* thoughtsTokenCount

* totalTokenCount 

Для Gemini удобно помнить, что totalTokenCount — это сумма promptTokenCount \+ candidatesTokenCount \+ toolUsePromptTokenCount \+ thoughtsTokenCount. 

Нормализуем к одному виду, который вы сможете:

* показывать в UI как prompt\_tokens / completion\_tokens / total\_tokens,

* хранить в SQLite,

* кормить в cost estimator.

  from \_\_future\_\_ import annotations  
    
  from dataclasses import dataclass, asdict  
  from typing import Any, Dict, Literal, Optional, Tuple, Union  
    
  Provider \= Literal\["openai", "google"\]  
    
  @dataclass(frozen=True)  
  class NormalizedUsage:  
      provider: Provider  
      model: str  
    
      \# UI-compatible trio  
      prompt\_tokens: int  
      completion\_tokens: int  
      total\_tokens: int  
    
      \# Breakdowns useful for cost \+ diagnostics  
      cached\_prompt\_tokens: int \= 0            \# OpenAI cached\_tokens / Gemini cachedContentTokenCount  
      thinking\_tokens: int \= 0                 \# OpenAI reasoning\_tokens / Gemini thoughtsTokenCount  
      tool\_prompt\_tokens: int \= 0              \# Gemini toolUsePromptTokenCount (0 for our MVP)  
    
      \# Provider raw usage payload for debugging/audit  
      raw\_usage: Optional\[Dict\[str, Any\]\] \= None  
    
    
  def \_get(obj: Any, path: Tuple\[Union\[str, int\], ...\], default: Any \= None) \-\> Any:  
      """  
      Safe getter supporting dicts and attribute objects.  
      Example: \_get(resp, ("usage", "input\_tokens"), 0\)  
      """  
      cur \= obj  
      for key in path:  
          if cur is None:  
              return default  
          try:  
              if isinstance(cur, dict):  
                  cur \= cur.get(key, default if key \== path\[-1\] else None)  
              else:  
                  cur \= getattr(cur, key)  
          except Exception:  
              return default  
      return cur if cur is not None else default  
    
    
  def normalize\_usage\_openai(response\_obj: Any, model: str) \-\> NormalizedUsage:  
      """  
      OpenAI Responses API normalization.  
      Expects 'usage' compatible with:  
        usage.input\_tokens  
        usage.input\_tokens\_details.cached\_tokens  
        usage.output\_tokens  
        usage.output\_tokens\_details.reasoning\_tokens  
        usage.total\_tokens  
      """  
      usage \= \_get(response\_obj, ("usage",), None) or {}  
      input\_tokens \= int(\_get(response\_obj, ("usage", "input\_tokens"), 0\) or 0\)  
      cached \= int(\_get(response\_obj, ("usage", "input\_tokens\_details", "cached\_tokens"), 0\) or 0\)  
      output\_tokens \= int(\_get(response\_obj, ("usage", "output\_tokens"), 0\) or 0\)  
      reasoning\_tokens \= int(\_get(response\_obj, ("usage", "output\_tokens\_details", "reasoning\_tokens"), 0\) or 0\)  
      total\_tokens \= int(\_get(response\_obj, ("usage", "total\_tokens"), input\_tokens \+ output\_tokens) or 0\)  
    
      \# prompt\_tokens/completion\_tokens are directly what UI expects  
      return NormalizedUsage(  
          provider="openai",  
          model=model,  
          prompt\_tokens=input\_tokens,  
          completion\_tokens=output\_tokens,  
          total\_tokens=total\_tokens,  
          cached\_prompt\_tokens=cached,  
          thinking\_tokens=reasoning\_tokens,  
          tool\_prompt\_tokens=0,  
          raw\_usage=usage if isinstance(usage, dict) else None,  
      )  
    
    
  def normalize\_usage\_gemini(generate\_content\_resp: Any, model: str) \-\> NormalizedUsage:  
      """  
      Gemini generateContent normalization.  
      Expects usageMetadata (JSON) or usage\_metadata (Pythonic attr) with fields:  
        promptTokenCount, cachedContentTokenCount, candidatesTokenCount,  
        toolUsePromptTokenCount, thoughtsTokenCount, totalTokenCount  
      """  
      \# Gemini REST JSON uses 'usageMetadata'. Some SDKs expose snake\_case.  
      usage \= (  
          \_get(generate\_content\_resp, ("usageMetadata",), None)  
          or \_get(generate\_content\_resp, ("usage\_metadata",), None)  
          or {}  
      )  
    
      prompt \= int(\_get(usage, ("promptTokenCount",), 0\) or 0\)  
      cached \= int(\_get(usage, ("cachedContentTokenCount",), 0\) or 0\)  
      candidates \= int(\_get(usage, ("candidatesTokenCount",), 0\) or 0\)  
      tool\_prompt \= int(\_get(usage, ("toolUsePromptTokenCount",), 0\) or 0\)  
      thoughts \= int(\_get(usage, ("thoughtsTokenCount",), 0\) or 0\)  
      total \= int(\_get(usage, ("totalTokenCount",), prompt \+ candidates \+ tool\_prompt \+ thoughts) or 0\)  
    
      \# UI-compatible:  
      \# \- prompt\_tokens: prompt \+ tool prompt (because totalTokenCount counts them separately)  
      \# \- completion\_tokens: candidates \+ thoughts (output billable includes thinking tokens)  
      return NormalizedUsage(  
          provider="google",  
          model=model,  
          prompt\_tokens=prompt \+ tool\_prompt,  
          completion\_tokens=candidates \+ thoughts,  
          total\_tokens=total,  
          cached\_prompt\_tokens=cached,  
          thinking\_tokens=thoughts,  
          tool\_prompt\_tokens=tool\_prompt,  
          raw\_usage=usage if isinstance(usage, dict) else None,  
      )

**Почему completion\_tokens \= candidates \+ thoughts для Gemini:** thoughtsTokenCount выделен отдельно, а totalTokenCount считается суммой с thoughtsTokenCount, то есть “thinking” не должен теряться при расчёте. 

---

## **2\) Стоимость по** 

## **pricing.yaml**

## **: формулы \+ минимальный формат**

### **2.1 Минимальный** 

### **pricing.yaml**

###  **(актуальные цифры для MVP-моделей)**

Пример ниже использует официальные цены:

* OpenAI (Standard/Flex/Priority) для gpt-5.1 и gpt-5.2 

* Gemini Developer API для gemini-3.1-pro-preview и gemini-3-flash-preview 

* Mistral OCR 3 (mistral-ocr-2512) $2/1000 страниц 

  version: "2026-02-24"  
  currency: "USD"  
    
  providers:  
    openai:  
      unit: "per\_1m\_tokens"  
      tiers:  
        standard:  
          models:  
            gpt-5.1: { input: 1.25,  cached\_input: 0.125, output: 10.00 }  
            gpt-5.2: { input: 1.75,  cached\_input: 0.175, output: 14.00 }  
        flex:  
          models:  
            gpt-5.1: { input: 0.625, cached\_input: 0.0625, output: 5.00 }  
            gpt-5.2: { input: 0.875, cached\_input: 0.0875, output: 7.00 }  
        priority:  
          models:  
            gpt-5.1: { input: 2.50,  cached\_input: 0.25,  output: 20.00 }  
            gpt-5.2: { input: 3.50,  cached\_input: 0.35,  output: 28.00 }  
    
    google:  
      unit: "per\_1m\_tokens"  
      models:  
        gemini-3.1-pro-preview:  
          prompt\_tiers:  
            \- max\_prompt\_tokens\_inclusive: 200000  
              input: 2.00  
              output: 12.00      \# includes thinking tokens  
              cached\_input: 0.20 \# "context caching price"  
              cache\_storage\_per\_1m\_tokens\_per\_hour: 4.50  
            \- max\_prompt\_tokens\_inclusive: null  
              input: 4.00  
              output: 18.00  
              cached\_input: 0.40  
              cache\_storage\_per\_1m\_tokens\_per\_hour: 4.50  
    
        gemini-3-flash-preview:  
          input: 0.50  
          output: 3.00          \# includes thinking tokens  
          cached\_input: 0.05     \# "context caching price"  
          cache\_storage\_per\_1m\_tokens\_per\_hour: 1.00  
    
    mistral:  
      unit: "per\_1000\_pages"  
      models:  
        mistral-ocr-2512:  
          pages: 2.00  
          annotated\_pages: 3.00  
          batch\_discount\_factor: 0.5  
  ---

  ### **2.2 Формулы стоимости LLM (универсально)**

  #### **OpenAI (Responses API)**

Пусть:

* P \= usage.prompt\_tokens (input tokens),

* C \= usage.cached\_prompt\_tokens,

* O \= usage.completion\_tokens (output tokens).

Тогда:

* P\_uncached \= max(P \- C, 0),

* cost\_usd \= (P\_uncached/1e6)\*price.input \+ (C/1e6)\*price.cached\_input \+ (O/1e6)\*price.output.

Важно: OpenAI прямо указывает, что reasoning tokens хоть и не видны, **биллятся как output tokens** — поэтому O можно использовать как “billable output”. 

#### **Gemini (generateContent)**

Пусть:

* promptTokenCount включает cached content как “total effective prompt size” 

* cachedContentTokenCount — сколько токенов из prompt было кэшировано 

* output billable \= candidatesTokenCount \+ thoughtsTokenCount (output price “including thinking tokens”) 

Тогда:

* P\_total \= promptTokenCount \+ toolUsePromptTokenCount

* C \= cachedContentTokenCount

* P\_uncached \= max(P\_total \- C, 0\)

* O \= candidatesTokenCount \+ thoughtsTokenCount

* cost\_usd \= (P\_uncached/1e6)\*price.input \+ (C/1e6)\*price.cached\_input \+ (O/1e6)\*price.output

Где price.cached\_input — это “context caching price”. В документации про context caching прямо сказано, что cached tokens “billed at a reduced rate when included in subsequent prompts”, плюс отдельно считается storage по TTL. 

---

### **2.3 (Опционально) Стоимость storage для Gemini explicit caching**

Если вы создаёте explicit cache (TTL), то для **storage**:

* storage\_cost \= (cached\_tokens/1e6) \* storage\_price\_per\_1m\_tokens\_per\_hour \* (ttl\_seconds/3600)

Это следует из того, что billing учитывает “storage duration (TTL)” и размер кеша. 

---

### **2.4 Стоимость OCR (Mistral OCR 3\)**

Если:

* pages\_total — суммарное число страниц по всем документам,

* цена ocr\_price\_per\_1000\_pages \= 2.00 (обычный режим). 

Тогда:

* ocr\_cost \= (pages\_total / 1000\) \* 2.00

Если будете использовать Batch API (скидка 50% упоминается в материалах Mistral), можно умножить на batch\_discount\_factor=0.5. 

---

### **2.5 Реализация cost estimator (Python, типизировано)**

from \_\_future\_\_ import annotations

from dataclasses import dataclass

from typing import Any, Dict, Optional, Tuple

@dataclass(frozen=True)

class CostBreakdown:

    currency: str

    ocr\_usd: float

    llm\_usd: float

    total\_usd: float

    details: Dict\[str, Any\]

def \_per\_1m(tokens: int, rate: float) \-\> float:

    return (max(tokens, 0\) / 1\_000\_000.0) \* float(rate)

def estimate\_openai\_cost(

    usage: NormalizedUsage,

    pricing: Dict\[str, Any\],

    tier: str \= "standard",

) \-\> float:

    models \= pricing\["providers"\]\["openai"\]\["tiers"\]\[tier\]\["models"\]

    if usage.model not in models:

        raise KeyError(f"Missing OpenAI pricing for model={usage.model} tier={tier}")

    p \= models\[usage.model\]

    uncached \= max(usage.prompt\_tokens \- usage.cached\_prompt\_tokens, 0\)

    return (

        \_per\_1m(uncached, p\["input"\])

        \+ \_per\_1m(usage.cached\_prompt\_tokens, p\["cached\_input"\])

        \+ \_per\_1m(usage.completion\_tokens, p\["output"\])

    )

def \_pick\_gemini\_tier(model\_cfg: Dict\[str, Any\], prompt\_token\_count\_effective: int) \-\> Dict\[str, Any\]:

    tiers \= model\_cfg.get("prompt\_tiers")

    if not tiers:

        return model\_cfg

    for t in tiers:

        limit \= t\["max\_prompt\_tokens\_inclusive"\]

        if limit is None or prompt\_token\_count\_effective \<= int(limit):

            return t

    return tiers\[-1\]

def estimate\_gemini\_cost(

    usage: NormalizedUsage,

    pricing: Dict\[str, Any\],

    \# IMPORTANT: promptTokenCount from usageMetadata, NOT usage.prompt\_tokens (which may include tool tokens).

    prompt\_token\_count\_effective: int,

) \-\> float:

    model\_cfg \= pricing\["providers"\]\["google"\]\["models"\]\[usage.model\]

    tier\_cfg \= \_pick\_gemini\_tier(model\_cfg, prompt\_token\_count\_effective)

    uncached \= max(usage.prompt\_tokens \- usage.cached\_prompt\_tokens, 0\)

    return (

        \_per\_1m(uncached, tier\_cfg\["input"\])

        \+ \_per\_1m(usage.cached\_prompt\_tokens, tier\_cfg\["cached\_input"\])

        \+ \_per\_1m(usage.completion\_tokens, tier\_cfg\["output"\])

    )

def estimate\_mistral\_ocr\_cost\_pages(

    pages\_total: int,

    pricing: Dict\[str, Any\],

    model: str \= "mistral-ocr-2512",

    batch: bool \= False,

) \-\> float:

    cfg \= pricing\["providers"\]\["mistral"\]\["models"\]\[model\]

    base \= (max(pages\_total, 0\) / 1000.0) \* float(cfg\["pages"\])

    if batch:

        base \*= float(cfg.get("batch\_discount\_factor", 1.0))

    return base

def estimate\_total\_cost(

    \*,

    pricing: Dict\[str, Any\],

    currency: str,

    pages\_total: int,

    llm\_provider: str,

    llm\_usage: Optional\[NormalizedUsage\],

    openai\_tier: str \= "standard",

    gemini\_prompt\_token\_count\_effective: Optional\[int\] \= None,

    ocr\_batch: bool \= False,

) \-\> CostBreakdown:

    ocr\_cost \= estimate\_mistral\_ocr\_cost\_pages(pages\_total, pricing, batch=ocr\_batch)

    llm\_cost \= 0.0

    if llm\_usage:

        if llm\_provider \== "openai":

            llm\_cost \= estimate\_openai\_cost(llm\_usage, pricing, tier=openai\_tier)

        elif llm\_provider \== "google":

            if gemini\_prompt\_token\_count\_effective is None:

                raise ValueError("gemini\_prompt\_token\_count\_effective is required for google cost estimate")

            llm\_cost \= estimate\_gemini\_cost(llm\_usage, pricing, prompt\_token\_count\_effective=gemini\_prompt\_token\_count\_effective)

        else:

            raise ValueError(f"Unknown provider: {llm\_provider}")

    total \= ocr\_cost \+ llm\_cost

    return CostBreakdown(

        currency=currency,

        ocr\_usd=ocr\_cost,

        llm\_usd=llm\_cost,

        total\_usd=total,

        details={

            "pages\_total": pages\_total,

            "llm\_provider": llm\_provider,

            "llm\_model": (llm\_usage.model if llm\_usage else None),

            "openai\_tier": openai\_tier if llm\_provider \== "openai" else None,

            "cached\_prompt\_tokens": (llm\_usage.cached\_prompt\_tokens if llm\_usage else None),

            "thinking\_tokens": (llm\_usage.thinking\_tokens if llm\_usage else None),

        },

    )

---

## **3\) Минимальная SQLite схема:** 

## **runs / docs / artifacts**

Цель: чтобы storage-код писался “без гаданий”, но оставался лёгким (SQLite \+ файловая система).

### **3.1 Принципы**

* **Артефакты на диске**, в SQLite — пути \+ метаданные (и небольшие JSON-и).

* В runs храним всё, что нужно для воспроизводимости: модель/параметры/версия промпта/usage/cost/timings/статус/ошибка.

* В docs — что пользователь загрузил \+ базовые атрибуты \+ статус OCR.

* В artifacts — произвольное число файлов/директорий, привязанных к run/doc.

  ### **3.2 DDL (можно как** 

  ### **storage/schema.sql**

  ### **)**

  PRAGMA foreign\_keys \= ON;  
    
  \-- 1\) RUNS  
  CREATE TABLE IF NOT EXISTS runs (  
    run\_id TEXT PRIMARY KEY,  
    session\_id TEXT NOT NULL,  
    
    created\_at TEXT NOT NULL,              \-- ISO8601 UTC  
    finished\_at TEXT,                      \-- ISO8601 UTC  
    
    status TEXT NOT NULL CHECK (status IN (  
      'created','running','succeeded','failed','cancelled'  
    )),  
    
    \-- LLM config snapshot  
    llm\_provider TEXT NOT NULL CHECK (llm\_provider IN ('openai','google')),  
    llm\_model TEXT NOT NULL,  
    reasoning\_effort TEXT,                 \-- openai: auto|low|medium|high (nullable)  
    temperature REAL,  
    max\_output\_tokens INTEGER,  
    
    prompt\_ref TEXT NOT NULL,              \-- e.g. "kaucja\_gap\_v003"  
    prompt\_sha256 TEXT,                    \-- snapshot hash for reproducibility  
    schema\_sha256 TEXT,                    \-- json schema hash used for this run  
    
    \-- Metrics (store both raw \+ normalized)  
    usage\_raw\_json TEXT,                   \-- provider payload (JSON as TEXT)  
    usage\_norm\_json TEXT,                  \-- NormalizedUsage as JSON string  
    timings\_json TEXT,                     \-- {"ocr\_ms":..., "llm\_ms":..., "total\_ms":...}  
    cost\_json TEXT,                        \-- {"ocr\_usd":..., "llm\_usd":..., "total\_usd":..., "pricing\_version":...}  
    pricing\_snapshot\_json TEXT,            \-- optional: embed portion of pricing.yaml used (for audit)  
    
    \-- LLM outputs  
    llm\_output\_json TEXT,                  \-- validated JSON (as TEXT)  
    llm\_output\_raw\_text TEXT,              \-- raw model text (for debugging)  
    llm\_validation\_errors\_json TEXT,       \-- if schema validation failed  
    
    \-- Errors  
    error\_stage TEXT,                      \-- ocr|llm|storage|ui|other  
    error\_type TEXT,  
    error\_message TEXT,  
    error\_trace TEXT  
  );  
    
  CREATE INDEX IF NOT EXISTS idx\_runs\_session\_created  
  ON runs(session\_id, created\_at);  
    
    
  \-- 2\) DOCS (one row per input document per run)  
  CREATE TABLE IF NOT EXISTS docs (  
    doc\_pk INTEGER PRIMARY KEY AUTOINCREMENT,  
    run\_id TEXT NOT NULL REFERENCES runs(run\_id) ON DELETE CASCADE,  
    
    doc\_id TEXT NOT NULL,                  \-- your internal stable "0000001" etc  
    original\_filename TEXT NOT NULL,  
    mime\_type TEXT,  
    file\_path TEXT NOT NULL,               \-- where the uploaded file is stored  
    file\_sha256 TEXT,  
    page\_count INTEGER,  
    
    status TEXT NOT NULL CHECK (status IN (  
      'uploaded','ocr\_running','ocr\_succeeded','ocr\_failed'  
    )),  
    
    ocr\_model TEXT,                        \-- e.g. "mistral-ocr-2512"  
    ocr\_started\_at TEXT,  
    ocr\_finished\_at TEXT,  
    ocr\_error\_message TEXT,  
    
    UNIQUE(run\_id, doc\_id)  
  );  
    
  CREATE INDEX IF NOT EXISTS idx\_docs\_run  
  ON docs(run\_id);  
    
    
  \-- 3\) ARTIFACTS (generic registry of filesystem artifacts)  
  CREATE TABLE IF NOT EXISTS artifacts (  
    artifact\_pk INTEGER PRIMARY KEY AUTOINCREMENT,  
    run\_id TEXT NOT NULL REFERENCES runs(run\_id) ON DELETE CASCADE,  
    doc\_id TEXT,                           \-- nullable for run-level artifacts  
    kind TEXT NOT NULL,                    \-- e.g. ocr\_markdown|ocr\_tables|ocr\_images\_dir|ocr\_page\_image|llm\_request|llm\_response\_raw  
    path TEXT NOT NULL,                    \-- file or directory path  
    meta\_json TEXT,                        \-- any JSON metadata (page number, bbox, etc)  
    created\_at TEXT NOT NULL,  
    
    FOREIGN KEY (run\_id, doc\_id) REFERENCES docs(run\_id, doc\_id) ON DELETE CASCADE  
  );  
    
  CREATE INDEX IF NOT EXISTS idx\_artifacts\_run\_doc  
  ON artifacts(run\_id, doc\_id);  
    
  CREATE INDEX IF NOT EXISTS idx\_artifacts\_run\_kind  
  ON artifacts(run\_id, kind);

  ### **3.3 Рекомендуемый минимальный набор** 

  ### **artifacts.kind**

  ###  **для OCR**

* ocr\_markdown → путь к .md (извлечённый текст)

* ocr\_tables\_json → путь к .json (если таблицы отдельно)

* ocr\_images\_dir → путь к директории с изображениями/кропами страниц

* ocr\_page\_map\_json → путь к .json с мэппингом “страница → список артефактов”

* ocr\_raw\_response\_json → сырой ответ OCR API (для дебага)

  ---

  ## **4\) Human renderer: JSON → Markdown отчёт \+ таблица checklist**

Задача renderer’а для Gradio:

* **показать результат понятным юристу языком**,

* параллельно дать **таблицу checklist**,

* вытащить **“чего не хватает”** (список пунктов со статусом missing/ambiguous/conflict),

* сделать **defense-in-depth masking** (на случай если модель не замаскировала PESEL/IBAN).

  ### **4.1 PII masking (простая защита на UI-слое)**

  import re  
    
  \_RE\_PESEL \= re.compile(r"\\b(\\d{2})(\\d{7})(\\d{2})\\b")           \# 11 digits  
  \_RE\_IBAN\_PL \= re.compile(r"\\b(PL)(\\d{2})(\[ \\d\]{20,30})\\b")     \# rough  
  \_RE\_LONG\_DIGITS \= re.compile(r"\\b(\\d{2,4})(\\d{6,20})(\\d{2,4})\\b")  
    
  def mask\_pii(text: str) \-\> str:  
      if not text:  
          return text  
    
      text \= \_RE\_PESEL.sub(r"\\1XXXXXXX\\3", text)  
    
      def \_iban\_sub(m: re.Match) \-\> str:  
          prefix \= m.group(1) \+ m.group(2)  
          rest \= re.sub(r"\\d", "X", m.group(3))  
          \# keep last 4 digits if present  
          if len(rest) \>= 4:  
              rest \= rest\[:-4\] \+ m.group(3).replace(" ", "")\[-4:\]  
          return prefix \+ rest  
    
      text \= \_RE\_IBAN\_PL.sub(\_iban\_sub, text)  
    
      \# fallback: if there is a suspicious long digit run, hide middle  
      text \= \_RE\_LONG\_DIGITS.sub(lambda m: f"{m.group(1)}{'X'\*len(m.group(2))}{m.group(3)}", text)  
      return text

  ### **4.2 Рендеринг отчёта (Markdown)**

  from \_\_future\_\_ import annotations  
    
  from typing import Any, Dict, List, Tuple  
  import json  
    
  CHECKLIST\_ORDER \= \[  
    "CONTRACT\_EXISTS",  
    "CONTRACT\_SIGNED\_AND\_DATED",  
    "PROPERTY\_ADDRESS\_CONFIRMED",  
    "LEASE\_TYPE\_CONFIRMED",  
    "KAUCJA\_CLAUSE\_PRESENT",  
    "KAUCJA\_AMOUNT\_STATED",  
    "KAUCJA\_PAYMENT\_PROOF",  
    "CZYNSZ\_AT\_DEPOSIT\_DATE",  
    "CZYNSZ\_AT\_RETURN\_DATE",  
    "MOVE\_IN\_PROTOCOL",  
    "MOVE\_OUT\_PROTOCOL",  
    "VACATE\_DATE\_PROOF",  
    "KEY\_HANDOVER\_PROOF",  
    "METER\_READINGS\_AT\_EXIT",  
    "UTILITIES\_SETTLEMENT",  
    "RENT\_AND\_FEES\_PAID",  
    "LANDLORD\_DEDUCTIONS\_EXPLAINED",  
    "PHOTOS\_VIDEOS\_CONDITION",  
    "PRECOURT\_DEMAND\_LETTER",  
    "DELIVERY\_PROOF",  
    "LANDLORD\_RESPONSE",  
    "TENANT\_BANK\_ACCOUNT\_FOR\_RETURN",  
  \]  
    
  STATUS\_LABEL \= {  
      "confirmed": "confirmed",  
      "missing": "missing",  
      "ambiguous": "ambiguous",  
      "conflict": "conflict",  
  }  
    
  IMPORTANCE\_LABEL \= {"critical": "critical", "recommended": "recommended"}  
    
    
  def \_fmt\_sources(sources: List\[Dict\[str, Any\]\]) \-\> str:  
      if not sources:  
          return ""  
      parts \= \[\]  
      for s in sources\[:5\]:  \# keep UI compact  
          doc\_id \= s.get("doc\_id", "?")  
          quote \= mask\_pii(str(s.get("quote", ""))).strip()  
          if quote:  
              parts.append(f'- {doc\_id}: "{quote}"')  
          else:  
              parts.append(f"- {doc\_id}")  
      if len(sources) \> 5:  
          parts.append(f"- … (+{len(sources)-5} источников)")  
      return "\\n".join(parts)  
    
    
  def render\_case\_facts(case\_facts: Dict\[str, Any\]) \-\> str:  
      \# case\_facts is structured as described in schema: each fact has value/status/sources  
      md \= \[\]  
      md.append("\#\# Факты дела (из документов)\\n")  
    
      def add\_fact(label: str, fact: Dict\[str, Any\]) \-\> None:  
          if not isinstance(fact, dict):  
              return  
          status \= fact.get("status", "missing")  
          value \= fact.get("value", None)  
          sources \= fact.get("sources", \[\]) or \[\]  
          md.append(f"\#\#\# {label}")  
          md.append(f"- Статус: \*\*{status}\*\*")  
          md.append(f"- Значение: {value\!r}")  
          src\_md \= \_fmt\_sources(sources)  
          if src\_md:  
              md.append("- Источники:\\n" \+ src\_md)  
          md.append("")  
    
      parties \= case\_facts.get("parties", {})  
      if isinstance(parties, dict):  
          md.append("\#\#\# Стороны")  
          \# parties may be nested; show high-level keys  
          for k, v in parties.items():  
              if isinstance(v, dict) and {"value", "status"}.issubset(v.keys()):  
                  add\_fact(f"Стороны / {k}", v)  
              else:  
                  \# best-effort stringify  
                  md.append(f"- {k}: {json.dumps(v, ensure\_ascii=False) if isinstance(v, (dict, list)) else v}")  
          md.append("")  
    
      \# common top-level blocks per schema  
      for key, label in \[  
          ("property\_address", "Адрес объекта"),  
          ("lease\_type", "Тип найма"),  
          ("key\_dates", "Ключевые даты"),  
          ("money", "Деньги"),  
      \]:  
          block \= case\_facts.get(key, {})  
          if isinstance(block, dict):  
              md.append(f"\#\#\# {label}")  
              for k, v in block.items():  
                  if isinstance(v, dict) and {"value", "status"}.issubset(v.keys()):  
                      add\_fact(f"{label} / {k}", v)  
                  else:  
                      md.append(f"- {k}: {json.dumps(v, ensure\_ascii=False) if isinstance(v, (dict, list)) else v}")  
              md.append("")  
    
      notes \= case\_facts.get("notes", \[\])  
      if notes:  
          md.append("\#\#\# Примечания")  
          for n in notes\[:20\]:  
              md.append(f"- {n}")  
          if len(notes) \> 20:  
              md.append(f"- … (+{len(notes)-20} заметок)")  
          md.append("")  
    
      return "\\n".join(md)  
    
    
  def render\_summary\_sections(payload: Dict\[str, Any\]) \-\> str:  
      md \= \[\]  
    
      gaps \= payload.get("critical\_gaps\_summary", \[\]) or \[\]  
      if gaps:  
          md.append("\#\# Критические пробелы\\n")  
          for g in gaps\[:20\]:  
              md.append(f"- {g}")  
          md.append("")  
    
      questions \= payload.get("next\_questions\_to\_user", \[\]) or \[\]  
      if questions:  
          md.append("\#\# Следующие вопросы пользователю\\n")  
          for i, q in enumerate(questions\[:10\], 1):  
              md.append(f"{i}. {q}")  
          md.append("")  
    
      conflicts \= payload.get("conflicts\_and\_red\_flags", \[\]) or \[\]  
      if conflicts:  
          md.append("\#\# Конфликты и red flags\\n")  
          for c in conflicts\[:20\]:  
              t \= c.get("type", "red\_flag")  
              desc \= c.get("description", "")  
              rel \= c.get("related\_doc\_ids", \[\]) or \[\]  
              rel\_s \= ", ".join(rel) if rel else "-"  
              md.append(f"- \[{t}\] {desc} (docs: {rel\_s})")  
          md.append("")  
    
      ocr\_warn \= payload.get("ocr\_quality\_warnings", \[\]) or \[\]  
      if ocr\_warn:  
          md.append("\#\# Предупреждения по качеству OCR\\n")  
          for w in ocr\_warn\[:20\]:  
              md.append(f"- {w}")  
          md.append("")  
    
      return "\\n".join(md)  
    
    
  def render\_human\_report(payload: Dict\[str, Any\]) \-\> str:  
      """  
      Main entry: returns Markdown.  
      """  
      md \= \["\# Отчёт по достаточности доказательств (kaucja)\\n"\]  
      case\_facts \= payload.get("case\_facts", {}) or {}  
      if isinstance(case\_facts, dict):  
          md.append(render\_case\_facts(case\_facts))  
      md.append(render\_summary\_sections(payload))  
      return "\\n".join(\[x for x in md if x\])

  ### **4.3 Таблица checklist (pandas DataFrame для Gradio)**

  from \_\_future\_\_ import annotations  
    
  from typing import Any, Dict, List  
  import pandas as pd  
    
  def checklist\_to\_dataframe(payload: Dict\[str, Any\]) \-\> pd.DataFrame:  
      items: List\[Dict\[str, Any\]\] \= payload.get("checklist", \[\]) or \[\]  
      by\_id \= {it.get("item\_id"): it for it in items if isinstance(it, dict)}  
    
      rows \= \[\]  
      for item\_id in CHECKLIST\_ORDER:  
          it \= by\_id.get(item\_id, {})  
          status \= it.get("status", "missing")  
          importance \= it.get("importance", "recommended")  
          confidence \= it.get("confidence", "low")  
    
          findings \= it.get("findings", \[\]) or \[\]  
          sources \= \[\]  
          for f in findings\[:3\]:  
              doc\_id \= f.get("doc\_id", "")  
              quote \= mask\_pii(str(f.get("quote", ""))).strip()  
              if doc\_id and quote:  
                  sources.append(f"{doc\_id}: {quote}")  
              elif doc\_id:  
                  sources.append(doc\_id)  
    
          missing \= it.get("missing\_what\_exactly", "") or ""  
          ask \= ""  
          req \= it.get("request\_from\_user", {}) or {}  
          if isinstance(req, dict):  
              ask \= req.get("ask", "") or ""  
    
          rows.append({  
              "item\_id": item\_id,  
              "importance": importance,  
              "status": status,  
              "confidence": confidence,  
              "what\_it\_supports": (it.get("what\_it\_supports", "") or "")\[:200\],  
              "top\_sources": " | ".join(sources),  
              "missing\_what\_exactly": missing\[:200\],  
              "request\_to\_user": ask\[:200\],  
          })  
    
      return pd.DataFrame(rows)  
    
    
  def extract\_missing\_requests(payload: Dict\[str, Any\]) \-\> List\[str\]:  
      """  
      Convenience list for a dedicated UI panel:  
      \- all checklist items that are missing/ambiguous/conflict,  
      \- human-readable ask string.  
      """  
      res \= \[\]  
      for it in payload.get("checklist", \[\]) or \[\]:  
          status \= it.get("status")  
          if status in ("missing", "ambiguous", "conflict"):  
              item\_id \= it.get("item\_id", "?")  
              req \= (it.get("request\_from\_user", {}) or {}).get("ask", "")  
              if req:  
                  res.append(f"{item\_id}: {req}")  
              else:  
                  res.append(f"{item\_id}: требуется уточнение/документ")  
      return res  
  ---

  ### **4.4 Как это использовать в Gradio Blocks (минимальная связка)**

В pipeline после получения JSON от LLM:

1. payload \= json.loads(model\_text)

2. report\_md \= render\_human\_report(payload)

3. df \= checklist\_to\_dataframe(payload)

4. missing \= extract\_missing\_requests(payload)

5. UI показывает:

* gr.Markdown(report\_md)

* gr.Dataframe(df)

* gr.JSON(payload) (сырой JSON)

* gr.Textbox("\\n".join(missing)) или gr.Dataframe для missing.

  ---

  


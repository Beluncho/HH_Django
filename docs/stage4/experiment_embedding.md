=== ЭКСПЕРИМЕНТ: embedding ===
Цель: сравнить ранжирование тестовых фраз двумя провайдерами
Запрос: Python-разработчик
Примечание: это микробенчмарк на фиксированном наборе фраз, он не заменяет переиндексацию коллекции.

--- hash (модель local-hash-v1) ---
    +0.2500  Опыт разработки на Python и Django, понимание ORM
    +0.0000  Настройка CI/CD, Docker и Kubernetes
    +0.0000  Работа с PostgreSQL, оптимизация SQL-запросов
    +0.0000  Вёрстка интерфейсов на JavaScript и React

--- sentence_transformers (модель sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) ---
    +0.6638  Опыт разработки на Python и Django, понимание ORM
    +0.1761  Настройка CI/CD, Docker и Kubernetes
    +0.1165  Вёрстка интерфейсов на JavaScript и React
    +0.0483  Работа с PostgreSQL, оптимизация SQL-запросов

Вывод (заполнить): какая модель даёт более осмысленное ранжирование.

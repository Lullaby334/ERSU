# ERSU — Flask + Supabase PostgreSQL

Prototyp systemu rezerwacji sprzętu uczelnianego zgodny z założeniami projektu ERSU.

## Co jest gotowe

- rejestracja i logowanie użytkowników
- role: `STUDENT`, `EMPLOYEE`, `LAB_STAFF`, `ADMIN`
- katalog sprzętu z filtrowaniem
- szczegóły sprzętu + harmonogram rezerwacji
- tworzenie rezerwacji z blokadą konfliktów terminów
- anulowanie własnej rezerwacji przed rozpoczęciem
- panel laboratorium: zatwierdzanie / odrzucanie, wydanie, zwrot
- panel administratora: zarządzanie sprzętem i rolami użytkowników
- historia wypożyczeń, powiadomienia wewnętrzne, logi audytowe

## Jak uruchomić

### 1. Utwórz plik `.env`
Skopiuj `.env.example` do `.env` i wpisz swoje dane.

Najważniejsza linia:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@db.ygclulrbzfxofhvcqlpf.supabase.co:5432/postgres?sslmode=require
```

### 2. Uruchom SQL w Supabase
W `SQL Editor` uruchom:

1. `schema.sql`
2. `seed.sql` (opcjonalnie)

### 3. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 4. Start aplikacji

```bash
python app.py
```

Aplikacja uruchomi się domyślnie pod adresem `http://127.0.0.1:5000`.

## Demo-konta

Po pierwszym uruchomieniu aplikacja automatycznie doda konta demo, jeśli ich jeszcze nie ma:

- `admin@ersu.local` / `admin123`
- `lab@ersu.local` / `lab123`
- `student@ersu.local` / `student123`
- `employee@ersu.local` / `employee123`

Hasła i adresy można zmienić w `.env`.

## Uwaga o Supabase

Ten projekt używa Supabase jako zwykłego PostgreSQL. Nie korzysta z Supabase Auth ani RLS. Dzięki temu wszystko działa prosto z Flask i SQLAlchemy.

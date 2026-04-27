-- Optional demo data for ERSU
-- Run after schema.sql

insert into public.equipment (name, category, laboratory, serial_number, description, image_url, status)
values
  (
    'Oscyloskop Rigol DS1054Z',
    'Aparatura pomiarowa',
    'Laboratorium Elektroniki A-101',
    'RIG-DS1054Z-001',
    'Cyfrowy oscyloskop wykorzystywany podczas zajęć z elektroniki i diagnostyki sygnałów.',
    'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  ),
  (
    'Multimetr UNI-T UT61E',
    'Aparatura pomiarowa',
    'Laboratorium Elektroniki A-101',
    'UNI-UT61E-002',
    'Multimetr laboratoryjny do pomiaru napięcia, prądu, rezystancji i ciągłości obwodu.',
    'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  ),
  (
    'Zasilacz laboratoryjny Korad KA3005P',
    'Zasilanie',
    'Laboratorium Automatyki B-204',
    'KOR-KA3005P-003',
    'Programowalny zasilacz laboratoryjny do ćwiczeń z automatyki, elektroniki i sterowania.',
    'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  ),
  (
    'Zestaw Arduino Mega 2560',
    'Mikrokontrolery',
    'Laboratorium IoT C-110',
    'ARD-MEGA-004',
    'Zestaw dydaktyczny do laboratoriów z systemów wbudowanych, IoT i sterowania.',
    'https://images.unsplash.com/photo-1553406830-ef2513450d76?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  )
on conflict (serial_number) do nothing;

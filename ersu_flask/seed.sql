-- Optional demo data for ERSU
-- Run after schema.sql

insert into public.equipment (name, category, laboratory, serial_number, description, image_url, status)
values
  (
    'Dell Latitude 5520',
    'Laptop',
    'Lab A-101',
    'DL-5520-001',
    'Laptop do zajęć laboratoryjnych i projektów studenckich.',
    'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  ),
  (
    'Canon EOS 250D',
    'Camera',
    'Media Lab B-204',
    'CAN-250D-002',
    'Aparat do zajęć multimedialnych i dokumentacji projektów.',
    'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  ),
  (
    'Epson EB-X06',
    'Projector',
    'Lab C-110',
    'EPS-X06-003',
    'Projektor do prezentacji i zajęć seminaryjnych.',
    'https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  ),
  (
    'Mikrofon Blue Yeti',
    'Audio',
    'Podcast Room D-010',
    'BY-004',
    'Mikrofon do nagrań i laboratoriów z obróbki dźwięku.',
    'https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=1200&q=80',
    'AVAILABLE'
  )
on conflict (serial_number) do nothing;

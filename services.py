import os
import csv

def export_to_csv(data, filename):
    if not os.path.exists('export'):
        os.makedirs('export')
    filepath = os.path.join('export', filename)
    if not data:
        print("\nНемає даних для експорту.")
        return
    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"\nУспішно! Файл збережено: {filepath}")
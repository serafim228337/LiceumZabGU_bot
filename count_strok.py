import os
import re
from pathlib import Path


def count_lines_in_file(filepath):
    """Подсчёт непустых строк в файле, исключая комментарии"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    code_lines = 0
    in_multiline_comment = False

    for line in lines:
        stripped = line.strip()

        # Учитываем строку кода
        code_lines += 1

    return code_lines


def count_project_lines(root_dir):
    """Рекурсивный подсчёт строк во всех Python-файлах проекта"""
    total_lines = 0
    file_stats = []
    ignore_dirs = {'.venv', 'venv', 'env', '__pycache__'}  # Папки для игнорирования

    for root, dirs, files in os.walk(root_dir):
        # Удаляем игнорируемые папки из списка для обхода
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    lines = count_lines_in_file(filepath)
                    total_lines += lines
                    file_stats.append((filepath, lines))
                except UnicodeDecodeError:
                    print(f"Ошибка чтения файла (не UTF-8): {filepath}")
                except Exception as e:
                    print(f"Ошибка обработки файла {filepath}: {str(e)}")

    # Сортируем файлы по количеству строк
    file_stats.sort(key=lambda x: x[1], reverse=True)

    return total_lines, file_stats


def print_stats(total_lines, file_stats):
    """Вывод статистики"""
    print("\nТоп 20 самых больших файлов:")
    for i, (file, lines) in enumerate(file_stats[:20], 1):
        rel_path = os.path.relpath(file, project_dir)
        print(f"{i:2}. {lines:4} строк | {rel_path}")

    print(f"\nОбщий анализ:")
    print(f"Всего файлов: {len(file_stats)}")
    print(f"Общее количество строк кода: {total_lines}")
    avg_lines = total_lines / len(file_stats) if file_stats else 0
    print(f"Среднее количество строк на файл: {avg_lines:.1f}")


def main():
    global project_dir
    project_dir = input("Введите путь к папке проекта: ").strip('"\' ')

    if not os.path.isdir(project_dir):
        print("Ошибка: указанная папка не существует")
        return

    total, files = count_project_lines(project_dir)
    print_stats(total, files)


if __name__ == "__main__":
    main()
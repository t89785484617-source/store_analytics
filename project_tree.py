import os
import argparse
from pathlib import Path

def read_project_description(root_dir):
    """
    Читает файлы с описанием проекта и возвращает их содержимое
    """
    description_files = [
        'README.md', 'README.txt', 'README',
        'DESCRIPTION.md', 'ABOUT.md',
        '.project', 'PROJECT.md',
        'docs/README.md', 'documentation.md'
    ]
    
    descriptions = []
    
    for desc_file in description_files:
        file_path = Path(root_dir) / desc_file
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                    if content:  # Если файл не пустой
                        # Ограничиваем размер для больших файлов
                        if len(content) > 5000:
                            content = content[:5000] + "\n\n... (файл усечен, полная версия в репозитории)"
                        
                        descriptions.append(f"=== {desc_file} ===\n{content}\n")
            except Exception as e:
                descriptions.append(f"=== {desc_file} ===\n[Ошибка чтения: {e}]\n")
    
    return "\n".join(descriptions) if descriptions else "❌ Файлы с описанием проекта не найдены"

def read_config_files(root_dir):
    """
    Читает важные конфигурационные файлы
    """
    config_files = {
        'requirements.txt': '🐍 Python зависимости',
        'package.json': '📦 Node.js зависимости', 
        'pyproject.toml': '🐍 Python конфигурация',
        'setup.py': '🐍 Python установка',
        'environment.yml': '🐍 Conda окружение',
        'Dockerfile': '🐳 Docker конфигурация',
        'docker-compose.yml': '🐳 Docker Compose',
        '.env.example': '🔐 Пример переменных окружения',
        'Makefile': '⚙️ Make команды'
    }
    
    configs = []
    
    for config_file, description in config_files.items():
        file_path = Path(root_dir) / config_file
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                    if content:
                        # Для больших файлов показываем только начало
                        if len(content) > 2000:
                            content = content[:2000] + "\n... (файл усечен)"
                        configs.append(f"--- {description} ({config_file}) ---\n{content}\n")
            except Exception as e:
                configs.append(f"--- {description} ({config_file}) ---\n[Ошибка чтения: {e}]\n")
    
    return "\n".join(configs) if configs else ""

def should_ignore(path, ignore_list):
    """Проверяет, нужно ли игнорировать файл/папку"""
    path_str = str(path)
    for ignore in ignore_list:
        if ignore in path_str:
            return True
    return False

def get_file_icon(filename):
    """Возвращает иконку для типа файла"""
    ext = Path(filename).suffix.lower()
    
    icon_map = {
        '.py': '🐍', '.js': '📜', '.jsx': '⚛️', '.ts': '📘', '.tsx': '⚛️',
        '.html': '🌐', '.css': '🎨', '.scss': '🎨', '.sass': '🎨',
        '.json': '📋', '.md': '📖', '.txt': '📄', '.pdf': '📕',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.svg': '🖼️', '.mp4': '🎬', '.mp3': '🎵', '.avi': '🎬',
        '.zip': '📦', '.rar': '📦', '.tar': '📦', '.gz': '📦',
        '.exe': '⚙️', '.dll': '⚙️', '.sql': '🗃️', '.db': '🗃️',
        '.xml': '📄', '.yml': '⚙️', '.yaml': '⚙️', '.toml': '⚙️',
        '.lock': '🔒', '.env': '🔐', '.gitignore': '👁️',
        '.ipynb': '📓', '.java': '☕', '.cpp': '⚙️', '.c': '⚙️',
        '.h': '⚙️', '.php': '🐘', '.rb': '💎', '.go': '🐹',
        '.rs': '🦀', '.swift': '🐦', '.kt': '🅺', '.dart': '🎯'
    }
    
    return icon_map.get(ext, '📄')

def get_size_info(path):
    """Возвращает информацию о размере файла"""
    if path.is_file():
        size = path.stat().st_size
        if size < 1024:
            return f"({size} B)"
        elif size < 1024 * 1024:
            return f"({size // 1024} KB)"
        else:
            return f"({size // (1024 * 1024)} MB)"
    return "(dir)"

def generate_project_tree(root_dir, max_depth=None, output_file=None, include_hidden=False):
    """
    Генерирует дерево проекта
    """
    root_path = Path(root_dir)
    
    # Список файлов и папок для игнорирования
    ignore_list = [
        '__pycache__', '.pyc', '.git', 'node_modules', '.env',
        '.venv', 'venv', 'dist', 'build', '.pytest_cache',
        '.vscode', '.idea', '.DS_Store', 'package-lock.json',
        'yarn.lock', '.npm', '.cache'
    ]
    
    if not include_hidden:
        ignore_list.extend(['.', '__'])
    
    tree_lines = []
    tree_lines.append(f"📁 {root_path.name}/")
    tree_lines.append(f"📍 Путь: {root_path.absolute()}")
    tree_lines.append("")
    
    def add_directory_contents(directory, prefix="", depth=0):
        if max_depth and depth >= max_depth:
            tree_lines.append(f"{prefix}└── ... (глубина ограничена {max_depth})")
            return
            
        try:
            # Получаем все элементы и сортируем: сначала папки, потом файлы
            items = []
            for item in directory.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                if not should_ignore(item, ignore_list):
                    items.append(item)
            
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for index, item in enumerate(items):
                is_last = index == len(items) - 1
                connector = "└── " if is_last else "├── "
                
                if item.is_dir():
                    tree_lines.append(f"{prefix}{connector}📁 {item.name}/")
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    add_directory_contents(item, new_prefix, depth + 1)
                else:
                    file_icon = get_file_icon(item.name)
                    tree_lines.append(f"{prefix}{connector}{file_icon} {item.name}")
        except PermissionError:
            tree_lines.append(f"{prefix}└── 🔒 [Доступ запрещен]")
    
    add_directory_contents(root_path)
    
    # Полный результат
    full_tree = "\n".join(tree_lines)
    
    # Сохраняем в файл если указано
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_tree)
        print(f"✅ Дерево проекта сохранено в: {output_file}")
    
    return full_tree

def generate_complete_project_report(root_dir, max_depth=None, include_configs=True):
    """
    Генерирует полный отчет о проекте включая описание и конфиги
    """
    report = []
    
    # Заголовок
    report.append("=" * 60)
    report.append("🚀 ПОЛНЫЙ ОТЧЕТ О ПРОЕКТЕ ДЛЯ ИИ")
    report.append("=" * 60)
    report.append("")
    
    # Описание проекта
    report.append("📋 ОПИСАНИЕ ПРОЕКТА")
    report.append("-" * 40)
    description = read_project_description(root_dir)
    report.append(description)
    report.append("")
    
    # Конфигурационные файлы
    if include_configs:
        report.append("⚙️ КОНФИГУРАЦИОННЫЕ ФАЙЛЫ")
        report.append("-" * 40)
        configs = read_config_files(root_dir)
        report.append(configs if configs else "Конфигурационные файлы не найдены")
        report.append("")
    
    # Структура проекта
    report.append("🌳 СТРУКТУРА ПРОЕКТА")
    report.append("-" * 40)
    tree = generate_project_tree(root_dir, max_depth=max_depth, include_hidden=False)
    report.append(tree)
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Генератор дерева проекта для ИИ')
    parser.add_argument('path', nargs='?', default='.', help='Путь к проекту (по умолчанию: текущая директория)')
    parser.add_argument('-d', '--depth', type=int, help='Максимальная глубина вложенности')
    parser.add_argument('-o', '--output', help='Файл для сохранения результата')
    parser.add_argument('--hidden', action='store_true', help='Включать скрытые файлы и папки')
    parser.add_argument('--detailed', action='store_true', help='Показать детальную информацию с размерами файлов')
    parser.add_argument('--full-report', action='store_true', help='Полный отчет с описанием проекта и конфигами')
    parser.add_argument('--no-configs', action='store_true', help='Не включать конфиги в полный отчет')
    
    args = parser.parse_args()
    
    print("🌳 Генерация дерева проекта...\n")
    
    try:
        if args.full_report:
            report = generate_complete_project_report(
                root_dir=args.path,
                max_depth=args.depth,
                include_configs=not args.no_configs
            )
            print(report)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"\n✅ Полный отчет сохранен в: {args.output}")
                
        elif args.detailed:
            # Детальная версия (старая функциональность)
            from detailed_version import generate_detailed_tree  # Импорт для обратной совместимости
            tree = generate_detailed_tree(
                root_dir=args.path,
                max_depth=args.depth or 4
            )
            print(tree)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(tree)
                print(f"✅ Детальное дерево проекта сохранено в: {args.output}")
        else:
            # Базовая версия
            tree = generate_project_tree(
                root_dir=args.path,
                max_depth=args.depth,
                output_file=args.output,
                include_hidden=args.hidden
            )
            print(tree)
            print(f"\n📊 Всего строк: {len(tree.splitlines())}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
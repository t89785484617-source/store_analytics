#!/usr/bin/env python3
"""
Скрипт для отображения структуры проекта и содержимого файлов
"""

import os
import pathlib
import sys
from typing import List, Set

class ProjectExplorer:
    def __init__(self, root_dir: str = ".", max_file_size: int = 100000):
        self.root_dir = pathlib.Path(root_dir).resolve()
        self.max_file_size = max_file_size
        self.ignore_dirs = {
            '__pycache__', '.git', '.vscode', '.idea', 'node_modules',
            'venv', 'env', '.env', 'dist', 'build', '*.egg-info'
        }
        self.ignore_files = {
            '.gitignore', '.gitattributes', '*.pyc', '*.pyo', '*.so',
            '*.dll', '*.exe', '*.bin', '*.db', '*.sqlite', '*.log'
        }
        
    def should_ignore(self, path: pathlib.Path) -> bool:
        """Проверка, нужно ли игнорировать файл/директорию"""
        name = path.name
        
        # Игнорируем скрытые файлы/папки (кроме .env.example)
        if name.startswith('.') and name not in ['.env.example', '.gitignore']:
            return True
            
        # Игнорируем системные папки
        if name in self.ignore_dirs:
            return True
            
        # Игнорируем скомпилированные файлы
        if any(name.endswith(ext) for ext in ['.pyc', '.pyo', '.so']):
            return True
            
        return False
    
    def get_file_tree(self) -> str:
        """Генерация дерева директорий"""
        tree_lines = []
        
        def add_directory(dir_path: pathlib.Path, prefix: str = "", is_last: bool = True):
            nonlocal tree_lines
            
            # Добавляем текущую директорию
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{dir_path.name}/")
            
            # Новый префикс для содержимого
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            try:
                # Получаем все элементы и сортируем (директории сначала)
                items = sorted(dir_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                
                # Фильтруем элементы
                items = [item for item in items if not self.should_ignore(item)]
                
                for i, item in enumerate(items):
                    is_last_item = i == len(items) - 1
                    
                    if item.is_dir():
                        add_directory(item, new_prefix, is_last_item)
                    else:
                        connector = "└── " if is_last_item else "├── "
                        size = self.get_file_size(item)
                        tree_lines.append(f"{new_prefix}{connector}{item.name} ({size})")
                        
            except PermissionError:
                tree_lines.append(f"{new_prefix}    [Permission Denied]")
        
        tree_lines.append(f"📁 {self.root_dir.name}/")
        add_directory(self.root_dir)
        return "\n".join(tree_lines)
    
    def get_file_size(self, file_path: pathlib.Path) -> str:
        """Получение размера файла в читаемом формате"""
        try:
            size = file_path.stat().st_size
            if size == 0:
                return "empty"
            elif size < 1024:
                return f"{size}B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f}KB"
            else:
                return f"{size/(1024*1024):.1f}MB"
        except:
            return "unknown"
    
    def read_file_content(self, file_path: pathlib.Path) -> str:
        """Чтение содержимого файла"""
        try:
            if file_path.stat().st_size > self.max_file_size:
                return f"[File too large: {self.get_file_size(file_path)} - showing first 50 lines]\n" + \
                       self.read_limited_content(file_path, 50)
            
            content = file_path.read_text(encoding='utf-8')
            if not content.strip():
                return "[Empty file]"
            return content
            
        except UnicodeDecodeError:
            return f"[Binary file: {self.get_file_size(file_path)} - cannot display content]"
        except Exception as e:
            return f"[Error reading file: {str(e)}]"
    
    def read_limited_content(self, file_path: pathlib.Path, max_lines: int = 50) -> str:
        """Чтение ограниченного количества строк из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"... [showing first {max_lines} lines only]")
                        break
                    lines.append(line.rstrip())
                return "\n".join(lines)
        except:
            return "[Cannot read file content]"
    
    def get_file_extension(self, file_path: pathlib.Path) -> str:
        """Получение расширения файла для подсветки синтаксиса"""
        ext = file_path.suffix.lower()
        return {
            '.py': 'python',
            '.txt': 'text',
            '.md': 'markdown',
            '.json': 'json',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.html': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.xml': 'xml',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bat': 'batch',
            '.cfg': 'config',
            '.ini': 'config',
            '.toml': 'config'
        }.get(ext, 'text')
    
    def explore_project(self) -> str:
        """Основная функция исследования проекта"""
        output = []
        
        # Заголовок
        output.append("=" * 80)
        output.append("🚀 PROJECT STRUCTURE EXPLORER")
        output.append("=" * 80)
        output.append(f"Root directory: {self.root_dir}")
        output.append("")
        
        # Дерево файлов
        output.append("📁 PROJECT STRUCTURE:")
        output.append("")
        output.append(self.get_file_tree())
        output.append("")
        output.append("=" * 80)
        output.append("")
        
        # Содержимое файлов
        output.append("📄 FILE CONTENTS:")
        output.append("")
        
        # Собираем все файлы
        all_files = []
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file() and not self.should_ignore(file_path):
                all_files.append(file_path)
        
        # Сортируем файлы по пути
        all_files.sort(key=lambda x: x.relative_to(self.root_dir))
        
        for i, file_path in enumerate(all_files):
            relative_path = file_path.relative_to(self.root_dir)
            
            # Разделитель между файлами
            if i > 0:
                output.append("\n" + "-" * 60 + "\n")
            
            # Заголовок файла
            file_size = self.get_file_size(file_path)
            output.append(f"📄 File: {relative_path} ({file_size})")
            output.append("📏 " + "─" * min(60, len(str(relative_path)) + 15))
            
            # Содержимое файла
            content = self.read_file_content(file_path)
            output.append(content)
        
        return "\n".join(output)
    
    def save_to_file(self, output_file: str = "project_structure.txt"):
        """Сохранение результата в файл"""
        content = self.explore_project()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Project structure saved to: {output_file}")

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "project_structure.txt"
    
    # Проверяем существование директории
    if not os.path.exists(root_dir):
        print(f"❌ Error: Directory '{root_dir}' does not exist")
        sys.exit(1)
    
    print("🔍 Scanning project structure...")
    
    try:
        explorer = ProjectExplorer(root_dir)
        
        # Выводим в консоль
        print("\n" + explorer.explore_project())
        
        # Сохраняем в файл
        explorer.save_to_file(output_file)
        
        print(f"\n✅ Exploration complete! Results also saved to '{output_file}'")
        
    except Exception as e:
        print(f"❌ Error during exploration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
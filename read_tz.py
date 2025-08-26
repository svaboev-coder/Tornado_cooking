#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import docx
import sys

def read_docx(file_path):
    """Читает содержимое файла .docx"""
    try:
        doc = docx.Document(file_path)
        content = []
        
        print("=" * 80)
        print("ТЕХНИЧЕСКОЕ ЗАДАНИЕ")
        print("=" * 80)
        
        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                content.append(paragraph.text)
                print(f"{i+1:3d}. {paragraph.text}")
        
        print("=" * 80)
        print(f"Всего абзацев: {len(content)}")
        
        return content
        
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None

if __name__ == "__main__":
    tz_file = "ТЗ.docx"
    content = read_docx(tz_file)





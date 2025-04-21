# -*- coding: utf-8 -*-
import re
from collections import Counter
import pdfplumber
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
import os
import shutil

# 下载 NLTK 所需的数据
nltk.download('punkt')  # 用于分词
nltk.download('punkt_tab')  # 用于英文分词

def extract_text_from_pdf(pdf_path):
    """从 PDF 文件中提取文本，使用 pdfplumber 以保留更好的格式"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 提取文本，保留格式
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"  # 添加换行符以保持页面分隔
    return text

def save_raw_text(text, output_path):
    """保存原始文本到文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

def clean_text(text):
    """清理文本，只保留英文单词"""
    # 只保留英文字母、空格和基本标点
    text = re.sub(r'[^a-zA-Z\s.,!?]', ' ', text)
    # 转换为小写
    text = text.lower()
    # 使用 NLTK 的 word_tokenize 进行分词
    words = word_tokenize(text)
    # 只保留长度大于1的单词
    words = [word for word in words if len(word) > 1]
    return words

def count_words(words):
    """统计单词频率"""
    return Counter(words)

def process_file(input_file, output_dir):
    """处理单个文件"""
    # 获取文件名（不含扩展名）
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # 构建输出文件路径
    raw_text_path = os.path.join(output_dir, f"{base_name}.txt")
    
    # 提取文本
    text = extract_text_from_pdf(input_file)
    
    # 保存原始文本
    save_raw_text(text, raw_text_path)
    print(f"原始文本已保存到 {raw_text_path}")
    
    # 清理文本
    words = clean_text(text)
    
    # 统计词频
    word_counts = count_words(words)
    
    return word_counts

def clear_output_directory(output_dir):
    """清空输出目录"""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"已清空并创建输出目录: {output_dir}")

def main():
    # 获取目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(current_dir, 'res/input')
    output_dir = os.path.join(current_dir, 'res/output')
    
    # 确保输入目录存在
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"创建输入目录: {input_dir}")
        return
    
    # 清空并创建输出目录
    clear_output_directory(output_dir)
    
    # 存储所有文件的统计结果
    all_word_counts = Counter()
    
    # 遍历输入目录中的所有 PDF 文件
    for file in os.listdir(input_dir):
        if file.endswith('.pdf'):
            input_file = os.path.join(input_dir, file)
            print(f"\n处理文件: {file}")
            word_counts = process_file(input_file, output_dir)
            
            # 更新总词频统计
            all_word_counts.update(word_counts)
    
    # 创建汇总的 DataFrame
    output_csv = os.path.join(output_dir, 'word_counts.csv')
    df = pd.DataFrame(all_word_counts.most_common(), columns=['Word', 'Count'])
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n所有文件的词频统计结果已保存到 {output_csv}")

if __name__ == "__main__":
    main() 
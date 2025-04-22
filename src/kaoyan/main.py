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

def is_valid_word(word):
    """检查单词是否有效"""
    # 如果单词长度超过20，很可能是多个单词连在一起
    if len(word) > 10:
        return False
    
    # 检查是否包含数字
    if any(c.isdigit() for c in word):
        return False
    
    # 检查是否包含特殊字符（除了连字符和单引号）
    if not all(c.isalpha() or c in ['-', "'"] for c in word):
        return False
 
    return True

def clean_text(text):
    """清理文本，只保留英文单词"""
    # 转换为小写
    text = text.lower()
    
    # 只保留英文字母、空格、连字符和单引号
    text = re.sub(r'[^a-zA-Z\s\'-]', ' ', text)
    
    # 处理特殊情况
    # 1. 将多个空格替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    # 2. 确保连字符前后有空格（除了在单词内部）
    text = re.sub(r'(?<=\w)-(?=\w)', '', text)  # 保留单词内部的连字符
    text = re.sub(r'-', ' ', text)  # 其他连字符替换为空格
    
    # 使用正则表达式进行分词
    # 匹配英文单词（包括带连字符和缩写的单词）
    words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?(?:-[a-zA-Z]+)*\b", text)
    
    # 过滤掉长度小于2的单词和无效单词
    words = [word for word in words if len(word) > 1 and is_valid_word(word)]
    
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

def get_word_variants(word):
    """生成单词的所有可能变体形式"""
    variants = {word}
    
    # 单复数变体
    if word.endswith('s'):
        variants.add(word[:-1])  # cats -> cat
    if word.endswith('es'):
        variants.add(word[:-2])  # boxes -> box
    if word.endswith('ies'):
        variants.add(word[:-3] + 'y')  # cities -> city
    if word.endswith('ves'):
        variants.add(word[:-3] + 'f')  # leaves -> leaf
        variants.add(word[:-3] + 'fe')  # knives -> knife
    
    # 动词分词变体
    if word.endswith('ing'):
        variants.add(word[:-3])  # running -> run
        variants.add(word[:-3] + 'e')  # making -> make
    if word.endswith('ed'):
        variants.add(word[:-2])  # walked -> walk
        variants.add(word[:-2] + 'e')  # loved -> love
    if word.endswith('d'):
        variants.add(word[:-1])  # played -> play
    
    return variants

def compare_word_lists():
    """比较大纲.csv和word_counts.csv中的单词，生成差异报告"""
    # 获取目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(current_dir, 'res/input')
    output_dir = os.path.join(current_dir, 'res/output')
    
    # 读取大纲.csv
    outline_df = pd.read_csv(os.path.join(input_dir, '大纲.csv'), encoding='utf-8')
    # 创建大纲单词到其对应行的映射
    outline_dict = dict(zip(outline_df.iloc[:, 0].str.lower(), outline_df.iloc[:, 1:].values))
    
    # 读取word_counts.csv
    word_counts_df = pd.read_csv(os.path.join(output_dir, 'word_counts.csv'), encoding='utf-8')
    word_counts_dict = dict(zip(word_counts_df['Word'].str.lower(), word_counts_df['Count']))
    
    # 创建单词到基础形式的映射和计数
    word_to_base = {}
    base_word_counts = {}
    
    # 处理大纲单词
    for word in outline_dict.keys():
        # 只处理实际存在的单词
        if not is_valid_word(word):
            continue
            
        variants = get_word_variants(word)
        # 检查是否有变体已经在映射中
        found_base = None
        for variant in variants:
            if variant in word_to_base:
                found_base = word_to_base[variant]
                break
        
        if found_base is None:
            # 使用最短的形式作为基础形式
            found_base = min(variants, key=len)
            base_word_counts[found_base] = 0
        
        # 更新映射
        for variant in variants:
            word_to_base[variant] = found_base
    
    # 处理word_counts单词
    for word, count in word_counts_dict.items():
        # 只处理实际存在的单词
        if not is_valid_word(word):
            continue
            
        variants = get_word_variants(word)
        # 检查是否有变体已经在映射中
        found_base = None
        for variant in variants:
            if variant in word_to_base:
                found_base = word_to_base[variant]
                break
        
        if found_base is None:
            # 使用最短的形式作为基础形式
            found_base = min(variants, key=len)
            base_word_counts[found_base] = 0
        
        # 更新映射和计数
        for variant in variants:
            word_to_base[variant] = found_base
            # 累加变体形式的计数
            if variant in word_counts_dict:
                base_word_counts[found_base] = base_word_counts.get(found_base, 0) + word_counts_dict[variant]
    
    # 创建结果DataFrame
    result_data = []
    for base_word in sorted(base_word_counts.keys()):
        # 检查是否在大纲中存在（包括变体）
        outline_match = None
        for variant in get_word_variants(base_word):
            if variant in outline_dict:
                outline_match = outline_dict[variant]
                break
        
        # 检查是否在word_counts中存在（包括变体）
        in_word_counts = any(v in word_counts_dict for v in get_word_variants(base_word))
        
        # 只有当单词至少在一个列表中存在时才添加到结果中
        if outline_match is not None or in_word_counts:
            result_data.append({
                'Word': base_word,
                'In_Outline': outline_match is not None,
                'In_Word_Counts': in_word_counts,
                'Count': base_word_counts[base_word],
                'Column2': outline_match[0] if outline_match is not None else '',
                'Column3': outline_match[1] if outline_match is not None else ''
            })
    
    result_df = pd.DataFrame(result_data)
    
    # 保存结果
    output_path = os.path.join(output_dir, 'diff.csv')
    result_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"差异报告已保存到 {output_path}")

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
    
    # 比较单词列表
    compare_word_lists()

if __name__ == "__main__":
    main() 
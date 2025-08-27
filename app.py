from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import random, os, datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi.responses import FileResponse

app = FastAPI(title="智能宝宝起名 API", description="基于传统文化的AI智能起名系统", version="1.0.0")

class BabyInfo(BaseModel):
    surname: str
    gender: str  # male 或 female
    birthdate: str
    birth_time: Optional[str] = "12:00"
    naming_style: str = "modern"  # traditional, modern, literary, auspicious, five-elements
    expectations: Optional[List[str]] = []
    avoid_chars: Optional[str] = ""
    format: str = "json"

# 传统文化起名数据库
NAME_DATABASE = {
    "five_elements": {
        "wood": {
            "male": ['林', '森', '柏', '松', '梓', '栋', '楠', '彬', '杰', '桂'],
            "female": ['竹', '兰', '菊', '梅', '柳', '桃', '杏', '桂', '莲', '荷']
        },
        "fire": {
            "male": ['炎', '焱', '烽', '煜', '炳', '昊', '晨', '旭', '阳', '曦'],
            "female": ['晴', '暖', '晶', '曦', '炫', '烁', '焰', '丹', '彤', '朱']
        },
        "earth": {
            "male": ['坤', '垚', '培', '墨', '城', '均', '坚', '境', '岩', '峰'],
            "female": ['娅', '婉', '嫣', '瑛', '瑜', '璐', '琳', '珊', '珍', '玉']
        },
        "metal": {
            "male": ['铭', '锋', '钢', '铁', '锐', '钧', '铮', '锦', '钊', '钰'],
            "female": ['钰', '鑫', '银', '铃', '钗', '锦', '钏', '钿', '镯', '链']
        },
        "water": {
            "male": ['海', '江', '河', '湖', '波', '涛', '流', '泽', '源', '清'],
            "female": ['雨', '雪', '霜', '露', '云', '霞', '淼', '涵', '溪', '潇']
        }
    },
    "traditional": {
        "male": ['文', '武', '德', '仁', '义', '礼', '智', '信', '忠', '孝'],
        "female": ['淑', '贤', '雅', '静', '婉', '慧', '敏', '秀', '丽', '美']
    },
    "modern": {
        "male": ['轩', '宇', '浩', '博', '涵', '俊', '泽', '睿', '航', '晨'],
        "female": ['雨', '欣', '诗', '琪', '雅', '萱', '怡', '若', '婉', '梓']
    },
    "literary": {
        "male": ['诗', '书', '礼', '易', '乐', '知', '仁', '义', '信', '智'],
        "female": ['诗', '词', '画', '琴', '棋', '书', '雅', '韵', '墨', '兰']
    },
    "auspicious": {
        "male": ['福', '禄', '寿', '喜', '财', '贵', '荣', '华', '富', '康'],
        "female": ['福', '慧', '安', '宁', '康', '乐', '怡', '悦', '欣', '喜']
    }
}

def calculate_bazi(birthdate, birth_time):
    """计算生辰八字（简化版）"""
    elements = ['wood', 'fire', 'earth', 'metal', 'water']
    element_names = {'wood': '木', 'fire': '火', 'earth': '土', 'metal': '金', 'water': '水'}
    
    date_sum = sum(int(d) for d in birthdate.replace('-', '') if d.isdigit())
    lacking = elements[date_sum % 5]
    strong = elements[(date_sum + 2) % 5]
    
    return {
        'lacking': lacking,
        'strong': strong,
        'lacking_name': element_names[lacking],
        'strong_name': element_names[strong],
        'analysis': f"根据出生时间分析，五行中{element_names[lacking]}偏弱，{element_names[strong]}较旺。"
    }

def generate_names(info: BabyInfo):
    """智能生成名字"""
    bazi = calculate_bazi(info.birthdate, info.birth_time)
    names = []
    
    # 根据风格选择字库
    if info.naming_style == 'five-elements':
        character_pool = NAME_DATABASE['five_elements'][bazi['lacking']][info.gender]
    else:
        character_pool = NAME_DATABASE.get(info.naming_style, NAME_DATABASE['modern'])[info.gender]
    
    # 过滤避讳字符
    if info.avoid_chars:
        character_pool = [char for char in character_pool if char not in info.avoid_chars]
    
    # 生成10个候选名字
    for i in range(10):
        char1 = random.choice(character_pool)
        char2 = random.choice(character_pool) if random.random() > 0.6 else ''
        
        full_name = info.surname + char1 + char2
        score = 75 + random.randint(0, 20)  # 基础分75-95
        
        if info.naming_style == 'five-elements':
            score += 5
        
        names.append({
            'name': full_name,
            'score': min(100, score),
            'meaning': f"{char1}寓意美好，{char2 if char2 else ''}象征吉祥",
            'characters': char1 + char2
        })
    
    names.sort(key=lambda x: x['score'], reverse=True)
    return names, bazi

@app.post("/api/generate-name-report")
def generate_name_report(info: BabyInfo):
    # 智能生成名字
    names, bazi = generate_names(info)
    best_name = names[0]['name'] if names else f"{info.surname}智"
    
    result = {
        "surname": info.surname,
        "gender": info.gender,
        "birthdate": info.birthdate,
        "birth_time": info.birth_time,
        "naming_style": info.naming_style,
        "recommended_names": [n['name'] for n in names[:5]],
        "best_name": best_name,
        "best_score": names[0]['score'] if names else 85,
        "best_meaning": names[0]['meaning'] if names else "智慧聪明，寓意美好",
        "bazi_analysis": bazi,
        "detailed_names": names[:5]
    }

    if info.format == "pdf":
        filename = f"naming_report_{info.surname}_{info.gender}_{info.birthdate.replace('-', '')}.pdf"
        filepath = os.path.join("/tmp", filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # 标题
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height-50, "🌱 智能宝宝起名报告")
        
        # 基本信息
        c.setFont("Helvetica", 12)
        y_position = height - 100
        
        basic_info = [
            f"姓氏: {info.surname}",
            f"性别: {'男孩' if info.gender == 'male' else '女孩'}",
            f"出生日期: {info.birthdate}",
            f"出生时间: {info.birth_time}",
            f"起名风格: {info.naming_style}"
        ]
        
        for info_line in basic_info:
            c.drawString(50, y_position, info_line)
            y_position -= 20
        
        # 五行分析
        y_position -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "☘️ 五行命理分析")
        y_position -= 20
        
        c.setFont("Helvetica", 12)
        c.drawString(50, y_position, result['bazi_analysis']['analysis'])
        y_position -= 20
        c.drawString(50, y_position, f"五行缺失: {result['bazi_analysis']['lacking_name']}")
        y_position -= 20
        c.drawString(50, y_position, f"五行旺盛: {result['bazi_analysis']['strong_name']}")
        y_position -= 30
        
        # 最佳名字
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "✨ AI推荐最佳名字")
        y_position -= 20
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, f"🏆 {result['best_name']} (评分: {result['best_score']}分)")
        y_position -= 20
        
        c.setFont("Helvetica", 12) 
        c.drawString(50, y_position, f"寓意: {result['best_meaning']}")
        y_position -= 30
        
        # 其他推荐
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "🎆 其他候选名字")
        y_position -= 20
        
        c.setFont("Helvetica", 12)
        for i, name_info in enumerate(result['detailed_names'][1:5], 1):
            c.drawString(50, y_position, f"{i+1}. {name_info['name']} (评分: {name_info['score']}分)")
            y_position -= 15
            c.drawString(70, y_position, f"寓意: {name_info['meaning'][:40]}...")
            y_position -= 20
        
        # 页脚
        c.setFont("Helvetica", 10)
        c.drawString(50, 50, f"报告生成时间: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        c.drawString(50, 35, "禹意生活 - 东方智慧测算")
        
        c.save()
        return FileResponse(filepath, filename=filename, media_type="application/pdf")

    return result

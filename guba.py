import requests
from bs4 import BeautifulSoup
import time
import csv  # 导入 csv 模块

def get_guba_titles(stock_code, pages=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'Cookie': 'rankpromt=1; st_si=05887098178896; qgqp_b_id=772c1f0eee811fb0a495dca38f4b5e65; fullscreengg=1; fullscreengg2=1; st_pvi=13788631049269; st_sp=2025-04-14%2010%3A16%3A57; st_inirUrl=https%3A%2F%2Fguba.eastmoney.com%2Frank%2F; st_sn=6; st_psi=20250414101921150-117001356556-0660930737; st_asi=delete',
        'Referer': 'https://guba.eastmoney.com/'
    }

    all_titles = []
    
    for page in range(1, pages+1):
        url = f'https://guba.eastmoney.com/list,{stock_code}_{page}.html'
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 检查请求是否成功
            response.encoding = 'utf-8'  # 确保使用正确的编码
            soup = BeautifulSoup(response.text, 'lxml')  # 建议使用 lxml 解析器
            
            # 查找包含标题的 <a> 标签，这些标签位于 class="title" 的 div 内
            # 注意：网站结构可能变化，需要定期检查选择器是否仍然有效
            title_tags = soup.select('div.title a') 
            
            # 提取 <a> 标签的文本内容
            # 过滤掉可能的广告或其他非标题链接（例如，没有 href 或 href 指向 javascript）
            page_titles = [
                a.get_text(strip=True) 
                for a in title_tags 
                if a.has_attr('href') and a['href'].startswith('/news,')  # 根据实际链接格式调整过滤条件
            ]
            
            if not page_titles:
                # 尝试查找另一种可能的结构（如果页面布局变化）
                # 例如，有时标题可能在不同的选择器下
                # 注意：网站结构可能变化，需要定期检查选择器是否仍然有效
                alternative_titles = soup.select('div.articleh.normal_post > span.l3 > a')  # 修正选择器语法错误
                if alternative_titles:
                     page_titles = [
                        a.get_text(strip=True) 
                        for a in alternative_titles 
                        if a.has_attr('href') and a['href'].startswith('/news,')  # 同样需要过滤
                    ]
                
                if not page_titles:
                    print(f'第 {page} 页未找到标题数据，可能已到达末页或页面结构已更改。')
                    break  # 如果两种方式都找不到，则停止
                
            all_titles.extend(page_titles)
            print(f'已爬取第 {page} 页，找到 {len(page_titles)} 条标题')
            
            # 添加随机延迟避免被封
            time.sleep(1.5 + time.time() % 1)  # 稍微随机化延迟
            
        except requests.exceptions.RequestException as e:
            print(f'请求第 {page} 页时出错: {str(e)}')
            break
        except Exception as e:
            print(f'处理第 {page} 页时出错: {str(e)}')
            break
            
    return all_titles

# 使用示例
if __name__ == '__main__':
    # 中芯国际 岭南控股 立讯精密
    stock_codes = ['688981', '000524', '002475']

    for stock_code in stock_codes:
        print(f"\n--- 开始爬取股票代码: {stock_code} ---")
        titles = get_guba_titles(stock_code, pages=3)  # 减少页数以便测试和演示
        if titles:
            print(f'\n--- 股票代码 {stock_code} 爬取到的标题 ---')
            print(f'--- 共爬取 {len(titles)} 条标题 ---')

            # 保存标题到 CSV 文件
            title_name = f'{stock_code}_titles.csv'
            try:
                # 使用 'w' 模式打开文件，指定 newline='' 防止空行，encoding='utf-8-sig' 确保 Excel 正确识别中文
                with open(title_name, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Title'])  # 写入表头
                    for title in titles:
                        writer.writerow([title])  # 将每个标题作为一行写入
                print(f'标题已保存到 {title_name}')
            except IOError as e:
                print(f"写入文件 {title_name} 时出错: {e}")
            except Exception as e:
                print(f"处理文件 {title_name} 时发生未知错误: {e}")

        else:
            print(f'\n未能为股票代码 {stock_code} 爬取到任何标题。')

        # 在处理下一个股票代码前稍作停顿，避免请求过于频繁
        time.sleep(2 + time.time() % 1)

    print("\n--- 所有股票代码处理完毕 ---")
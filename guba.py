import requests
from bs4 import BeautifulSoup
import time
import csv  # 导入 csv 模块

# 函数重命名以反映其功能扩展
def get_guba_posts(stock_code, pages=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        # Cookie 可能需要定期更新
        'Cookie': 'rankpromt=1; qgqp_b_id=772c1f0eee811fb0a495dca38f4b5e65; fullscreengg=1; fullscreengg2=1; st_si=80898044280764; st_pvi=13788631049269; st_sp=2025-04-14%2010%3A16%3A57; st_inirUrl=https%3A%2F%2Fguba.eastmoney.com%2Frank%2F; st_sn=1; st_psi=20250414135032194-117001356556-3694883848; st_asi=delete',
        'Referer': 'https://guba.eastmoney.com/'
    }

    all_posts_data = [] # 用于存储所有帖子数据 (阅读量, 标题, 时间)
    
    for page in range(1, pages+1):
        url = f'https://guba.eastmoney.com/list,{stock_code}_{page}.html'
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 查找包含帖子信息的 tr 标签
            post_rows = soup.select('tbody.listbody tr.listitem')
            
            page_posts = []
            if post_rows:
                for row in post_rows:
                    read_tag = row.select_one('div.read')
                    title_tag = row.select_one('div.title a')
                    update_tag = row.select_one('div.update')
                    
                    # 确保所有需要的标签都存在，并且标题链接是有效的帖子链接
                    if read_tag and title_tag and update_tag and title_tag.has_attr('href') and title_tag['href'].startswith('/news,'):
                        read_count = read_tag.get_text(strip=True)
                        title = title_tag.get_text(strip=True)
                        update_time = update_tag.get_text(strip=True)
                        page_posts.append({'read_count': read_count, 'title': title, 'update_time': update_time})
            
            # 如果主要选择器未找到数据，可以尝试备用选择器（如果网站结构有多种可能）
            # 注意：备用选择器逻辑需要根据实际情况调整，这里仅作示例保留
            if not page_posts:
                 # 尝试查找另一种可能的结构，例如针对置顶帖或不同类型的帖子
                 # 注意：这里的备用选择器 'div.articleh.normal_post' 看起来不像是行选择器，需要根据实际HTML调整
                 alternative_rows = soup.select('div.articleh.normal_post') # 示例，需要根据实际HTML调整
                 if alternative_rows:
                     print(f'第 {page} 页尝试备用选择器...')
                     # 此处需要添加从 alternative_rows 提取数据的逻辑
                     # ... (根据 alternative_rows 的结构编写提取代码) ...
                     pass # 占位符

                 if not page_posts: # 如果备用逻辑也没有提取到数据
                    print(f'第 {page} 页未找到帖子数据，可能已到达末页或页面结构已更改。')
                    break

            all_posts_data.extend(page_posts)
            print(f'已爬取第 {page} 页，找到 {len(page_posts)} 条帖子数据')
            
            time.sleep(1.5 + time.time() % 1)
            
        except requests.exceptions.RequestException as e:
            print(f'请求第 {page} 页时出错: {str(e)}')
            break
        except Exception as e:
            print(f'处理第 {page} 页时出错: {str(e)}')
            break
            
    return all_posts_data

# 使用示例
if __name__ == '__main__':
    stock_codes = ['688981', '000524', '002475']

    for stock_code in stock_codes:
        print(f"\n--- 开始爬取股票代码: {stock_code} ---")
        # 调用更新后的函数
        posts_data = get_guba_posts(stock_code, pages=7) 
        if posts_data:
            print(f'\n--- 股票代码 {stock_code} 爬取到的数据 ---')
            # 可以选择性打印部分数据进行预览
            # for i, post in enumerate(posts_data[:5], 1): # 打印前5条
            #     print(f"{i}. 阅读: {post['read_count']}, 标题: {post['title']}, 时间: {post['update_time']}")
            print(f'--- 共爬取 {len(posts_data)} 条帖子数据 ---')

            # 保存数据到 CSV 文件
            file_name = f'{stock_code}_posts_data.csv' # 更新文件名
            try:
                with open(file_name, 'w', newline='', encoding='utf-8-sig') as f:
                    # 定义表头
                    fieldnames = ['read_count', 'title', 'update_time']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    
                    writer.writeheader()  # 写入表头
                    writer.writerows(posts_data) # 写入数据行
                print(f'数据已保存到 {file_name}')
            except IOError as e:
                print(f"写入文件 {file_name} 时出错: {e}")
            except Exception as e:
                 print(f"处理文件 {file_name} 时发生未知错误: {e}")

        else:
            print(f'\n未能为股票代码 {stock_code} 爬取到任何帖子数据。')

        time.sleep(2 + time.time() % 1)

    print("\n--- 所有股票代码处理完毕 ---")